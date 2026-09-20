"""SQLAlchemy ORM models. Schema changes always go through an Alembic migration.

Every model is imported here so that ``Base.metadata`` is complete by the time
Alembic compares it against the database; a model that is only imported by the
code that uses it would be invisible to autogenerate.
"""

from app.models.enums import (
    InterviewLevel,
    InterviewStatus,
    QuestionCategory,
    QuestionDifficulty,
)
from app.models.interview import MAX_SKILLS, SKILL_MAX_LENGTH, Interview
from app.models.question import MAX_QUESTIONS, Question
from app.models.user import User

__all__ = [
    "MAX_QUESTIONS",
    "MAX_SKILLS",
    "SKILL_MAX_LENGTH",
    "Interview",
    "InterviewLevel",
    "InterviewStatus",
    "Question",
    "QuestionCategory",
    "QuestionDifficulty",
    "User",
]
