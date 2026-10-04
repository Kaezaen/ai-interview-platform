"""Application settings, loaded from the environment.

Required variables are declared without a default on purpose: if one is missing the
application fails immediately at startup with a clear validation error, instead of
appearing healthy and then failing inside a request much later.
"""

from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

#: Which canned response ``FakeProvider`` returns. ``invalid`` and ``unavailable``
#: exist so both 503 paths can be exercised end to end without a network call.
FakeMode = Literal["valid", "invalid", "unavailable"]


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

    # Long enough to cover a practice interview without a re-login, short enough
    # that a leaked token expires on its own. There is no revocation list, so
    # this lifetime is the only thing that limits a stolen token, and there is no
    # refresh token yet — see README.
    access_token_expire_minutes: int = Field(default=30, gt=0)

    # --- Backing services (required) -----------------------------------------
    database_url: str
    redis_url: str

    # --- AI provider ---------------------------------------------------------
    ai_provider: Literal["fake", "gemini"] = "fake"

    # SecretStr so the key cannot leak through a settings repr or a debug dump.
    gemini_api_key: SecretStr | None = None
    gemini_model: str = "gemini-3.6-flash"

    # The deadline this application enforces itself, independent of whatever the
    # vendor SDK does with its own timeout setting.
    ai_request_timeout_seconds: float = Field(default=20.0, gt=0)

    # Total transport attempts per call, not extra retries on top of the first.
    # Capped because the budget multiplies with the one corrective content retry.
    ai_max_attempts: int = Field(default=2, ge=1, le=3)

    # Only consulted when ai_provider == "fake".
    ai_fake_mode: FakeMode = "valid"

    @model_validator(mode="after")
    def _require_gemini_key(self) -> "Settings":
        """Refuse to start with a provider that cannot possibly authenticate."""
        if self.ai_provider == "gemini" and self.gemini_api_key is None:
            raise ValueError("GEMINI_API_KEY is required when AI_PROVIDER=gemini")
        return self


@lru_cache
def get_settings() -> Settings:
    """Return the process-wide settings, building them on first use."""
    return Settings()
