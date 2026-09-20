"""POST /interviews/{id}/questions — the endpoint Day 3 exists for."""

from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.services.ai.fake_provider import FakeProvider
from app.services.question import QUESTION_COUNT
from tests.conftest import create_interview, register_and_login


async def _count_questions(interview_id: str) -> int:
    """Read straight from the database, past the API and past the ORM cache."""
    sessions = get_db()
    session: AsyncSession = await anext(sessions)
    try:
        return int(
            await session.scalar(
                text("select count(*) from questions where interview_id = :id"),
                {"id": interview_id},
            )
            or 0
        )
    finally:
        await sessions.aclose()


def _auth(token: str) -> dict[str, str]:
    return {"authorization": f"Bearer {token}"}


async def test_generate_questions_creates_a_set(client: AsyncClient) -> None:
    token = await register_and_login(client, "creates@example.com")
    interview_id = await create_interview(client, token, skills=["Python", "FastAPI"])

    response = await client.post(f"/interviews/{interview_id}/questions", headers=_auth(token))

    assert response.status_code == 201, response.text
    body = response.json()
    assert len(body) == QUESTION_COUNT
    assert [question["ordinal"] for question in body] == list(range(1, QUESTION_COUNT + 1))
    # Every question is about something that was actually requested.
    assert {question["skill"] for question in body} <= {"Python", "FastAPI"}
    assert await _count_questions(interview_id) == QUESTION_COUNT


async def test_generate_questions_moves_the_interview_on(client: AsyncClient) -> None:
    token = await register_and_login(client, "status@example.com")
    interview_id = await create_interview(client, token)

    await client.post(f"/interviews/{interview_id}/questions", headers=_auth(token))

    response = await client.get(f"/interviews/{interview_id}", headers=_auth(token))
    assert response.json()["status"] == "questions_generated"


async def test_generate_questions_never_exposes_traceability_fields(
    client: AsyncClient,
) -> None:
    token = await register_and_login(client, "fields@example.com")
    interview_id = await create_interview(client, token)

    response = await client.post(f"/interviews/{interview_id}/questions", headers=_auth(token))

    # prompt_version and model_name are stored for us, not published to callers.
    assert "prompt_version" not in response.json()[0]
    assert "model_name" not in response.json()[0]


async def test_generate_questions_twice_does_not_duplicate(client: AsyncClient) -> None:
    """The property the unique constraint exists for."""
    token = await register_and_login(client, "idempotent@example.com")
    interview_id = await create_interview(client, token)

    first = await client.post(f"/interviews/{interview_id}/questions", headers=_auth(token))
    second = await client.post(f"/interviews/{interview_id}/questions", headers=_auth(token))

    assert first.status_code == 201
    assert second.status_code == 200
    assert [question["id"] for question in first.json()] == [
        question["id"] for question in second.json()
    ]
    assert await _count_questions(interview_id) == QUESTION_COUNT


async def test_generate_questions_reports_503_when_output_never_validates(
    client: AsyncClient,
    use_provider,
) -> None:
    """Output that cannot be trusted must not reach the database."""
    use_provider(FakeProvider(mode="invalid"))
    token = await register_and_login(client, "invalid@example.com")
    interview_id = await create_interview(client, token)

    response = await client.post(f"/interviews/{interview_id}/questions", headers=_auth(token))

    assert response.status_code == 503, response.text
    error = response.json()["error"]
    assert error["code"] == "AI_INVALID_OUTPUT"
    assert error["request_id"]
    assert await _count_questions(interview_id) == 0


async def test_generate_questions_reports_503_when_provider_is_down(
    client: AsyncClient,
    use_provider,
) -> None:
    use_provider(FakeProvider(mode="unavailable"))
    token = await register_and_login(client, "down@example.com")
    interview_id = await create_interview(client, token)

    response = await client.post(f"/interviews/{interview_id}/questions", headers=_auth(token))

    assert response.status_code == 503, response.text
    assert response.json()["error"]["code"] == "AI_UNAVAILABLE"
    assert await _count_questions(interview_id) == 0


async def test_generate_questions_rejects_another_users_interview(
    client: AsyncClient,
) -> None:
    """404 rather than 403: a stranger must not learn that the id exists."""
    owner = await register_and_login(client, "owner@example.com")
    interview_id = await create_interview(client, owner)
    intruder = await register_and_login(client, "intruder@example.com")

    response = await client.post(
        f"/interviews/{interview_id}/questions",
        headers=_auth(intruder),
    )

    assert response.status_code == 404, response.text
    assert response.json()["error"]["code"] == "INTERVIEW_NOT_FOUND"
    assert await _count_questions(interview_id) == 0


async def test_generate_questions_requires_a_token(client: AsyncClient) -> None:
    token = await register_and_login(client, "anonymous@example.com")
    interview_id = await create_interview(client, token)

    response = await client.post(f"/interviews/{interview_id}/questions")

    assert response.status_code == 401, response.text
    assert response.json()["error"]["code"] == "INVALID_TOKEN"
