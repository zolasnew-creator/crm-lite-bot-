from pathlib import Path
from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Telegram
    bot_token: SecretStr
    manager_id: int

    # Google Sheets
    google_creds_path: Path
    sheet_id: str
    sheet_name: str = "tickets"

    # Local storage
    db_path: str = "crm.db"

    # Sync & Timeouts
    sync_interval_seconds: int = 180
    fsm_timeout_seconds: int = 900

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )


settings = Settings()