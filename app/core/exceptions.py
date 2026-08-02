"""Application exception hierarchy + helpers.

The backend raises these typed exceptions from services and routes; the
global handlers in :mod:`app.core.handlers` translate them into
:rfc:`7807`-style problem+json error responses with proper HTTP status
codes.
"""

from __future__ import annotations

from typing import Any


class AppError(Exception):
    """Base class for all backend application errors."""

    status_code: int = 500
    code: str = "internal_error"

    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        code: str | None = None,
        details: dict[str, Any] | list[Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        if code is not None:
            self.code = code
        self.details = details or {}

    def to_dict(self) -> dict[str, Any]:
        return {
            "error": {
                "code": self.code,
                "message": self.message,
                "status_code": self.status_code,
                "details": self.details,
            }
        }


class AuthenticationError(AppError):
    """401 — missing/invalid credentials."""

    status_code = 401
    code = "authentication_error"


class ForbiddenError(AppError):
    """403 — authenticated but not permitted."""

    status_code = 403
    code = "forbidden"


class NotFoundError(AppError):
    """404 — requested resource does not exist."""

    status_code = 404
    code = "not_found"


class ConflictError(AppError):
    """409 — resource conflicts with existing state (e.g. duplicate email)."""

    status_code = 409
    code = "conflict"


class ValidationAppError(AppError):
    """422 — domain/business validation failed (not Pydantic)."""

    status_code = 422
    code = "validation_error"


# Backward-compatible alias used by services that import ``ValidationError``.
ValidationError = ValidationAppError


class RateLimitError(AppError):
    """429 — too many requests."""

    status_code = 429
    code = "rate_limit_exceeded"


class DatabaseError(AppError):
    """500-ish — persistence layer failure."""

    status_code = 500
    code = "database_error"


class ExternalServiceError(AppError):
    """502/503 — an upstream dependency (Redis, market feed) failed."""

    status_code = 503
    code = "external_service_unavailable"

