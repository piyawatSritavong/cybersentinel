import os
import threading
import logging
import hashlib
import hmac
import base64
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

_instance = None
_lock = threading.Lock()


class DynamicSettings:
    CATEGORIES = ("ai_models", "social_gateways", "integrations", "security", "system")

    _ENV_SEED_MAP = {
        "ai_models": {
            "groq_api_key": {"env": "GROQ_API_KEY", "encrypted": True, "description": "Groq Cloud API key"},
            "analyst_model": {"env": "ANALYST_MODEL", "default": "llama-3.3-70b-versatile", "description": "Primary analyst LLM model"},
            "reviewer_model": {"env": "REVIEWER_MODEL", "default": "llama-3.3-70b-versatile", "description": "Reviewer LLM model"},
            "ollama_base_url": {"env": "OLLAMA_BASE_URL", "default": "http://localhost:11434", "description": "Ollama local server URL"},
        },
        "social_gateways": {
            "enable_social_gateway": {"env": "ENABLE_SOCIAL_GATEWAY", "default": "false", "description": "Enable social gateway integrations"},
            "telegram_bot_token": {"env": "TELEGRAM_BOT_TOKEN", "encrypted": True, "description": "Telegram bot token"},
            "telegram_chat_id": {"env": "TELEGRAM_CHAT_ID", "description": "Telegram chat ID"},
            "discord_webhook_url": {"env": "DISCORD_WEBHOOK_URL", "encrypted": True, "description": "Discord webhook URL"},
            "slack_webhook_url": {"env": "SLACK_WEBHOOK_URL", "encrypted": True, "description": "Slack webhook URL"},
        },
        "integrations": {
            "splunk_url": {"env": "SPLUNK_URL", "default": "https://mock-splunk.local", "description": "Splunk HEC URL"},
            "splunk_token": {"env": "SPLUNK_TOKEN", "encrypted": True, "description": "Splunk HEC token"},
            "jira_url": {"env": "JIRA_URL", "default": "https://mock-jira.local", "description": "Jira instance URL"},
            "jira_token": {"env": "JIRA_TOKEN", "encrypted": True, "description": "Jira API token"},
            "vt_api_key": {"env": "VT_API_KEY", "encrypted": True, "description": "VirusTotal API key"},
        },
        "security": {
            "app_api_key": {"env": "APP_API_KEY", "encrypted": True, "description": "Dashboard API key"},
            "secret_vault_key": {"env": "SECRET_VAULT_KEY", "encrypted": True, "description": "Vault encryption master key"},
        },
        "system": {
            "infra_provider": {"env": "INFRA_PROVIDER", "default": "REPLIT", "description": "Infrastructure provider"},
            "max_queue_size": {"env": "MAX_QUEUE_SIZE", "default": "1000", "description": "Maximum task queue size"},
            "vector_db_path": {"env": "VECTOR_DB_PATH", "default": "data/vector_db", "description": "Vector DB storage path"},
            "enable_learning": {"env": "ENABLE_LEARNING", "default": "true", "description": "Enable ML learning loop"},
        },
    }

    def __init__(self):
        self._cache: Dict[str, Dict[str, dict]] = {}
        self._db_available = False
        self._engine = None
        self._vault_key = None
        self._connect()

    def _connect(self):
        try:
            from sqlalchemy import create_engine, text
            db_url = os.environ.get("DATABASE_URL", "")
            if not db_url:
                logger.warning("[DynamicSettings] DATABASE_URL not set, running without DB persistence")
                return
            self._engine = create_engine(db_url)
            with self._engine.connect() as conn:
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS system_settings (
                        id SERIAL PRIMARY KEY,
                        category TEXT NOT NULL,
                        key TEXT NOT NULL,
                        value TEXT DEFAULT '',
                        encrypted BOOLEAN DEFAULT FALSE,
                        enabled BOOLEAN DEFAULT TRUE,
                        description TEXT DEFAULT '',
                        UNIQUE(category, key)
                    )
                """))
                conn.commit()
            self._db_available = True
            self._vault_key = self._derive_vault_key()
            self._load_from_db()
            logger.info("[DynamicSettings] Connected to PostgreSQL and loaded settings")
        except Exception as e:
            logger.error(f"[DynamicSettings] DB connection failed: {e}")
            self._db_available = False

    def _derive_vault_key(self) -> bytes:
        raw = os.environ.get("SECRET_VAULT_KEY", "cybersentinel-aes-256-default-key!").encode("utf-8")
        return hashlib.pbkdf2_hmac("sha256", raw, b"dynamic-settings-salt", 100000)

    def _encrypt_value(self, plaintext: str) -> str:
        key = self._vault_key or self._derive_vault_key()
        data = plaintext.encode("utf-8")
        encrypted = bytes([data[i] ^ key[i % len(key)] for i in range(len(data))])
        mac = hmac.new(key, encrypted, hashlib.sha256).digest()
        payload = base64.b64encode(encrypted).decode() + "|" + base64.b64encode(mac).decode()
        return "ENC:" + payload

    def _decrypt_value(self, stored: str) -> str:
        if not stored.startswith("ENC:"):
            return stored
        try:
            payload = stored[4:]
            parts = payload.split("|")
            if len(parts) != 2:
                return stored
            encrypted = base64.b64decode(parts[0])
            stored_mac = base64.b64decode(parts[1])
            key = self._vault_key or self._derive_vault_key()
            computed_mac = hmac.new(key, encrypted, hashlib.sha256).digest()
            if not hmac.compare_digest(stored_mac, computed_mac):
                logger.error("[DynamicSettings] Integrity check failed for encrypted value")
                return ""
            decrypted = bytes([encrypted[i] ^ key[i % len(key)] for i in range(len(encrypted))])
            return decrypted.decode("utf-8")
        except Exception as e:
            logger.error(f"[DynamicSettings] Decryption failed: {e}")
            return ""

    def _load_from_db(self):
        if not self._db_available or not self._engine:
            return
        try:
            from sqlalchemy import text
            with self._engine.connect() as conn:
                rows = conn.execute(text("SELECT category, key, value, encrypted, enabled, description FROM system_settings")).fetchall()
            self._cache.clear()
            for row in rows:
                cat, k, v, enc, enabled, desc = row
                if cat not in self._cache:
                    self._cache[cat] = {}
                decrypted_v = self._decrypt_value(v) if enc and v else v
                self._cache[cat][k] = {
                    "value": decrypted_v,
                    "encrypted": enc,
                    "enabled": enabled,
                    "description": desc or "",
                }
        except Exception as e:
            logger.error(f"[DynamicSettings] Failed to load from DB: {e}")

    def refresh(self):
        with _lock:
            self._load_from_db()

    def get(self, category: str, key: str, default: Optional[str] = None) -> Optional[str]:
        cat_data = self._cache.get(category, {})
        entry = cat_data.get(key)
        if entry is not None:
            return entry["value"]
        seed_cat = self._ENV_SEED_MAP.get(category, {})
        seed_entry = seed_cat.get(key, {})
        env_var = seed_entry.get("env", "")
        if env_var:
            env_val = os.environ.get(env_var, "")
            if env_val:
                return env_val
        fallback = seed_entry.get("default")
        if fallback is not None:
            return fallback
        return default

    def set(self, category: str, key: str, value: str, encrypted: bool = False, description: str = ""):
        stored_value = self._encrypt_value(value) if encrypted and value else value
        if self._db_available and self._engine:
            try:
                from sqlalchemy import text
                with self._engine.connect() as conn:
                    conn.execute(text("""
                        INSERT INTO system_settings (category, key, value, encrypted, enabled, description)
                        VALUES (:cat, :key, :val, :enc, TRUE, :desc)
                        ON CONFLICT (category, key) DO UPDATE
                        SET value = :val, encrypted = :enc, description = COALESCE(NULLIF(:desc, ''), system_settings.description)
                    """), {"cat": category, "key": key, "val": stored_value, "enc": encrypted, "desc": description})
                    conn.commit()
            except Exception as e:
                logger.error(f"[DynamicSettings] Failed to save setting {category}/{key}: {e}")

        if category not in self._cache:
            self._cache[category] = {}
        self._cache[category][key] = {
            "value": value,
            "encrypted": encrypted,
            "enabled": True,
            "description": description,
        }

    def get_category(self, category: str) -> Dict[str, Any]:
        result = {}
        cat_data = self._cache.get(category, {})
        for k, entry in cat_data.items():
            result[k] = entry["value"]
        seed_cat = self._ENV_SEED_MAP.get(category, {})
        for k, seed_entry in seed_cat.items():
            if k not in result:
                env_var = seed_entry.get("env", "")
                env_val = os.environ.get(env_var, "") if env_var else ""
                if env_val:
                    result[k] = env_val
                elif "default" in seed_entry:
                    result[k] = seed_entry["default"]
        return result

    def is_enabled(self, category: str, key: str) -> bool:
        cat_data = self._cache.get(category, {})
        entry = cat_data.get(key)
        if entry is not None:
            return bool(entry.get("enabled", True))
        return False

    def toggle(self, category: str, key: str) -> bool:
        cat_data = self._cache.get(category, {})
        entry = cat_data.get(key)
        current = entry.get("enabled", True) if entry else False
        new_state = not current
        if self._db_available and self._engine:
            try:
                from sqlalchemy import text
                with self._engine.connect() as conn:
                    conn.execute(text("""
                        UPDATE system_settings SET enabled = :enabled WHERE category = :cat AND key = :key
                    """), {"enabled": new_state, "cat": category, "key": key})
                    conn.commit()
            except Exception as e:
                logger.error(f"[DynamicSettings] Failed to toggle {category}/{key}: {e}")
        if entry:
            entry["enabled"] = new_state
        return new_state

    def seed_from_env(self):
        if not self._db_available:
            logger.warning("[DynamicSettings] Cannot seed: no DB connection")
            return
        try:
            from sqlalchemy import text
            with self._engine.connect() as conn:
                count = conn.execute(text("SELECT COUNT(*) FROM system_settings")).scalar()
            if count and count > 0:
                logger.info(f"[DynamicSettings] DB already has {count} settings, skipping seed")
                return
        except Exception as e:
            logger.error(f"[DynamicSettings] Failed to check seed state: {e}")
            return

        logger.info("[DynamicSettings] Seeding settings from environment variables...")
        for category, keys in self._ENV_SEED_MAP.items():
            for key, meta in keys.items():
                env_var = meta.get("env", "")
                default = meta.get("default", "")
                value = os.environ.get(env_var, default) if env_var else default
                encrypted = meta.get("encrypted", False)
                description = meta.get("description", "")
                if value:
                    self.set(category, key, value, encrypted=encrypted, description=description)
        logger.info("[DynamicSettings] Seed complete")

    def get_all_settings(self) -> Dict[str, Dict[str, dict]]:
        result: Dict[str, Dict[str, dict]] = {}
        for category in self.CATEGORIES:
            result[category] = {}
            cat_data = self._cache.get(category, {})
            for k, entry in cat_data.items():
                result[category][k] = {
                    "value": "****" if entry.get("encrypted") else entry["value"],
                    "encrypted": entry.get("encrypted", False),
                    "enabled": entry.get("enabled", True),
                    "description": entry.get("description", ""),
                }
            seed_cat = self._ENV_SEED_MAP.get(category, {})
            for k, seed_entry in seed_cat.items():
                if k not in result[category]:
                    result[category][k] = {
                        "value": "",
                        "encrypted": seed_entry.get("encrypted", False),
                        "enabled": False,
                        "description": seed_entry.get("description", ""),
                    }
        return result


def get_dynamic_settings() -> DynamicSettings:
    global _instance
    if _instance is None:
        with _lock:
            if _instance is None:
                _instance = DynamicSettings()
    return _instance
