"""FastAPI application entry point.

Creates the application, wires middleware, exception handlers, CORS,
Redis, the scheduler and the API router.

Usage
-----
    uvicorn app.main:app --reload          # development
    uvicorn app.main:app                   # production
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from app.api import api_router
from app.config import settings
from app.core import cache
from app.core.handlers import register_exception_handlers
from app.core.logging import configure_logging
from app.core.security import configure_cors
from app.middleware.request_context import RequestContextMiddleware

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> None:
    """Application lifespan: startup and shutdown hooks."""
    # ── startup ─────────────────────────────────────────────────────
    logger.info(
        "Starting %s (%s) — env=%s",
        settings.APP_NAME,
        settings.APP_VERSION,
        settings.APP_ENV,
    )
    configure_logging()

    cache.cache.connect()

    if settings.SCHEDULER_ENABLED:
        _start_scheduler()

    yield

    # ── shutdown ────────────────────────────────────────────────────
    cache.cache.close()
    if settings.SCHEDULER_ENABLED:
        _stop_scheduler()
    logger.info("Application shut down")


def create_app() -> FastAPI:
    """Build and return the configured FastAPI application."""
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description=(
            "Production-ready backend for the Wealth Management System.\n\n"
            "The financial planning engine is completely independent — the "
            "backend calls it as a library. No duplicate calculations exist "
            "in the API layer.\n\n"
            "All endpoints require JWT authentication unless marked public. "
            "Rate limiting, CORS, security headers and structured logging "
            "are enabled."
        ),
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        contact={
            "name": "Wealth Management System",
            "url": "https://github.com/wealth-management-system",
        },
        license_info={
            "name": "MIT",
            "url": "https://opensource.org/licenses/MIT",
        },
    )

    # ── middleware order (last added = first executed) ────────────────
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=settings.ALLOWED_HOSTS,
    )
    app.add_middleware(RequestContextMiddleware)
    configure_cors(app)

    # ── exception handlers ──────────────────────────────────────────
    register_exception_handlers(app)

    # ── routers ─────────────────────────────────────────────────────
    app.include_router(api_router, prefix=settings.API_V1_PREFIX)

    # ── root endpoint ───────────────────────────────────────────────
    @app.get("/", include_in_schema=False)
    def root() -> dict:
        return {
            "app": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "docs": f"{settings.API_V1_PREFIX}/docs",
        }

    return app


# ── scheduler (lightweight APScheduler) ──────────────────────────────

_scheduler = None


def _start_scheduler() -> None:
    """Start the background scheduler for periodic tasks.

    Tasks are registered here so they are visible in one place.
    Actual task implementations live in ``app.services.background``.
    """
    try:
        from apscheduler.schedulers.background import BackgroundScheduler

        global _scheduler
        _scheduler = BackgroundScheduler(daemon=True)

        from app.services.background import (
            generate_portfolio_snapshots,
            refresh_market_data_cache,
            update_goal_progress,
        )
        from app.tasks.ai import (
            cleanup_old_memories,
            index_knowledge_base,
            refresh_embeddings,
        )

        _scheduler.add_job(
            refresh_market_data_cache,
            "interval",
            hours=settings.MARKET_DATA_REFRESH_HOURS,
            id="market_data_refresh",
            max_instances=1,
        )
        _scheduler.add_job(
            generate_portfolio_snapshots,
            "interval",
            hours=settings.SNAPSHOT_GENERATION_HOURS,
            id="portfolio_snapshot",
            max_instances=1,
        )
        _scheduler.add_job(
            update_goal_progress,
            "interval",
            hours=24,
            id="goal_progress_update",
            max_instances=1,
        )
        _scheduler.add_job(
            cleanup_old_memories,
            "interval",
            hours=24,
            id="ai_memory_cleanup",
            max_instances=1,
        )
        _scheduler.add_job(
            index_knowledge_base,
            "interval",
            hours=24,
            id="ai_knowledge_index",
            max_instances=1,
        )
        _scheduler.add_job(
            refresh_embeddings,
            "interval",
            hours=168,
            id="ai_embeddings_refresh",
            max_instances=1,
        )

        _scheduler.start()
        logger.info("Background scheduler started with %d jobs", len(_scheduler.get_jobs()))
    except Exception as exc:
        logger.warning("Background scheduler could not start (%s); continuing without it", exc)


def _stop_scheduler() -> None:
    """Shut down the background scheduler gracefully."""
    global _scheduler
    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
        logger.info("Background scheduler shut down")


# ── application instance ─────────────────────────────────────────────

app = create_app()
