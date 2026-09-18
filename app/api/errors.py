"""Translation of exceptions into the single API error envelope.

This module is the only place that decides what HTTP status a failure deserves.
Services raise domain exceptions; routers do not catch them; these handlers turn
them into a response whose shape never varies.
"""

import logging

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.middleware import get_request_id
from app.core.exceptions import (
    AppError,
    EmailAlreadyRegisteredError,
    InactiveUserError,
    InterviewNotFoundError,
    InvalidCredentialsError,
    InvalidTokenError,
)
from app.schemas.common import ErrorBody, ErrorDetail, ErrorResponse

logger = logging.getLogger(__name__)

#: The single mapping from a domain failure to an HTTP status.
_STATUS_BY_ERROR: dict[type[AppError], int] = {
    EmailAlreadyRegisteredError: status.HTTP_409_CONFLICT,
    InvalidCredentialsError: status.HTTP_401_UNAUTHORIZED,
    InvalidTokenError: status.HTTP_401_UNAUTHORIZED,
    InactiveUserError: status.HTTP_403_FORBIDDEN,
    InterviewNotFoundError: status.HTTP_404_NOT_FOUND,
}

#: Codes for failures raised by the framework rather than by the domain, such as
#: an unknown path or a method that does not exist.
_CODE_BY_STATUS: dict[int, str] = {
    status.HTTP_400_BAD_REQUEST: "BAD_REQUEST",
    status.HTTP_401_UNAUTHORIZED: "UNAUTHORIZED",
    status.HTTP_403_FORBIDDEN: "FORBIDDEN",
    status.HTTP_404_NOT_FOUND: "NOT_FOUND",
    status.HTTP_405_METHOD_NOT_ALLOWED: "METHOD_NOT_ALLOWED",
    status.HTTP_422_UNPROCESSABLE_ENTITY: "VALIDATION_ERROR",
}


def _json_error(
    *,
    status_code: int,
    code: str,
    message: str,
    request_id: str,
    details: list[ErrorDetail] | None = None,
) -> JSONResponse:
    """Build the error envelope, omitting ``details`` when there are none."""
    body = ErrorResponse(
        error=ErrorBody(code=code, message=message, request_id=request_id, details=details)
    )
    headers = (
        {"WWW-Authenticate": "Bearer"} if status_code == status.HTTP_401_UNAUTHORIZED else None
    )
    return JSONResponse(
        status_code=status_code,
        content=body.model_dump(exclude_none=True),
        headers=headers,
    )


async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    """Render a domain exception."""
    return _json_error(
        status_code=_STATUS_BY_ERROR.get(type(exc), status.HTTP_500_INTERNAL_SERVER_ERROR),
        code=exc.code,
        message=exc.message,
        request_id=get_request_id(request),
    )


async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Render a request that failed schema validation.

    Only the location and the message of each problem are copied out. Pydantic
    also reports the offending input, which for a registration request would be
    the password.
    """
    details = [
        ErrorDetail(
            field=".".join(str(part) for part in error["loc"]),
            message=error["msg"],
        )
        for error in exc.errors()
    ]
    return _json_error(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        code="VALIDATION_ERROR",
        message="Request tidak valid",
        request_id=get_request_id(request),
        details=details,
    )


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """Render failures raised by the framework, such as 404 and 405."""
    code = _CODE_BY_STATUS.get(exc.status_code, f"HTTP_{exc.status_code}")
    return _json_error(
        status_code=exc.status_code,
        code=code,
        message=str(exc.detail),
        request_id=get_request_id(request),
    )


async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """Render anything that was not anticipated.

    This is the outermost boundary, so the exception is logged in full here and
    nothing of it reaches the client: the correlation id is what ties the two
    together.
    """
    request_id = get_request_id(request)
    logger.exception(
        "unhandled error (request_id=%s method=%s path=%s)",
        request_id,
        request.method,
        request.url.path,
    )
    return _json_error(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        code="INTERNAL_ERROR",
        message="Terjadi kesalahan internal",
        request_id=request_id,
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Install every handler. Registering the base class covers its subclasses."""
    app.add_exception_handler(AppError, app_error_handler)
    app.add_exception_handler(RequestValidationError, validation_error_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(Exception, unhandled_error_handler)
