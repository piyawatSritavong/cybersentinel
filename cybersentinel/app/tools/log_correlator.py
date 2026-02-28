from typing import Dict, Any, List
import logging
import asyncio
from langchain_groq import ChatGroq
from app.core.config import settings

logger = logging.getLogger(__name__)


def correlate_logs_tool(current_log: str,
                        recent_incidents: List[Dict[str, Any]]) -> str:
    """
    Tool: LogCorrelator
    Groups logs from different sources to find common attack patterns.
    """
    if not recent_incidents:
        return "No recent incidents available for correlation."

    incidents_text = "\n".join([
        f"- ID: {i.get('alert_id','?')} | Source: {i.get('source_type','?')} | Log: {i.get('raw_log','')[:100]}"
        for i in recent_incidents
    ])

    prompt = f"""You are an advanced SOC Log Correlation Engine.

CURRENT LOG:
{current_log[:500]}

RECENT NETWORK/SYSTEM INCIDENTS:
{incidents_text}

Your task:
Analyze the current log alongside the recent incidents and determine if they are part of a broader, coordinated attack pattern (e.g., Lateral Movement, Distributed Brute Force, Multi-vector attack).

Provide a concise correlation summary. If there is no correlation, state "No correlation found."
"""

    try:
        llm = ChatGroq(
            api_key=settings.groq_api_key,
            model_name=settings.analyst_model,
            temperature=0.1,
        )
        response = llm.invoke(prompt)
        return response.content
    except Exception as e:
        logger.error(f"Correlation error: {e}")
        return "Correlation engine unavailable."
