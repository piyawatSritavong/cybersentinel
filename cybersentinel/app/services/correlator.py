from typing import Dict, Any, List
import logging
from langchain_groq import ChatGroq
from app.core.config import settings

def correlate_logs(current_log: str, recent_incidents: List[Dict[str, Any]]) -> str:
    """
    Advanced Cyber-Skill: Log Correlation.
    Groups logs from different sources to find common attack patterns.
    """
    if not recent_incidents:
        return "No recent incidents available for correlation."
        
    incidents_text = "\n".join([f"- ID: {i['alert_id']} | Source: {i['source_type']} | Log: {i['raw_log']}" for i in recent_incidents])
    
    prompt = f"""You are an advanced SOC Log Correlation Engine.

CURRENT LOG:
{current_log}

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
        logging.error(f"Correlation error: {e}")
        return "Correlation engine unavailable."
