from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    db_url: str = "sqlite+aiosqlite:///./crm.db"
    attachment_dir: Path = Path("attachments")
    debug: bool = False
    # Maximum upload size enforced at service layer (1 MB)
    max_attachment_bytes: int = 1_048_576
    # Authentication
    session_timeout_minutes: int = 30
    bcrypt_rounds: int = 12
    environment: str = "development"
    allowed_mime_types: frozenset[str] = frozenset({
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "image/jpeg",
        "image/png",
    })


settings = Settings()
