import logging
import requests
from app.core.config import settings

logger = logging.getLogger(__name__)


def lookup_threat_intel(ioc: str, ioc_type: str = "ip") -> dict:
    """
    Tool: ThreatIntelLookup
    Connects to VirusTotal/AbuseIPDB for threat intelligence on an IOC.
    Falls back to mock data if no API key is configured.
    """
    logger.info(f"[TOOL:ThreatIntel] Looking up {ioc_type}: {ioc}")

    if settings.vt_api_key == "mock" or not settings.vt_api_key:
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
        logger.error(f"ThreatIntel lookup failed: {e}")
        return {"error": str(e), "fallback": "mock_data"}
