"""Queries against the ``users`` table."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User


class UserRepository:
    """The only place ``users`` is queried.

    Nothing here commits: the service layer owns the transaction boundary, so a
    registration that has to do more than one write can still do it atomically.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_email(self, email: str) -> User | None:
        """Return the user with this exact email, if any.

        The caller passes an already-lowercased address; emails are stored
        lowercased so the unique constraint is effectively case-insensitive.
        """
        result = await self._session.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def get_by_id(self, user_id: uuid.UUID) -> User | None:
        """Return the user with this id, if any."""
        return await self._session.get(User, user_id)

    async def create(self, *, email: str, password_hash: str) -> User:
        """Stage a new user and flush it, so its id is available immediately."""
        user = User(email=email, password_hash=password_hash)
        self._session.add(user)
        await self._session.flush()
        return user
