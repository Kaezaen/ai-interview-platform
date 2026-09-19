"""Domain exceptions.

Every expected failure in the application is one of these. They carry a stable
machine-readable ``code`` and a ``message`` that is safe to show a client, and
they deliberately know nothing about HTTP: the mapping from exception to status
code lives in exactly one place, ``app/api/errors.py``. That is what lets a
service raise a failure without importing ``HTTPException``.
"""


class AppError(Exception):
    """Base class for expected, translatable failures."""

    code: str = "INTERNAL_ERROR"
    message: str = "Terjadi kesalahan internal"

    def __init__(self, message: str | None = None) -> None:
        if message is not None:
            self.message = message
        super().__init__(self.message)


class EmailAlreadyRegisteredError(AppError):
    """Registration was attempted with an email that already exists."""

    code = "EMAIL_ALREADY_REGISTERED"
    message = "Email sudah terdaftar"


class InvalidCredentialsError(AppError):
    """Login failed.

    Raised for an unknown email, a wrong password, and a disabled account alike.
    Distinguishing them would tell an attacker which emails are registered.
    """

    code = "INVALID_CREDENTIALS"
    message = "Email atau password salah"


class InvalidTokenError(AppError):
    """The bearer token is missing, malformed, expired, or not an access token."""

    code = "INVALID_TOKEN"
    message = "Token tidak valid atau sudah kedaluwarsa"


class InactiveUserError(AppError):
    """The token is valid but the account behind it has been disabled.

    Unlike a failed login this does not leak anything: the caller has already
    proven who they are.
    """

    code = "INACTIVE_USER"
    message = "Akun tidak aktif"


class InterviewNotFoundError(AppError):
    """The interview does not exist, or does not belong to the caller.

    One exception covers both on purpose. Answering differently would confirm
    that somebody else's interview exists.
    """

    code = "INTERVIEW_NOT_FOUND"
    message = "Interview tidak ditemukan"
