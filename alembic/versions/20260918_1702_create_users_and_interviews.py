"""create users and interviews

Revision ID: 779f98d47a63
Revises:
Create Date: 2026-09-18 17:02:57.286560+00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "779f98d47a63"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# The enum types are created and dropped explicitly rather than as a side effect
# of creating the table. Autogenerate leaves this out, and the result is a
# downgrade that drops the tables but leaves the types behind, so the next
# upgrade fails with "type already exists".
interview_level = postgresql.ENUM(
    "junior",
    "mid",
    "senior",
    "lead",
    name="interview_level",
    create_type=False,
)
interview_status = postgresql.ENUM(
    "created",
    "questions_generated",
    "in_progress",
    "completed",
    name="interview_status",
    create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    interview_level.create(bind, checkfirst=False)
    interview_status.create(bind, checkfirst=False)

    op.create_table(
        "users",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
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
        sa.PrimaryKeyConstraint("id", name=op.f("pk_users")),
        sa.UniqueConstraint("email", name=op.f("uq_users_email")),
    )

    op.create_table(
        "interviews",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("position", sa.String(length=120), nullable=False),
        sa.Column("level", interview_level, nullable=False),
        sa.Column("skills", postgresql.ARRAY(sa.Text()), nullable=False),
        sa.Column(
            "status",
            interview_status,
            server_default=sa.text("'created'::interview_status"),
            nullable=False,
        ),
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
            "cardinality(skills) BETWEEN 1 AND 10",
            name=op.f("ck_interviews_skills_len"),
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_interviews_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_interviews")),
    )

    # Serves "filter by owner, newest first" with id as the tiebreaker.
    op.create_index(
        "ix_interviews_user_id_created_at_id",
        "interviews",
        ["user_id", "created_at", "id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_interviews_user_id_created_at_id", table_name="interviews")
    op.drop_table("interviews")
    op.drop_table("users")

    # Dropped after the tables, since a type cannot be dropped while a column
    # still uses it.
    bind = op.get_bind()
    interview_status.drop(bind, checkfirst=False)
    interview_level.drop(bind, checkfirst=False)
