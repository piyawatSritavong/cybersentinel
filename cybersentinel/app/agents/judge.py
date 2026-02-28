from langchain_groq import ChatGroq
from app.core.config import settings
import logging

def make_final_verdict(analyst_report: str, skeptic_report: str, masked_log: str, context: str = "") -> dict:
    """
    Judge Agent: Makes the final verdict based on Analyst's assessment, Skeptic's challenges, and Playbooks.
    Also provides Auto-Remediation Recommendation based on ISO 27001/NIST.
    """
    
    prompt = f"""You are the final Judge in a Security Operations Center. You must make a definitive verdict.

ORIGINAL ALERT DATA (PII Masked):
{masked_log}

CONTEXT (Historical Cases & Policies):
{context}

ANALYST'S ASSESSMENT:
{analyst_report}

SKEPTIC'S CHALLENGES:
{skeptic_report}

Your task:
1. Weigh both the Analyst's and Skeptic's arguments.
2. Reference the provided context/playbooks to make your decision.
3. Provide a FINAL VERDICT: "True Positive" or "False Positive".
4. Explain your reasoning clearly.
5. Provide a "Remediation" section based on ISO 27001 or NIST standards. Ensure this section is clearly labeled.

Respond ONLY with your verdict, reasoning, and remediation. Be decisive.
"""

    try:
        llm = ChatGroq(
            api_key=settings.groq_api_key,
            model_name=settings.reviewer_model,
            temperature=0.2,
        )
        response = llm.invoke(prompt)
        verdict_text = response.content
        
        if "true positive" in verdict_text.lower():
            verdict = "True Positive"
        elif "false positive" in verdict_text.lower():
            verdict = "False Positive"
        else:
            verdict = "Undetermined"
            
        # Try to extract remediation from the text
        remediation = "See full reasoning for remediation details."
        if "remediation" in verdict_text.lower():
            parts = verdict_text.lower().split("remediation", 1)
            if len(parts) > 1:
                remediation = "Remediation" + parts[1]
        
        return {
            "verdict": verdict,
            "reasoning": verdict_text,
            "remediation": remediation,
            "playbook_refs": ["Retrieved from Memory"] if context else []
        }
    
    except Exception as e:
        logging.error(f"Judge Agent error: {e}")
        return {
            "verdict": "Undetermined",
            "reasoning": f"Error connecting to AI: {str(e)}",
            "remediation": "N/A",
            "playbook_refs": []
        }
