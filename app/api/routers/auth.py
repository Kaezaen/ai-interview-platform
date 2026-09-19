"""Registration, login, and the current user's profile."""

from fastapi import APIRouter, status

from app.api.deps import AuthServiceDep, CurrentUser
from app.api.errors import error_responses
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserRead

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
    summary="Create an account",
    response_model=UserRead,
    responses=error_responses(
        status.HTTP_409_CONFLICT,
        status.HTTP_422_UNPROCESSABLE_ENTITY,
    ),
)
async def register(payload: RegisterRequest, auth: AuthServiceDep) -> UserRead:
    """Register a new account and return its public profile."""
    user = await auth.register(email=payload.email, password=payload.password)
    return UserRead.model_validate(user)


@router.post(
    "/login",
    summary="Exchange credentials for an access token",
    response_model=TokenResponse,
    responses=error_responses(
        status.HTTP_401_UNAUTHORIZED,
        status.HTTP_422_UNPROCESSABLE_ENTITY,
    ),
)
async def login(payload: LoginRequest, auth: AuthServiceDep) -> TokenResponse:
    """Verify credentials and issue an access token."""
    token = await auth.authenticate(email=payload.email, password=payload.password)
    return TokenResponse(access_token=token.token, expires_in=token.expires_in)


@router.get(
    "/me",
    summary="The current user",
    response_model=UserRead,
    responses=error_responses(
        status.HTTP_401_UNAUTHORIZED,
        status.HTTP_403_FORBIDDEN,
    ),
)
async def read_current_user(user: CurrentUser) -> UserRead:
    """Return the profile of the account the token belongs to."""
    return UserRead.model_validate(user)
