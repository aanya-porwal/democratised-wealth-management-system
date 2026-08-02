"""Repository unit tests with a real SQLite session."""

from __future__ import annotations

import uuid
from datetime import date, datetime, timedelta, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.database.base import Base
from app.models.user import Role, User
from app.repositories.user_repository import UserRepository
from app.repositories.goal_repository import GoalRepository
from app.repositories.portfolio_repository import PortfolioRepository
from app.repositories.health_repository import HealthScoreRepository
from app.repositories.recommendation_repository import RecommendationRepository
from app.repositories.simulation_repository import SimulationRepository
from app.repositories.audit_repository import AuditRepository


@pytest.fixture
def repo_session() -> Session:
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    session = Session(bind=engine)
    yield session
    session.close()


class TestUserRepository:
    def test_create_and_get(self, repo_session: Session) -> None:
        repo = UserRepository(repo_session)
        user = repo.create(
            email="test@example.com",
            password_hash="hash",
            full_name="Test User",
            role=Role.USER,
        )
        assert user.id is not None
        fetched = repo.get(user.id)
        assert fetched is not None
        assert fetched.email == "test@example.com"

    def test_get_by_email(self, repo_session: Session) -> None:
        repo = UserRepository(repo_session)
        repo.create(email="a@b.com", password_hash="hash", full_name="A", role=Role.USER)
        found = repo.get_by_email("a@b.com")
        assert found is not None
        assert repo.get_by_email("missing@x.com") is None

    def test_list_paginated(self, repo_session: Session) -> None:
        repo = UserRepository(repo_session)
        for i in range(10):
            repo.create(
                email=f"user{i}@test.com",
                password_hash="hash",
                full_name=f"User {i}",
                role=Role.USER,
            )
        users = repo.list_paginated(skip=0, limit=5)
        assert len(users) == 5

    def test_search(self, repo_session: Session) -> None:
        repo = UserRepository(repo_session)
        repo.create(email="alice@test.com", password_hash="hash", full_name="Alice", role=Role.USER)
        repo.create(email="bob@test.com", password_hash="hash", full_name="Bob", role=Role.USER)
        results = repo.list_paginated(skip=0, limit=10, search="alice")
        assert len(results) == 1
        assert results[0].email == "alice@test.com"


class TestGoalRepository:
    def test_create_and_list_for_user(self, repo_session: Session) -> None:
        user_repo = UserRepository(repo_session)
        user = user_repo.create(
            email="test@test.com", password_hash="hash", full_name="T", role=Role.USER
        )
        goal_repo = GoalRepository(repo_session)
        goal = goal_repo.create(
            user_id=user.id,
            goal_type="retirement",
            priority="critical",
            target_amount=1000000,
            target_date=date(2040, 1, 1),
        )
        assert goal.id is not None

        goals = goal_repo.list_for_user(user.id)
        assert len(goals) == 1
        assert goals[0].goal_type == "retirement"


class TestHealthScoreRepository:
    def test_create_and_latest(self, repo_session: Session) -> None:
        user_repo = UserRepository(repo_session)
        user = user_repo.create(
            email="h@test.com", password_hash="hash", full_name="H", role=Role.USER
        )
        repo = HealthScoreRepository(repo_session)
        record = repo.create(user_id=user.id, score=75, grade="good")
        assert record.score == 75

        latest = repo.latest_for_user(user.id)
        assert len(latest) == 1
        assert latest[0].grade == "good"


class TestAuditRepository:
    def test_record_and_list(self, repo_session: Session) -> None:
        repo = AuditRepository(repo_session)
        entry = repo.record(
            user_id=None, action="test_action", resource_type="test", status="success"
        )
        assert entry.id is not None
        assert entry.action == "test_action"
