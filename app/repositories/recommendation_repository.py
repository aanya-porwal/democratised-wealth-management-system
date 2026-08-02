"""Recommendation repository."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from app.models.recommendation import Recommendation
from app.repositories.base import BaseRepository


class RecommendationRepository(BaseRepository[Recommendation]):
    """Persistence for recommendations."""

    model = Recommendation

    def create(
        self,
        *,
        user_id: uuid.UUID,
        hours_valid: float = 24.0,
        **values,
    ) -> Recommendation:
        """Create a recommendation row with an expiry timestamp."""
        record = Recommendation(
            user_id=user_id,
            valid_until=datetime.now(timezone.utc) + timedelta(hours=hours_valid),
            **values,
        )
        self.session.add(record)
        self.session.flush()
        return record

    def list_for_user(
        self,
        user_id: uuid.UUID,
        status: str | None = None,
        limit: int | None = None,
    ) -> list[Recommendation]:
        stmt = select(Recommendation).where(Recommendation.user_id == user_id)
        if status:
            stmt = stmt.where(Recommendation.status == status)
        stmt = stmt.order_by(Recommendation.priority.desc(), Recommendation.created_at.desc())
        if limit:
            stmt = stmt.limit(limit)
        return list(self.session.execute(stmt).scalars().all())

    def get_for_user(self, recommendation_id: uuid.UUID, user_id: uuid.UUID) -> Recommendation | None:
        stmt = select(Recommendation).where(
            Recommendation.id == recommendation_id,
            Recommendation.user_id == user_id,
        )
        return self.session.execute(stmt).scalars().first()

    def set_status(self, recommendation: Recommendation, status: str) -> Recommendation:
        recommendation.status = status
        self.session.flush()
        return recommendation

