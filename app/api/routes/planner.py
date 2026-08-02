"""Planner endpoint — the full explained financial plan via the engine."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_db
from app.models.user import User
from app.services.planner_service import PlannerService

router = APIRouter()


def _planner_service(session: Annotated[Session, Depends(get_db)]) -> PlannerService:
    return PlannerService(session)


@router.get(
    "/plan",
    response_model=dict,
    summary="Build the full financial plan",
    description="Runs the complete planning pipeline (cashflow → health → goals "
    "→ risk → portfolio → probability → actions) and returns the explained plan.",
)
def build_plan(
    current: Annotated[User, Depends(get_current_user)],
    service: Annotated[PlannerService, Depends(_planner_service)],
) -> dict:
    """Return the complete explained financial plan for the current user."""
    return service.plan(current)

