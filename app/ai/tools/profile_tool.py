"""Profile tool — manages user, financial, and behavioral profiles."""

from __future__ import annotations

from typing import Any

from app.ai.tools.base import BaseTool, ToolError
from app.database.session import SessionLocal


class ProfileTool(BaseTool):
    """Manage user profiles — demographic, financial, behavioral."""

    name: str = "profile_tool"
    description: str = "Manage user profiles (demographic, financial, behavioral)"
    requires_confirmation: bool = False

    def execute(self, action: str, user_id: str, **kwargs: Any) -> dict[str, Any]:
        if not user_id:
            raise ToolError("user_id is required")
        db = SessionLocal()
        try:
            from app.models.user import User
            user = db.query(User).filter(User.id == user_id).first()
            if user is None:
                raise ToolError(f"user not found: {user_id}")
            from app.services.profile_service import ProfileService
            service = ProfileService(db)

            if action == "get_user_profile":
                profile = service.get_user_profile(user.id)
                return {"profile": _profile_to_dict(profile)}
            elif action == "get_financial_profile":
                profile = service.get_financial_profile(user.id)
                return {"financial_profile": _financial_to_dict(profile)}
            elif action == "get_behavioral_profile":
                profile = service.get_behavioral_profile(user.id)
                return {"behavioral_profile": _behavioral_to_dict(profile)}
            elif action == "assess_risk":
                result = service.assess_risk(user)
                return {"risk_assessment": result}
            else:
                raise ToolError(f"unknown action: {action}")
        finally:
            db.close()

    def validate_input(self, **kwargs: Any) -> list[str]:
        errors: list[str] = []
        if "action" not in kwargs:
            errors.append("action is required")
        if "user_id" not in kwargs:
            errors.append("user_id is required")
        return errors


def _profile_to_dict(p) -> dict:
    return {
        "id": str(p.id), "name": p.name, "age": p.age,
        "date_of_birth": str(p.date_of_birth) if p.date_of_birth else None,
        "dependents": p.dependents,
    }


def _financial_to_dict(p) -> dict:
    return {
        "id": str(p.id), "monthly_income": p.monthly_income,
        "employment_type": p.employment_type,
        "monthly_fixed_expenses": p.monthly_fixed_expenses,
        "monthly_variable_expenses": p.monthly_variable_expenses,
        "emergency_fund_months": p.emergency_fund_months,
        "existing_investments": p.existing_investments,
        "total_debt": p.total_debt,
    }


def _behavioral_to_dict(p) -> dict:
    return {
        "id": str(p.id), "risk_tolerance": p.risk_tolerance,
        "financial_literacy_score": p.financial_literacy_score,
        "loss_aversion_score": p.loss_aversion_score,
    }
