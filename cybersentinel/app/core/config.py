from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    splunk_url: str = "https://mock-splunk.local"
    splunk_token: str = "mock"
    ollama_base_url: str = "http://localhost:11434"
    jira_url: str = "https://mock-jira.local"
    jira_token: str = "mock"
    vt_api_key: str = "mock"

    # Ticketing Plugin Settings
    ticket_system_type: str = "webhook"
    ticket_webhook_url: str = "https://mock-webhook.local/receive"
    ticket_export_path: str = "data/exports/"

    # Groq Settings
    groq_api_key: str = ""
    analyst_model: str = "llama-3.3-70b-versatile"
    reviewer_model: str = "llama-3.3-70b-versatile"

    # Security
    app_api_key: str = Field(default="",
                             env="APP_API_KEY")
    secret_vault_key: str = Field(default="cybersentinel-aes-256-default-key!",
                                  env="SECRET_VAULT_KEY")

    # Memory Settings
    vector_db_path: str = "data/vector_db"
    enable_learning: bool = True

    # Database URL
    database_url: str = ""

    # Social Gateway Settings
    enable_social_gateway: bool = False
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""
    discord_webhook_url: str = ""
    slack_webhook_url: str = ""

    # Task Queue
    max_queue_size: int = 1000

    # Infrastructure Adapter
    infra_provider: str = "REPLIT"

    class Config:
        env_file = ".env"


settings = Settings()

try:
    from app.core.dynamic_settings import get_dynamic_settings
    dynamic_settings = get_dynamic_settings()
except Exception:
    dynamic_settings = None
