import logging
import asyncio
import json
import urllib.request
import urllib.error
from typing import Dict, Any, Optional
from datetime import datetime, timezone

from app.gateways.base import BaseGateway
from app.core.config import settings

logger = logging.getLogger(__name__)

SEVERITY_ICONS = {
    "critical": "[!!!]",
    "high": "[!!]",
    "medium": "[!]",
    "low": "[.]",
    "info": "[i]",
}


class TelegramGateway(BaseGateway):
    """Full Telegram bot gateway for CyberSentinel alerts and HITL interaction."""

    name = "telegram"
    gateway_type = "messaging"

    def __init__(self, bot_token: str = "", chat_id: str = ""):
        super().__init__()
        self.bot_token = bot_token or settings.telegram_bot_token
        self.chat_id = chat_id or settings.telegram_chat_id
        self._api_base = f"https://api.telegram.org/bot{self.bot_token}"
        self._polling_task: Optional[asyncio.Task] = None
        self._last_update_id: int = 0
        self._command_handlers: Dict[str, Any] = {}
        self._register_default_commands()

    def _register_default_commands(self):
        self._command_handlers = {
            "/status": self._cmd_status,
            "/analyze": self._cmd_analyze,
            "/squad_stats": self._cmd_squad_stats,
            "/help": self._cmd_help,
        }

    def _api_request_sync(self, method: str, data: Dict[str, Any] = None) -> Optional[Dict]:
        url = f"{self._api_base}/{method}"
        try:
            body = json.dumps(data or {}).encode("utf-8")
            req = urllib.request.Request(
                url,
                data=body,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=15) as resp:
                return json.loads(resp.read())
        except urllib.error.HTTPError as e:
            text = e.read().decode("utf-8", errors="replace")
            logger.error(f"[TELEGRAM] API error {e.code}: {text[:200]}")
            return None
        except Exception as e:
            logger.error(f"[TELEGRAM] Request failed for {method}: {e}")
            return None

    async def _api_request(self, method: str, data: Dict[str, Any] = None) -> Optional[Dict]:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._api_request_sync, method, data)

    def _format_alert(self, alert: Dict[str, Any]) -> str:
        severity = alert.get("severity", "info").lower()
        icon = SEVERITY_ICONS.get(severity, "[?]")
        title = alert.get("title", "Security Alert")
        description = alert.get("description", "No details available.")
        source = alert.get("source", "Unknown")
        timestamp = alert.get("timestamp", datetime.now(timezone.utc).isoformat())

        lines = [
            f"{icon} *CyberSentinel Alert*",
            f"*Severity:* {severity.upper()}",
            f"*Title:* {title}",
            f"*Source:* {source}",
            f"*Time:* {timestamp}",
            "",
            f"_{description}_",
        ]

        iocs = alert.get("iocs", [])
        if iocs:
            lines.append("")
            lines.append("*IOCs:*")
            for ioc in iocs[:5]:
                lines.append(f"  - `{ioc}`")

        actions = alert.get("recommended_actions", [])
        if actions:
            lines.append("")
            lines.append("*Recommended Actions:*")
            for i, action in enumerate(actions[:5], 1):
                lines.append(f"  {i}. {action}")

        lines.append("")
        lines.append("Reply with feedback for Purple Team HITL loop.")

        return "\n".join(lines)

    async def send_alert(self, alert: Dict[str, Any]) -> bool:
        if not self.bot_token or not self.chat_id:
            logger.warning("[TELEGRAM] Bot token or chat ID not configured")
            return False

        text = self._format_alert(alert)
        result = await self._api_request("sendMessage", {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": "Markdown",
        })

        if result and result.get("ok"):
            self._message_count += 1
            logger.info(f"[TELEGRAM] Alert sent: {alert.get('title', 'N/A')}")
            return True
        return False

    async def send_message(self, message: str, target: Optional[str] = None) -> bool:
        chat_id = target or self.chat_id
        if not self.bot_token or not chat_id:
            logger.warning("[TELEGRAM] Bot token or chat ID not configured")
            return False

        result = await self._api_request("sendMessage", {
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "Markdown",
        })

        if result and result.get("ok"):
            self._message_count += 1
            return True
        return False

    async def handle_command(self, command: str, args: list, context: Dict[str, Any]) -> str:
        handler = self._command_handlers.get(command)
        if handler:
            return await handler(args, context)
        return f"Unknown command: {command}. Use /help for available commands."

    async def start(self) -> bool:
        if not self.bot_token:
            logger.warning("[TELEGRAM] No bot token configured, skipping start")
            return False

        me = await self._api_request("getMe")
        if me and me.get("ok"):
            bot_name = me["result"].get("username", "unknown")
            logger.info(f"[TELEGRAM] Connected as @{bot_name}")
            self._connected = True
            self._polling_task = asyncio.create_task(self._poll_updates())
            return True
        else:
            logger.error("[TELEGRAM] Failed to connect - invalid bot token")
            self._connected = False
            return False

    async def stop(self) -> bool:
        self._connected = False
        if self._polling_task and not self._polling_task.done():
            self._polling_task.cancel()
            try:
                await self._polling_task
            except asyncio.CancelledError:
                pass
        logger.info("[TELEGRAM] Gateway stopped")
        return True

    async def _poll_updates(self):
        logger.info("[TELEGRAM] Starting update polling")
        while self._connected:
            try:
                result = await self._api_request("getUpdates", {
                    "offset": self._last_update_id + 1,
                    "timeout": 30,
                    "allowed_updates": ["message"],
                })

                if result and result.get("ok"):
                    for update in result.get("result", []):
                        self._last_update_id = update["update_id"]
                        await self._process_update(update)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"[TELEGRAM] Polling error: {e}")
                await asyncio.sleep(5)

    async def _process_update(self, update: Dict[str, Any]):
        message = update.get("message", {})
        text = message.get("text", "").strip()
        chat_id = str(message.get("chat", {}).get("id", ""))
        user = message.get("from", {}).get("username", "unknown")

        if not text:
            return

        context = {
            "chat_id": chat_id,
            "user": user,
            "message_id": message.get("message_id"),
        }

        if text.startswith("/"):
            parts = text.split()
            command = parts[0].split("@")[0].lower()
            args = parts[1:]
            response = await self.handle_command(command, args, context)
            await self.send_message(response, target=chat_id)
        else:
            logger.info(f"[TELEGRAM] HITL feedback from @{user}: {text[:100]}")
            await self._forward_to_purple_team(text, user, chat_id)

    async def _forward_to_purple_team(self, feedback: str, user: str, chat_id: str):
        try:
            from app.tools.purple_team import purple_team_analyze
            task = f"HITL Feedback from analyst @{user}: {feedback}"
            result = purple_team_analyze(task)
            summary = result.get("result", "Feedback received and logged.")
            if len(summary) > 500:
                summary = summary[:500] + "..."
            await self.send_message(
                f"*Purple Team Response:*\n{summary}",
                target=chat_id
            )
        except Exception as e:
            logger.error(f"[TELEGRAM] Purple Team forward failed: {e}")
            await self.send_message(
                "Feedback received. Purple Team processing encountered an error.",
                target=chat_id
            )

    async def _cmd_status(self, args: list, context: Dict[str, Any]) -> str:
        try:
            from app.core.queue import task_queue
            metrics = task_queue.get_metrics()
            return (
                "*CyberSentinel Status*\n"
                f"Queue Depth: {metrics.get('queue_depth', 'N/A')}\n"
                f"Processed: {metrics.get('processed_count', 'N/A')}\n"
                f"Workers: {metrics.get('active_workers', 'N/A')}\n"
                f"Gateway: Connected"
            )
        except Exception:
            return "*CyberSentinel Status*\nSystem is operational. Use /help for commands."

    async def _cmd_analyze(self, args: list, context: Dict[str, Any]) -> str:
        if not args:
            return "Usage: /analyze <IP|hash|domain|query>\nExample: `/analyze 192.168.1.100`"

        query = " ".join(args)
        try:
            from app.tools.blue_team import blue_team_analyze
            result = blue_team_analyze(f"Quick analysis request: {query}")
            analysis = result.get("result", "Analysis unavailable.")
            if len(analysis) > 1000:
                analysis = analysis[:1000] + "..."
            return f"*Blue Team Analysis:*\n{analysis}"
        except Exception as e:
            return f"Analysis failed: {str(e)}"

    async def _cmd_squad_stats(self, args: list, context: Dict[str, Any]) -> str:
        try:
            from app.core.queue import task_queue
            metrics = task_queue.get_metrics()
            return (
                "*Squad Statistics*\n"
                f"Active Workers: {metrics.get('active_workers', 'N/A')}\n"
                f"Messages Sent: {self._message_count}\n"
                f"Gateway: {self.name}\n"
                f"Connected: {self._connected}"
            )
        except Exception:
            return (
                "*Squad Statistics*\n"
                f"Messages Sent: {self._message_count}\n"
                f"Gateway: {self.name}\n"
                f"Connected: {self._connected}"
            )

    async def _cmd_help(self, args: list, context: Dict[str, Any]) -> str:
        return (
            "*CyberSentinel Bot Commands*\n"
            "/status - System status overview\n"
            "/analyze <target> - Quick threat analysis\n"
            "/squad\\_stats - Agent squad statistics\n"
            "/help - Show this help message\n"
            "\nReply to any alert to send feedback to the Purple Team HITL loop."
        )
