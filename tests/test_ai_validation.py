"""Semantic validation of generated questions. Pure functions, no database."""

import pytest

from app.models import InterviewLevel, QuestionCategory, QuestionDifficulty
from app.services.ai.schemas import GeneratedQuestion, QuestionSpec
from app.services.ai.validation import canonical_skill, find_problems

_SPEC = QuestionSpec(
    position="Backend Engineer",
    level=InterviewLevel.MID,
    skills=("Python", "FastAPI"),
    count=2,
)


def _question(content: str, skill: str) -> GeneratedQuestion:
    return GeneratedQuestion(
        content=content,
        category=QuestionCategory.TECHNICAL,
        skill=skill,
        difficulty=QuestionDifficulty.MEDIUM,
    )


def test_find_problems_accepts_a_matching_set() -> None:
    questions = [
        _question("Bagaimana kamu mengelola dependency di Python?", "Python"),
        _question("Kapan kamu memakai dependency injection di FastAPI?", "FastAPI"),
    ]

    assert find_problems(_SPEC, questions) == []


@pytest.mark.parametrize("count", [1, 3])
def test_find_problems_rejects_the_wrong_number_of_questions(count: int) -> None:
    questions = [
        _question(f"Pertanyaan nomor {index} tentang Python di produksi.", "Python")
        for index in range(count)
    ]

    problems = find_problems(_SPEC, questions)

    assert any("expected exactly 2 questions" in problem for problem in problems)


def test_find_problems_rejects_a_skill_that_was_not_requested() -> None:
    questions = [
        _question("Bagaimana kamu mengelola dependency di Python?", "Python"),
        _question("Bagaimana kamu menangani goroutine leak di Go?", "Go"),
    ]

    problems = find_problems(_SPEC, questions)

    assert any("'Go' was not requested" in problem for problem in problems)


def test_find_problems_rejects_duplicate_questions() -> None:
    repeated = "Bagaimana kamu mengelola dependency di Python?"
    questions = [_question(repeated, "Python"), _question(repeated.upper(), "FastAPI")]

    problems = find_problems(_SPEC, questions)

    assert any("duplicates an earlier question" in problem for problem in problems)


def test_find_problems_never_quotes_the_question_itself() -> None:
    """Problem strings are fed back to the model and written to logs."""
    secret = "Sebutkan satu hal yang tidak boleh bocor ke log."
    questions = [_question(secret, "Rust"), _question(secret, "Rust")]

    for problem in find_problems(_SPEC, questions):
        assert secret not in problem


def test_find_problems_accepts_a_differently_capitalised_skill() -> None:
    """A request keeps the user's capitalisation, so the model's may differ."""
    questions = [
        _question("Bagaimana kamu mengelola dependency di Python?", "python"),
        _question("Kapan kamu memakai dependency injection di FastAPI?", "fastapi"),
    ]

    assert find_problems(_SPEC, questions) == []


def test_canonical_skill_returns_the_requested_spelling() -> None:
    assert canonical_skill("PYTHON", ("Python", "FastAPI")) == "Python"


def test_canonical_skill_returns_none_for_an_unrequested_skill() -> None:
    assert canonical_skill("Go", ("Python", "FastAPI")) is None
