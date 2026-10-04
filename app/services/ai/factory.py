"""Choosing the concrete provider, in one place.

Nothing outside this module imports a concrete provider: routers and services
depend on the ``AIProvider`` interface. Tests replace the whole thing by
overriding ``get_ai_provider`` as a FastAPI dependency.
"""

import logging
from functools import lru_cache

from app.core.config import get_settings
from app.services.ai.base import AIProvider

logger = logging.getLogger(__name__)


@lru_cache
def get_ai_provider() -> AIProvider:
    """Return the process-wide provider, building it on first use.

    The concrete classes are imported inside the function deliberately: with
    ``AI_PROVIDER=fake`` the Gemini SDK is then never imported at all, which is
    what lets the whole flow run with no key and no network.
    """
    settings = get_settings()

    if settings.ai_provider == "gemini":
        from app.services.ai.gemini_provider import GeminiProvider

        if settings.gemini_api_key is None:  # pragma: no cover - the settings validator
            raise ValueError("GEMINI_API_KEY is required when AI_PROVIDER=gemini")

        logger.info(
            "ai provider ready (provider=gemini model=%s timeout_s=%s attempts=%d)",
            settings.gemini_model,
            settings.ai_request_timeout_seconds,
            settings.ai_max_attempts,
        )
        return GeminiProvider(
            api_key=settings.gemini_api_key.get_secret_value(),
            model_name=settings.gemini_model,
            timeout_seconds=settings.ai_request_timeout_seconds,
            max_attempts=settings.ai_max_attempts,
        )

    from app.services.ai.fake_provider import FakeProvider

    logger.info("ai provider ready (provider=fake mode=%s)", settings.ai_fake_mode)
    return FakeProvider()
