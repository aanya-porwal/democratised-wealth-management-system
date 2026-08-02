"""Simulation repository."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone

from sqlalchemy import select

from app.models.simulation import ScenarioAnalysis, SimulationResult
from app.repositories.base import BaseRepository


class SimulationRepository(BaseRepository[SimulationResult]):
    """Persistence for simulation runs and scenario analyses."""

    model = SimulationResult

    # ── simulation results ──────────────────────────────────────────

    def create_simulation(
        self,
        *,
        user_id: uuid.UUID,
        goal_id: uuid.UUID | None = None,
        simulation_type: str = "monte_carlo",
        parameters: dict | None = None,
        statistics: dict | None = None,
        median: float | None = None,
        probability_of_success: float | None = None,
        run_at: datetime | None = None,
    ) -> SimulationResult:
        """Create a persisted simulation result row.

        ``parameters``/``statistics``/``percentiles`` are stored as JSON
        columns; the model stores the whole ``parameters`` dict directly.
        """
        record = SimulationResult(
            user_id=user_id,
            goal_id=goal_id,
            simulation_type=simulation_type,
            parameters=parameters if isinstance(parameters, dict) else json.loads(parameters or "{}"),
            statistics=statistics if isinstance(statistics, dict) else None,
            median=median,
            probability_of_success=probability_of_success,
            run_at=run_at or datetime.now(timezone.utc),
        )
        self.session.add(record)
        self.session.flush()
        return record

    def list_simulations(self, user_id: uuid.UUID, limit: int = 20) -> list[SimulationResult]:
        stmt = (
            select(SimulationResult)
            .where(SimulationResult.user_id == user_id)
            .order_by(SimulationResult.run_at.desc())
            .limit(limit)
        )
        return list(self.session.execute(stmt).scalars().all())

    def get_simulation(self, sim_id: uuid.UUID, user_id: uuid.UUID) -> SimulationResult | None:
        stmt = select(SimulationResult).where(
            SimulationResult.id == sim_id, SimulationResult.user_id == user_id
        )
        return self.session.execute(stmt).scalars().first()

    # ── scenario analyses ───────────────────────────────────────────

    def create_scenario(
        self,
        *,
        user_id: uuid.UUID,
        scenario_type: str,
        name: str,
        description: str | None,
        summary: str,
        adjustments: dict | None = None,
        goal_probabilities: dict | None = None,
        total_required_sip: float | None = None,
        net_worth: float | None = None,
        allocation: dict | None = None,
        run_at: datetime | None = None,
    ) -> ScenarioAnalysis:
        """Create a persisted scenario analysis row.

        ``adjustments`` maps to the model's ``adjustments`` JSON column.
        """
        record = ScenarioAnalysis(
            user_id=user_id,
            scenario_type=scenario_type,
            name=name,
            description=description,
            summary=summary,
            adjustments=adjustments if isinstance(adjustments, dict) else json.loads(adjustments or "{}"),
            goal_probabilities=goal_probabilities if isinstance(goal_probabilities, dict) else json.loads(goal_probabilities or "{}"),
            total_required_sip=total_required_sip,
            net_worth=net_worth,
            allocation=allocation if isinstance(allocation, dict) else json.loads(allocation or "{}"),
            run_at=run_at or datetime.now(timezone.utc),
        )
        self.session.add(record)
        self.session.flush()
        return record

    def list_scenarios(self, user_id: uuid.UUID, limit: int = 20) -> list[ScenarioAnalysis]:
        stmt = (
            select(ScenarioAnalysis)
            .where(ScenarioAnalysis.user_id == user_id)
            .order_by(ScenarioAnalysis.run_at.desc())
            .limit(limit)
        )
        return list(self.session.execute(stmt).scalars().all())

    def get_scenario(self, scenario_id: uuid.UUID, user_id: uuid.UUID) -> ScenarioAnalysis | None:
        stmt = select(ScenarioAnalysis).where(
            ScenarioAnalysis.id == scenario_id,
            ScenarioAnalysis.user_id == user_id,
        )
        return self.session.execute(stmt).scalars().first()

