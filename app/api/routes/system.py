"""System endpoints — health checks, readiness and public settings."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import settings
from app.core import cache
from app.dependencies import get_db

router = APIRouter()


@router.get(
    "/health",
    response_model=dict,
    summary="Liveness probe",
    description="Returns the application name, version and environment. "
    "Used by orchestrators to confirm the process is up.",
)
def health() -> dict:
    """Liveness check — always 200 while the process is running."""
    return {
        "status": "ok",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.APP_ENV,
    }


@router.get(
    "/ready",
    response_model=dict,
    summary="Readiness probe",
    description="Verifies the database connection and (optionally) Redis. "
    "Returns 200 when the service can serve traffic.",
)
def ready(session: Annotated[Session, Depends(get_db)]) -> dict:
    """Readiness check — verifies DB connectivity."""
    db_ok = True
    try:
        session.execute(text("SELECT 1"))
    except Exception:
        db_ok = False

    redis_ok = bool(cache.cache.available)

    return {
        "status": "ok" if db_ok else "degraded",
        "database": "ok" if db_ok else "unreachable",
        "redis": "ok" if redis_ok else "unavailable",
    }


@router.get(
    "/info",
    response_model=dict,
    summary="Public system information",
    description="Exposes non-sensitive public settings for client configuration.",
)
def system_info() -> dict:
    """Public, non-sensitive configuration."""
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "api_prefix": settings.API_V1_PREFIX,
        "rate_limit_enabled": settings.RATE_LIMIT_ENABLED,
    }

