"""Goal repository."""

from __future__ import annotations

import uuid

from sqlalchemy import select

from app.models.goal import Goal, GoalProgress
from app.repositories.base import BaseRepository


class GoalRepository(BaseRepository[Goal]):
    """Persistence for goals and goal-progress snapshots."""

    model = Goal

    def list_for_user(self, user_id: uuid.UUID) -> list[Goal]:
        stmt = select(Goal).where(Goal.user_id == user_id).order_by(Goal.created_at)
        return list(self.session.execute(stmt).scalars().all())

    def get_for_user(self, goal_id: uuid.UUID, user_id: uuid.UUID) -> Goal | None:
        stmt = select(Goal).where(Goal.id == goal_id, Goal.user_id == user_id)
        return self.session.execute(stmt).scalars().first()

    def count_for_user(self, user_id: uuid.UUID) -> int:
        return self.count(user_id=user_id)

    def add_progress(
        self,
        *,
        goal_id: uuid.UUID,
        user_id: uuid.UUID,
        recorded_at,
        current_savings: float,
        progress_percent: float,
        probability_of_success: float | None = None,
        required_sip: float | None = None,
        remaining_gap: float | None = None,
    ) -> GoalProgress:
        record = GoalProgress(
            goal_id=goal_id,
            user_id=user_id,
            recorded_at=recorded_at,
            current_savings=current_savings,
            progress_percent=progress_percent,
            probability_of_success=probability_of_success,
            required_sip=required_sip,
            remaining_gap=remaining_gap,
        )
        self.session.add(record)
        self.session.flush()
        return record

    def progress_for_goal(self, goal_id: uuid.UUID, limit: int = 30) -> list[GoalProgress]:
        stmt = (
            select(GoalProgress)
            .where(GoalProgress.goal_id == goal_id)
            .order_by(GoalProgress.recorded_at.desc())
            .limit(limit)
        )
        return list(self.session.execute(stmt).scalars().all())

