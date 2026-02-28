import logging
from typing import Dict, Any
from .base import TicketingPlugin
from .webhook_plugin import WebhookPlugin
from .json_export_plugin import JsonExportPlugin
from .jira_plugin import JiraPlugin
from ...core.config import settings

class TicketingManager:
    """
    Factory class that dynamically loads the appropriate ticketing plugin
    based on configuration.
    """
    
    def __init__(self):
        self.plugin_type = settings.ticket_system_type.lower()
        self.plugin = self._load_plugin()
        
    def _load_plugin(self) -> TicketingPlugin:
        logging.info(f"Loading ticketing plugin: {self.plugin_type}")
        if self.plugin_type == "jira":
            return JiraPlugin()
        elif self.plugin_type == "json":
            return JsonExportPlugin()
        elif self.plugin_type == "webhook":
            return WebhookPlugin()
        else:
            logging.warning(f"Unknown ticketing plugin '{self.plugin_type}', defaulting to WebhookPlugin")
            return WebhookPlugin()
            
    def dispatch_ticket(self, report_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Dispatches the report data to the configured ticketing system.
        """
        return self.plugin.create_ticket(report_data)
