"""Request and response schemas for the authentication endpoints."""

from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, StringConstraints

#: Eight characters is the floor NIST recommends. The upper bound exists so that
#: a very large body cannot be turned into expensive hashing work.
PASSWORD_MIN_LENGTH = 8
PASSWORD_MAX_LENGTH = 128

#: 64 for the local part, 1 for "@", 255 for the domain.
EMAIL_MAX_LENGTH = 320

Email = Annotated[EmailStr, StringConstraints(max_length=EMAIL_MAX_LENGTH)]


class RegisterRequest(BaseModel):
    """A new account."""

    email: Email
    password: Annotated[
        str,
        StringConstraints(min_length=PASSWORD_MIN_LENGTH, max_length=PASSWORD_MAX_LENGTH),
    ]


class LoginRequest(BaseModel):
    """Credentials for an existing account.

    The password policy is deliberately not applied here: rejecting a short
    password at login would both break accounts created under an older policy
    and tell a caller what the policy is.
    """

    email: Email
    password: Annotated[str, StringConstraints(min_length=1, max_length=PASSWORD_MAX_LENGTH)]


class TokenResponse(BaseModel):
    """An issued access token."""

    access_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_in: int = Field(description="Seconds until the token expires")


class UserRead(BaseModel):
    """A user as the API exposes it.

    There is no password field of any kind here, and this is the only schema
    used to render a user, so a hash cannot leak through some other route.
    """

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: EmailStr
    is_active: bool
    created_at: datetime
