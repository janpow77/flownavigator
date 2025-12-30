"""Application configuration."""

from functools import lru_cache
from typing import Any

from pydantic import PostgresDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


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
    secret_key: str = "dev-secret-key-change-in-production"
    access_token_expire_minutes: int = 60 * 24  # 24 hours
    algorithm: str = "HS256"

    # CORS
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]

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
