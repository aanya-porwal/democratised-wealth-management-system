"""Goal service — goal CRUD plus engine goal analysis and progress
snapshots.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.models import Goal, User
from app.repositories.goal_repository import GoalRepository
from app.schemas.goal import GoalCreate, GoalUpdate
from app.services.engine_adapter import EngineAdapter

from engine import GoalEngine  # thin shim → wealth_management_system.goals


class GoalService:
    """Business workflows around goals."""

    def __init__(self, session: Session) -> None:
        self.session = session
        self.goals = GoalRepository(session)
        self._goal_engine: GoalEngine | None = None

    @property
    def goal_engine(self) -> GoalEngine:
        if self._goal_engine is None:
            self._goal_engine = GoalEngine(simulations=10_000)
        return self._goal_engine

    # ── CRUD ────────────────────────────────────────────────────────

    def create_goal(self, user: User, data: GoalCreate) -> Goal:
        return self.goals.create(user_id=user.id, **data.model_dump())

    def get_goal(self, user_id: uuid.UUID, goal_id: uuid.UUID) -> Goal:
        goal = self.goals.get_for_user(goal_id, user_id)
        if goal is None:
            raise NotFoundError("Goal not found", code="goal_not_found")
        return goal

    def list_goals(self, user_id: uuid.UUID) -> list[Goal]:
        return self.goals.list_for_user(user_id)

    def update_goal(self, user_id: uuid.UUID, goal_id: uuid.UUID, data: GoalUpdate) -> Goal:
        goal = self.get_goal(user_id, goal_id)
        updates = {k: v for k, v in data.model_dump().items() if v is not None}
        return self.goals.update(goal, **updates)

    def delete_goal(self, user_id: uuid.UUID, goal_id: uuid.UUID) -> None:
        goal = self.get_goal(user_id, goal_id)
        self.goals.delete(goal)

    # ── engine analysis ─────────────────────────────────────────────

    def analyse_goal(self, user_id: uuid.UUID, goal_id: uuid.UUID) -> dict:
        goal = self.get_goal(user_id, goal_id)
        engine_goal = EngineAdapter.to_engine_goal(goal)
        analysis = self.goal_engine.analyse(engine_goal)
        return EngineAdapter.goal_analysis_to_dict(analysis)

    def analyse_all_goals(self, user: User) -> list[dict]:
        goals = self.goals.list_for_user(user.id)
        engine_goals = [EngineAdapter.to_engine_goal(g) for g in goals]
        engine_user = EngineAdapter.build_engine_user_with_goals(user, goals)
        engine_user.goals = engine_goals
        result = self.goal_engine.analyse_all(engine_user)
        return [EngineAdapter.goal_analysis_to_dict(a) for a in result.goals]

    # ── progress snapshot ───────────────────────────────────────────

    def record_progress(self, user_id: uuid.UUID, goal_id: uuid.UUID) -> dict:
        goal = self.get_goal(user_id, goal_id)
        analysis = self.goal_engine.analyse(EngineAdapter.to_engine_goal(goal))
        record = self.goals.add_progress(
            goal_id=goal.id,
            user_id=user_id,
            recorded_at=datetime.now(timezone.utc),
            current_savings=goal.current_savings_for_goal,
            progress_percent=analysis.current_progress * 100,
            probability_of_success=analysis.probability_of_success,
            required_sip=analysis.required_sip,
            remaining_gap=analysis.remaining_gap,
        )
        return {
            "id": str(record.id),
            "goal_id": str(record.goal_id),
            "recorded_at": record.recorded_at.isoformat(),
            "current_savings": record.current_savings,
            "progress_percent": record.progress_percent,
            "probability_of_success": record.probability_of_success,
            "required_sip": record.required_sip,
            "remaining_gap": record.remaining_gap,
        }

