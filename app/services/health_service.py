"""Health service — financial health score via the engine, persisted as
a FinancialHealthScore row.
"""

from __future__ import annotations

import json

from sqlalchemy.orm import Session

from app.models import User
from app.repositories.health_repository import HealthScoreRepository
from app.services.engine_adapter import EngineAdapter

from engine import HealthScoreEngine  # noqa: E402


class HealthService:
    """Compute and persist the financial health score."""

    def __init__(self, session: Session) -> None:
        self.session = session
        self.scores = HealthScoreRepository(session)

    def compute(self, user: User, persist: bool = True) -> dict:
        engine_user = self._engine_user(user)
        result = HealthScoreEngine().score(engine_user)
        data = EngineAdapter.health_to_dict(result)
        if persist:
            self.scores.create(
                user_id=user.id,
                score=result.score,
                grade=result.grade,
                factors=data["factors"],
                strengths=list(result.strengths),
                weaknesses=list(result.weaknesses),
                suggestions=list(result.suggestions),
            )
        return data

    def latest_scores(self, user_id, limit: int = 10) -> list[dict]:
        records = self.scores.latest_for_user(user_id, limit=limit)
        out = []
        for r in records:
            out.append(
                {
                    "id": str(r.id),
                    "score": r.score,
                    "grade": r.grade,
                    "created_at": r.created_at.isoformat() if r.created_at else None,
                }
            )
        return out

    # ── helpers ─────────────────────────────────────────────────────

    def _engine_user(self, user: User):
        from app.services.engine_adapter import load_engine_parts

        profile, financial, behavioral, goals = load_engine_parts(self.session, user)
        return EngineAdapter.to_engine_user(user, profile, financial, behavioral, goals)

