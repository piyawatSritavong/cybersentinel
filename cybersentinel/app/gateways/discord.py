import logging
from typing import Dict, Any, Optional

from app.gateways.base import BaseGateway
from app.core.config import settings

logger = logging.getLogger(__name__)


class DiscordGateway(BaseGateway):
    """Stub Discord gateway implementing BaseGateway for extensibility."""

    name = "discord"
    gateway_type = "messaging"

    def __init__(self, webhook_url: str = ""):
        super().__init__()
        self.webhook_url = webhook_url or settings.discord_webhook_url

    async def send_alert(self, alert: Dict[str, Any]) -> bool:
        logger.info(f"[DISCORD] (stub) Would send alert: {alert.get('title', 'N/A')}")
        return False

    async def send_message(self, message: str, target: Optional[str] = None) -> bool:
        logger.info(f"[DISCORD] (stub) Would send message: {message[:80]}")
        return False

    async def handle_command(self, command: str, args: list, context: Dict[str, Any]) -> str:
        return "Discord gateway is not yet implemented."

    async def start(self) -> bool:
        logger.info("[DISCORD] (stub) Discord gateway start requested - not implemented")
        self._connected = False
        return False

    async def stop(self) -> bool:
        logger.info("[DISCORD] (stub) Discord gateway stopped")
        self._connected = False
        return True
