"""Creating and reading interviews."""

import logging
import uuid
from collections.abc import Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import InterviewNotFoundError
from app.models import Interview, InterviewLevel
from app.repositories.interview import InterviewRepository

logger = logging.getLogger(__name__)


class InterviewService:
    """Business logic for interviews. Knows nothing about HTTP."""

    def __init__(self, session: AsyncSession, interviews: InterviewRepository) -> None:
        self._session = session
        self._interviews = interviews

    async def create_interview(
        self,
        *,
        user_id: uuid.UUID,
        position: str,
        level: InterviewLevel,
        skills: list[str],
    ) -> Interview:
        """Create an interview owned by ``user_id``.

        It starts in the ``created`` state; questions arrive separately.
        """
        interview = await self._interviews.create(
            user_id=user_id,
            position=position,
            level=level,
            skills=skills,
        )
        await self._session.commit()
        logger.info("created interview %s for user %s", interview.id, user_id)
        return interview

    async def list_interviews(
        self,
        *,
        user_id: uuid.UUID,
        limit: int,
        offset: int,
    ) -> tuple[Sequence[Interview], int]:
        """Return one page of this user's interviews and the total count."""
        return await self._interviews.list_for_user(user_id, limit=limit, offset=offset)

    async def get_interview(self, *, interview_id: uuid.UUID, user_id: uuid.UUID) -> Interview:
        """Return one of this user's interviews.

        Raises:
            InterviewNotFoundError: it does not exist, or belongs to somebody
                else. The two cases are not distinguished, so the answer cannot
                be used to discover which ids exist.
        """
        interview = await self._interviews.get_for_user(interview_id, user_id)
        if interview is None:
            raise InterviewNotFoundError
        return interview
