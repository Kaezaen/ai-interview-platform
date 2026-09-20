"""The provider interface that business logic depends on.

A service may import this module. It may not import a concrete provider, and no
vendor SDK may be imported anywhere in this file — that is what keeps the choice
of provider from leaking into the rest of the application.
"""

from abc import ABC, abstractmethod

from app.services.ai.schemas import GeneratedQuestionSet, QuestionSpec


class AIProvider(ABC):
    """Generates interview questions, whatever is actually answering."""

    #: Short identifier used in log lines, e.g. "fake" or "gemini".
    name: str

    @abstractmethod
    async def generate_questions(
        self,
        spec: QuestionSpec,
        *,
        feedback: str | None = None,
    ) -> GeneratedQuestionSet:
        """Produce ``spec.count`` questions for the given position and skills.

        Implementations own transport only: an explicit timeout, and a bounded
        retry for transient failures. Whether the answer is *correct* for the
        spec is decided by the caller, which may then call this once more with
        ``feedback`` describing what was wrong.

        Args:
            spec: Position, level, skills, and how many questions to produce.
            feedback: Problems found in a previous attempt, to be shown to the
                model. ``None`` on the first attempt.

        Raises:
            AIUnavailableError: The provider could not be reached or kept failing.
            AIInvalidOutputError: The answer was not parseable JSON, or did not
                match the expected schema.
        """

    async def aclose(self) -> None:
        """Release anything the provider holds open.

        Concrete, not abstract, and a no-op by default: only a provider with a
        network client has something to close, and the lifespan should not have
        to know which ones those are.
        """
        return None
