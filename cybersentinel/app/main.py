from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Depends
from pydantic import BaseModel
from typing import Dict, Any, Optional
import logging
import io
import re
import os
import string
import time
import resource

try:
    import PyPDF2
except ImportError:
    PyPDF2 = None

from app.core.config import settings
from app.core.memory import memory
from app.core.vault import vault
from app.core.tenant import TenantContext, DEFAULT_TENANT
from app.core.engine import supervisor, AgentState
from app.core.queue import task_queue, TaskStatus
from app.core.plugin_loader import plugin_loader
from app.core.database import init_chromadb
from app.utils.masking import mask_pii
from app.utils.reporter import generate_executive_report, generate_technical_report
from app.plugins.ticketing import TicketingManager
from app.core.security import get_api_key
from app.core.resilience import get_circuit_breaker

from app.tools.log_correlator import correlate_logs_tool
from app.tools.analyst_tool import analyze_log_tool
from app.tools.skeptic_tool import challenge_analysis_tool
from app.tools.judge_tool import make_verdict_tool
from app.tools.memory_consolidator import consolidate_memory
from app.tools.blue_team import blue_team_analyze
from app.tools.red_team import red_team_analyze
from app.tools.purple_team import purple_team_analyze
from app.core.skill_engine import skill_engine
from app.core.scheduler import scheduler

from app.gateways import MultiChannelGateway
from app.gateways.telegram import TelegramGateway
from app.gateways.discord import DiscordGateway
from app.gateways.slack import SlackGateway

from config.infra_adapter import Infra

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

logger = logging.getLogger(__name__)

_start_time = time.time()

app = FastAPI(
    title="CyberSentinel AI - Autonomous Agentic SOC",
    description="AI-Native Self-Learning Security Operations Center",
    version="1.0.0")


class AlertWebhook(BaseModel):
    alert_id: str
    description: str
    raw_data: str
    risk_score: Optional[int] = None
    source: Optional[str] = "splunk"
    timestamp: Optional[str] = None
    org_id: Optional[str] = "default_org"
    user_id: Optional[str] = "default_user"


class AnalyzeResponse(BaseModel):
    alert_id: str
    verdict: str
    masked_log: str
    analyst_report: str
    skeptic_report: str
    judge_reasoning: str
    remediation: str
    correlation: str
    playbook_refs: list
    executive_report: str
    technical_report: str
    ticketing_result: Dict[str, Any]


class IngestResponse(BaseModel):
    alert_id: str
    task_id: str
    status: str
    message: str


class TaskStatusResponse(BaseModel):
    task_id: str
    status: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class FeedbackWebhook(BaseModel):
    alert_id: str
    raw_log: str
    verdict: str
    is_correct: bool
    reason: str


ticketing_manager = None
multi_channel_gateway = MultiChannelGateway()


def get_log_fingerprint(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', '[IP]', text)
    text = re.sub(r'\d+', '', text)
    text = text.translate(str.maketrans('', '', string.punctuation))
    return " ".join(text.lower().split())


@app.on_event("startup")
async def startup_event():
    global ticketing_manager
    logger.info("[STARTUP] Initializing CyberSentinel AI v1.0.0...")

    init_chromadb()
    logger.info("[STARTUP] ChromaDB initialized with playbooks")

    ticketing_manager = TicketingManager()
    logger.info("[STARTUP] Ticketing manager initialized")

    supervisor.register_tool("correlate_logs", correlate_logs_tool)
    supervisor.register_tool("analyze_log", analyze_log_tool)
    supervisor.register_tool("challenge_analysis", challenge_analysis_tool)
    supervisor.register_tool("make_verdict", make_verdict_tool)
    supervisor.register_tool("consolidate_memory", consolidate_memory)
    logger.info("[STARTUP] Agent tools registered")

    plugin_loader.discover_and_load()
    logger.info("[STARTUP] Plugins loaded")

    await scheduler.start()
    logger.info("[STARTUP] Background scheduler started")

    if settings.enable_social_gateway:
        if settings.telegram_bot_token:
            tg = TelegramGateway()
            multi_channel_gateway.register(tg)
            logger.info("[STARTUP] Telegram gateway registered")

        if settings.discord_webhook_url:
            dc = DiscordGateway()
            multi_channel_gateway.register(dc)
            logger.info("[STARTUP] Discord gateway registered")

        if settings.slack_webhook_url:
            sl = SlackGateway()
            multi_channel_gateway.register(sl)
            logger.info("[STARTUP] Slack gateway registered")

        start_results = await multi_channel_gateway.start_all()
        logger.info(f"[STARTUP] Social gateways started: {start_results}")
    else:
        logger.info("[STARTUP] Social gateway disabled (set ENABLE_SOCIAL_GATEWAY=true to enable)")

    logger.info("[STARTUP] CyberSentinel AI v1.0.0 ready.")


@app.get("/")
async def root():
    return {
        "service": "CyberSentinel AI",
        "version": "1.0.0",
        "status": "operational",
        "architecture": "AI-Native Agentic SOC"
    }


async def _process_alert(webhook: AlertWebhook) -> Dict[str, Any]:
    tenant = TenantContext(user_id=webhook.user_id, org_id=webhook.org_id)
    masked_log = mask_pii(webhook.raw_data)

    state = AgentState(
        alert_id=webhook.alert_id,
        masked_log=masked_log,
        source=webhook.source or "splunk"
    )

    final_state = await supervisor.run(state, tenant)

    risk_level = "High" if webhook.risk_score and webhook.risk_score > 75 else "Medium"
    if final_state.verdict == "False Positive":
        risk_level = "Low"

    try:
        memory.save_incident(
            raw_log=masked_log,
            analysis={
                "alert_id": webhook.alert_id,
                "risk_level": risk_level,
                "category": "General",
                "summary": final_state.remediation[:200] if final_state.remediation else "Analyzed",
                "source_type": webhook.source
            },
            tenant=tenant
        )
    except Exception as db_err:
        logger.error(f"Database save failed: {db_err}")

    plugin_loader.notify_all("alert_analyzed", {
        "alert_id": webhook.alert_id,
        "verdict": final_state.verdict,
        "risk_level": risk_level
    })

    if risk_level in ("High", "Critical") or (webhook.risk_score and webhook.risk_score > 75):
        try:
            await multi_channel_gateway.broadcast_alert({
                "title": f"Alert {webhook.alert_id}",
                "severity": risk_level.lower(),
                "description": webhook.description,
                "source": webhook.source,
                "timestamp": webhook.timestamp or time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "iocs": [],
                "recommended_actions": [final_state.remediation[:200]] if final_state.remediation else [],
            })
        except Exception as gw_err:
            logger.error(f"Gateway broadcast failed: {gw_err}")

    return {
        "alert_id": webhook.alert_id,
        "verdict": final_state.verdict,
        "masked_log": masked_log,
        "analyst_report": final_state.analyst_report,
        "skeptic_report": final_state.skeptic_report,
        "judge_reasoning": final_state.judge_reasoning,
        "remediation": final_state.remediation,
        "correlation": final_state.correlation,
        "playbook_refs": final_state.playbook_refs,
        "risk_level": risk_level
    }


@app.post("/v1/ingest",
          response_model=IngestResponse,
          dependencies=[Depends(get_api_key)])
async def ingest_alert(webhook: AlertWebhook):
    try:
        current_fp = get_log_fingerprint(webhook.raw_data)
        tenant = TenantContext(user_id=webhook.user_id, org_id=webhook.org_id)
        recent_cases = memory.get_recent_incidents(limit=50, tenant=tenant)

        for case in recent_cases:
            if get_log_fingerprint(case.get('raw_log', '')) == current_fp:
                return IngestResponse(
                    alert_id=webhook.alert_id,
                    task_id="duplicate",
                    status="skipped",
                    message="Identical attack pattern detected. Skipping to prevent DB spam.")

        task_id = await task_queue.enqueue(_process_alert(webhook))

        return IngestResponse(
            alert_id=webhook.alert_id,
            task_id=task_id,
            status="queued",
            message="Alert queued for analysis. Poll /v1/task/{task_id} for results.")

    except Exception as e:
        logger.error(f"Ingest error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/v1/task/{task_id}",
         response_model=TaskStatusResponse,
         dependencies=[Depends(get_api_key)])
async def get_task_status(task_id: str):
    task = task_queue.get_status(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    return TaskStatusResponse(
        task_id=task.task_id,
        status=task.status.value,
        result=task.result,
        error=task.error
    )


@app.post("/analyze",
          response_model=AnalyzeResponse,
          dependencies=[Depends(get_api_key)])
async def analyze_alert(webhook: AlertWebhook):
    try:
        result = await _process_alert(webhook)

        alert_data = {
            "alert_id": webhook.alert_id,
            "description": webhook.description,
            "raw_data": result["masked_log"],
            "risk_score": webhook.risk_score,
            "source": webhook.source,
            "timestamp": webhook.timestamp
        }

        reasoning = {
            "analyst": result.get("analyst_report", ""),
            "skeptic": result.get("skeptic_report", ""),
            "judge": result.get("judge_reasoning", ""),
            "remediation": result.get("remediation", ""),
            "correlation": result.get("correlation", "")
        }

        executive_report = generate_executive_report(
            verdict=result["verdict"],
            alert_data=alert_data,
            reasoning=reasoning)

        technical_report = generate_technical_report(
            verdict=result["verdict"],
            alert_data=alert_data,
            reasoning=reasoning,
            playbook_refs=result.get("playbook_refs", []))

        report_payload = {
            "alert_id": webhook.alert_id,
            "verdict": result["verdict"],
            "executive_report": executive_report,
            "technical_report": technical_report,
            "masked_log": result["masked_log"],
            "reasoning": reasoning
        }

        ticketing_result = ticketing_manager.dispatch_ticket(report_payload)

        return AnalyzeResponse(
            alert_id=webhook.alert_id,
            verdict=result["verdict"],
            masked_log=result["masked_log"],
            analyst_report=result.get("analyst_report", ""),
            skeptic_report=result.get("skeptic_report", ""),
            judge_reasoning=result.get("judge_reasoning", ""),
            remediation=result.get("remediation", ""),
            correlation=result.get("correlation", ""),
            playbook_refs=result.get("playbook_refs", []),
            executive_report=executive_report,
            technical_report=technical_report,
            ticketing_result=ticketing_result)

    except Exception as e:
        logger.error(f"Error processing alert: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/confirm-verdict", dependencies=[Depends(get_api_key)])
async def confirm_verdict(feedback: FeedbackWebhook):
    try:
        memory.add_to_memory(
            alert_id=feedback.alert_id,
            raw_log=feedback.raw_log,
            verdict=feedback.verdict,
            is_correct=feedback.is_correct,
            reason=feedback.reason)
        return {"status": "success", "message": "Feedback integrated into memory."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/upload-knowledge", dependencies=[Depends(get_api_key)])
async def upload_knowledge(file: UploadFile = File(...),
                           doc_id: str = Form(...)):
    try:
        content = ""
        if file.filename.endswith(".pdf"):
            if not PyPDF2:
                raise Exception("PyPDF2 is not installed.")
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(await file.read()))
            for page in pdf_reader.pages:
                text = page.extract_text()
                if text:
                    content += text + "\n"
        else:
            content = (await file.read()).decode("utf-8")

        memory.add_document(doc_id=doc_id,
                            text=content,
                            metadata={"filename": file.filename})
        return {"status": "success", "message": f"Document {file.filename} added to knowledge base."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/v1/vault/audit", dependencies=[Depends(get_api_key)])
async def vault_audit():
    return {"audit_log": vault.get_audit_log()}


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": "1.0.0",
        "architecture": "AI-Native Agentic",
        "chromadb": "connected",
        "groq": "configured",
        "ticketing_plugin": ticketing_manager.plugin_type if ticketing_manager else "uninitialized",
        "agents": ["analyst", "skeptic", "judge", "blue_team", "red_team", "purple_team"],
        "tools": list(supervisor.tools.keys()),
        "plugins": plugin_loader.get_loaded(),
        "learning_mode": memory.enabled,
        "queue_workers": task_queue._max_workers,
        "gateways": multi_channel_gateway.get_status(),
    }


@app.get("/v1/health/pro", dependencies=[Depends(get_api_key)])
async def health_pro():
    uptime_seconds = time.time() - _start_time
    days = int(uptime_seconds // 86400)
    hours = int((uptime_seconds % 86400) // 3600)
    minutes = int((uptime_seconds % 3600) // 60)

    try:
        usage = resource.getrusage(resource.RUSAGE_SELF)
        memory_mb = usage.ru_maxrss / 1024
    except Exception:
        memory_mb = 0

    queue_metrics = task_queue.get_metrics()

    agent_tools = list(supervisor.tools.keys())
    agent_responsive = len(agent_tools) >= 5

    groq_cb = get_circuit_breaker("groq")

    gateway_status = multi_channel_gateway.get_status()

    return {
        "status": "operational",
        "version": "1.0.0",
        "uptime": f"{days}d {hours}h {minutes}m",
        "uptime_seconds": round(uptime_seconds, 1),
        "memory": {
            "rss_mb": round(memory_mb, 1),
        },
        "queue": queue_metrics,
        "agents": {
            "registered_tools": len(agent_tools),
            "responsive": agent_responsive,
            "squads": ["blue", "red", "purple"],
        },
        "vault": {
            "tokens_stored": len(vault._vault),
            "audit_entries": vault.audit_log_count,
        },
        "gateways": gateway_status,
        "circuit_breakers": {
            "groq": groq_cb.get_status(),
        },
        "scheduler": {
            "active_jobs": len([j for j in scheduler.list_jobs() if j.get("enabled")]),
            "total_jobs": len(scheduler.list_jobs()),
        },
        "skills": {
            "loaded": len(skill_engine.list_skills()),
        },
    }


@app.get("/v1/infra/status")
async def infra_status():
    return Infra.get_config()


@app.get("/v1/gateways/status")
async def gateways_status():
    return multi_channel_gateway.get_status()


@app.post("/v1/gateways/test", dependencies=[Depends(get_api_key)])
async def test_gateway(data: Dict[str, Any] = {}):
    gateway_name = data.get("gateway", "telegram")
    gw = multi_channel_gateway.get_gateway(gateway_name)
    if not gw:
        available = [g["name"] for g in multi_channel_gateway.list_gateways()]
        return {
            "success": False,
            "error": f"Gateway '{gateway_name}' not registered. Available: {available}"
        }

    try:
        result = await gw.send_message(
            f"CyberSentinel Gateway Test - {time.strftime('%Y-%m-%d %H:%M:%S UTC')}"
        )
        return {
            "success": result,
            "gateway": gateway_name,
            "status": gw.get_status()
        }
    except Exception as e:
        return {
            "success": False,
            "gateway": gateway_name,
            "error": str(e)
        }


class AgentRunRequest(BaseModel):
    squad: str
    task: str


class SkillGenerateRequest(BaseModel):
    name: str
    description: str


class CronJobRequest(BaseModel):
    name: str
    schedule: str
    squad: str
    task: str


@app.post("/v1/agents/run", dependencies=[Depends(get_api_key)])
async def run_agent_squad(req: AgentRunRequest):
    squad_map = {
        "blue": blue_team_analyze,
        "red": red_team_analyze,
        "purple": purple_team_analyze,
    }

    handler = squad_map.get(req.squad)
    if not handler:
        raise HTTPException(status_code=400, detail=f"Unknown squad: {req.squad}")

    raw = handler(req.task)
    if isinstance(raw, dict):
        result_text = raw.get("result", str(raw))
        status_text = raw.get("status", "complete")
    else:
        result_text = str(raw)
        status_text = "complete"

    return {
        "agent": f"{req.squad}_team",
        "result": result_text,
        "status": status_text,
    }


@app.get("/v1/skills", dependencies=[Depends(get_api_key)])
async def list_skills():
    return skill_engine.list_skills()


@app.post("/v1/skills/generate", dependencies=[Depends(get_api_key)])
async def generate_skill(req: SkillGenerateRequest):
    result = skill_engine.generate_skill(req.name, req.description)
    return result


@app.get("/v1/cron", dependencies=[Depends(get_api_key)])
async def list_cron_jobs():
    return scheduler.list_jobs()


@app.post("/v1/cron", dependencies=[Depends(get_api_key)])
async def create_cron_job(req: CronJobRequest):
    import uuid
    job_id = f"cron-{str(uuid.uuid4())[:8]}"
    job = scheduler.add_job(job_id, req.name, req.schedule, req.squad, req.task)
    return job.to_dict()


@app.patch("/v1/cron/{job_id}/toggle", dependencies=[Depends(get_api_key)])
async def toggle_cron_job(job_id: str):
    job = scheduler.toggle_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job.to_dict()


@app.delete("/v1/cron/{job_id}", dependencies=[Depends(get_api_key)])
async def delete_cron_job(job_id: str):
    scheduler.remove_job(job_id)
    return {"status": "deleted"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
