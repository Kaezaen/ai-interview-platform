"""FastAPI application factory and ASGI entrypoint."""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routers import health
from app.core.config import Settings, get_settings

logger = logging.getLogger(__name__)

API_VERSION = "0.1.0"

TAGS_METADATA = [
    {
        "name": "health",
        "description": "Liveness and readiness probes used by Docker and orchestrators.",
    },
]

DESCRIPTION = """\
Backend for an AI-powered interview preparation platform.

The AI generates questions for a given position, level, and skill set; the user
answers; the AI evaluates each answer against a structured rubric. Aggregate scores
are computed by the backend, never by the model.
"""


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Manage startup and shutdown of process-wide resources."""
    settings: Settings = app.state.settings
    logger.info("starting %s (env=%s)", settings.app_name, settings.app_env)

    # Database and Redis connection pools are opened here on Day 2 and Day 4, and
    # register their readiness probes via app.core.health.register_check().

    yield

    logger.info("shutdown complete")


def create_app() -> FastAPI:
    """Build the FastAPI application.

    Settings are read first so that missing configuration fails here, at startup,
    rather than on the first request that needs it.
    """
    settings = get_settings()

    logging.basicConfig(
        level=settings.log_level,
        format="%(asctime)s %(levelname)-8s %(name)s: %(message)s",
    )

    app = FastAPI(
        title=settings.app_name,
        version=API_VERSION,
        summary="AI-powered interview preparation and evaluation platform",
        description=DESCRIPTION,
        openapi_tags=TAGS_METADATA,
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )
    app.state.settings = settings
    app.include_router(health.router)
    return app


app = create_app()
