import logging
import asyncio
from typing import Dict, Any, List, Optional

from app.gateways.base import BaseGateway

logger = logging.getLogger(__name__)


class MultiChannelGateway:
    """Gateway registry/manager that manages all registered gateways,
    broadcasts critical alerts, and routes HITL feedback."""

    def __init__(self):
        self._gateways: Dict[str, BaseGateway] = {}
        self._broadcast_history: List[Dict[str, Any]] = []
        self._max_history = 100

    def register(self, gateway: BaseGateway) -> None:
        self._gateways[gateway.name] = gateway
        logger.info(f"[GATEWAY] Registered: {gateway.name} ({gateway.gateway_type})")

    def unregister(self, name: str) -> bool:
        if name in self._gateways:
            del self._gateways[name]
            logger.info(f"[GATEWAY] Unregistered: {name}")
            return True
        return False

    def get_gateway(self, name: str) -> Optional[BaseGateway]:
        return self._gateways.get(name)

    def list_gateways(self) -> List[Dict[str, Any]]:
        return [gw.get_status() for gw in self._gateways.values()]

    async def start_all(self) -> Dict[str, bool]:
        results = {}
        for name, gw in self._gateways.items():
            try:
                results[name] = await gw.start()
            except Exception as e:
                logger.error(f"[GATEWAY] Failed to start {name}: {e}")
                results[name] = False
        return results

    async def stop_all(self) -> Dict[str, bool]:
        results = {}
        for name, gw in self._gateways.items():
            try:
                results[name] = await gw.stop()
            except Exception as e:
                logger.error(f"[GATEWAY] Failed to stop {name}: {e}")
                results[name] = False
        return results

    async def broadcast_alert(self, alert: Dict[str, Any]) -> Dict[str, bool]:
        """Broadcast a critical alert to all connected gateways."""
        results = {}
        for name, gw in self._gateways.items():
            if gw.is_connected:
                try:
                    results[name] = await gw.send_alert(alert)
                except Exception as e:
                    logger.error(f"[GATEWAY] Alert broadcast failed for {name}: {e}")
                    results[name] = False
            else:
                results[name] = False

        self._broadcast_history.append({
            "alert_title": alert.get("title", "Unknown"),
            "severity": alert.get("severity", "unknown"),
            "results": results,
            "gateways_notified": sum(1 for v in results.values() if v),
        })
        if len(self._broadcast_history) > self._max_history:
            self._broadcast_history = self._broadcast_history[-self._max_history:]

        return results

    async def send_to(self, gateway_name: str, message: str, target: Optional[str] = None) -> bool:
        gw = self._gateways.get(gateway_name)
        if gw and gw.is_connected:
            return await gw.send_message(message, target)
        return False

    def get_broadcast_history(self) -> List[Dict[str, Any]]:
        return list(self._broadcast_history)

    def get_status(self) -> Dict[str, Any]:
        return {
            "total_gateways": len(self._gateways),
            "connected": sum(1 for gw in self._gateways.values() if gw.is_connected),
            "gateways": self.list_gateways(),
            "broadcast_count": len(self._broadcast_history),
        }
