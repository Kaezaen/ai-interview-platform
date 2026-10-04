"""The ``interviews`` table."""

import uuid

from sqlalchemy import CheckConstraint, ForeignKey, Index, String, Text, text
from sqlalchemy.dialects.postgresql import ARRAY, ENUM, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import InterviewLevel, InterviewStatus

#: Native PostgreSQL enum types. ``create_type=False`` keeps their creation in
#: the hands of the migration rather than letting SQLAlchemy emit CREATE TYPE as
#: a side effect of creating a table. ``values_callable`` stores the lowercase
#: member values instead of the uppercase member names.
_LEVEL_ENUM = ENUM(
    InterviewLevel,
    name="interview_level",
    create_type=False,
    values_callable=lambda enum_type: [member.value for member in enum_type],
)
_STATUS_ENUM = ENUM(
    InterviewStatus,
    name="interview_status",
    create_type=False,
    values_callable=lambda enum_type: [member.value for member in enum_type],
)

#: An interview aimed at more skills than this is not a focused interview, and
#: the bound keeps a single row from growing without limit.
MAX_SKILLS = 10

#: Long enough for "Distributed Systems", short enough to stay a label. Shared
#: with questions.skill so a generated skill can never exceed what a request may
#: ask for, and with the request schema so the two cannot drift apart.
SKILL_MAX_LENGTH = 60


class Interview(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """One interview session belonging to exactly one user."""

    __tablename__ = "interviews"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        # An interview is meaningless without its owner, so deleting the account
        # takes its interviews with it rather than leaving orphans behind.
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    position: Mapped[str] = mapped_column(String(120), nullable=False)
    level: Mapped[InterviewLevel] = mapped_column(_LEVEL_ENUM, nullable=False)

    # Skills are free-form labels used to steer question generation; there is no
    # skill catalogue to reference, so they are stored denormalised as text[].
    skills: Mapped[list[str]] = mapped_column(ARRAY(Text), nullable=False)

    status: Mapped[InterviewStatus] = mapped_column(
        _STATUS_ENUM,
        nullable=False,
        server_default=text(f"'{InterviewStatus.CREATED.value}'::interview_status"),
    )

    __table_args__ = (
        CheckConstraint(
            f"cardinality(skills) BETWEEN 1 AND {MAX_SKILLS}",
            name="skills_len",
        ),
        # Matches GET /interviews exactly: filter by owner, newest first, with id
        # as the tiebreaker for rows written inside the same transaction (which
        # share a now() timestamp). PostgreSQL scans this index backwards for the
        # descending order, so no DESC columns are needed.
        Index("ix_interviews_user_id_created_at_id", "user_id", "created_at", "id"),
    )

    def __repr__(self) -> str:
        """Identify the row without echoing its contents."""
        return f"<Interview id={self.id} status={self.status}>"
