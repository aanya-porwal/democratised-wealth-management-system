"""Financial health score repository."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select

from app.models.health import FinancialHealthScore
from app.repositories.base import BaseRepository


class HealthScoreRepository(BaseRepository[FinancialHealthScore]):
    """Persistence for financial health score snapshots."""

    model = FinancialHealthScore

    def create(
        self,
        *,
        user_id: uuid.UUID,
        score: int,
        grade: str,
        factors: list | None = None,
        strengths: list | None = None,
        weaknesses: list | None = None,
        suggestions: list | None = None,
        scored_at: datetime | None = None,
    ) -> FinancialHealthScore:
        """Create a health-score row (JSON arrays stored directly)."""
        record = FinancialHealthScore(
            user_id=user_id,
            score=score,
            grade=grade,
            factors=factors,
            strengths=strengths,
            weaknesses=weaknesses,
            suggestions=suggestions,
            scored_at=scored_at or datetime.now(timezone.utc),
        )
        self.session.add(record)
        self.session.flush()
        return record

    def latest_for_user(self, user_id: uuid.UUID, limit: int = 1) -> list[FinancialHealthScore]:
        stmt = (
            select(FinancialHealthScore)
            .where(FinancialHealthScore.user_id == user_id)
            .order_by(FinancialHealthScore.scored_at.desc())
            .limit(limit)
        )
        return list(self.session.execute(stmt).scalars().all())

    def list_for_user(self, user_id: uuid.UUID, limit: int = 30) -> list[FinancialHealthScore]:
        stmt = (
            select(FinancialHealthScore)
            .where(FinancialHealthScore.user_id == user_id)
            .order_by(FinancialHealthScore.scored_at.desc())
            .limit(limit)
        )
        return list(self.session.execute(stmt).scalars().all())

