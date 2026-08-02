"""pytest configuration and shared fixtures.

Uses SQLite for test isolation so no external Postgres is required.
The engine's ``get_config`` cache is reset before each test to avoid
cross-test leakage.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime, timedelta, timezone
from typing import AsyncGenerator, Generator

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from app.config import settings
from app.database.base import Base
from app.database.session import get_db
from app.main import create_app
from app.models.user import Role, User

# ── overrides ────────────────────────────────────────────────────────

settings.SECRET_KEY = "test-secret-key-32-chars-minimum!!"
settings.RATE_LIMIT_ENABLED = False
settings.SCHEDULER_ENABLED = False
settings.ACCESS_TOKEN_EXPIRE_MINUTES = 15
settings.REFRESH_TOKEN_EXPIRE_MINUTES = 60

# ── engine ───────────────────────────────────────────────────────────

TEST_DATABASE_URL = "sqlite:///./test.db"


# ── fixtures ─────────────────────────────────────────────────────────


@pytest.fixture(scope="session")
def engine():
    """Create a fresh SQLite engine for the entire test session."""
    eng = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=eng)
    yield eng
    Base.metadata.drop_all(bind=eng)
    eng.dispose()


@pytest.fixture
def db_session(engine) -> Generator[Session, None, None]:
    """Yield a fresh session per test, rolling back on teardown."""
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def app(db_session: Session) -> FastAPI:
    """Create a FastAPI app wired to the test DB session."""

    def _get_db_override() -> Generator[Session, None, None]:
        yield db_session

    application = create_app()
    application.dependency_overrides[get_db] = _get_db_override
    return application


@pytest.fixture
async def async_client(app: FastAPI) -> AsyncGenerator[AsyncClient, None]:
    """Provide an async HTTP client for the test app."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


# ── user fixtures ────────────────────────────────────────────────────


@pytest.fixture
def default_user(db_session: Session) -> User:
    """Create a plain user for general tests."""
    import hashlib, secrets

    user = User(
        id=uuid.uuid4(),
        email="test@example.com",
        phone="+919999999999",
        password_hash=hashlib.sha256("password123".encode()).hexdigest(),
        full_name="Test User",
        role=Role.USER,
        is_active=True,
        is_email_verified=False,
    )
    db_session.add(user)
    db_session.flush()
    return user


@pytest.fixture
def admin_user(db_session: Session) -> User:
    """Create an admin user for RBAC tests."""
    import hashlib

    user = User(
        id=uuid.uuid4(),
        email="admin@example.com",
        password_hash=hashlib.sha256("admin123".encode()).hexdigest(),
        full_name="Admin User",
        role=Role.ADMIN,
        is_active=True,
        is_email_verified=True,
    )
    db_session.add(user)
    db_session.flush()
    return user


@pytest.fixture
def auth_headers(default_user: User) -> dict[str, str]:
    """Generate JWT headers for the default user."""
    from app.auth.jwt import create_token_pair

    tokens = create_token_pair(str(default_user.id), default_user.role.value)
    return {"Authorization": f"Bearer {tokens.access_token}"}


@pytest.fixture
def admin_auth_headers(admin_user: User) -> dict[str, str]:
    """Generate JWT headers for the admin user."""
    from app.auth.jwt import create_token_pair

    tokens = create_token_pair(str(admin_user.id), admin_user.role.value)
    return {"Authorization": f"Bearer {tokens.access_token}"}
