from langchain_groq import ChatGroq
from app.core.config import settings
import logging

def challenge_analysis(analyst_report: str, masked_log: str, context: str = "") -> str:
    """
    Skeptic Agent: Adversarial agent that challenges the Analyst's findings.
    Uses ChatGroq with llama-3.3-70b-versatile to find False Positives and alternative explanations.
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
        logging.error(f"Skeptic Agent error: {e}")
        return f"Error connecting to AI: {str(e)}"
