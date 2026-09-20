"""Request and response schemas for the interview endpoints."""

from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator

from app.models import MAX_SKILLS, SKILL_MAX_LENGTH, InterviewLevel, InterviewStatus

#: Long enough for "Senior Backend Engineer (Payments)", short enough to stay a
#: job title rather than a description. SKILL_MAX_LENGTH is imported rather than
#: repeated: it is also the length of the questions.skill column.
POSITION_MAX_LENGTH = 120

Position = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=2, max_length=POSITION_MAX_LENGTH),
]
Skill = Annotated[str, StringConstraints(strip_whitespace=True, max_length=SKILL_MAX_LENGTH)]


class InterviewCreate(BaseModel):
    """A new interview session."""

    position: Position = Field(examples=["Software Engineer"])
    level: InterviewLevel = Field(examples=["junior"])
    skills: Annotated[list[Skill], Field(min_length=1, max_length=MAX_SKILLS)] = Field(
        examples=[["Python", "FastAPI", "PostgreSQL"]]
    )

    @field_validator("level", mode="before")
    @classmethod
    def _accept_any_case(cls, value: object) -> object:
        """Accept "Junior" as well as "junior"; the stored value is lowercase."""
        return value.lower() if isinstance(value, str) else value

    @field_validator("skills", mode="after")
    @classmethod
    def _normalise_skills(cls, value: list[str]) -> list[str]:
        """Collapse whitespace, drop blanks, and remove case-insensitive repeats.

        Duplicates are removed here rather than in the database because they are
        a client mistake with an obvious correct reading, not a conflict.
        """
        seen: set[str] = set()
        skills: list[str] = []
        for raw in value:
            skill = " ".join(raw.split())
            if not skill or skill.casefold() in seen:
                continue
            seen.add(skill.casefold())
            skills.append(skill)

        if not skills:
            raise ValueError("at least one non-empty skill is required")
        return skills


class InterviewRead(BaseModel):
    """An interview as the API exposes it.

    ``user_id`` is left out deliberately: an interview is only ever returned to
    the user who owns it, so the field would carry no information.
    """

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    position: str
    level: InterviewLevel
    skills: list[str]
    status: InterviewStatus
    created_at: datetime
    updated_at: datetime
