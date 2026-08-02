"""Database tool — query user data from the database (requires confirmation)."""

from __future__ import annotations

from typing import Any

from app.ai.tools.base import BaseTool, ToolError
from app.database.session import SessionLocal


class DatabaseTool(BaseTool):
    """Query user data from the database. Requires confirmation."""

    name: str = "database_tool"
    description: str = "Query user data from the database"
    requires_confirmation: bool = True

    def execute(self, action: str, user_id: str, **kwargs: Any) -> dict[str, Any]:
        if not user_id:
            raise ToolError("user_id is required")
        db = SessionLocal()
        try:
            from app.models.user import User
            user = db.query(User).filter(User.id == user_id).first()
            if user is None:
                raise ToolError(f"user not found: {user_id}")

            if action == "user_info":
                return {"user": {"id": str(user.id), "email": user.email, "full_name": user.full_name, "role": user.role}}
            elif action == "count_goals":
                from app.models.goal import Goal
                count = db.query(Goal).filter(Goal.user_id == user.id, Goal.deleted_at.is_(None)).count()
                return {"goal_count": count}
            elif action == "count_portfolios":
                from app.models.portfolio import Portfolio
                count = db.query(Portfolio).filter(Portfolio.user_id == user.id, Portfolio.deleted_at.is_(None)).count()
                return {"portfolio_count": count}
            else:
                raise ToolError(f"unknown action: {action}")
        finally:
            db.close()

    def validate_input(self, **kwargs: Any) -> list[str]:
        errors = []
        if "action" not in kwargs:
            errors.append("action is required")
        if "user_id" not in kwargs:
            errors.append("user_id is required")
        return errors
