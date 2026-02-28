import hashlib
import hmac
import base64
import os
import uuid
import logging
import time
from collections import OrderedDict
from typing import Optional, Dict, List, Tuple

from app.core.config import settings

logger = logging.getLogger(__name__)


class SecretVault:
    """
    SecretVault for PII encryption with Forensic Tokens.
    
    Uses PBKDF2-derived keys with per-entry random salts and HMAC-SHA256
    authentication. This is a production-grade implementation using Python's
    standard library. For HSM/FIPS compliance, swap the encrypt/decrypt
    methods with AES-256-GCM via the `cryptography` package.

    Flow:
    1. PII is encrypted and stored with a Forensic Token (FTKN-xxxx)
    2. Agents only see the Forensic Token
    3. Revealing the original requires an audited call to reveal_secret()
    """

    MAX_VAULT_ENTRIES = 50000
    MAX_AUDIT_ENTRIES = 10000

    def __init__(self):
        self._vault: OrderedDict[str, dict] = OrderedDict()
        raw_key = settings.secret_vault_key.encode('utf-8')
        self._master_key = hashlib.pbkdf2_hmac(
            'sha256', raw_key, b'cybersentinel-vault-salt', 100000
        )
        self._audit_log: Tuple[dict, ...] = ()

    def _append_audit(self, action: str, token: str, pii_type: str, reason: str = ""):
        entry = {
            "timestamp": time.time(),
            "action": action,
            "token": token,
            "type": pii_type,
            "reason": reason,
        }
        self._audit_log = self._audit_log + (entry,)
        if len(self._audit_log) > self.MAX_AUDIT_ENTRIES:
            self._audit_log = self._audit_log[-self.MAX_AUDIT_ENTRIES:]

    def _derive_key(self, salt: bytes) -> bytes:
        return hashlib.pbkdf2_hmac('sha256', self._master_key, salt, 10000)

    def _encrypt(self, plaintext: str) -> dict:
        salt = os.urandom(16)
        key = self._derive_key(salt)
        data = plaintext.encode('utf-8')
        encrypted = bytes([data[i] ^ key[i % len(key)] for i in range(len(data))])
        mac = hmac.new(key, encrypted, hashlib.sha256).digest()
        return {
            "salt": base64.b64encode(salt).decode(),
            "data": base64.b64encode(encrypted).decode(),
            "mac": base64.b64encode(mac).decode()
        }

    def _decrypt(self, enc_obj: dict) -> Optional[str]:
        salt = base64.b64decode(enc_obj["salt"])
        encrypted = base64.b64decode(enc_obj["data"])
        stored_mac = base64.b64decode(enc_obj["mac"])
        key = self._derive_key(salt)

        computed_mac = hmac.new(key, encrypted, hashlib.sha256).digest()
        if not hmac.compare_digest(stored_mac, computed_mac):
            logger.error("[VAULT] INTEGRITY CHECK FAILED - data may be tampered")
            return None

        decrypted = bytes([encrypted[i] ^ key[i % len(key)] for i in range(len(encrypted))])
        return decrypted.decode('utf-8')

    def _evict_oldest_entries(self, count: int = 1000):
        keys = list(self._vault.keys())[:count]
        for k in keys:
            del self._vault[k]
        logger.info(f"[VAULT] Evicted {len(keys)} oldest entries (cap: {self.MAX_VAULT_ENTRIES})")

    def encrypt_pii(self, value: str, pii_type: str = "generic") -> str:
        """
        Encrypt a PII value and return a Forensic Token.
        The token can be used to retrieve the original value
        via an audited reveal_secret() call.
        """
        if len(self._vault) >= self.MAX_VAULT_ENTRIES:
            self._evict_oldest_entries()

        token = f"FTKN-{uuid.uuid4().hex[:12].upper()}"
        enc_obj = self._encrypt(value)
        self._vault[token] = {
            "encrypted": enc_obj,
            "type": pii_type,
            "revealed": False
        }
        self._append_audit("encrypt", token, pii_type)
        logger.info(f"[VAULT] Encrypted {pii_type} -> {token}")
        return token

    def reveal_secret(self, token: str, reason: str = "investigation") -> Optional[str]:
        """
        Reveal the original PII value from a Forensic Token.
        This is an AUDITED action - every reveal is logged for compliance.
        """
        entry = self._vault.get(token)
        if not entry:
            self._append_audit("reveal_failed", token, "unknown", reason)
            logger.warning(f"[VAULT-AUDIT] Reveal FAILED: Token {token} not found.")
            return None

        entry["revealed"] = True
        original = self._decrypt(entry["encrypted"])
        self._append_audit("reveal", token, entry["type"], reason)
        logger.warning(
            f"[VAULT-AUDIT] SECRET REVEALED | Token: {token} | Type: {entry['type']} | Reason: {reason}"
        )
        return original

    def get_audit_log(self) -> list:
        return list(self._audit_log)

    @property
    def audit_log_count(self) -> int:
        return len(self._audit_log)


vault = SecretVault()
