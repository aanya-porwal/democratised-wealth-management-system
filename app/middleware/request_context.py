"""Request-scoped middleware.

* Generates / propagates a correlation ID (``X-Request-ID``) so a single
  request can be traced across logs.
* Logs every request with method, path, status and duration.
* Injects security headers on every response.
* Keeps the request-start time for the logging handler.
"""

from __future__ import annotations

import time
import uuid
from typing import Awaitable, Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.core.logging import get_logger
from app.core.security import SECURITY_HEADERS

logger = get_logger("middleware.request")

_CORRELATION_HEADER = "X-Request-ID"
_CONTEXT_ATTR = "_request_started_at"
_CONTEXT_ID = "_correlation_id"


def get_correlation_id(request: Request) -> str:
    """Return the correlation ID attached to the request (if any)."""
    return getattr(request.state, _CONTEXT_ID, "")


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Attach correlation IDs, security headers and request logging."""

    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        request_id = request.headers.get(_CORRELATION_HEADER) or str(uuid.uuid4())
        setattr(request.state, _CONTEXT_ID, request_id)
        setattr(request.state, _CONTEXT_ATTR, time.perf_counter())

        response = await call_next(request)

        elapsed_ms = (time.perf_counter() - getattr(request.state, _CONTEXT_ATTR, time.perf_counter())) * 1000
        response.headers[_CORRELATION_HEADER] = request_id
        for header, value in SECURITY_HEADERS.items():
            response.headers[header] = value

        logger.info(
            "request completed method=%s path=%s status=%d duration_ms=%.1f request_id=%s",
            request.method,
            request.url.path,
            response.status_code,
            elapsed_ms,
            request_id,
        )
        return response

