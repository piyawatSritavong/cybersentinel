import requests
from core.config import settings
import logging


def query_virustotal(ioc: str, ioc_type: str = "ip"):
    """
    Query VirusTotal for threat intelligence.
    If API key is missing, returns mock data.
    """
    if settings.vt_api_key == "mock":
        return {
            "ioc": ioc,
            "type": ioc_type,
            "malicious": False,
            "reputation": "clean",
            "source": "mock_virustotal"
        }

    try:
        headers = {"x-apikey": settings.vt_api_key}

        if ioc_type == "ip":
            url = f"https://www.virustotal.com/api/v3/ip_addresses/{ioc}"
        elif ioc_type == "domain":
            url = f"https://www.virustotal.com/api/v3/domains/{ioc}"
        else:
            return {"error": "Unsupported IOC type"}

        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logging.error(f"VirusTotal query failed: {e}")
        return {"error": str(e), "fallback": "mock_data"}
