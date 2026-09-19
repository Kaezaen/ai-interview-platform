"""Queries against the ``interviews`` table."""

import uuid
from collections.abc import Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Interview, InterviewLevel


class InterviewRepository:
    """The only place ``interviews`` is queried.

    Every read takes the owner's id and puts it in the WHERE clause. Ownership
    is a filter, not an assertion made after the fact, so a row belonging to
    someone else is never loaded in the first place.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        user_id: uuid.UUID,
        position: str,
        level: InterviewLevel,
        skills: list[str],
    ) -> Interview:
        """Stage a new interview and flush it, so its id and defaults are set."""
        interview = Interview(
            user_id=user_id,
            position=position,
            level=level,
            skills=skills,
        )
        self._session.add(interview)
        await self._session.flush()
        await self._session.refresh(interview)
        return interview

    async def get_for_user(
        self,
        interview_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> Interview | None:
        """Return the interview if it exists *and* belongs to this user."""
        result = await self._session.execute(
            select(Interview).where(
                Interview.id == interview_id,
                Interview.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    async def list_for_user(
        self,
        user_id: uuid.UUID,
        *,
        limit: int,
        offset: int,
    ) -> tuple[Sequence[Interview], int]:
        """Return one page of this user's interviews, newest first, and the total.

        The ordering matches ix_interviews_user_id_created_at_id. id breaks ties
        because rows written in the same transaction share a now() timestamp,
        which would otherwise let offset pagination repeat or skip a row.
        """
        total = await self._session.scalar(
            select(func.count()).select_from(Interview).where(Interview.user_id == user_id)
        )
        result = await self._session.execute(
            select(Interview)
            .where(Interview.user_id == user_id)
            .order_by(Interview.created_at.desc(), Interview.id.desc())
            .limit(limit)
            .offset(offset)
        )
        return result.scalars().all(), total or 0
