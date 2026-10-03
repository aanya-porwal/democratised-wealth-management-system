"""Service-level integration tests (engine adapter + repository)."""

from __future__ import annotations

import uuid
from datetime import date, datetime, timedelta, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.database.base import Base
from app.models.user import Role, User
from app.models.behavioral_profile import BehavioralProfile
from app.models.financial_profile import FinancialProfile
from app.repositories.user_repository import UserRepository
from app.services.auth_service import AuthService
from app.services.user_service import UserService
from app.services.goal_service import GoalService
from app.services.health_service import HealthService
from app.schemas.goal import GoalCreate


@pytest.fixture
def svc_session() -> Session:
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    session = Session(bind=engine)
    yield session
    session.close()


class TestAuthService:
    def test_register_and_login(self, svc_session: Session) -> None:
        from app.schemas.auth import RegisterRequest

        svc = AuthService(svc_session)
        payload = RegisterRequest(
            email="new@test.com", password="StrongPass1!", full_name="New User"
        )
        user = svc.register(payload)
        assert user.id is not None
        assert user.email == "new@test.com"

        result = svc.login("new@test.com", "StrongPass1!")
        assert "access_token" in result.model_dump()["tokens"]
        assert "refresh_token" in result.model_dump()["tokens"]

    def test_register_duplicate(self, svc_session: Session) -> None:
        from app.schemas.auth import RegisterRequest

        svc = AuthService(svc_session)
        payload = RegisterRequest(
            email="dup@test.com", password="StrongPass1!", full_name="Dup"
        )
        svc.register(payload)
        with pytest.raises(Exception):
            svc.register(payload)


class TestGoalService:
    def test_create_and_analyse(self, svc_session: Session) -> None:
        from app.schemas.goal import GoalCreate

        user_repo = UserRepository(svc_session)
        user = user_repo.create(
            email="g@test.com", password_hash="hash", full_name="G", role=Role.USER
        )

        svc = GoalService(svc_session)
        payload = GoalCreate(
            name="Retirement",
            goal_type="retirement",
            priority="critical",
            target_amount=20000000,
            target_date=date(2045, 1, 1),
            current_savings_for_goal=500000,
            current_monthly_contribution=15000,
        )
        goal = svc.create_goal(user, payload)
        assert goal.goal_type == "retirement"

        analysis = svc.analyse_goal(user.id, goal.id)
        assert analysis is not None
        assert "inflation_adjusted_target" in analysis


class TestHealthService:
    def test_compute_health_score(self, svc_session: Session) -> None:
        user_repo = UserRepository(svc_session)
        user = user_repo.create(
            email="hservice@test.com", password_hash="hash", full_name="H", role=Role.USER
        )
        # The engine aggregate needs a complete profile (B9): without these
        # rows the health service now returns a clean 404 instead of a score.
        svc_session.add(
            FinancialProfile(
                user_id=user.id,
                monthly_income=100000.0,
                employment_type="salaried_private",
                income_stability=0.8,
                monthly_fixed_expenses=30000.0,
                monthly_variable_expenses=20000.0,
                emergency_fund_months=6.0,
            )
        )
        svc_session.add(
            BehavioralProfile(
                user_id=user.id,
                risk_tolerance="moderate",
                drawdown_reaction_score=3,
            )
        )
        svc_session.flush()

        svc = HealthService(svc_session)
        result = svc.compute(user, persist=False)
        assert "score" in result
        assert 0 <= result["score"] <= 100
        assert "grade" in result
