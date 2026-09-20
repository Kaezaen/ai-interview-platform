"""Generating, validating and storing an interview's questions."""

import asyncio
import logging
import time
import uuid
from collections.abc import Sequence

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.exceptions import AIInvalidOutputError, AIUnavailableError, InterviewNotFoundError
from app.models import Question
from app.repositories.interview import InterviewRepository
from app.repositories.question import NewQuestion, QuestionRepository
from app.services.ai.base import AIProvider
from app.services.ai.schemas import GeneratedQuestionSet, QuestionSpec
from app.services.ai.validation import canonical_skill, find_problems

logger = logging.getLogger(__name__)

#: How many questions one interview gets. A server-side constant rather than a
#: request field: a second call asking for a different number would have to be
#: ignored to stay idempotent, which is a wart. Adding a field later is additive.
QUESTION_COUNT = 5

#: One corrective retry on top of the first attempt, and no more. A model that
#: has ignored the rules twice is not going to get it right on the third go.
_CONTENT_ATTEMPTS = 2

#: Slack for validation and the round trips around the provider itself.
_DEADLINE_SLACK_SECONDS = 5.0

#: Name of the constraint that makes generation idempotent.
_ORDINAL_UNIQUE_CONSTRAINT = "uq_questions_interview_id_ordinal"


class QuestionService:
    """Business logic for question generation. Knows nothing about HTTP."""

    def __init__(
        self,
        session: AsyncSession,
        questions: QuestionRepository,
        interviews: InterviewRepository,
        ai: AIProvider,
    ) -> None:
        self._session = session
        self._questions = questions
        self._interviews = interviews
        self._ai = ai

        settings = get_settings()
        # The transport budget multiplies with the content budget, so the sum of
        # the parts is not a bound anybody would guess. This is the real ceiling
        # on how long one request can hold a worker.
        self._deadline_seconds = (
            settings.ai_request_timeout_seconds * settings.ai_max_attempts * _CONTENT_ATTEMPTS
            + _DEADLINE_SLACK_SECONDS
        )

    async def generate_questions(
        self,
        *,
        interview_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> tuple[Sequence[Question], bool]:
        """Return this interview's questions, generating them if it has none.

        Returns the rows and whether this call is the one that created them, so
        the router can answer 201 the first time and 200 on every repeat.

        Raises:
            InterviewNotFoundError: it does not exist, or belongs to somebody else.
            AIUnavailableError: the provider could not be reached in time.
            AIInvalidOutputError: the provider answered, twice, with something
                that does not match what was asked for.
        """
        interview = await self._interviews.get_for_user(interview_id, user_id)
        if interview is None:
            raise InterviewNotFoundError

        existing = await self._questions.list_for_interview(interview_id)

        # Ends the read transaction and hands the connection back before the AI
        # call. Without this the pool is held for the whole of it, and enough
        # concurrent generations would block every other request, reads included.
        # expire_on_commit=False keeps `interview` readable afterwards.
        await self._session.commit()

        if existing:
            return existing, False

        spec = QuestionSpec(
            position=interview.position,
            level=interview.level,
            skills=tuple(interview.skills),
            count=QUESTION_COUNT,
        )
        generated = await self._generate(spec)

        try:
            rows = await self._persist(interview_id, spec, generated)
            await self._interviews.mark_questions_generated(interview)
            await self._session.commit()
        except IntegrityError as error:
            await self._session.rollback()
            if not _violates_ordinal_uniqueness(error):
                raise
            # Lost a race: another request generated for this interview while
            # this one was waiting on the provider. Its rows are the real ones.
            logger.info("concurrent generation lost the race (interview=%s)", interview_id)
            rows = await self._questions.list_for_interview(interview_id)
            await self._session.commit()
            return rows, False

        return rows, True

    async def _generate(self, spec: QuestionSpec) -> GeneratedQuestionSet:
        """Ask the provider, and accept the answer only if it fits the spec."""
        started = time.perf_counter()
        try:
            async with asyncio.timeout(self._deadline_seconds):
                result = await self._ask(spec)
        except TimeoutError as error:
            logger.warning(
                "ai generation exceeded its deadline (provider=%s deadline_s=%.1f)",
                self._ai.name,
                self._deadline_seconds,
            )
            raise AIUnavailableError from error

        logger.info(
            "generated questions (provider=%s model=%s prompt_version=%s count=%d latency_ms=%d)",
            self._ai.name,
            result.model_name,
            result.prompt_version,
            len(result.questions),
            round((time.perf_counter() - started) * 1000),
        )
        return result

    async def _ask(self, spec: QuestionSpec) -> GeneratedQuestionSet:
        """Call the provider, once more with feedback if the answer was wrong.

        The provider's own retry covers transient transport failures. This one
        covers an answer that arrived intact but did not follow the request —
        the two are deliberately in different layers so neither can stand in for
        the other.
        """
        feedback: str | None = None
        for attempt in range(1, _CONTENT_ATTEMPTS + 1):
            result = await self._ai.generate_questions(spec, feedback=feedback)
            problems = find_problems(spec, result.questions)
            if not problems:
                return result

            logger.warning(
                "ai output rejected (provider=%s attempt=%d/%d problems=%s)",
                self._ai.name,
                attempt,
                _CONTENT_ATTEMPTS,
                "; ".join(problems),
            )
            feedback = "; ".join(problems)

        raise AIInvalidOutputError

    async def _persist(
        self,
        interview_id: uuid.UUID,
        spec: QuestionSpec,
        generated: GeneratedQuestionSet,
    ) -> Sequence[Question]:
        """Write the validated set, storing the interview's spelling of each skill."""
        rows = [
            NewQuestion(
                ordinal=ordinal,
                content=question.content,
                category=question.category,
                # Validation already proved a match exists; store the requested
                # spelling rather than the model's echo of it.
                skill=canonical_skill(question.skill, spec.skills) or question.skill,
                difficulty=question.difficulty,
            )
            for ordinal, question in enumerate(generated.questions, start=1)
        ]
        return await self._questions.create_many(
            interview_id=interview_id,
            questions=rows,
            prompt_version=generated.prompt_version,
            model_name=generated.model_name,
        )


def _violates_ordinal_uniqueness(error: IntegrityError) -> bool:
    """Report whether ``error`` is the questions ordinal unique violation.

    Same shape as the registration guard in ``app/services/auth.py``: the
    constraint name is read from the driver exception rather than matched inside
    the server's message text, so an unrelated integrity error is never reported
    as a lost race.
    """
    driver_error = getattr(error, "orig", None)
    for candidate in (driver_error, getattr(driver_error, "__cause__", None)):
        name = getattr(candidate, "constraint_name", None)
        if name is not None:
            return bool(name == _ORDINAL_UNIQUE_CONSTRAINT)

    return _ORDINAL_UNIQUE_CONSTRAINT in str(driver_error)
