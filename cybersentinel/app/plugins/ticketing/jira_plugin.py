import requests
import logging
from typing import Dict, Any
from .base import TicketingPlugin
from ...core.config import settings

class JiraPlugin(TicketingPlugin):
    """
    Jira Plugin for creating Jira issues.
    """
    
    def create_ticket(self, report_data: Dict[str, Any]) -> Dict[str, Any]:
        summary = f"[CyberSentinel] {report_data.get('alert_id', 'Unknown')} - {report_data.get('verdict', 'Unknown')}"
        description = report_data.get('technical_report', 'No description available')[:1000]
        
        if settings.jira_token == "mock" or not settings.jira_url or settings.jira_url.startswith("https://mock-jira"):
            logging.info("[Mock Mode] Jira ticket creation.")
            return {
                "ticket_id": "MOCK-12345",
                "summary": summary,
                "status": "created_mock",
                "url": f"{settings.jira_url}/browse/MOCK-12345",
                "plugin": "jira"
            }
        
        try:
            headers = {
                "Authorization": f"Bearer {settings.jira_token}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "fields": {
                    "project": {"key": "SEC"},
                    "summary": summary,
                    "description": description,
                    "issuetype": {"name": "Incident"}
                }
            }
            
            response = requests.post(
                f"{settings.jira_url}/rest/api/2/issue",
                headers=headers,
                json=payload,
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            
            return {
                "ticket_id": data.get("key"),
                "status": "created",
                "url": f"{settings.jira_url}/browse/{data.get('key')}",
                "plugin": "jira"
            }
        except Exception as e:
            logging.error(f"Jira ticket creation failed: {e}")
            return {
                "status": "error",
                "plugin": "jira",
                "error": str(e)
            }
