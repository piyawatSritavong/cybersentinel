from abc import ABC, abstractmethod
from typing import Dict, Any

class TicketingPlugin(ABC):
    """
    Abstract Base Class for all ticketing plugins.
    Ensures a consistent interface across different ticketing platforms.
    """
    
    @abstractmethod
    def create_ticket(self, report_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a ticket in the target system.
        
        Args:
            report_data: A dictionary containing the full analysis and report details.
                         (Expected to be pre-masked to protect PII).
                         
        Returns:
            A dictionary containing the ticketing system's response (e.g., ticket ID, status, URL).
        """
        pass
