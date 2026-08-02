"""Profile service — user profile, financial profile, behavioral profile
CRUD plus derived engine risk assessment persistence.
"""

from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError, ValidationError
from app.models import (
    BehavioralProfile,
    FinancialProfile,
    User,
    UserProfile,
)
from app.schemas.user import (
    BehavioralProfileCreate,
    FinancialProfileCreate,
    UserProfileCreate,
)
from app.services.engine_adapter import EngineAdapter


class ProfileService:
    """CRUD + engine integration for the three profile tables."""

    def __init__(self, session: Session) -> None:
        self.session = session

    # ── user profile ────────────────────────────────────────────────

    def get_user_profile(self, user_id: uuid.UUID) -> UserProfile:
        profile = (
            self.session.query(UserProfile)
            .filter(UserProfile.user_id == user_id)
            .first()
        )
        if profile is None or profile.is_deleted:
            raise NotFoundError("User profile not found", code="profile_not_found")
        return profile

    def upsert_user_profile(self, user: User, data: UserProfileCreate) -> UserProfile:
        profile = (
            self.session.query(UserProfile)
            .filter(UserProfile.user_id == user.id)
            .first()
        )
        if profile is None:
            profile = UserProfile(user_id=user.id, **data.model_dump())
            self.session.add(profile)
        else:
            for key, value in data.model_dump().items():
                setattr(profile, key, value)
        self.session.flush()
        return profile

    # ── financial profile ───────────────────────────────────────────

    def get_financial_profile(self, user_id: uuid.UUID) -> FinancialProfile:
        profile = (
            self.session.query(FinancialProfile)
            .filter(FinancialProfile.user_id == user_id)
            .first()
        )
        if profile is None:
            raise NotFoundError("Financial profile not found", code="financial_profile_not_found")
        return profile

    def upsert_financial_profile(self, user: User, data: FinancialProfileCreate) -> FinancialProfile:
        profile = (
            self.session.query(FinancialProfile)
            .filter(FinancialProfile.user_id == user.id)
            .first()
        )
        if profile is None:
            profile = FinancialProfile(user_id=user.id, **data.model_dump())
            self.session.add(profile)
        else:
            for key, value in data.model_dump().items():
                setattr(profile, key, value)
        self.session.flush()
        return profile

    # ── behavioral profile ──────────────────────────────────────────

    def get_behavioral_profile(self, user_id: uuid.UUID) -> BehavioralProfile:
        profile = (
            self.session.query(BehavioralProfile)
            .filter(BehavioralProfile.user_id == user_id)
            .first()
        )
        if profile is None:
            raise NotFoundError("Behavioral profile not found", code="behavioral_profile_not_found")
        return profile

    def upsert_behavioral_profile(self, user: User, data: BehavioralProfileCreate) -> BehavioralProfile:
        profile = (
            self.session.query(BehavioralProfile)
            .filter(BehavioralProfile.user_id == user.id)
            .first()
        )
        if profile is None:
            profile = BehavioralProfile(user_id=user.id, **data.model_dump())
            self.session.add(profile)
        else:
            for key, value in data.model_dump().items():
                setattr(profile, key, value)
        self.session.flush()
        return profile

    # ── risk assessment (engine) ────────────────────────────────────

    def assess_risk(self, user: User) -> dict:
        """Build the engine user aggregate and run the risk engine."""
        engine_user = self._engine_user(user)
        from engine import assess_risk  # thin shim → wealth_management_system.risk_engine

        result = assess_risk(engine_user)
        return {
            "capacity_score": result.capacity_score,
            "tolerance_score": result.tolerance_score,
            "final_score": result.final_score,
            "final_score_100": result.final_score_100,
            "risk_category": result.risk_category,
            "capacity_was_binding": result.capacity_was_binding,
            "breakdown": result.breakdown,
        }

    # ── helpers ─────────────────────────────────────────────────────

    def _engine_user(self, user: User):
        from app.services.engine_adapter import load_engine_parts

        profile, financial, behavioral, goals = load_engine_parts(self.session, user)
        return EngineAdapter.to_engine_user(
            user=user,
            profile=profile,
            financial=financial,
            behavioral=behavioral,
            goals=goals,
        )

