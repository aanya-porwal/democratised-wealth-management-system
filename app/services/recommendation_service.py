"""Recommendation service — engine explainable recommendations,
persisted as Recommendation rows each run.
"""

from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.models import User
from app.repositories.recommendation_repository import RecommendationRepository
from app.services.engine_adapter import EngineAdapter

from engine import RecommendationEngine  # noqa: E402


class RecommendationService:
    """Generate recommendations via the engine and persist them."""

    def __init__(self, session: Session) -> None:
        self.session = session
        self.recommendations = RecommendationRepository(session)

    def generate(self, user: User, hours_valid: float = 24.0) -> list[dict]:
        """Run the engine, persist each recommendation, return dicts."""
        engine_user = self._engine_user(user)
        recs = RecommendationEngine().recommend(engine_user)
        dicts = EngineAdapter.recommendations_to_dicts(recs)

        created = []
        for data in dicts:
            record = self.recommendations.create(user_id=user.id, **data, hours_valid=hours_valid)
            created.append(self._record_to_dict(record))
        return created

    def refresh_validity(self, user_id: uuid.UUID, hours_valid: float = 24.0) -> int:
        """Refresh ``valid_until`` for pending recommendations."""
        records = self.list_for_user(user_id)
        updated = 0
        for record in records:
            # list_for_user returns dicts; fetch & extend from the repo.
            from datetime import datetime, timedelta, timezone

            obj = self.recommendations.get_for_user(uuid.UUID(record["id"]), user_id)  # type: ignore[arg-type]
            if obj is not None and obj.status == "pending":
                obj.valid_until = datetime.now(timezone.utc) + timedelta(hours=hours_valid)
                self.session.flush()
                updated += 1
        return updated

    def list_for_user(self, user_id: uuid.UUID, limit: int = 50) -> list[dict]:
        records = self.recommendations.list_for_user(user_id, limit=limit)
        return [self._record_to_dict(r) for r in records]

    def get(self, user_id: uuid.UUID, recommendation_id: uuid.UUID) -> dict:
        record = self.recommendations.get_for_user(recommendation_id, user_id)
        if record is None:
            raise NotFoundError("Recommendation not found", code="recommendation_not_found")
        return self._record_to_dict(record)

    def dismiss(self, user_id: uuid.UUID, recommendation_id: uuid.UUID) -> None:
        record = self.recommendations.get_for_user(recommendation_id, user_id)
        if record is None:
            raise NotFoundError("Recommendation not found", code="recommendation_not_found")
        self.recommendations.delete(record)

    # ── helpers ─────────────────────────────────────────────────────

    def _engine_user(self, user: User):
        from app.services.engine_adapter import load_engine_parts

        profile, financial, behavioral, goals = load_engine_parts(self.session, user)
        return EngineAdapter.to_engine_user(user, profile, financial, behavioral, goals)

    @staticmethod
    def _record_to_dict(r) -> dict:
        return {
            "id": str(r.id),
            "recommendation_type": r.recommendation_type,
            "title": r.title,
            "description": r.description,
            "confidence": r.confidence,
            "reasons": r.reasons,
            "action": r.action,
            "impact": r.impact,
            "priority": r.priority,
            "status": r.status,
            "valid_until": r.valid_until.isoformat() if r.valid_until else None,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }

