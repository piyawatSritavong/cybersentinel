import logging
from langchain_groq import ChatGroq
from app.core.config import settings

logger = logging.getLogger(__name__)


def blue_team_analyze(task: str) -> dict:
    """
    Blue Team Agent: Defensive Operations
    Specializes in log analysis, forensics, and auto-remediation.
    """
    prompt = f"""You are an elite Blue Team SOC analyst specializing in defensive security operations.

TASK:
{task}

Your capabilities:
1. Deep log analysis and forensic investigation
2. Auto-remediation recommendations (ISO 27001/NIST compliant)
3. Incident response playbook execution
4. Threat hunting and IOC extraction
5. PII protection and vault management

Provide a detailed, actionable response. Include specific remediation steps where applicable.
Format your response clearly with sections for: Analysis, Findings, and Recommended Actions.
"""
    try:
        llm = ChatGroq(
            api_key=settings.groq_api_key,
            model_name=settings.analyst_model,
            temperature=0.2,
        )
        response = llm.invoke(prompt)
        return {
            "agent": "Blue Team",
            "result": response.content,
            "status": "completed"
        }
    except Exception as e:
        logger.error(f"Blue Team error: {e}")
        return {
            "agent": "Blue Team",
            "result": f"Blue Team analysis failed: {str(e)}",
            "status": "error"
        }
