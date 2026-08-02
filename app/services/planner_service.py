"""Planner service — orchestrates the full engine planning pipeline
(``build_plan``) and returns the explained plan.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.models import User
from app.services.engine_adapter import EngineAdapter

from engine import build_plan  # noqa: E402


class PlannerService:
    """Runs the full financial planning pipeline against the engine."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def plan(self, user: User) -> dict:
        """Return the complete explained plan for a user."""
        engine_user = self._engine_user(user)
        plan = build_plan(engine_user)
        return self._plan_to_dict(plan)

    # ── helpers ─────────────────────────────────────────────────────

    def _engine_user(self, user: User):
        from app.services.engine_adapter import load_engine_parts

        profile, financial, behavioral, goals = load_engine_parts(self.session, user)
        return EngineAdapter.to_engine_user(user, profile, financial, behavioral, goals)

    @staticmethod
    def _plan_to_dict(plan) -> dict:
        """Flatten the engine FinancialPlan into a JSON-friendly dict."""
        return {
            "user_name": plan.user_name,
            "summary": plan.summary,
            "cashflow": {
                "monthly_surplus": plan.cashflow.monthly_surplus,
                "savings_rate": plan.cashflow.savings_rate,
                "emergency_fund_months": plan.cashflow.emergency_fund_months,
                "emergency_fund_target_months": plan.cashflow.emergency_fund_target_months,
                "emergency_fund_amount_needed": plan.cashflow.emergency_fund_amount_needed,
                "emergency_fund_priority": plan.cashflow.emergency_fund_priority,
            },
            "health": {
                "score": plan.health.score,
                "grade": plan.health.grade,
            },
            "risk": {
                "final_score_100": plan.risk.final_score_100,
                "risk_category": plan.risk.risk_category,
                "capacity_was_binding": plan.risk.capacity_was_binding,
            },
            "portfolio": EngineAdapter.portfolio_plan_to_dict(plan.portfolio),
            "goals": {
                "surplus_after_foundations": plan.goals.surplus_after_foundations,
                "goal_plans": [
                    {
                        "goal_type": gp.goal_type,
                        "priority": gp.priority,
                        "target_amount": gp.target_amount,
                        "current_savings": gp.current_savings,
                        "monthly_contribution": gp.monthly_contribution,
                        "years": gp.years,
                        "projected_value": gp.projected_value,
                        "probability": gp.probability,
                        "required_monthly": gp.required_monthly,
                        "shortfall": gp.shortfall,
                        "feasible": gp.feasible,
                    }
                    for gp in getattr(plan.goals, "goals", [])
                ],
            },
            "probabilities": [
                {
                    "goal_type": p.goal_type.value
                    if hasattr(p.goal_type, "value")
                    else str(p.goal_type),
                    "probability": p.probability,
                    "median_outcome": p.median_outcome,
                    "shortfall_median": p.shortfall_median,
                    "verdict": p.verdict,
                }
                for p in plan.probabilities
            ],
            "actions": [
                {"action": a.action, "reason": a.reason, "priority": a.priority}
                for a in plan.actions
            ],
        }

