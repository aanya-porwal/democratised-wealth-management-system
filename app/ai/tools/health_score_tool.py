"""Health score tool — financial health score via the engine."""

from __future__ import annotations

from typing import Any

from app.ai.tools.base import BaseTool, ToolError
from app.database.session import SessionLocal


class HealthScoreTool(BaseTool):
    """Compute the financial health score using the engine."""

    name: str = "health_score_tool"
    description: str = "Compute financial health score using the engine"
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
            from app.services.health_service import HealthService
            service = HealthService(db)
            result = service.compute(user, persist=True)
            return {"health_score": result}
        finally:
            db.close()

    def validate_input(self, **kwargs: Any) -> list[str]:
        errors = []
        if "user_id" not in kwargs:
            errors.append("user_id is required")
        return errors
