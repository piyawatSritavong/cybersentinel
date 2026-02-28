import requests
from core.config import settings
import logging


def fetch_splunk_event(event_id: str):
    """
    Fetch a specific event from Splunk.
    If Splunk credentials are missing, returns mock data.
    """
    if settings.splunk_token == "mock" or not settings.splunk_url:
        return {
            "event_id": event_id,
            "source": "mock_splunk",
            "message": "Multiple failed login attempts from 192.168.1.100",
            "timestamp": "2026-02-24T10:00:00Z"
        }

    try:
        headers = {"Authorization": f"Bearer {settings.splunk_token}"}
        response = requests.get(
            f"{settings.splunk_url}/services/search/jobs/{event_id}/results",
            headers=headers,
            timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logging.error(f"Splunk fetch failed: {e}")
        return {"event_id": event_id, "error": str(e), "fallback": "mock_data"}
