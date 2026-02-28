import logging
from app.core.vault import vault

logger = logging.getLogger(__name__)


def execute_response(action: str, target_token: str = "",
                     reason: str = "automated_response") -> dict:
    """
    Tool: ResponseExecutor
    Executes mock containment actions (firewall blocks, host isolation).
    Works with Forensic Tokens from the SecretVault.
    """
    logger.info(f"[TOOL:ResponseExecutor] Action: {action} | Target: {target_token}")

    if action == "block_ip":
        if target_token.startswith("FTKN-"):
            original_ip = vault.reveal_secret(target_token, reason=reason)
            return {
                "action": "block_ip",
                "target": original_ip or target_token,
                "status": "mock_executed",
                "message": f"Firewall rule created to block {original_ip or target_token}"
            }
        return {
            "action": "block_ip",
            "target": target_token,
            "status": "mock_executed",
            "message": f"Firewall rule created to block {target_token}"
        }

    elif action == "isolate_host":
        return {
            "action": "isolate_host",
            "target": target_token,
            "status": "mock_executed",
            "message": f"Host isolation initiated for {target_token}"
        }

    elif action == "disable_account":
        return {
            "action": "disable_account",
            "target": target_token,
            "status": "mock_executed",
            "message": f"Account disabled: {target_token}"
        }

    return {"action": action, "status": "unknown_action"}
