"""Engine adapter — the single integration point between the backend and
the financial engine.

This module is the ONLY place in the backend allowed to import
``wealth_management_system`` directly. It performs bidirectional mapping
between backend ORM rows (users, financial/behavioral profiles, goals)
and the engine's dataclass models, then invokes the engine's pure
functions.

The engine remains completely independent: no backend code lives in
``wealth_management_system/``, no engine code lives in ``app/``, and no
calculation is duplicated here.
"""

from __future__ import annotations

from datetime import date
from typing import Any

# ── engine imports (isolated here by design) ─────────────────────────
from wealth_management_system.models import (  # type: ignore
    BehavioralProfile,
    EmploymentType,
    FinancialProfile,
    Goal as EngineGoal,
    GoalPriority,
    GoalType,
    RiskToleranceLevel,
    UserProfile,
)

# ── engine exceptions forwarded to the error handlers ────────────────
from wealth_management_system.exceptions import WealthManagementError  # type: ignore

from app.core.exceptions import NotFoundError
from app.models import (
    BehavioralProfile as DBBehavioralProfile,
    FinancialProfile as DBFinancialProfile,
    Goal as DBGoal,
    User,
    UserProfile as DBUserProfile,
)

def load_engine_parts(session, user: User):
    """Load the ORM rows that make up a user's engine profile.

    This is the single, correct way to assemble the backend ORM rows
    (user profile, financial profile, behavioral profile, goals) from an
    authenticated :class:`app.models.user.User` into the shapes the
    engine needs.

    Why this helper exists
    ----------------------
    ``UserProfile`` (and each profile table) has its *own* UUID primary
    key ``id``; the FK back to ``users`` is the ``user_id`` column.
    Querying with ``session.get(UserProfile, user.id)`` therefore always
    returns ``None`` and silently emptied every engine input. All
    services must lookup by ``UserProfile.user_id == user.id`` instead.
    """
    from sqlalchemy import select

    from app.models import (
        BehavioralProfile as DBBehavioralProfile,
        FinancialProfile as DBFinancialProfile,
        UserProfile as DBUserProfile,
    )
    from app.repositories.goal_repository import GoalRepository

    profile = session.execute(
        select(DBUserProfile).where(DBUserProfile.user_id == user.id)
    ).scalars().first()
    financial = session.execute(
        select(DBFinancialProfile).where(DBFinancialProfile.user_id == user.id)
    ).scalars().first()
    behavioral = session.execute(
        select(DBBehavioralProfile).where(DBBehavioralProfile.user_id == user.id)
    ).scalars().first()
    goals = GoalRepository(session).list_for_user(user.id)

    # Financial and behavioral profiles are genuinely required to build the
    # engine aggregate; without them the engine crashes with AttributeError.
    # The profile endpoints already surface these as 404s, so mirror that.
    if financial is None:
        raise NotFoundError(
            "Financial profile is required for this operation",
            code="financial_profile_not_found",
        )
    if behavioral is None:
        raise NotFoundError(
            "Behavioral profile is required for this operation",
            code="behavioral_profile_not_found",
        )

    return profile, financial, behavioral, goals


__all__ = ["WealthManagementError", "EngineAdapter", "load_engine_parts"]


class EngineAdapter:
    """Stateless mapping helpers + thin engine call wrappers.

    Kept as a class so services can depend on it and tests can subclass
    or mock it. Methods marked ``@staticmethod`` are pure converters.
    """

    # ── enums ───────────────────────────────────────────────────────

    @staticmethod
    def employment_type(value: str | None) -> EmploymentType:
        try:
            return EmploymentType(value or "salaried_private")
        except ValueError:
            return EmploymentType.SALARIED_PRIVATE

    @staticmethod
    def risk_tolerance(value: str | None) -> RiskToleranceLevel:
        mapping = {
            "very_conservative": RiskToleranceLevel.VERY_CONSERVATIVE,
            "conservative": RiskToleranceLevel.CONSERVATIVE,
            "moderate": RiskToleranceLevel.MODERATE,
            "aggressive": RiskToleranceLevel.AGGRESSIVE,
            "very_aggressive": RiskToleranceLevel.VERY_AGGRESSIVE,
        }
        return mapping.get(value or "moderate", RiskToleranceLevel.MODERATE)

    @staticmethod
    def goal_type(value: str) -> GoalType:
        try:
            return GoalType(value)
        except ValueError:
            return GoalType.OTHER

    @staticmethod
    def goal_priority(value: str) -> GoalPriority:
        try:
            return GoalPriority(value)
        except ValueError:
            return GoalPriority.HIGH

    # ── DB → engine (user aggregate) ────────────────────────────────

    @staticmethod
    def to_engine_user(
        user: User,
        profile: DBUserProfile | None,
        financial: DBFinancialProfile | None,
        behavioral: DBBehavioralProfile | None,
        goals: list[DBGoal],
    ) -> UserProfile:
        """Assemble an engine ``UserProfile`` from ORM rows."""
        name = profile.name if profile else (user.full_name or user.email)
        age = profile.age if profile else 0

        engine_financial = None
        if financial:
            engine_financial = FinancialProfile(
                monthly_income=financial.monthly_income,
                employment_type=EngineAdapter.employment_type(financial.employment_type),
                income_stability=financial.income_stability,
                monthly_fixed_expenses=financial.monthly_fixed_expenses,
                monthly_variable_expenses=financial.monthly_variable_expenses,
                has_secondary_income=financial.secondary_income,
                secondary_monthly_income=financial.secondary_monthly_income,
                emergency_fund_months=financial.emergency_fund_months,
                existing_investments=financial.existing_investments,
                provident_fund_balance=financial.provident_fund_balance,
                real_estate_value=financial.real_estate_value,
                gold_value=financial.gold_value,
                total_debt=financial.total_debt,
                monthly_emi_total=financial.monthly_emi_total,
                tax_bracket_percent=financial.tax_bracket_percent,
                has_term_life_insurance=financial.has_term_life_insurance,
                has_health_insurance=financial.has_health_insurance,
                existing_monthly_sip=financial.existing_monthly_sip,
            )

        engine_behavioral = None
        if behavioral:
            engine_behavioral = BehavioralProfile(
                risk_tolerance=EngineAdapter.risk_tolerance(behavioral.risk_tolerance),
                drawdown_reaction_score=behavioral.drawdown_reaction_score,
                has_invested_before=behavioral.has_invested_before,
                has_experienced_market_crash=behavioral.has_experienced_market_crash,
                financial_literacy_score=behavioral.financial_literacy_score,
                loss_aversion_score=behavioral.loss_aversion_score,
            )

        engine_goals = [EngineAdapter.to_engine_goal(g) for g in goals]

        return UserProfile(
            user_id=str(user.id),
            name=name,
            age=max(age, 0),
            date_of_birth=profile.date_of_birth if profile and profile.date_of_birth else date.today(),
            dependents=profile.dependents if profile else 0,
            financial=engine_financial,
            behavioral=engine_behavioral,
            goals=engine_goals,
        )

    @staticmethod
    def to_engine_goal(goal: DBGoal) -> EngineGoal:
        return EngineGoal(
            goal_type=EngineAdapter.goal_type(goal.goal_type),
            priority=EngineAdapter.goal_priority(goal.priority),
            target_amount=float(goal.target_amount),
            target_date=goal.target_date,
            current_savings_for_goal=float(goal.current_savings_for_goal),
            current_monthly_contribution=float(goal.current_monthly_contribution),
            notes=goal.name or goal.notes or "",
        )

    @staticmethod
    def build_engine_user_with_goals(
        user: User, goals: list[DBGoal]
    ) -> UserProfile:
        """Build a minimal engine user carrying only goals.

        Used for goal-only engine calls (e.g. ``GoalEngine.analyse_all``)
        when the financial/behavioral profiles are not required.
        """
        return EngineAdapter.to_engine_user(
            user=user,
            profile=None,
            financial=None,
            behavioral=None,
            goals=goals,
        )

    # ── engine → DB (persistence helpers) ───────────────────────────

    @staticmethod
    def goal_analysis_to_dict(analysis: Any) -> dict[str, Any]:
        """Flatten an engine ``GoalAnalysis`` into a persistable dict."""
        return {
            "name": analysis.name,
            "goal_type": analysis.goal_type,
            "priority": analysis.priority,
            "current_amount": analysis.current_amount,
            "target_amount": analysis.target_amount,
            "current_progress": analysis.current_progress,
            "target_date": analysis.target_date.isoformat(),
            "years_remaining": analysis.years_remaining,
            "inflation_rate": analysis.inflation_rate,
            "expected_return": analysis.expected_return,
            "inflation_adjusted_target": analysis.inflation_adjusted_target,
            "future_value": analysis.future_value,
            "present_value": analysis.present_value,
            "required_sip": analysis.required_sip,
            "remaining_gap": analysis.remaining_gap,
            "expected_corpus": analysis.expected_corpus,
            "probability_of_success": analysis.probability_of_success,
            "verdict": analysis.verdict.value if hasattr(analysis.verdict, "value") else str(analysis.verdict),
            "notes": list(analysis.notes),
        }

    @staticmethod
    def allocation_to_dict(result: Any) -> dict[str, Any]:
        """Flatten an engine ``AllocationResult`` into a dict."""
        return {
            "buckets": [
                {"bucket": b.bucket, "weight": b.weight, "instruments": list(b.instruments)}
                for b in result.buckets
            ],
            "risk_score": result.risk_score,
            "risk_category": result.risk_category,
            "explanation": result.explanation,
        }

    @staticmethod
    def portfolio_plan_to_dict(plan: Any) -> dict[str, Any]:
        """Flatten a legacy ``PortfolioPlan`` (from ``build_plan``) into a dict.

        The legacy plan carries ``slices`` (bucket name, weight,
        instruments) rather than the newer ``AllocationResult.buckets``.
        """
        slices = getattr(plan, "slices", None) or []
        return {
            "slices": [
                {
                    "bucket": s.bucket,
                    "weight": s.weight,
                    "instruments": [i.value for i in getattr(s, "instruments", [])],
                }
                for s in slices
            ],
            "risk_score": getattr(plan, "risk_score", None),
            "risk_category": getattr(plan, "risk_category", None),
        }

    @staticmethod
    def health_to_dict(result: Any) -> dict[str, Any]:
        """Flatten an engine ``HealthScoreResult`` into a dict."""
        return {
            "score": result.score,
            "grade": result.grade,
            "factors": [
                {
                    "name": f.name,
                    "score": f.score,
                    "max_points": f.max_points,
                    "severity": f.severity,
                    "message": f.message,
                    "percentage": f.percentage,
                }
                for f in result.factors
            ],
            "strengths": list(result.strengths),
            "weaknesses": list(result.weaknesses),
            "suggestions": list(result.suggestions),
        }

    @staticmethod
    def recommendations_to_dicts(result: Any) -> list[dict[str, Any]]:
        """Flatten an engine recommendation list into persistable dicts."""
        out: list[dict[str, Any]] = []
        for rec in result:
            out.append(
                {
                    "recommendation_type": rec.recommendation_type.value
                    if hasattr(rec.recommendation_type, "value")
                    else str(rec.recommendation_type),
                    "title": rec.title,
                    "description": rec.description,
                    "confidence": rec.confidence.value
                    if hasattr(rec.confidence, "value")
                    else str(rec.confidence),
                    "reasons": [r.text for r in rec.reasons],
                    "action": rec.action,
                    "impact": rec.impact,
                    "priority": EngineAdapter._priority_score(rec),
                }
            )
        return out

    @staticmethod
    def simulation_to_dict(result: Any) -> dict[str, Any]:
        """Flatten an engine ``SimulationResult`` (statistics only)."""
        stats = result.statistics
        return {
            "median": stats.median,
            "percentile_5": stats.percentile_5,
            "percentile_25": stats.percentile_25,
            "percentile_75": stats.percentile_75,
            "percentile_95": stats.percentile_95,
            "worst_case": stats.worst_case,
            "best_case": stats.best_case,
            "mean": stats.mean,
            "std_dev": stats.std_dev,
            "probability_of_success": stats.probability_of_success,
        }

    @staticmethod
    def rebalance_to_dict(result: Any) -> dict[str, Any]:
        """Flatten an engine ``RebalanceResult`` into a dict."""
        return {
            "rebalance_required": result.rebalance_required,
            "actions": [
                {
                    "bucket": a.bucket,
                    "direction": a.direction.value,
                    "current_weight": a.current_weight,
                    "target_weight": a.target_weight,
                    "drift": a.drift,
                    "trade_amount": a.trade_amount,
                    "reason": a.reason,
                }
                for a in result.actions
            ],
            "trades": [
                {
                    "asset_class": t.asset_class.value,
                    "amount": t.amount,
                    "reason": t.reason,
                    "estimated_tax_impact": t.estimated_tax_impact,
                    "estimated_transaction_cost": t.estimated_transaction_cost,
                }
                for t in result.trades
            ],
            "total_transaction_cost": result.total_transaction_cost,
            "total_tax_impact": result.total_tax_impact,
            "portfolio_value": result.portfolio_value,
            "notes": list(result.notes),
        }

    # ── helpers ─────────────────────────────────────────────────────

    @staticmethod
    def _priority_score(rec: Any) -> float:
        """Heuristic priority (1.0 = most urgent)."""
        conf = rec.confidence.value if hasattr(rec.confidence, "value") else str(rec.confidence)
        if conf == "high":
            return 1.0
        if conf == "medium":
            return 0.6
        return 0.3

