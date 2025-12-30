"""Application configuration."""

import warnings
from functools import lru_cache
from typing import Any

from pydantic import PostgresDsn, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


# Default insecure key - only for development
_DEV_SECRET_KEY = "dev-secret-key-change-in-production"


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # App
    app_name: str = "FlowAudit API"
    debug: bool = False
    api_prefix: str = "/api"

    # Database
    database_url: PostgresDsn

    # Security
    secret_key: str = _DEV_SECRET_KEY
    access_token_expire_minutes: int = 60 * 24  # 24 hours
    algorithm: str = "HS256"

    @model_validator(mode="after")
    def validate_secret_key(self) -> "Settings":
        """Validate that secret key is set in production."""
        if self.secret_key == _DEV_SECRET_KEY:
            if not self.debug:
                raise ValueError(
                    "SECRET_KEY must be set to a secure value in production. "
                    "Set DEBUG=true for development or provide a secure SECRET_KEY."
                )
            warnings.warn(
                "Using default SECRET_KEY - DO NOT use in production!",
                UserWarning,
                stacklevel=2,
            )
        return self

    # CORS
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    # File Upload
    upload_dir: str = "/data/uploads"
    max_upload_size: int = 50 * 1024 * 1024  # 50 MB
    allowed_mime_types: list[str] = [
        "application/pdf",
        "image/jpeg",
        "image/png",
        "image/gif",
        "image/webp",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/vnd.ms-excel",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "text/plain",
        "text/csv",
    ]

    @field_validator("database_url", mode="before")
    @classmethod
    def assemble_db_connection(cls, v: Any) -> Any:
        """Validate database URL."""
        if isinstance(v, str):
            return v
        return v


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
