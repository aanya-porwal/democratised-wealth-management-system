"""Simulation tool — Monte Carlo simulation via the engine."""

from __future__ import annotations

from typing import Any

from app.ai.tools.base import BaseTool, ToolError
from app.database.session import SessionLocal


class SimulationTool(BaseTool):
    """Run Monte Carlo simulations using the engine."""

    name: str = "simulation_tool"
    description: str = "Run Monte Carlo portfolio simulations"
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
            from app.schemas.simulation import SimulationCreate
            data = SimulationCreate(
                expected_return=kwargs.get("expected_return", 0.12),
                volatility=kwargs.get("volatility", 0.18),
                monthly_investment=kwargs.get("monthly_investment", 0),
                inflation=kwargs.get("inflation", 0.06),
                horizon_years=kwargs.get("horizon_years", 20),
                initial_corpus=kwargs.get("initial_corpus", 0),
                target_amount=kwargs.get("target_amount"),
                simulations=kwargs.get("simulations", 10000),
            )
            result = service.run_simulation(user, data)
            return {"simulation": result}
        finally:
            db.close()

    def validate_input(self, **kwargs: Any) -> list[str]:
        errors = []
        if "user_id" not in kwargs:
            errors.append("user_id is required")
        return errors
