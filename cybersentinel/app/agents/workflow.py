from typing import Dict, Any
import logging
import json
from app.agents.analyst import log_analyzer
from app.agents.skeptic import challenge_analysis
from app.agents.judge import make_final_verdict
from app.core.memory import memory
from app.core.normalizer import Normalizer
from app.services.correlator import correlate_logs


class WorkflowState:
    """
    State machine for the Multi-Agent workflow.
    """

    def __init__(self, masked_log: str, context: str, correlation: str):
        self.masked_log = masked_log
        self.context = context
        self.correlation = correlation
        self.analyst_report = None
        self.skeptic_report = None
        self.judge_verdict = None


async def execute_workflow(masked_log: str,
                           source: str = "splunk",
                           alert_id: str = "unknown") -> Dict[str, Any]:
    """
    Execute the multi-agent workflow using LangGraph-style state transitions.
    Includes memory retrieval and log correlation.
    """
    logging.info("Starting Multi-Agent Workflow")

    # 0. Log Incident to PostgreSQL Memory
    memory.log_incident(alert_id, masked_log, source)

    # 1. Normalize
    raw_log_dict = {"raw_data": masked_log, "alert_id": alert_id}
    normalized_log = Normalizer.to_ocsf(raw_log_dict, source)
    normalized_json = normalized_log.model_dump_json()

    # 2. Memory Search (Retrieve)
    logging.info("Retrieving memory context...")
    similar_incidents = memory.get_similar_cases(normalized_json)
    company_docs = memory.get_company_docs(normalized_json)

    context_str = ""
    # Deduplication & Efficiency: If highly similar cases exist, prioritize them.
    if similar_incidents:
        context_str += "PREVIOUS SIMILAR CASES (Confirmed by Human):\n" + "\n".join(
            similar_incidents) + "\n\n"
    if company_docs:
        context_str += "OFFICIAL POLICIES/DOCS:\n" + "\n".join(
            company_docs) + "\n\n"

    # 3. Correlate (Log Correlation Skill)
    logging.info("Correlating with recent incidents...")
    recent_incidents = memory.get_recent_incidents(limit=5)
    correlation_result = correlate_logs(normalized_json, recent_incidents)
    context_str += "LOG CORRELATION ANALYSIS:\n" + correlation_result + "\n\n"

    state = WorkflowState(masked_log, context_str, correlation_result)

    # Step 4: Analyst Agent
    logging.info("Analyst Agent analyzing alert...")
    state.analyst_report = await log_analyzer.analyze_log(state.masked_log)

    # Step 5: Skeptic Agent
    logging.info("Skeptic Agent challenging analysis...")
    state.skeptic_report = challenge_analysis(state.analyst_report,
                                              state.masked_log, state.context)

    # Step 6: Judge Agent (Recommend & Decide)
    logging.info("Judge Agent making final verdict with remediation...")
    judge_result = make_final_verdict(state.analyst_report,
                                      state.skeptic_report, state.masked_log,
                                      state.context)
    state.judge_verdict = judge_result

    logging.info(f"Workflow complete. Verdict: {judge_result['verdict']}")

    return {
        "masked_log": state.masked_log,
        "analyst_report": state.analyst_report,
        "skeptic_report": state.skeptic_report,
        "verdict": judge_result["verdict"],
        "judge_reasoning": judge_result["reasoning"],
        "remediation": judge_result.get("remediation", ""),
        "correlation": correlation_result,
        "playbook_refs": judge_result["playbook_refs"]
    }
