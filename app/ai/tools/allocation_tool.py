"""Allocation tool — strategic asset allocation via the engine."""

from __future__ import annotations

from typing import Any

from app.ai.tools.base import BaseTool, ToolError
from app.database.session import SessionLocal


class AllocationTool(BaseTool):
    """Compute strategic asset allocation using the engine."""

    name: str = "allocation_tool"
    description: str = "Compute strategic asset allocation via the engine"
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
            from app.services.portfolio_service import PortfolioService
            service = PortfolioService(db)
            from app.schemas.allocation import AllocationRequest
            req = AllocationRequest(
                risk_score=kwargs.get("risk_score", 50),
                horizon_years=kwargs.get("horizon_years", 20),
                monthly_investment=kwargs.get("monthly_investment", 0),
                liquidity_need=kwargs.get("liquidity_need"),
            )
            result = service.get_allocation(user, req)
            return {"allocation": result}
        finally:
            db.close()

    def validate_input(self, **kwargs: Any) -> list[str]:
        errors = []
        if "user_id" not in kwargs:
            errors.append("user_id is required")
        return errors
