"""Schemas for the AI boundary.

Deliberately separate from the API schemas and from the ORM models. What a model
is asked for and what it answers is a contract with a vendor; letting the request
schema or a mapped class double as that contract would mean a change on either
side silently redefines the other.

Nothing here is trusted yet. These types only establish that the answer has the
right *shape*; whether it answers the question that was asked is decided in
``validation.py``.
"""

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator

from app.models import (
    MAX_QUESTIONS,
    SKILL_MAX_LENGTH,
    InterviewLevel,
    QuestionCategory,
    QuestionDifficulty,
)
from app.models.question import CONTENT_MAX_LENGTH, CONTENT_MIN_LENGTH

Content = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        min_length=CONTENT_MIN_LENGTH,
        max_length=CONTENT_MAX_LENGTH,
    ),
]
Skill = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=SKILL_MAX_LENGTH),
]


class QuestionSpec(BaseModel):
    """What the application asks a provider to produce.

    Frozen and built from tuples so that the same spec can be handed to a retry
    without any chance of the first attempt having mutated it.
    """

    model_config = ConfigDict(frozen=True)

    position: str
    level: InterviewLevel
    skills: tuple[str, ...] = Field(min_length=1)
    count: int = Field(ge=1, le=MAX_QUESTIONS)


class GeneratedQuestion(BaseModel):
    """One question exactly as a provider returned it.

    ``extra="ignore"`` because a model that volunteers an extra key has not done
    anything wrong; a strict setting would turn a harmless surplus into a 503.
    """

    model_config = ConfigDict(extra="ignore")

    content: Content
    category: QuestionCategory
    skill: Skill
    difficulty: QuestionDifficulty

    @field_validator("category", "difficulty", mode="before")
    @classmethod
    def _accept_any_case(cls, value: object) -> object:
        """Accept "Technical" as well as "technical"; the stored value is lowercase."""
        return value.lower() if isinstance(value, str) else value


class QuestionPayload(BaseModel):
    """The whole JSON document a provider is expected to return."""

    model_config = ConfigDict(extra="ignore")

    questions: list[GeneratedQuestion]


class GeneratedQuestionSet(BaseModel):
    """A shape-valid payload, together with the provenance that explains it.

    ``model_name`` and ``prompt_version`` travel with the questions rather than
    being looked up when the rows are written, so the values stored are the ones
    that actually produced this text.
    """

    # model_name would otherwise collide with Pydantic's protected "model_" prefix.
    model_config = ConfigDict(frozen=True, protected_namespaces=())

    questions: tuple[GeneratedQuestion, ...]
    model_name: str
    prompt_version: str
