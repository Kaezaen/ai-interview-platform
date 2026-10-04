"""Semantic validation of generated questions against the spec that asked for them.

Pure functions: no I/O, no provider, no database. They answer one question — does
this answer the request that was actually made — which is a statement about the
business, not about a vendor. Keeping it here means every provider is held to it,
including ones written later.

Shape is *not* checked here. That the fields exist, that the strings fit, and
that ``category``/``difficulty`` are valid enum members is already guaranteed by
``GeneratedQuestion``; anything reaching this module has parsed.
"""

from collections.abc import Sequence

from app.services.ai.schemas import GeneratedQuestion, QuestionSpec


def canonical_skill(skill: str, requested: Sequence[str]) -> str | None:
    """Return the requested spelling of ``skill``, or ``None`` if unrequested.

    Matching is case-insensitive on purpose. A request deduplicates skills with
    ``casefold`` but keeps the user's capitalisation, so a model answering
    "python" to a requested "Python" is correct — and the row should still store
    "Python", the spelling the interview was created with.
    """
    folded = skill.casefold()
    return next((item for item in requested if item.casefold() == folded), None)


def find_problems(spec: QuestionSpec, questions: Sequence[GeneratedQuestion]) -> list[str]:
    """List everything wrong with ``questions``; empty means usable.

    Every string is safe to log and safe to hand back to the model: problems are
    described by position and reason, and never quote the question text.
    """
    problems: list[str] = []

    if len(questions) != spec.count:
        problems.append(f"expected exactly {spec.count} questions, got {len(questions)}")

    seen: set[str] = set()
    for index, question in enumerate(questions, start=1):
        if canonical_skill(question.skill, spec.skills) is None:
            problems.append(f"question {index}: skill {question.skill!r} was not requested")

        fingerprint = " ".join(question.content.casefold().split())
        if fingerprint in seen:
            problems.append(f"question {index}: duplicates an earlier question")
        seen.add(fingerprint)

    return problems
