"""Application settings, loaded from the environment.

Required variables are declared without a default on purpose: if one is missing the
application fails immediately at startup with a clear validation error, instead of
appearing healthy and then failing inside a request much later.
"""

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


class Settings(BaseSettings):
    """Runtime configuration read from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # --- Application ---------------------------------------------------------
    app_name: str = "AI Interview Platform"
    app_env: Literal["development", "staging", "production"] = "development"
    debug: bool = False
    log_level: LogLevel = "INFO"

    # --- Security (required) -------------------------------------------------
    secret_key: str = Field(min_length=32)

    # --- Backing services (required) -----------------------------------------
    database_url: str
    redis_url: str

    # --- AI provider ---------------------------------------------------------
    ai_provider: Literal["fake", "gemini"] = "fake"
    gemini_api_key: str | None = None


@lru_cache
def get_settings() -> Settings:
    """Return the process-wide settings, building them on first use."""
    return Settings()
