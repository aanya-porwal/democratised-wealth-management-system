"""Simulation service — Monte Carlo portfolio simulation and scenario
analysis, both persisted as simulation/analysis rows.
"""

from __future__ import annotations

import json
import uuid

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.models import User
from app.repositories.simulation_repository import SimulationRepository
from app.schemas.simulation import ScenarioCreate, SimulationCreate
from app.services.engine_adapter import EngineAdapter

from engine import MonteCarloEngine, Scenario, ScenarioEngine, ScenarioType  # noqa: E402


class SimulationService:
    """Runs the Monte Carlo and scenario engines and persists results."""

    def __init__(self, session: Session) -> None:
        self.session = session
        self.simulations = SimulationRepository(session)

    # ── Monte Carlo ─────────────────────────────────────────────────

    def run_simulation(self, user: User, data: SimulationCreate) -> dict:
        """Run a Monte Carlo simulation for a user and persist the result."""
        result = MonteCarloEngine(simulations=data.simulations).run(
            expected_return=data.expected_return,
            volatility=data.volatility,
            monthly_investment=data.monthly_investment,
            inflation=data.inflation,
            horizon_years=data.horizon_years,
            initial_corpus=data.initial_corpus or 0.0,
            target_amount=data.target_amount,
        )
        stats = EngineAdapter.simulation_to_dict(result)
        record = self.simulations.create_simulation(
            user_id=user.id,
            goal_id=data.goal_id,
            simulation_type=data.simulation_type,
            simulations=data.simulations,
            horizon_years=data.horizon_years,
            expected_return=data.expected_return,
            volatility=data.volatility,
            inflation=data.inflation,
            monthly_investment=data.monthly_investment,
            initial_corpus=data.initial_corpus or 0.0,
            target_amount=data.target_amount,
            parameters=data.model_dump(exclude={"goal_id", "simulation_type", "simulations"}),
            statistics=stats,
            median=stats["median"],
            probability_of_success=stats["probability_of_success"],
        )
        return {
            "id": str(record.id),
            "simulation_type": record.simulation_type,
            "parameters": data.model_dump(),
            "statistics": stats,
        }

    def list_simulations(self, user_id: uuid.UUID, limit: int = 50) -> list[dict]:
        records = self.simulations.list_simulations(user_id, limit=limit)
        out = []
        for r in records:
            out.append(
                {
                    "id": str(r.id),
                    "simulation_type": r.simulation_type,
                    "median": r.median,
                    "probability_of_success": r.probability_of_success,
                    "created_at": r.created_at.isoformat() if r.created_at else None,
                }
            )
        return out

    # ── scenarios ───────────────────────────────────────────────────

    def run_scenario(self, user: User, data: ScenarioCreate) -> dict:
        """Apply a what-if scenario via the engine and persist the result."""
        engine_user = self._engine_user(user)
        scenario = self._build_scenario(data)
        variant = ScenarioEngine(simulations=data.simulations).apply(engine_user, scenario)
        record = self.simulations.create_scenario(
            user_id=user.id,
            scenario_type=data.scenario_type,
            name=data.name or variant.scenario.name,
            description=data.description or variant.scenario.description,
            adjustments=self._scenario_params(variant.scenario),
            goal_probabilities=variant.goal_probabilities,
            total_required_sip=variant.total_required_sip,
            net_worth=variant.net_worth,
            allocation=variant.allocation,
            summary=variant.summary,
        )
        return {
            "id": str(record.id),
            "scenario": data.scenario_type,
            "goal_probabilities": variant.goal_probabilities,
            "total_required_sip": variant.total_required_sip,
            "net_worth": variant.net_worth,
            "allocation": variant.allocation,
            "summary": variant.summary,
        }

    def list_scenarios(self, user_id: uuid.UUID, limit: int = 50) -> list[dict]:
        records = self.simulations.list_scenarios(user_id, limit=limit)
        out = []
        for r in records:
            out.append(
                {
                    "id": str(r.id),
                    "scenario_type": r.scenario_type,
                    "name": r.name,
                    "summary": r.summary,
                    "created_at": r.created_at.isoformat() if r.created_at else None,
                }
            )
        return out

    def get_scenario(self, user_id: uuid.UUID, scenario_id: uuid.UUID) -> dict:
        record = self.simulations.get_scenario(scenario_id, user_id)
        if record is None:
            raise NotFoundError("Scenario not found", code="scenario_not_found")
        return {
            "id": str(record.id),
            "scenario_type": record.scenario_type,
            "name": record.name,
            "description": record.description,
            "adjustments": record.adjustments or {},
            "goal_probabilities": record.goal_probabilities or {},
            "total_required_sip": record.total_required_sip,
            "net_worth": record.net_worth,
            "allocation": record.allocation or {},
            "summary": record.summary,
        }

    # ── helpers ─────────────────────────────────────────────────────

    @staticmethod
    def _build_scenario(data: ScenarioCreate) -> Scenario:
        return Scenario(
            scenario_type=ScenarioType(data.scenario_type),
            name=data.name or "",
            description=data.description or "",
            income_multiplier=data.income_multiplier,
            expense_multiplier=data.expense_multiplier,
            portfolio_drawdown=data.portfolio_drawdown,
            one_time_expense=data.one_time_expense,
            monthly_contribution_adjustment=data.monthly_contribution_adjustment,
            emergency_fund_months=data.emergency_fund_months,
            retirement_age=data.retirement_age,
            target_date_shift_years=data.target_date_shift_years,
        )

    @staticmethod
    def _scenario_params(scenario: Scenario) -> dict:
        return {
            "scenario_type": scenario.scenario_type.value,
            "name": scenario.name,
            "description": scenario.description,
            "income_multiplier": scenario.income_multiplier,
            "expense_multiplier": scenario.expense_multiplier,
            "portfolio_drawdown": scenario.portfolio_drawdown,
            "one_time_expense": scenario.one_time_expense,
            "monthly_contribution_adjustment": scenario.monthly_contribution_adjustment,
            "emergency_fund_months": scenario.emergency_fund_months,
            "retirement_age": scenario.retirement_age,
            "target_date_shift_years": scenario.target_date_shift_years,
        }

    def _engine_user(self, user: User):
        from app.services.engine_adapter import load_engine_parts

        profile, financial, behavioral, goals = load_engine_parts(self.session, user)
        return EngineAdapter.to_engine_user(user, profile, financial, behavioral, goals)

