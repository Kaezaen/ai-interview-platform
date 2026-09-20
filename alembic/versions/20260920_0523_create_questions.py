"""create questions

Revision ID: f06892d85ea0
Revises: 779f98d47a63
Create Date: 2026-09-20 05:23:31.481865+00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "f06892d85ea0"
down_revision: str | None = "779f98d47a63"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Same treatment as the first revision: autogenerate inlines the enums into
# create_table, which creates the types as a side effect and leaves a downgrade
# that drops the table but keeps the types — so the next upgrade fails with
# "type already exists". Creating and dropping them explicitly is what makes the
# revision reversible.
question_category = postgresql.ENUM(
    "technical",
    "behavioral",
    "situational",
    "system_design",
    name="question_category",
    create_type=False,
)
question_difficulty = postgresql.ENUM(
    "easy",
    "medium",
    "hard",
    name="question_difficulty",
    create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    question_category.create(bind, checkfirst=False)
    question_difficulty.create(bind, checkfirst=False)

    op.create_table(
        "questions",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("interview_id", sa.UUID(), nullable=False),
        sa.Column("ordinal", sa.SmallInteger(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("category", question_category, nullable=False),
        sa.Column("skill", sa.String(length=60), nullable=False),
        sa.Column("difficulty", question_difficulty, nullable=False),
        sa.Column("prompt_version", sa.String(length=32), nullable=False),
        sa.Column("model_name", sa.String(length=100), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "char_length(content) BETWEEN 10 AND 2000",
            name=op.f("ck_questions_content_len"),
        ),
        sa.CheckConstraint(
            "ordinal BETWEEN 1 AND 10",
            name=op.f("ck_questions_ordinal_range"),
        ),
        sa.ForeignKeyConstraint(
            ["interview_id"],
            ["interviews.id"],
            name=op.f("fk_questions_interview_id_interviews"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_questions")),
        # What makes generation idempotent under a race, and the index that
        # serves "this interview's questions, in order".
        sa.UniqueConstraint(
            "interview_id",
            "ordinal",
            name=op.f("uq_questions_interview_id_ordinal"),
        ),
    )


def downgrade() -> None:
    op.drop_table("questions")

    # After the table, since a type cannot be dropped while a column still uses it.
    bind = op.get_bind()
    question_difficulty.drop(bind, checkfirst=False)
    question_category.drop(bind, checkfirst=False)
