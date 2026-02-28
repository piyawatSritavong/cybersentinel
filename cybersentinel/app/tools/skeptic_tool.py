from langchain_groq import ChatGroq
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


def challenge_analysis_tool(analyst_report: str, masked_log: str,
                            context: str = "") -> str:
    """
    Tool: SkepticAgent
    Adversarial agent that challenges the Analyst's findings.
    Focuses on finding False Positives and alternative benign explanations.
    """
    prompt = f"""You are a skeptical security analyst whose job is to challenge assumptions and find False Positives.

ORIGINAL ALERT DATA (PII Masked):
{masked_log}

CONTEXT (Historical Cases & Policies):
{context}

ANALYST'S ASSESSMENT:
{analyst_report}

Your task:
1. Find flaws in the analyst's reasoning
2. Propose alternative benign explanations for the observed behavior
3. Identify any signs this might be a False Positive
4. Challenge severity assessments if they seem inflated

Be critical but constructive. Your goal is to prevent alert fatigue from False Positives.
"""

    try:
        llm = ChatGroq(
            api_key=settings.groq_api_key,
            model_name=settings.reviewer_model,
            temperature=0.7,
        )
        response = llm.invoke(prompt)
        return response.content
    except Exception as e:
        logger.error(f"Skeptic tool error: {e}")
        return f"Error connecting to AI: {str(e)}"
