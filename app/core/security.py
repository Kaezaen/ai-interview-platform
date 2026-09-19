"""Password hashing and access tokens.

Nothing outside this module knows which hashing algorithm or JWT library is in
use, so replacing either is a change to one file.

Argon2id is used rather than bcrypt: it is the PHC winner, it is memory-hard,
and it has no 72-byte input limit that would silently truncate a long password.
The parameters are argon2-cffi's defaults (t=3, m=64 MiB, p=4).
"""

import logging
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from functools import lru_cache
from typing import Final

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError

from app.core.config import get_settings
from app.core.exceptions import InvalidTokenError

logger = logging.getLogger(__name__)

JWT_ALGORITHM: Final = "HS256"

#: Distinguishes an access token from any other token type added later, so that
#: a refresh token can never be presented where an access token is expected.
ACCESS_TOKEN_TYPE: Final = "access"

_password_hasher = PasswordHasher()


@lru_cache(maxsize=1)
def dummy_password_hash() -> str:
    """A hash to verify against when no user matched.

    Logging in with an unknown email must take about as long as logging in with
    a known one, otherwise response time alone reveals which emails are
    registered. Computed once, on first use.
    """
    return _password_hasher.hash(uuid.uuid4().hex)


def hash_password(password: str) -> str:
    """Return the Argon2id hash to store for ``password``."""
    return _password_hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    """Report whether ``password`` matches ``password_hash``.

    A stored hash that cannot be parsed is treated as a failed verification
    rather than an error: it means the row is corrupt, which is not something
    the person logging in can do anything about.
    """
    try:
        _password_hasher.verify(password_hash, password)
    except VerificationError:
        return False
    except InvalidHashError:
        logger.error("stored password hash is unreadable")
        return False
    return True


@dataclass(frozen=True, slots=True)
class AccessToken:
    """A signed access token and how long it stays valid."""

    token: str
    expires_in: int


def create_access_token(subject: uuid.UUID) -> AccessToken:
    """Issue an access token for the user identified by ``subject``."""
    settings = get_settings()
    lifetime = timedelta(minutes=settings.access_token_expire_minutes)
    issued_at = datetime.now(UTC)

    claims = {
        "sub": str(subject),
        "typ": ACCESS_TOKEN_TYPE,
        "iat": issued_at,
        "exp": issued_at + lifetime,
        # A unique id per token. Nothing reads it yet; it is what a revocation
        # list would key on.
        "jti": uuid.uuid4().hex,
    }
    return AccessToken(
        token=jwt.encode(claims, settings.secret_key, algorithm=JWT_ALGORITHM),
        expires_in=int(lifetime.total_seconds()),
    )


def decode_access_token(token: str) -> uuid.UUID:
    """Return the user id carried by a valid access token.

    Raises:
        InvalidTokenError: the token is malformed, unsigned by us, expired, of
            the wrong type, or carries a subject that is not a user id.
    """
    settings = get_settings()
    try:
        claims = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[JWT_ALGORITHM],
            options={"require": ["sub", "exp", "iat"]},
        )
    except jwt.PyJWTError as error:
        # The reason is logged, never returned. The token itself is never logged.
        logger.info("rejected access token: %s", error)
        raise InvalidTokenError from error

    if claims.get("typ") != ACCESS_TOKEN_TYPE:
        logger.info("rejected token of type %r", claims.get("typ"))
        raise InvalidTokenError

    try:
        return uuid.UUID(claims["sub"])
    except (TypeError, ValueError) as error:
        logger.info("rejected access token with a non-uuid subject")
        raise InvalidTokenError from error
