"""Registration, login, and resolving a token back to a user."""

import logging
import uuid

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    EmailAlreadyRegisteredError,
    InactiveUserError,
    InvalidCredentialsError,
    InvalidTokenError,
)
from app.core.security import (
    AccessToken,
    create_access_token,
    dummy_password_hash,
    hash_password,
    verify_password,
)
from app.models import User
from app.repositories.user import UserRepository

logger = logging.getLogger(__name__)

#: Name of the unique constraint that guards registration. Matching on it keeps
#: an unrelated integrity error from being reported as a duplicate email.
_EMAIL_UNIQUE_CONSTRAINT = "uq_users_email"


class AuthService:
    """Business logic for accounts. Knows nothing about HTTP."""

    def __init__(self, session: AsyncSession, users: UserRepository) -> None:
        self._session = session
        self._users = users

    async def register(self, *, email: str, password: str) -> User:
        """Create an account.

        Raises:
            EmailAlreadyRegisteredError: the address is taken.
        """
        address = _normalise_email(email)

        if await self._users.get_by_email(address) is not None:
            raise EmailAlreadyRegisteredError

        user = await self._users.create(email=address, password_hash=hash_password(password))
        try:
            await self._session.commit()
        except IntegrityError as error:
            await self._session.rollback()
            # Two registrations for the same address can both pass the check
            # above; the unique constraint is the guarantee, the check is only
            # there to give the common case a clean answer.
            if _EMAIL_UNIQUE_CONSTRAINT not in str(error.orig):
                raise
            raise EmailAlreadyRegisteredError from error

        logger.info("registered user %s", user.id)
        return user

    async def authenticate(self, *, email: str, password: str) -> AccessToken:
        """Verify credentials and issue an access token.

        Raises:
            InvalidCredentialsError: unknown address, wrong password, or a
                disabled account. One error covers all three so that a caller
                cannot learn which addresses are registered.
        """
        user = await self._users.get_by_email(_normalise_email(email))

        # A hash is always verified, even when no user matched, so that an
        # unknown address costs about as much time as a known one.
        stored_hash = user.password_hash if user is not None else dummy_password_hash()
        matches = verify_password(password, stored_hash)

        if user is None or not matches or not user.is_active:
            logger.info("failed login attempt")
            raise InvalidCredentialsError

        return create_access_token(user.id)

    async def get_active_user(self, user_id: uuid.UUID) -> User:
        """Return the user a valid token belongs to.

        Raises:
            InvalidTokenError: the account behind the token no longer exists.
            InactiveUserError: the account exists but has been disabled. The
                caller has already proven who they are, so this one is specific.
        """
        user = await self._users.get_by_id(user_id)
        if user is None:
            logger.info("token references a user that no longer exists")
            raise InvalidTokenError
        if not user.is_active:
            raise InactiveUserError
        return user


def _normalise_email(email: str) -> str:
    """Trim and lowercase an address, the form in which they are stored."""
    return email.strip().lower()
