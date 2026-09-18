"""Interview sessions belonging to the current user."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Query, status

from app.api.deps import CurrentUser, InterviewServiceDep
from app.schemas.common import ErrorResponse, Page
from app.schemas.interview import InterviewCreate, InterviewRead

router = APIRouter(prefix="/interviews", tags=["interviews"])

#: A page big enough to be useful, capped so one request cannot ask for
#: everything at once.
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100

_UNAUTHORIZED = {
    status.HTTP_401_UNAUTHORIZED: {
        "model": ErrorResponse,
        "description": "Missing, invalid, or expired token",
    }
}


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    summary="Create an interview",
    response_model=InterviewRead,
    responses=_UNAUTHORIZED,
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
    responses=_UNAUTHORIZED,
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
    responses={
        **_UNAUTHORIZED,
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": "No such interview for this user",
        },
    },
)
async def read_interview(
    interview_id: uuid.UUID,
    user: CurrentUser,
    interviews: InterviewServiceDep,
) -> InterviewRead:
    """Return one interview, provided it belongs to the current user."""
    interview = await interviews.get_interview(interview_id=interview_id, user_id=user.id)
    return InterviewRead.model_validate(interview)
