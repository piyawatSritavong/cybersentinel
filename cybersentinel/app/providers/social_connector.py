import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)


class BaseSocialConnector(ABC):
    """Abstract base class for social/messaging connectors."""

    name: str = "base"
    display_name: str = "Base Connector"
    connector_type: str = "messaging"

    @abstractmethod
    async def send_message(self, message: str, target: Optional[str] = None) -> bool:
        pass

    @abstractmethod
    async def send_alert(self, alert: Dict[str, Any]) -> bool:
        pass

    @abstractmethod
    def is_configured(self) -> bool:
        pass

    def get_status(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "display_name": self.display_name,
            "type": self.connector_type,
            "configured": self.is_configured(),
        }


class LineConnector(BaseSocialConnector):
    """LINE messaging connector stub."""

    name = "line"
    display_name = "LINE"
    connector_type = "messaging"

    def __init__(self, channel_token: str = "", channel_secret: str = ""):
        self._channel_token = channel_token
        self._channel_secret = channel_secret

    async def send_message(self, message: str, target: Optional[str] = None) -> bool:
        if not self.is_configured():
            logger.warning("[LINE] Not configured")
            return False
        logger.info(f"[LINE] (stub) Would send message: {message[:80]}")
        return False

    async def send_alert(self, alert: Dict[str, Any]) -> bool:
        if not self.is_configured():
            logger.warning("[LINE] Not configured")
            return False
        logger.info(f"[LINE] (stub) Would send alert: {alert.get('title', 'N/A')}")
        return False

    def is_configured(self) -> bool:
        return bool(self._channel_token and self._channel_secret)


class WhatsAppConnector(BaseSocialConnector):
    """WhatsApp Business API connector stub."""

    name = "whatsapp"
    display_name = "WhatsApp"
    connector_type = "messaging"

    def __init__(self, api_token: str = "", phone_number_id: str = ""):
        self._api_token = api_token
        self._phone_number_id = phone_number_id

    async def send_message(self, message: str, target: Optional[str] = None) -> bool:
        if not self.is_configured():
            logger.warning("[WHATSAPP] Not configured")
            return False
        logger.info(f"[WHATSAPP] (stub) Would send message: {message[:80]}")
        return False

    async def send_alert(self, alert: Dict[str, Any]) -> bool:
        if not self.is_configured():
            logger.warning("[WHATSAPP] Not configured")
            return False
        logger.info(f"[WHATSAPP] (stub) Would send alert: {alert.get('title', 'N/A')}")
        return False

    def is_configured(self) -> bool:
        return bool(self._api_token and self._phone_number_id)


_CONNECTORS = {
    "line": LineConnector,
    "whatsapp": WhatsAppConnector,
}


def list_social_connectors() -> List[Dict[str, Any]]:
    """Returns all social connectors with their current status."""
    results = []
    for name, cls in _CONNECTORS.items():
        try:
            connector = cls()
            status = connector.get_status()
            results.append(status)
        except Exception as e:
            results.append({
                "name": name,
                "display_name": name.title(),
                "type": "messaging",
                "configured": False,
                "error": str(e),
            })
    return results
