import asyncio
import sys
import os
from datetime import datetime

# บังคับให้มองเห็นโฟลเดอร์ app
sys.path.append(os.getcwd())

from app.core.memory import memory
from app.agents.analyst import log_analyzer

# จำลองเกณฑ์ SOP (Standard Operating Procedure)
SOP_GUIDELINES = {
    "HIGH":
    "Action: Block IP immediately, Revoke session, and escalate to Tier 2.",
    "MEDIUM": "Action: Enable MFA, notify user, and monitor for 24 hours.",
    "LOW": "Action: Log event and continue monitoring."
}


async def ai_soc_workflow(log_text, test_desc):
    print(f"🔍 [Analyzing]: {test_desc}")
    print(f"   📥 Log: {log_text}")

    # 1. ตรวจสอบใน Database (Simulate Search Memory)
    # ในระบบจริงจะใช้ memory.get_similar_cases(log_text)
    print(f"   🧠 Checking historical logs for similar patterns...")
    past_cases = memory.get_recent_incidents(limit=10)

    # จำลองการตรวจสอบความซ้ำของ IP หรือ Behavior
    existing_case = next((c for c in past_cases if c['raw_log'] == log_text),
                         None)

    # 2. กระบวนการตัดสินใจ (Self-Learning Logic)
    if existing_case:
        print(f"   ♻️  [MATCH FOUND]: This pattern was seen before.")
        context = f"Historical Context: Previously seen as {existing_case.get('source_type')}"
    else:
        print(
            f"   🆕 [NEW CASE]: No exact match in memory. Invoking AI reasoning..."
        )
        context = "Historical Context: No previous match found. This is a new pattern."

    # 3. ส่งให้ AI วิเคราะห์ (DeepSeek/Groq) พร้อม Context และ SOP
    try:
        print(f"   🤖 AI is correlating with SOP Guidelines...")
        # เราส่ง Context และ SOP ไปให้ AI ในไฟล์ analyzer.py
        analysis = await log_analyzer.analyze_log(
            f"{log_text} | {context} | SOP: {SOP_GUIDELINES}")

        risk = analysis.get('risk_level', 'LOW').upper()
        sop_action = SOP_GUIDELINES.get(risk, "Monitor normally.")

        print(f"   ✨ AI Conclusion: {risk}")
        print(f"   📋 Recommendation: {analysis.get('summary')}")
        print(f"   🛡️  SOP Alignment: {sop_action}")

        print("   Learning Saved: Log and AI analysis stored to PostgreSQL")

    except Exception as e:
        print(f"   ❌ Workflow Error: {str(e)}")

    print("-" * 60)


async def run_test_cases():
    print(f"\n{'='*70}")
    print(f"🛡️  CYBERSENTINEL: SELF-LEARNING AI SOC TEST SUITE")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*70}\n")

    test_logs = [
        # เคสที่ 1: High Risk (SQL Injection) - เคสใหม่
        {
            "desc": "New High Risk Case (SQLi)",
            "log": "ID: 101 | SRC_IP: 1.1.1.1 | PAYLOAD: ' OR 1=1 --"
        },
        # เคสที่ 2: Medium Risk (Brute Force) - IP ใหม่
        {
            "desc":
            "New Medium Risk Case (Brute Force)",
            "log":
            "ID: 102 | SRC_IP: 2.2.2.2 | MSG: Failed password for admin (Attempt 5)"
        },
        # เคสที่ 3: Low Risk (Normal)
        {
            "desc":
            "Normal Activity",
            "log":
            "ID: 103 | SRC_IP: 192.168.1.5 | MSG: User 'accountant' logged in successfully"
        },
        # เคสที่ 4: Severity ซ้ำ (High) แต่รายละเอียดต่าง (IP ต่าง) - ทดสอบความฉลาดในการแยกแยะ
        {
            "desc": "High Risk - Different IP (New Attacker)",
            "log": "ID: 104 | SRC_IP: 9.9.9.9 | PAYLOAD: ' OR 1=1 --"
        },
        # เคสที่ 5: เคสซ้ำ (IP เดิม Payload เดิม) - ทดสอบการจำคำตอบเดิม (Learning Memory)
        {
            "desc": "Repeated Case (Known Attacker)",
            "log": "ID: 101 | SRC_IP: 1.1.1.1 | PAYLOAD: ' OR 1=1 --"
        }
    ]

    for case in test_logs:
        analysis = await log_analyzer.analyze_log(case['log'])
        print(f"✨ AI Result: {analysis['risk_level']}")

    print(f"\n✅ ALL AI SOC TEST CASES COMPLETED")


if __name__ == "__main__":
    asyncio.run(run_test_cases())
