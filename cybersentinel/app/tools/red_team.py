import logging
from langchain_groq import ChatGroq
from app.core.config import settings

logger = logging.getLogger(__name__)


def red_team_analyze(task: str) -> dict:
    """
    Red Team Agent: Offensive Operations
    Specializes in vulnerability scanning, exploit simulation, and attack surface mapping.
    """
    prompt = f"""You are an elite Red Team operator specializing in offensive security and penetration testing.

TASK:
{task}

Your capabilities:
1. Vulnerability assessment and scanning simulation
2. Attack surface mapping and reconnaissance
3. Exploit simulation (safe, theoretical analysis only)
4. Social engineering vector analysis
5. Lateral movement path identification

IMPORTANT: You are performing DEFENSIVE analysis by thinking like an attacker.
All findings should help the Blue Team strengthen defenses.

Provide a detailed response with: Attack Vectors Identified, Vulnerability Assessment, 
Exploitation Potential (rated Low/Medium/High/Critical), and Defensive Recommendations.
"""
    try:
        llm = ChatGroq(
            api_key=settings.groq_api_key,
            model_name=settings.analyst_model,
            temperature=0.3,
        )
        response = llm.invoke(prompt)
        return {
            "agent": "Red Team",
            "result": response.content,
            "status": "completed"
        }
    except Exception as e:
        logger.error(f"Red Team error: {e}")
        return {
            "agent": "Red Team",
            "result": f"Red Team analysis failed: {str(e)}",
            "status": "error"
        }
