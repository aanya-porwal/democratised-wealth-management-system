"""Scenario tool — what-if scenario analysis via the engine."""

from __future__ import annotations

from typing import Any

from app.ai.tools.base import BaseTool, ToolError
from app.database.session import SessionLocal


class ScenarioTool(BaseTool):
    """Run what-if scenario analyses using the engine."""

    name: str = "scenario_tool"
    description: str = "Run what-if scenario analysis (salary change, market crash, etc.)"
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
            from app.services.simulation_service import SimulationService
            service = SimulationService(db)
            from app.schemas.simulation import ScenarioCreate
            data = ScenarioCreate(
                scenario_type=kwargs.get("scenario_type", "market_crash"),
                name=kwargs.get("name"),
                description=kwargs.get("description"),
                income_multiplier=kwargs.get("income_multiplier"),
                expense_multiplier=kwargs.get("expense_multiplier"),
                portfolio_drawdown=kwargs.get("portfolio_drawdown"),
                one_time_expense=kwargs.get("one_time_expense"),
                monthly_contribution_adjustment=kwargs.get("monthly_contribution_adjustment"),
                emergency_fund_months=kwargs.get("emergency_fund_months"),
                retirement_age=kwargs.get("retirement_age"),
                target_date_shift_years=kwargs.get("target_date_shift_years"),
                simulations=kwargs.get("simulations", 10000),
            )
            result = service.run_scenario(user, data)
            return {"scenario": result}
        finally:
            db.close()

    def validate_input(self, **kwargs: Any) -> list[str]:
        errors = []
        if "user_id" not in kwargs:
            errors.append("user_id is required")
        if "scenario_type" not in kwargs:
            errors.append("scenario_type is required")
        return errors
