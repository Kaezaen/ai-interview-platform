"""The ``questions`` table."""

import uuid

from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import ENUM, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import QuestionCategory, QuestionDifficulty
from app.models.interview import SKILL_MAX_LENGTH

#: Native PostgreSQL enum types, created by the migration rather than as a side
#: effect of creating the table. Same recipe as the interview enums.
_CATEGORY_ENUM = ENUM(
    QuestionCategory,
    name="question_category",
    create_type=False,
    values_callable=lambda enum_type: [member.value for member in enum_type],
)
_DIFFICULTY_ENUM = ENUM(
    QuestionDifficulty,
    name="question_difficulty",
    create_type=False,
    values_callable=lambda enum_type: [member.value for member in enum_type],
)

#: Upper bound on one interview's questions. The generated count is smaller; this
#: is the bound the database enforces, so raising it later is a migration.
MAX_QUESTIONS = 10

#: A question shorter than this is not a question. The upper bound stops a model
#: that has started rambling from writing an essay into a row.
CONTENT_MIN_LENGTH = 10
CONTENT_MAX_LENGTH = 2000


class Question(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """One generated interview question, belonging to exactly one interview."""

    __tablename__ = "questions"

    interview_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        # A question outlives neither its interview nor the account behind it.
        ForeignKey("interviews.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Explicit 1-based position. created_at cannot order these: it comes from
    # server_default=now() and every row written in one transaction shares it.
    # It doubles as the idempotency key — see the unique constraint below.
    ordinal: Mapped[int] = mapped_column(SmallInteger, nullable=False)

    content: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[QuestionCategory] = mapped_column(_CATEGORY_ENUM, nullable=False)

    # The interview's own spelling of the skill, not the model's echo of it, and
    # bounded by the same length a request may ask for.
    skill: Mapped[str] = mapped_column(String(SKILL_MAX_LENGTH), nullable=False)

    difficulty: Mapped[QuestionDifficulty] = mapped_column(_DIFFICULTY_ENUM, nullable=False)

    # Traceability. Without these a row cannot be explained once the prompt is
    # rewritten or the model is swapped, and they cannot be backfilled.
    prompt_version: Mapped[str] = mapped_column(String(32), nullable=False)
    model_name: Mapped[str] = mapped_column(String(100), nullable=False)

    __table_args__ = (
        # What actually makes generation idempotent. The read-then-write check in
        # the service is a fast path; this is the guarantee, and it holds when two
        # requests race. Its btree also serves "WHERE interview_id = ? ORDER BY
        # ordinal", so the table needs no further index.
        # Unnamed on purpose: the uq naming convention has no
        # %(constraint_name)s token, so an explicit name would be taken
        # verbatim instead of becoming uq_questions_interview_id_ordinal.
        UniqueConstraint("interview_id", "ordinal"),
        CheckConstraint(
            f"ordinal BETWEEN 1 AND {MAX_QUESTIONS}",
            name="ordinal_range",
        ),
        CheckConstraint(
            f"char_length(content) BETWEEN {CONTENT_MIN_LENGTH} AND {CONTENT_MAX_LENGTH}",
            name="content_len",
        ),
    )

    def __repr__(self) -> str:
        """Identify the row without echoing the question itself."""
        return f"<Question id={self.id} interview_id={self.interview_id} ordinal={self.ordinal}>"
