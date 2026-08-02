"""SQLAlchemy 2.0 engine + session management.

The application uses a classic synchronous SQLAlchemy session bound to a
connection pool. FastAPI endpoints receive a session through the
:func:`get_db` dependency; background tasks use :func:`session_scope`.

PostgreSQL specifics (UUID via ``gen_random_uuid``, timezone-aware
timestamps) are handled by the base model and the drivers bundled in the
image (``psycopg2-binary``).
"""

from __future__ import annotations

import logging
from collections.abc import Generator
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import settings

logger = logging.getLogger(__name__)

connect_args: dict = {}
if settings.DATABASE_URL.startswith("sqlite"):
    # In-memory / file SQLite only for local smoke tests.
    connect_args = {"check_same_thread": False}

engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    echo=settings.DB_ECHO,
    future=True,
    connect_args=connect_args,
)

SessionLocal = sessionmaker(
    bind=engine,
    class_=Session,
    autoflush=False,
    expire_on_commit=False,
    future=True,
)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency yielding a request-scoped session.

    The session is always closed, and the transaction rolled back on
    unhandled exceptions, so no connection leaks across requests.
    """
    session = SessionLocal()
    try:
        yield session
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


@contextmanager
def session_scope() -> Generator[Session, None, None]:
    """Context manager for background tasks needing a fresh session."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def init_db() -> None:
    """Create all tables. Intended for tests / local first-run only.

    Production schema evolution is handled by Alembic migrations.
    """
    from app.database import base  # noqa: F401  (register models)
    from app import models  # noqa: F401

    base.Base.metadata.create_all(bind=engine)

