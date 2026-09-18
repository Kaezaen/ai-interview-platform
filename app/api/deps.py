"""Dependencies shared by the routers.

Wiring lives here so that a router receives a ready-made service and never
assembles a repository or touches a session itself.
"""

from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import InvalidTokenError
from app.core.security import decode_access_token
from app.db.session import get_db
from app.models import User
from app.repositories.interview import InterviewRepository
from app.repositories.user import UserRepository
from app.services.auth import AuthService
from app.services.interview import InterviewService

# auto_error=False so that a missing or malformed Authorization header becomes
# InvalidTokenError -> 401 in the usual envelope, rather than the bare 403 that
# HTTPBearer raises by default.
_bearer_scheme = HTTPBearer(auto_error=False, description="Access token from POST /auth/login")

DbSession = Annotated[AsyncSession, Depends(get_db)]


def get_auth_service(session: DbSession) -> AuthService:
    """Build the authentication service for this request."""
    return AuthService(session, UserRepository(session))


AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer_scheme)],
    auth: AuthServiceDep,
) -> User:
    """Resolve the bearer token into the user it belongs to.

    Raises:
        InvalidTokenError: no token, wrong scheme, or a token that does not
            decode to an existing user.
        InactiveUserError: the account has been disabled.
    """
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise InvalidTokenError

    user_id = decode_access_token(credentials.credentials)
    return await auth.get_active_user(user_id)


CurrentUser = Annotated[User, Depends(get_current_user)]


def get_interview_service(session: DbSession) -> InterviewService:
    """Build the interview service for this request."""
    return InterviewService(session, InterviewRepository(session))


InterviewServiceDep = Annotated[InterviewService, Depends(get_interview_service)]
