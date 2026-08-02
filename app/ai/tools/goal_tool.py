"""Goal tool — calls the GoalService/GoalEngine for goal analysis."""

from __future__ import annotations

from typing import Any

from app.ai.tools.base import BaseTool, ToolError
from app.database.session import SessionLocal


class GoalTool(BaseTool):
    """Analyze, create, list, and track financial goals."""

    name: str = "goal_tool"
    description: str = "Analyze, create, list, and track financial goals"
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
            from app.services.goal_service import GoalService
            service = GoalService(db)

            if action == "list":
                goals = service.list_goals(user.id)
                return {"goals": [_g_to_dict(g) for g in goals]}
            elif action == "analyse":
                goal_id = kwargs.get("goal_id")
                if not goal_id:
                    raise ToolError("goal_id required for analyse")
                result = service.analyse_goal(user.id, goal_id)
                return {"goal_analysis": result}
            elif action == "analyse_all":
                results = service.analyse_all_goals(user)
                return {"goal_analyses": results}
            elif action == "progress":
                goal_id = kwargs.get("goal_id")
                if not goal_id:
                    raise ToolError("goal_id required for progress")
                result = service.record_progress(user.id, goal_id)
                return {"goal_progress": result}
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


def _g_to_dict(g) -> dict:
    return {
        "id": str(g.id), "name": g.name, "goal_type": g.goal_type,
        "priority": g.priority, "target_amount": g.target_amount,
        "target_date": str(g.target_date) if g.target_date else None,
        "current_savings_for_goal": g.current_savings_for_goal,
        "current_monthly_contribution": g.current_monthly_contribution,
    }
