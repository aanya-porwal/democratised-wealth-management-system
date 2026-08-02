"""Scenario endpoints — what-if scenario analysis via the engine."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_db
from app.models.user import User
from app.schemas.simulation import ScenarioCreate, ScenarioOut
from app.services.simulation_service import SimulationService

router = APIRouter()


def _simulation_service(session: Annotated[Session, Depends(get_db)]) -> SimulationService:
    return SimulationService(session)


@router.post(
    "",
    response_model=dict,
    status_code=201,
    summary="Run a scenario analysis",
    description="Applies a what-if scenario (salary change, market crash, "
    "retirement shift, house purchase...) to the user and returns "
    "recomputed goal probabilities, required SIP, net worth and allocation.",
)
def run_scenario(
    payload: ScenarioCreate,
    current: Annotated[User, Depends(get_current_user)],
    service: Annotated[SimulationService, Depends(_simulation_service)],
) -> dict:
    """Run and persist a scenario analysis."""
    result = service.run_scenario(current, payload)
    service.session.commit()
    return result


@router.get(
    "",
    response_model=list[dict],
    summary="List scenario analyses",
    description="Lists the current user's past scenario runs.",
)
def list_scenarios(
    current: Annotated[User, Depends(get_current_user)],
    service: Annotated[SimulationService, Depends(_simulation_service)],
    limit: int = Query(50, ge=1, le=200),
) -> list[dict]:
    """List the current user's scenarios."""
    return service.list_scenarios(current.id, limit=limit)


@router.get(
    "/{scenario_id}",
    response_model=ScenarioOut,
    summary="Get a scenario analysis",
    description="Returns a persisted scenario by id (user-scoped).",
)
def get_scenario(
    scenario_id: uuid.UUID,
    current: Annotated[User, Depends(get_current_user)],
    service: Annotated[SimulationService, Depends(_simulation_service)],
) -> ScenarioOut:
    """Fetch a persisted scenario analysis."""
    return ScenarioOut(**service.get_scenario(current.id, scenario_id))

