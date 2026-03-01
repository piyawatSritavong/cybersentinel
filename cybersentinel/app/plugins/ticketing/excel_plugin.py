import logging
from typing import Dict, Any
from .base import TicketingPlugin


class ExcelPlugin(TicketingPlugin):
    """
    Excel/Word Export Plugin (Stub).
    Exports analysis reports to Excel (.xlsx) or Word (.docx) format.
    Requires openpyxl and python-docx packages when fully implemented.
    """

    def __init__(self):
        self.plugin_name = "excel_export"
        self.supported_formats = ["xlsx", "docx"]

    def create_ticket(self, report_data: Dict[str, Any]) -> Dict[str, Any]:
        logging.info(f"[Stub] ExcelPlugin.create_ticket called with alert: {report_data.get('alert_id', 'unknown')}")
        return {
            "status": "stub_not_implemented",
            "plugin": self.plugin_name,
            "message": "Excel/Word export plugin is not yet implemented. Install openpyxl and python-docx to enable.",
            "supported_formats": self.supported_formats,
        }

    def is_configured(self) -> bool:
        return False

    def get_status(self) -> Dict[str, Any]:
        return {
            "name": self.plugin_name,
            "configured": False,
            "message": "Stub: requires openpyxl and python-docx",
        }
