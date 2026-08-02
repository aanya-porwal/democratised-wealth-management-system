"""Risk assessment tool — calls the engine's risk assessment via ProfileService."""

from __future__ import annotations

from typing import Any

from app.ai.tools.base import BaseTool, ToolError
from app.database.session import SessionLocal
from app.services.profile_service import ProfileService


class RiskTool(BaseTool):
    """Assess the user's risk tolerance and capacity using the engine."""

    name: str = "risk_tool"
    description: str = "Assess risk tolerance and capacity via the risk engine"
    requires_confirmation: bool = False

    def execute(self, user_id: str, **kwargs: Any) -> dict[str, Any]:
        if not user_id:
            raise ToolError("user_id is required")
        db = SessionLocal()
        try:
            from app.models.user import User
            user = db.query(User).filter(User.id == user_id).first()
            if user is None:
                raise ToolError(f"user not found: {user_id}")
            service = ProfileService(db)
            result = service.assess_risk(user)
            return {"risk_assessment": result}
        finally:
            db.close()

    def validate_input(self, **kwargs: Any) -> list[str]:
        errors: list[str] = []
        if "user_id" not in kwargs:
            errors.append("user_id is required")
        return errors
