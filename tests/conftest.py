"""Shared test fixtures.

Two decisions worth stating, because they shape every test here:

*Its own database.* ``DATABASE_URL`` is repointed at ``<name>_test`` before any
application module is imported, so the settings, the engine and Alembic all
agree on it and a test run can never touch development data.

*Truncation, not rollback.* Wrapping each test in a transaction and rolling it
back is the usual trick, but the service under test commits on purpose — that is
the whole point of keeping the AI call out of an open transaction — so a test
that rolled everything back would not be exercising what the application does.
Emptying the tables between tests is slower and honest.
"""

import asyncio
import os
from collections.abc import AsyncIterator, Callable
from urllib.parse import urlsplit, urlunsplit

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

_TEST_DATABASE_SUFFIX = "_test"


def _with_suffix(url: str) -> str:
    """Return ``url`` pointing at the test database beside the real one."""
    parts = urlsplit(url)
    return urlunsplit(parts._replace(path=parts.path + _TEST_DATABASE_SUFFIX))


#: Repointed before the first application import, so the cached settings and the
#: Alembic environment both pick up the test database rather than the real one.
_CONFIGURED_URL = os.environ["DATABASE_URL"]
_ADMIN_URL = (
    _CONFIGURED_URL.removesuffix(_TEST_DATABASE_SUFFIX)
    if _CONFIGURED_URL.endswith(_TEST_DATABASE_SUFFIX)
    else _CONFIGURED_URL
)
_TEST_URL = _with_suffix(_ADMIN_URL)
os.environ["DATABASE_URL"] = _TEST_URL

from alembic import command  # noqa: E402
from alembic.config import Config  # noqa: E402
from httpx import ASGITransport, AsyncClient  # noqa: E402

from app.db.session import dispose_engine, init_engine  # noqa: E402
from app.main import app  # noqa: E402
from app.services.ai.base import AIProvider  # noqa: E402
from app.services.ai.factory import get_ai_provider  # noqa: E402
from app.services.ai.fake_provider import FakeProvider  # noqa: E402

#: Child before parent, so the truncate reads in a sensible order even though
#: CASCADE would handle it anyway.
_TABLES = ("questions", "interviews", "users")


@pytest.fixture(scope="session", autouse=True)
async def database() -> AsyncIterator[None]:
    """Create the test database, build its schema, and open the pool."""
    name = urlsplit(_TEST_URL).path.lstrip("/")
    admin = create_async_engine(_ADMIN_URL, isolation_level="AUTOCOMMIT")
    try:
        async with admin.connect() as connection:
            exists = await connection.scalar(
                text("select 1 from pg_database where datname = :name"),
                {"name": name},
            )
            if not exists:
                await connection.execute(text(f'create database "{name}"'))
    finally:
        await admin.dispose()

    # alembic's env.py drives the async engine with asyncio.run(), which refuses
    # to start inside an already-running loop. A worker thread has no loop of its
    # own, so the migration runs there.
    await asyncio.to_thread(command.upgrade, Config("alembic.ini"), "head")

    init_engine()
    yield
    await dispose_engine()


@pytest.fixture(autouse=True)
async def clean_tables() -> AsyncIterator[None]:
    """Leave the database empty for whichever test runs next."""
    yield
    engine = create_async_engine(_TEST_URL)
    try:
        async with engine.begin() as connection:
            await connection.execute(
                text(f"truncate {', '.join(_TABLES)} restart identity cascade")
            )
    finally:
        await engine.dispose()


@pytest.fixture
async def client() -> AsyncIterator[AsyncClient]:
    """An HTTP client driving the real application in-process.

    ASGITransport exercises the actual routing, dependencies and exception
    handlers, so a test asserting on a 503 envelope is asserting on the thing
    that will serve production traffic.
    """
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as instance:
        yield instance

    app.dependency_overrides.clear()


@pytest.fixture
def use_provider() -> Callable[[AIProvider], None]:
    """Install a provider for the duration of one test.

    This is the seam Day 3 owes the rest of the project: the provider is a
    FastAPI dependency, so a test replaces it without patching an import and
    without any chance of reaching a network.
    """

    def install(provider: AIProvider) -> None:
        app.dependency_overrides[get_ai_provider] = lambda: provider

    return install


@pytest.fixture(autouse=True)
def default_provider(use_provider: Callable[[AIProvider], None]) -> None:
    """Every test starts with a provider that works and never leaves the process."""
    use_provider(FakeProvider(mode="valid"))


async def register_and_login(client: AsyncClient, email: str) -> str:
    """Create an account and return a bearer token for it."""
    password = "a-sufficiently-long-password"
    response = await client.post("/auth/register", json={"email": email, "password": password})
    assert response.status_code == 201, response.text

    response = await client.post("/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200, response.text
    return str(response.json()["access_token"])


async def create_interview(
    client: AsyncClient,
    token: str,
    *,
    skills: list[str] | None = None,
) -> str:
    """Create an interview owned by ``token``'s user and return its id."""
    response = await client.post(
        "/interviews",
        headers={"authorization": f"Bearer {token}"},
        json={
            "position": "Backend Engineer",
            "level": "mid",
            "skills": skills if skills is not None else ["Python", "FastAPI"],
        },
    )
    assert response.status_code == 201, response.text
    return str(response.json()["id"])
