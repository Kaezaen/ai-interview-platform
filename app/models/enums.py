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
    ``completed``. Only ``created`` is reachable today; the rest arrive with
    question generation and answering.
    """

    CREATED = "created"
    QUESTIONS_GENERATED = "questions_generated"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
