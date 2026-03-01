import logging
from typing import Dict, Any
from .base import TicketingPlugin


class ScraperPlugin(TicketingPlugin):
    """
    Web Scraping Plugin (Stub).
    Scrapes threat intelligence data from web sources and attaches
    enrichment context to tickets before dispatch.
    Requires beautifulsoup4 and requests packages when fully implemented.
    """

    def __init__(self):
        self.plugin_name = "web_scraper"
        self.supported_sources = ["otx", "abuseipdb", "urlhaus"]

    def create_ticket(self, report_data: Dict[str, Any]) -> Dict[str, Any]:
        logging.info(f"[Stub] ScraperPlugin.create_ticket called with alert: {report_data.get('alert_id', 'unknown')}")
        return {
            "status": "stub_not_implemented",
            "plugin": self.plugin_name,
            "message": "Web scraping plugin is not yet implemented. Install beautifulsoup4 to enable.",
            "supported_sources": self.supported_sources,
        }

    def is_configured(self) -> bool:
        return False

    def get_status(self) -> Dict[str, Any]:
        return {
            "name": self.plugin_name,
            "configured": False,
            "message": "Stub: requires beautifulsoup4 and requests",
        }
