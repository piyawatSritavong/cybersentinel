from langchain_groq import ChatGroq
from app.core.config import settings
from app.core.memory import memory
import logging
import asyncio
import json
import re

logger = logging.getLogger(__name__)


def analyze_log_tool(log_text: str, context: str = "") -> dict:
    """
    Tool: AnalystAgent
    Acts as a Tier 1 SOC Analyst investigating SIEM logs.
    Uses Groq LLM with chain-of-thought reasoning.
    """
    similar_cases = memory.get_similar_cases(log_text, n_results=1)
    context_from_memory = similar_cases[0] if similar_cases else "No historical context available."

    full_context = context if context else ""
    full_context += f"\n\nDIRECT MEMORY MATCH:\n{context_from_memory}"

    prompt = f"""You are a Tier 1 SOC Analyst with Self-Learning capabilities.

INPUT LOG TO INVESTIGATE:
{log_text}

HISTORICAL CONTEXT (From your memory):
{full_context}

YOUR TASK:
1. Compare the INPUT LOG with HISTORICAL CONTEXT.
2. Provide the risk level, category, and a concise summary.

OUTPUT FORMAT (Strictly JSON):
{{
    "risk_level": "Low/Medium/High/Critical",
    "category": "Event Category",
    "summary": "Your analysis + recommended action based on SOP"
}}
"""

    try:
        llm = ChatGroq(
            api_key=settings.groq_api_key,
            model_name=settings.analyst_model,
            temperature=0.1,
        )
        response = llm.invoke(prompt)

        json_match = re.search(r'\{.*\}', response.content, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())

        return {
            "risk_level": "Medium",
            "category": "General",
            "summary": response.content[:500]
        }
    except Exception as e:
        logger.error(f"Analyst tool error: {e}")
        return {
            "risk_level": "High",
            "category": "System Error",
            "summary": f"Failed to analyze: {str(e)}"
        }
