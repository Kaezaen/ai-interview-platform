"""Async engine, session factory, and the request-scoped session dependency.

The engine is opened once in the application lifespan rather than at import
time: importing this module must stay free of side effects so that Alembic and
tooling can import models without opening a connection pool.
"""

import logging
from collections.abc import AsyncIterator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import get_settings
from app.core.health import CheckStatus, register_check

logger = logging.getLogger(__name__)

_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def init_engine() -> AsyncEngine:
    """Open the process-wide connection pool and register its readiness probe."""
    global _engine, _session_factory

    if _engine is not None:
        return _engine

    settings = get_settings()
    _engine = create_async_engine(
        settings.database_url,
        # A connection that died while idle (postgres restarted, network blipped)
        # is replaced instead of being handed to a request that would then fail.
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=10,
        # Bound parameters are kept out of exception messages, and therefore out
        # of the traceback the unhandled-error handler logs. They carry the
        # password hash on a failed INSERT into users, and will carry answer text
        # once answers exist. The statement itself is still reported, which is
        # what identifies the failure.
        hide_parameters=True,
        connect_args={
            # Every outbound call gets an explicit timeout: a hung database must
            # surface as an error, never as a request that waits forever.
            "timeout": 5,
            "command_timeout": 10,
        },
    )
    _session_factory = async_sessionmaker(_engine, expire_on_commit=False)
    register_check("database", check_database)
    logger.info("database engine initialised")
    return _engine


async def dispose_engine() -> None:
    """Close the connection pool on shutdown."""
    global _engine, _session_factory

    if _engine is None:
        return

    await _engine.dispose()
    _engine = None
    _session_factory = None
    logger.info("database engine disposed")


async def check_database() -> CheckStatus:
    """Readiness probe: take a connection from the pool and use it.

    Failures are deliberately not caught here; ``run_checks`` is the boundary
    that turns a raising probe into a reported failure and logs it.
    """
    if _engine is None:
        return CheckStatus.NOT_CONFIGURED

    async with _engine.connect() as connection:
        await connection.execute(text("SELECT 1"))
    return CheckStatus.OK


async def get_db() -> AsyncIterator[AsyncSession]:
    """Yield a session scoped to a single request.

    Committing is left to the service layer, which owns the transaction
    boundary. This dependency only guarantees that a failed request never
    leaves a dirty transaction behind on a pooled connection.
    """
    if _session_factory is None:  # pragma: no cover - a wiring mistake, not a runtime path
        raise RuntimeError("database engine is not initialised; call init_engine() first")

    async with _session_factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
