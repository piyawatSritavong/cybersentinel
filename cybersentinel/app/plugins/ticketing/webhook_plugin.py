import requests
import logging
from typing import Dict, Any
from .base import TicketingPlugin
from ...core.config import settings

class WebhookPlugin(TicketingPlugin):
    """
    Universal Webhook Plugin.
    Sends the analysis report as a JSON payload to a specified URL.
    """
    
    def create_ticket(self, report_data: Dict[str, Any]) -> Dict[str, Any]:
        webhook_url = settings.ticket_webhook_url
        
        # Mock mode fallback if no real URL is configured
        if not webhook_url or webhook_url.startswith("https://mock-webhook"):
            logging.info(f"[Mock Mode] Webhook would send data to {webhook_url}")
            return {
                "status": "mock_success",
                "plugin": "webhook",
                "destination": webhook_url,
                "message": "Webhook triggered in mock mode."
            }
            
        try:
            logging.info(f"Sending webhook to {webhook_url}")
            response = requests.post(
                webhook_url,
                json=report_data,
                timeout=10
            )
            response.raise_for_status()
            
            return {
                "status": "success",
                "plugin": "webhook",
                "destination": webhook_url,
                "response_code": response.status_code
            }
        except Exception as e:
            logging.error(f"Webhook ticketing failed: {e}")
            return {
                "status": "error",
                "plugin": "webhook",
                "error": str(e)
            }
