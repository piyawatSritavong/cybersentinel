import logging
from langchain_groq import ChatGroq
from app.core.config import settings

logger = logging.getLogger(__name__)


def purple_team_analyze(task: str) -> dict:
    """
    Purple Team Agent: Orchestration
    Manages the feedback loop between Blue and Red teams to harden defenses.
    """
    prompt = f"""You are a Purple Team orchestrator managing the feedback loop between Blue (Defensive) and Red (Offensive) security teams.

TASK:
{task}

Your capabilities:
1. Coordinate Blue-Red team exercises
2. Gap analysis between defensive controls and offensive capabilities
3. Continuous improvement cycle management
4. Defense hardening recommendations
5. Metrics and KPI tracking for security posture

Provide a comprehensive response with:
- Gap Analysis: Where defenses are weakest
- Red Team Insights: What attackers would target
- Blue Team Actions: Specific hardening steps
- Priority Matrix: What to fix first (Critical/High/Medium/Low)
- Metrics: How to measure improvement
"""
    try:
        llm = ChatGroq(
            api_key=settings.groq_api_key,
            model_name=settings.analyst_model,
            temperature=0.3,
        )
        response = llm.invoke(prompt)
        return {
            "agent": "Purple Team",
            "result": response.content,
            "status": "completed"
        }
    except Exception as e:
        logger.error(f"Purple Team error: {e}")
        return {
            "agent": "Purple Team",
            "result": f"Purple Team analysis failed: {str(e)}",
            "status": "error"
        }
