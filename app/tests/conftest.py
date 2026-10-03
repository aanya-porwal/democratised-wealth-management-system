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
    """Create a user with the profiles the engine needs for general tests."""
    from app.auth.password import hash_password
    from app.models.behavioral_profile import BehavioralProfile
    from app.models.financial_profile import FinancialProfile
    from app.models.user_profile import UserProfile

    user = User(
        id=uuid.uuid4(),
        email="test@example.com",
        phone="+919999999999",
        password_hash=hash_password("password123"),
        full_name="Test User",
        role=Role.USER,
        is_active=True,
        is_email_verified=False,
    )
    db_session.add(user)
    db_session.flush()

    db_session.add(
        UserProfile(
            user_id=user.id,
            name="Test User",
            age=30,
            date_of_birth=date(1994, 5, 15),
            dependents=1,
            life_stage="wealth_building",
            city="Mumbai",
            occupation="Engineer",
        )
    )
    db_session.add(
        FinancialProfile(
            user_id=user.id,
            monthly_income=100000.0,
            employment_type="salaried_private",
            income_stability=0.8,
            monthly_fixed_expenses=30000.0,
            monthly_variable_expenses=20000.0,
            emergency_fund_months=6.0,
            existing_investments=500000.0,
            tax_bracket_percent=20.0,
            has_term_life_insurance=True,
            has_health_insurance=True,
        )
    )
    db_session.add(
        BehavioralProfile(
            user_id=user.id,
            risk_tolerance="moderate",
            drawdown_reaction_score=3,
            has_invested_before=True,
            financial_literacy_score=3,
            loss_aversion_score=3,
        )
    )
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

    tokens = create_token_pair(subject=str(default_user.id), role=default_user.role.value)
    return {"Authorization": f"Bearer {tokens['access_token']}"}


@pytest.fixture
def admin_auth_headers(admin_user: User) -> dict[str, str]:
    """Generate JWT headers for the admin user."""
    from app.auth.jwt import create_token_pair

    tokens = create_token_pair(subject=str(admin_user.id), role=admin_user.role.value)
    return {"Authorization": f"Bearer {tokens['access_token']}"}
