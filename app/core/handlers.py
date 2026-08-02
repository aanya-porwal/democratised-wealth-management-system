"""Global exception handlers translating errors into JSON responses.

Registered on the FastAPI app in :mod:`app.main`. Every handler returns a
consistent ``{"error": {code, message, status_code, details}}`` envelope
so API clients can parse errors uniformly.
"""

from __future__ import annotations

import logging

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError, OperationalError, SQLAlchemyError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.exceptions import (
    AppError,
    AuthenticationError,
    ConflictError,
    DatabaseError,
    NotFoundError,
)
from app.core.logging import get_logger

logger = get_logger(__name__)


def _error_payload(code: str, message: str, status_code: int, details=None) -> dict:
    return {
        "error": {
            "code": code,
            "message": message,
            "status_code": status_code,
            "details": details or {},
        }
    }


def register_exception_handlers(app: FastAPI) -> None:
    """Attach every global handler to the application."""

    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
        logger.warning("AppError %s on %s: %s", exc.code, request.url.path, exc.message)
        return JSONResponse(
            status_code=exc.status_code,
            content=exc.to_dict(),
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=_error_payload(
                code=_http_code_to_error_code(exc.status_code),
                message=str(exc.detail),
                status_code=exc.status_code,
            ),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        errors = exc.errors()
        logger.info("Validation failed on %s: %s", request.url.path, errors)
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=_error_payload(
                code="validation_error",
                message="Request validation failed",
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                details=errors,
            ),
        )

    @app.exception_handler(IntegrityError)
    async def integrity_error_handler(request: Request, exc: IntegrityError) -> JSONResponse:
        logger.error("IntegrityError on %s: %s", request.url.path, exc, exc_info=True)
        message = "Resource already exists or violates a constraint"
        return JSONResponse(
            status_code=409,
            content=_error_payload("conflict", message, 409),
        )

    @app.exception_handler(OperationalError)
    async def operational_error_handler(request: Request, exc: OperationalError) -> JSONResponse:
        logger.error("Database operational error on %s: %s", request.url.path, exc, exc_info=True)
        return JSONResponse(
            status_code=503,
            content=_error_payload(
                "database_unavailable",
                "The database is temporarily unavailable",
                503,
            ),
        )

    @app.exception_handler(SQLAlchemyError)
    async def sqlalchemy_error_handler(request: Request, exc: SQLAlchemyError) -> JSONResponse:
        logger.error("SQLAlchemy error on %s: %s", request.url.path, exc, exc_info=True)
        return JSONResponse(
            status_code=500,
            content=_error_payload(
                "database_error",
                "An unexpected database error occurred",
                500,
            ),
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.critical("Unhandled exception on %s: %s", request.url.path, exc, exc_info=True)
        return JSONResponse(
            status_code=500,
            content=_error_payload(
                "internal_error",
                "An unexpected internal error occurred",
                500,
            ),
        )


def _http_code_to_error_code(status_code: int) -> str:
    if status_code == 401:
        return "authentication_error"
    if status_code == 403:
        return "forbidden"
    if status_code == 404:
        return "not_found"
    if status_code == 405:
        return "method_not_allowed"
    if status_code == 429:
        return "rate_limit_exceeded"
    return "http_error"

