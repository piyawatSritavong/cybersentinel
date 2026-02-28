import logging
import asyncio
import json
import time
from typing import Dict, Any, Optional
from pydantic import BaseModel
from app.core.config import settings
from app.core.tenant import TenantContext, DEFAULT_TENANT
from app.core.memory import memory
from app.core.normalizer import Normalizer

logger = logging.getLogger(__name__)


class AgentState(BaseModel):
    """Immutable state passed through the ReAct reasoning loop."""
    alert_id: str = "unknown"
    masked_log: str = ""
    source: str = "splunk"
    context: str = ""
    correlation: str = ""
    analyst_report: str = ""
    skeptic_report: str = ""
    verdict: str = ""
    judge_reasoning: str = ""
    remediation: str = ""
    playbook_refs: list = []
    lessons_learned: str = ""
    step: str = "init"
    error: Optional[str] = None


class AgentSupervisor:
    """
    Autonomous Supervisor Agent using a ReAct (Reason + Act) loop.
    Orchestrates the multi-agent workflow with tool calls,
    memory retrieval, and exponential backoff on rate limits.
    """

    def __init__(self):
        self.max_retries = 3
        self.tools = {}

    def register_tool(self, name: str, fn):
        """Register an atomic tool for the supervisor to call."""
        self.tools[name] = fn
        logger.info(f"[ENGINE] Registered tool: {name}")

    async def _call_tool(self, name: str, **kwargs) -> Any:
        """Call a registered tool with exponential backoff on failure."""
        fn = self.tools.get(name)
        if not fn:
            return f"Tool '{name}' not found."

        for attempt in range(self.max_retries):
            try:
                if asyncio.iscoroutinefunction(fn):
                    result = await fn(**kwargs)
                else:
                    loop = asyncio.get_event_loop()
                    result = await loop.run_in_executor(None, lambda: fn(**kwargs))
                return result
            except Exception as e:
                wait = 2 ** attempt
                logger.warning(
                    f"[ENGINE] Tool '{name}' failed (attempt {attempt+1}/{self.max_retries}): {e}. Retrying in {wait}s..."
                )
                await asyncio.sleep(wait)

        return f"Tool '{name}' failed after {self.max_retries} retries."

    async def run(self, state: AgentState,
                  tenant: TenantContext = DEFAULT_TENANT) -> AgentState:
        """
        Execute the full ReAct reasoning loop:
        1. RETRIEVE - Search memory for similar cases and playbooks
        2. CORRELATE - Cross-reference with recent incidents
        3. ANALYZE - Analyst Agent investigation
        4. CHALLENGE - Skeptic Agent adversarial review
        5. DECIDE - Judge Agent final verdict with remediation
        6. CONSOLIDATE - Save lessons learned to memory
        """
        logger.info(f"[ENGINE] Starting ReAct loop for alert: {state.alert_id}")

        # Step 1: RETRIEVE
        state.step = "retrieve"
        logger.info("[ENGINE] Step 1: RETRIEVE - Searching memory...")
        memory.log_incident(state.alert_id, state.masked_log, state.source, tenant)

        raw_log_dict = {"raw_data": state.masked_log, "alert_id": state.alert_id}
        normalized_log = Normalizer.to_ocsf(raw_log_dict, state.source)
        normalized_json = normalized_log.model_dump_json()

        similar_incidents = memory.get_similar_cases(normalized_json)
        company_docs = memory.get_company_docs(normalized_json)

        context_str = ""
        if similar_incidents:
            context_str += "PREVIOUS SIMILAR CASES (Confirmed by Human):\n" + "\n".join(
                similar_incidents) + "\n\n"
        if company_docs:
            context_str += "OFFICIAL POLICIES/DOCS:\n" + "\n".join(company_docs) + "\n\n"
        state.context = context_str

        # Step 2: CORRELATE
        state.step = "correlate"
        logger.info("[ENGINE] Step 2: CORRELATE - Cross-referencing incidents...")
        correlation_result = await self._call_tool(
            "correlate_logs",
            current_log=normalized_json,
            recent_incidents=memory.get_recent_incidents(limit=5, tenant=tenant)
        )
        state.correlation = str(correlation_result)
        state.context += "LOG CORRELATION ANALYSIS:\n" + state.correlation + "\n\n"

        # Step 3: ANALYZE
        state.step = "analyze"
        logger.info("[ENGINE] Step 3: ANALYZE - Analyst Agent investigating...")
        analyst_result = await self._call_tool(
            "analyze_log",
            log_text=state.masked_log,
            context=state.context
        )
        if isinstance(analyst_result, dict):
            state.analyst_report = json.dumps(analyst_result)
        else:
            state.analyst_report = str(analyst_result)

        # Step 4: CHALLENGE
        state.step = "challenge"
        logger.info("[ENGINE] Step 4: CHALLENGE - Skeptic Agent reviewing...")
        skeptic_result = await self._call_tool(
            "challenge_analysis",
            analyst_report=state.analyst_report,
            masked_log=state.masked_log,
            context=state.context
        )
        state.skeptic_report = str(skeptic_result)

        # Step 5: DECIDE
        state.step = "decide"
        logger.info("[ENGINE] Step 5: DECIDE - Judge Agent making final verdict...")
        judge_result = await self._call_tool(
            "make_verdict",
            analyst_report=state.analyst_report,
            skeptic_report=state.skeptic_report,
            masked_log=state.masked_log,
            context=state.context
        )
        if isinstance(judge_result, dict):
            state.verdict = judge_result.get("verdict", "Undetermined")
            state.judge_reasoning = judge_result.get("reasoning", "")
            state.remediation = judge_result.get("remediation", "")
            state.playbook_refs = judge_result.get("playbook_refs", [])
        else:
            state.verdict = "Undetermined"
            state.judge_reasoning = str(judge_result)

        # Step 6: CONSOLIDATE
        state.step = "consolidate"
        logger.info("[ENGINE] Step 6: CONSOLIDATE - Saving lessons learned...")
        lessons = await self._call_tool(
            "consolidate_memory",
            alert_id=state.alert_id,
            masked_log=state.masked_log,
            verdict=state.verdict,
            reasoning=state.judge_reasoning
        )
        state.lessons_learned = str(lessons)

        state.step = "complete"
        logger.info(f"[ENGINE] ReAct loop complete. Verdict: {state.verdict}")
        return state


supervisor = AgentSupervisor()
