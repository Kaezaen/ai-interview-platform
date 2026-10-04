"""Enumerations that are part of the domain vocabulary.

They live apart from the ORM classes so that Pydantic schemas can share the same
definitions without importing a mapped class.
"""

from enum import StrEnum


class InterviewLevel(StrEnum):
    """Seniority the interview is aimed at."""

    JUNIOR = "junior"
    MID = "mid"
    SENIOR = "senior"
    LEAD = "lead"


class InterviewStatus(StrEnum):
    """Lifecycle of an interview.

    The flow is ``created`` -> ``questions_generated`` -> ``in_progress`` ->
    ``completed``. Generating questions performs the first transition; the rest
    arrive with answering and evaluation.
    """

    CREATED = "created"
    QUESTIONS_GENERATED = "questions_generated"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class QuestionCategory(StrEnum):
    """What kind of thing a question probes.

    The set is fixed rather than free text because it is stored as a native
    PostgreSQL enum: adding a value later needs ALTER TYPE ... ADD VALUE, which
    cannot be rolled back and has no counterpart for removal, so a migration
    adding one could not have an honest downgrade.
    """

    TECHNICAL = "technical"
    BEHAVIORAL = "behavioral"
    SITUATIONAL = "situational"
    SYSTEM_DESIGN = "system_design"


class QuestionDifficulty(StrEnum):
    """How demanding a question is, relative to the interview's level.

    Relative, not absolute: a "hard" question for a junior interview is not the
    same question as a "hard" one for a lead.
    """

    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
