import logging
from app.core.memory import memory

logger = logging.getLogger(__name__)


def search_history(query: str, n_results: int = 3) -> list:
    """
    Tool: HistoryAnalyst
    Queries the Vector DB for similar historical attack patterns.
    Returns a list of similar past cases for context injection.
    """
    logger.info(f"[TOOL:HistoryAnalyst] Searching for similar patterns...")
    cases = memory.get_similar_cases(query, n_results=n_results)
    docs = memory.get_company_docs(query, n_results=2)
    return {"similar_cases": cases, "relevant_docs": docs}
