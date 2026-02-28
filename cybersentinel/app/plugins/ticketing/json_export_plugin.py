import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any
from .base import TicketingPlugin
from ...core.config import settings

class JsonExportPlugin(TicketingPlugin):
    """
    JSON Export Plugin.
    Saves the analysis report to a local JSON file. Useful for air-gapped environments.
    """
    
    def create_ticket(self, report_data: Dict[str, Any]) -> Dict[str, Any]:
        export_path = settings.ticket_export_path
        
        # Ensure the directory exists
        base_dir = Path(__file__).parent.parent.parent.parent
        full_export_path = base_dir / export_path
        os.makedirs(full_export_path, exist_ok=True)
        
        # Generate filename based on alert ID and timestamp
        alert_id = report_data.get("alert_id", "unknown_alert")
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"{alert_id}_{timestamp}.json"
        
        file_path = full_export_path / filename
        
        try:
            with open(file_path, 'w') as f:
                json.dump(report_data, f, indent=4)
                
            logging.info(f"Report exported successfully to {file_path}")
            return {
                "status": "success",
                "plugin": "json_export",
                "file_path": str(file_path)
            }
        except Exception as e:
            logging.error(f"JSON export failed: {e}")
            return {
                "status": "error",
                "plugin": "json_export",
                "error": str(e)
            }
