"""Simulation endpoints — Monte Carlo portfolio simulation."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_db
from app.models.user import User
from app.schemas.simulation import SimulationCreate, SimulationOut
from app.services.simulation_service import SimulationService

router = APIRouter()


def _simulation_service(session: Annotated[Session, Depends(get_db)]) -> SimulationService:
    return SimulationService(session)


@router.post(
    "",
    response_model=dict,
    status_code=201,
    summary="Run a Monte Carlo simulation",
    description="Simulates the user's corpus growth under lognormal returns and "
    "returns percentile statistics plus the probability of reaching a target.",
)
def run_simulation(
    payload: SimulationCreate,
    current: Annotated[User, Depends(get_current_user)],
    service: Annotated[SimulationService, Depends(_simulation_service)],
) -> dict:
    """Run and persist a Monte Carlo simulation."""
    result = service.run_simulation(current, payload)
    service.session.commit()
    return result


@router.get(
    "",
    response_model=list[dict],
    summary="List simulations",
    description="Lists the current user's past simulation runs.",
)
def list_simulations(
    current: Annotated[User, Depends(get_current_user)],
    service: Annotated[SimulationService, Depends(_simulation_service)],
    limit: int = Query(50, ge=1, le=200),
) -> list[dict]:
    """List the current user's simulations."""
    return service.list_simulations(current.id, limit=limit)


@router.get(
    "/{simulation_id}",
    response_model=SimulationOut,
    summary="Get a simulation result",
    description="Returns a persisted simulation by id (user-scoped).",
)
def get_simulation(
    simulation_id: uuid.UUID,
    current: Annotated[User, Depends(get_current_user)],
    service: Annotated[SimulationService, Depends(_simulation_service)],
) -> SimulationOut:
    """Fetch a persisted simulation."""
    return SimulationOut(**service.simulations.get_simulation(simulation_id, current.id).__dict__)  # type: ignore[arg-type]

