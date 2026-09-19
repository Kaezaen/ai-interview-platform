"""The ``users`` table."""

from sqlalchemy import Boolean, String, text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class User(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A registered account.

    Email is lowercased by the service layer before it is stored or looked up,
    which makes the unique constraint case-insensitive without requiring the
    ``citext`` extension.
    """

    __tablename__ = "users"

    # 320 characters: 64 for the local part, 1 for "@", 255 for the domain.
    email: Mapped[str] = mapped_column(String(320), nullable=False, unique=True)

    # Never exposed through any schema. An Argon2id encoded hash is well under
    # 255 characters at the parameters used here.
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    # Lets an account be disabled without deleting it and cascading away its
    # interviews.
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=text("true"),
    )

    def __repr__(self) -> str:
        """Identify the row without putting the email address into a log line."""
        return f"<User id={self.id}>"
