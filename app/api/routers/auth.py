"""Registration, login, and the current user's profile."""

from fastapi import APIRouter, status

from app.api.deps import AuthServiceDep, CurrentUser
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserRead
from app.schemas.common import ErrorResponse

router = APIRouter(prefix="/auth", tags=["auth"])

_UNAUTHORIZED = {
    status.HTTP_401_UNAUTHORIZED: {
        "model": ErrorResponse,
        "description": "Missing, invalid, or expired token",
    }
}


@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
    summary="Create an account",
    response_model=UserRead,
    responses={
        status.HTTP_409_CONFLICT: {
            "model": ErrorResponse,
            "description": "The email is already registered",
        }
    },
)
async def register(payload: RegisterRequest, auth: AuthServiceDep) -> UserRead:
    """Register a new account and return its public profile."""
    user = await auth.register(email=payload.email, password=payload.password)
    return UserRead.model_validate(user)


@router.post(
    "/login",
    summary="Exchange credentials for an access token",
    response_model=TokenResponse,
    responses={
        status.HTTP_401_UNAUTHORIZED: {
            "model": ErrorResponse,
            "description": "Wrong credentials, or the account is disabled",
        }
    },
)
async def login(payload: LoginRequest, auth: AuthServiceDep) -> TokenResponse:
    """Verify credentials and issue an access token."""
    token = await auth.authenticate(email=payload.email, password=payload.password)
    return TokenResponse(access_token=token.token, expires_in=token.expires_in)


@router.get(
    "/me",
    summary="The current user",
    response_model=UserRead,
    responses=_UNAUTHORIZED,
)
async def read_current_user(user: CurrentUser) -> UserRead:
    """Return the profile of the account the token belongs to."""
    return UserRead.model_validate(user)
