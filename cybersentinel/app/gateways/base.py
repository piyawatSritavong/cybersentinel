import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class BaseGateway(ABC):
    """Abstract base class for all social/messaging gateways."""

    name: str = "base"
    gateway_type: str = "unknown"

    def __init__(self):
        self._connected: bool = False
        self._message_count: int = 0

    @property
    def is_connected(self) -> bool:
        return self._connected

    @abstractmethod
    async def send_alert(self, alert: Dict[str, Any]) -> bool:
        """Send a security alert through this gateway.
        
        Args:
            alert: Dict containing alert details (severity, title, description, etc.)
            
        Returns:
            True if sent successfully, False otherwise.
        """
        pass

    @abstractmethod
    async def send_message(self, message: str, target: Optional[str] = None) -> bool:
        """Send a plain text message through this gateway.
        
        Args:
            message: The message text to send.
            target: Optional target channel/chat/user ID.
            
        Returns:
            True if sent successfully, False otherwise.
        """
        pass

    @abstractmethod
    async def handle_command(self, command: str, args: list, context: Dict[str, Any]) -> str:
        """Handle an incoming command from this gateway.
        
        Args:
            command: The command name (e.g., 'status', 'analyze').
            args: List of command arguments.
            context: Additional context (user, channel, etc.).
            
        Returns:
            Response string to send back.
        """
        pass

    @abstractmethod
    async def start(self) -> bool:
        """Start the gateway connection/polling.
        
        Returns:
            True if started successfully.
        """
        pass

    @abstractmethod
    async def stop(self) -> bool:
        """Stop the gateway connection/polling.
        
        Returns:
            True if stopped successfully.
        """
        pass

    def get_status(self) -> Dict[str, Any]:
        """Return current gateway status."""
        return {
            "name": self.name,
            "type": self.gateway_type,
            "connected": self._connected,
            "messages_sent": self._message_count,
        }
