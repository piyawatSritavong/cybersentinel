from langchain_groq import ChatGroq
from app.core.config import settings
from app.core.memory import memory  # ใช้ค้นหาความจำเท่านั้น
import logging
import asyncio
import json
import re

# ตั้งค่า Logging
logging.basicConfig(level=logging.INFO)


class LogAnalyzer:

    def __init__(self):
        self.name = "CyberSentinel AI"
        try:
            self.llm = ChatGroq(
                api_key=settings.groq_api_key,
                model_name=settings.analyst_model,
                temperature=0.1,
            )
        except Exception as e:
            logging.error(f"Failed to initialize ChatGroq: {e}")
            self.llm = None

    async def analyze_log(self, log_text: str):
        if not self.llm:
            return {
                "risk_level": "Error",
                "category": "Internal",
                "summary": "AI Model not configured"
            }

        # --- STEP 1: Check Vector Memory (ใช้เพื่อหาบริบทมาช่วยวิเคราะห์) ---
        logging.info("🧠 Searching vector memory for similar cases...")
        similar_cases = memory.get_similar_cases(log_text, n_results=1)

        if similar_cases:
            logging.info("♻️  Found similar patterns in experience.")
            context_from_memory = similar_cases[0]
        else:
            logging.info(
                "🆕 No similar cases found. This is a new learning opportunity."
            )
            context_from_memory = "No historical context available."

        # --- STEP 2: Construct Prompt ---
        prompt = f"""You are a Tier 1 SOC Analyst with Self-Learning capabilities.

INPUT LOG TO INVESTIGATE:
{log_text}

HISTORICAL CONTEXT (From your memory):
{context_from_memory}

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
            # วิเคราะห์ด้วย AI
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None, lambda: self.llm.invoke(prompt))

            # Clean & Parse JSON
            json_match = re.search(r'\{.*\}', response.content, re.DOTALL)
            if json_match:
                analysis = json.loads(json_match.group())

                # --- [จุดที่แก้ไข: ลบ memory.save_incident ออก] ---
                # เราจะไม่สั่ง Save ที่นี่แล้ว เพื่อให้ main.py เป็นคนจัดการจุดเดียว
                # ป้องกันปัญหา ID ซ้ำที่เกิดขึ้นก่อนหน้านี้

                return analysis

        except Exception as e:
            logging.error(f"Analyst Agent error: {e}")
            return {
                "risk_level": "High",
                "category": "System Error",
                "summary": f"Failed to analyze: {str(e)}"
            }


# สร้าง Instance พร้อมใช้งาน
log_analyzer = LogAnalyzer()
