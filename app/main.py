"""FastAPI application factory and ASGI entrypoint."""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.errors import register_exception_handlers
from app.api.middleware import RequestIDMiddleware
from app.api.routers import auth, health
from app.core.config import Settings, get_settings
from app.db.session import dispose_engine, init_engine

logger = logging.getLogger(__name__)

API_VERSION = "0.1.0"

TAGS_METADATA = [
    {
        "name": "health",
        "description": "Liveness and readiness probes used by Docker and orchestrators.",
    },
    {
        "name": "auth",
        "description": "Registration, login, and the current user's profile.",
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

    # Opening the pool here rather than at import time keeps module imports free
    # of side effects, and registers the database readiness probe. The Redis pool
    # joins it on Day 4.
    init_engine()

    yield

    await dispose_engine()
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

    # The correlation id has to exist before anything can fail, so this is added
    # first and therefore runs outermost.
    app.add_middleware(RequestIDMiddleware)
    register_exception_handlers(app)

    app.include_router(health.router)
    app.include_router(auth.router)
    return app


app = create_app()
