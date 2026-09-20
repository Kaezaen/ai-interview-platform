"""Interview sessions belonging to the current user."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Query, Response, status

from app.api.deps import CurrentUser, InterviewServiceDep, QuestionServiceDep
from app.api.errors import error_responses
from app.schemas.common import Page
from app.schemas.interview import InterviewCreate, InterviewRead
from app.schemas.question import QuestionRead

router = APIRouter(prefix="/interviews", tags=["interviews"])

#: A page big enough to be useful, capped so one request cannot ask for
#: everything at once.
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100

_AUTH_FAILURES = (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN)


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    summary="Create an interview",
    response_model=InterviewRead,
    responses=error_responses(*_AUTH_FAILURES, status.HTTP_422_UNPROCESSABLE_ENTITY),
)
async def create_interview(
    payload: InterviewCreate,
    user: CurrentUser,
    interviews: InterviewServiceDep,
) -> InterviewRead:
    """Create an interview owned by the current user."""
    interview = await interviews.create_interview(
        user_id=user.id,
        position=payload.position,
        level=payload.level,
        skills=payload.skills,
    )
    return InterviewRead.model_validate(interview)


@router.get(
    "",
    summary="List the current user's interviews",
    response_model=Page[InterviewRead],
    responses=error_responses(*_AUTH_FAILURES, status.HTTP_422_UNPROCESSABLE_ENTITY),
)
async def list_interviews(
    user: CurrentUser,
    interviews: InterviewServiceDep,
    limit: Annotated[int, Query(ge=1, le=MAX_PAGE_SIZE)] = DEFAULT_PAGE_SIZE,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> Page[InterviewRead]:
    """Return one page of the current user's interviews, newest first."""
    rows, total = await interviews.list_interviews(user_id=user.id, limit=limit, offset=offset)
    return Page[InterviewRead](
        items=[InterviewRead.model_validate(row) for row in rows],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/{interview_id}",
    summary="Read one interview",
    response_model=InterviewRead,
    responses=error_responses(
        *_AUTH_FAILURES,
        status.HTTP_404_NOT_FOUND,
        status.HTTP_422_UNPROCESSABLE_ENTITY,
    ),
)
async def read_interview(
    interview_id: uuid.UUID,
    user: CurrentUser,
    interviews: InterviewServiceDep,
) -> InterviewRead:
    """Return one interview, provided it belongs to the current user."""
    interview = await interviews.get_interview(interview_id=interview_id, user_id=user.id)
    return InterviewRead.model_validate(interview)


@router.post(
    "/{interview_id}/questions",
    status_code=status.HTTP_201_CREATED,
    summary="Generate this interview's questions",
    response_model=list[QuestionRead],
    responses=error_responses(
        *_AUTH_FAILURES,
        status.HTTP_404_NOT_FOUND,
        status.HTTP_422_UNPROCESSABLE_ENTITY,
        status.HTTP_503_SERVICE_UNAVAILABLE,
    ),
)
async def generate_questions(
    interview_id: uuid.UUID,
    user: CurrentUser,
    questions: QuestionServiceDep,
    response: Response,
) -> list[QuestionRead]:
    """Generate and store this interview's questions.

    Idempotent: the first call generates and answers 201, and every later call
    returns the same questions with 200 without spending another AI request. A
    client that retries after a timeout therefore always ends up with one set.
    """
    rows, created = await questions.generate_questions(
        interview_id=interview_id,
        user_id=user.id,
    )
    if not created:
        response.status_code = status.HTTP_200_OK
    return [QuestionRead.model_validate(row) for row in rows]
