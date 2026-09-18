"""HTTP middleware."""

import uuid
from collections.abc import Awaitable, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

REQUEST_ID_HEADER = "X-Request-ID"


def get_request_id(request: Request) -> str:
    """Return the current request's correlation id, or ``-`` if it has none."""
    return getattr(request.state, "request_id", "-")


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Give every request a correlation id and echo it back in a header.

    The id is always generated here. An inbound ``X-Request-ID`` is deliberately
    ignored: it is attacker-controlled text that would otherwise end up in log
    lines and in error responses.
    """

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        """Attach the id to the request state and to the response headers."""
        request_id = uuid.uuid4().hex
        request.state.request_id = request_id

        response = await call_next(request)
        response.headers[REQUEST_ID_HEADER] = request_id
        return response
