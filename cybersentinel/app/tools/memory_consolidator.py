import logging
from app.core.memory import memory

logger = logging.getLogger(__name__)


def consolidate_memory(alert_id: str, masked_log: str,
                       verdict: str, reasoning: str) -> str:
    """
    Tool: MemoryConsolidator
    Summarizes the case and saves "Lessons Learned" back to Vector Memory.
    This is the key to the self-learning loop.
    """
    logger.info(f"[TOOL:MemoryConsolidator] Consolidating case {alert_id}...")

    summary = f"Alert {alert_id} analyzed. Verdict: {verdict}. Key reasoning: {reasoning[:200]}"

    try:
        memory.cases_collection.add(
            documents=[f"Lesson Learned: {summary}\nLog: {masked_log}"],
            metadatas=[{"alert_id": alert_id, "verdict": verdict, "type": "lesson_learned"}],
            ids=[f"lesson_{alert_id}"]
        )
        logger.info(f"[TOOL:MemoryConsolidator] Lesson saved for {alert_id}")
        return summary
    except Exception as e:
        logger.error(f"Memory consolidation failed: {e}")
        return f"Consolidation failed: {e}"
