"""The Gemini provider — the only module in this repository that imports the SDK.

Everything vendor-specific is confined to three places: the client built in
``__init__``, ``_call_model`` which is the only method that handles SDK objects,
and ``_is_transient`` which is the only place SDK exception classes are named.
``generate_questions`` itself deals in ``str``, our own schemas and our own
exceptions, so swapping the package is a contained edit.
"""

import asyncio
import logging
import time

from google import genai
from google.genai import errors as genai_errors
from google.genai import types as genai_types
from pydantic import ValidationError

from app.core.exceptions import AIError, AIInvalidOutputError, AIUnavailableError
from app.models import QuestionCategory, QuestionDifficulty
from app.services.ai.base import AIProvider
from app.services.ai.prompt_loader import QUESTION_GENERATION, render_prompt
from app.services.ai.schemas import GeneratedQuestionSet, QuestionPayload, QuestionSpec

logger = logging.getLogger(__name__)

_TOO_MANY_REQUESTS = 429

#: First backoff pause; doubled on each further attempt.
_BACKOFF_BASE_SECONDS = 0.5

#: Written out by hand rather than taken from ``QuestionPayload.model_json_schema()``:
#: Gemini accepts a restricted subset of JSON Schema and rejects the ``$defs``/``$ref``
#: that Pydantic emits for enum fields. Keeping it explicit also means the schema the
#: model is held to cannot change silently when a Pydantic model is refactored.
_RESPONSE_SCHEMA: dict[str, object] = {
    "type": "object",
    "properties": {
        "questions": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "content": {"type": "string"},
                    "category": {
                        "type": "string",
                        "enum": [member.value for member in QuestionCategory],
                    },
                    "skill": {"type": "string"},
                    "difficulty": {
                        "type": "string",
                        "enum": [member.value for member in QuestionDifficulty],
                    },
                },
                "required": ["content", "category", "skill", "difficulty"],
            },
        },
    },
    "required": ["questions"],
}


def _feedback_block(feedback: str | None) -> str:
    """Render the corrective section, or nothing at all on a first attempt."""
    if feedback is None:
        return ""
    return (
        "## Correction\n\n"
        "A previous attempt was rejected. Fix all of the following and return "
        f"the full set again:\n\n{feedback}\n"
    )


def _is_transient(error: Exception) -> bool:
    """The only place SDK exception classes are named.

    Transient means the same request might succeed shortly: a timeout, a rate
    limit, or a server-side failure. A 4xx other than 429 is a fault in our own
    request — wrong key, wrong model, malformed schema — and retrying it only
    burns the caller's deadline.
    """
    if isinstance(error, TimeoutError):
        return True
    if isinstance(error, genai_errors.ServerError):
        return True
    if isinstance(error, genai_errors.ClientError):
        return error.code == _TOO_MANY_REQUESTS
    return False


class GeminiProvider(AIProvider):
    """Generates questions with Google's Gemini models."""

    name = "gemini"

    def __init__(
        self,
        *,
        api_key: str,
        model_name: str,
        timeout_seconds: float,
        max_attempts: int,
    ) -> None:
        """Build the client once; it is reused for the lifetime of the process."""
        self._model_name = model_name
        self._timeout_seconds = timeout_seconds
        self._max_attempts = max_attempts
        self._client = genai.Client(
            api_key=api_key,
            # HttpOptions.timeout is in MILLISECONDS, unlike every other timeout
            # in this codebase. It is set for good measure, but the deadline this
            # application relies on is the asyncio.timeout in _call_with_retry:
            # the SDK's handling of this value is unreliable for long requests,
            # and "every outbound call has an explicit timeout" has to be a
            # property we can demonstrate rather than one we hope for.
            http_options=genai_types.HttpOptions(timeout=int(timeout_seconds * 1000)),
        )

    async def generate_questions(
        self,
        spec: QuestionSpec,
        *,
        feedback: str | None = None,
    ) -> GeneratedQuestionSet:
        """Ask Gemini for questions, and return them if they parse."""
        prompt = render_prompt(
            QUESTION_GENERATION,
            position=spec.position,
            level=spec.level.value,
            skills=", ".join(spec.skills),
            count=spec.count,
            feedback=_feedback_block(feedback),
        )
        raw = await self._call_with_retry(prompt)

        try:
            payload = QuestionPayload.model_validate_json(raw)
        except ValidationError as error:
            # Only the number of problems is logged. The exception's own message
            # quotes the offending input, which is unvalidated model output.
            logger.warning(
                "gemini output failed schema validation (provider=%s model=%s problems=%d)",
                self.name,
                self._model_name,
                error.error_count(),
            )
            raise AIInvalidOutputError from error

        return GeneratedQuestionSet(
            questions=tuple(payload.questions),
            model_name=self._model_name,
            prompt_version=QUESTION_GENERATION.version,
        )

    async def _call_with_retry(self, prompt: str) -> str:
        """Call the model, retrying only failures that might resolve themselves."""
        for attempt in range(1, self._max_attempts + 1):
            started = time.perf_counter()
            try:
                async with asyncio.timeout(self._timeout_seconds):
                    return await self._call_model(prompt)
            except AIError:
                # Already ours, and already final: a content problem is not
                # something an identical second request would fix.
                raise
            except Exception as error:
                # Deliberately broad. This is the vendor boundary, and a raw SDK
                # exception escaping it would surface as a 500 whose traceback
                # can echo request content.
                elapsed_ms = round((time.perf_counter() - started) * 1000)
                transient = _is_transient(error)
                logger.warning(
                    "gemini call failed (provider=%s model=%s attempt=%d/%d "
                    "latency_ms=%d transient=%s error=%s)",
                    self.name,
                    self._model_name,
                    attempt,
                    self._max_attempts,
                    elapsed_ms,
                    transient,
                    type(error).__name__,
                )
                if not transient or attempt == self._max_attempts:
                    raise AIUnavailableError from error
                await asyncio.sleep(_BACKOFF_BASE_SECONDS * 2 ** (attempt - 1))

        # Unreachable: the loop either returns or raises on its final attempt.
        raise AIUnavailableError

    async def _call_model(self, prompt: str) -> str:
        """The only method that handles SDK objects. Returns the raw JSON text."""
        response = await self._client.aio.models.generate_content(
            model=self._model_name,
            contents=prompt,
            config=genai_types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=_RESPONSE_SCHEMA,
                # No tools are passed, so automatic function calling has nothing
                # to do; left enabled the SDK warns about it on every call.
                automatic_function_calling=genai_types.AutomaticFunctionCallingConfig(
                    disable=True,
                ),
            ),
        )
        text = response.text
        if not text:
            # A blocked or empty completion. The call succeeded, the answer is
            # unusable, and asking again would not change that.
            raise AIInvalidOutputError
        return text
