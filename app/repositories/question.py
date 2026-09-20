"""Queries against the ``questions`` table."""

import uuid
from collections.abc import Sequence
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Question, QuestionCategory, QuestionDifficulty


@dataclass(frozen=True, slots=True)
class NewQuestion:
    """One row to be written.

    A plain value object rather than an AI schema: the repository must not know
    where a question came from, only what a row looks like.
    """

    ordinal: int
    content: str
    category: QuestionCategory
    skill: str
    difficulty: QuestionDifficulty


class QuestionRepository:
    """The only place ``questions`` is queried.

    Reads take an interview id, never a user id: ownership is established once,
    against the interview, before anything here is called.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_for_interview(self, interview_id: uuid.UUID) -> Sequence[Question]:
        """Return an interview's questions in the order they were generated."""
        result = await self._session.execute(
            select(Question).where(Question.interview_id == interview_id).order_by(Question.ordinal)
        )
        return result.scalars().all()

    async def create_many(
        self,
        *,
        interview_id: uuid.UUID,
        questions: Sequence[NewQuestion],
        prompt_version: str,
        model_name: str,
    ) -> Sequence[Question]:
        """Write a whole set of questions and return the stored rows.

        ``prompt_version`` and ``model_name`` are per-set rather than per-row:
        one generation produced all of them, and storing them separately would
        allow rows of the same set to disagree.
        """
        self._session.add_all(
            [
                Question(
                    interview_id=interview_id,
                    ordinal=question.ordinal,
                    content=question.content,
                    category=question.category,
                    skill=question.skill,
                    difficulty=question.difficulty,
                    prompt_version=prompt_version,
                    model_name=model_name,
                )
                for question in questions
            ]
        )
        await self._session.flush()
        return await self._reload(interview_id)

    async def _reload(self, interview_id: uuid.UUID) -> Sequence[Question]:
        """Re-select the rows so server-generated columns are populated.

        ``created_at`` and ``updated_at`` come from ``server_default=now()`` and
        are not filled in by ``flush()`` alone. Reading one of them afterwards
        would trigger a lazy load, which on an async session raises instead of
        quietly emitting a query. One SELECT with ``populate_existing`` fills
        every row at once.
        """
        result = await self._session.execute(
            select(Question)
            .where(Question.interview_id == interview_id)
            .order_by(Question.ordinal)
            .execution_options(populate_existing=True)
        )
        return result.scalars().all()
