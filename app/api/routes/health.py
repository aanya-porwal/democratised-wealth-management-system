"""Financial health score endpoints — 0-100 score + explainable factors."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_db
from app.models.user import User
from app.schemas.health import HealthScoreOut
from app.services.health_service import HealthService

router = APIRouter()


def _health_service(session: Annotated[Session, Depends(get_db)]) -> HealthService:
    return HealthService(session)


@router.post(
    "",
    response_model=HealthScoreOut,
    summary="Compute financial health score",
    description="Runs the health-score engine for the current user and persists "
    "the score with per-factor breakdown, strengths, weaknesses and suggestions.",
)
def compute_health_score(
    current: Annotated[User, Depends(get_current_user)],
    service: Annotated[HealthService, Depends(_health_service)],
) -> HealthScoreOut:
    """Compute and persist the current health score."""
    data = service.compute(current, persist=True)
    service.session.commit()
    return HealthScoreOut(**data)


@router.get(
    "/latest",
    response_model=list[dict],
    summary="Latest health scores",
    description="Returns the most recent health score snapshots for the user.",
)
def latest_health_scores(
    current: Annotated[User, Depends(get_current_user)],
    service: Annotated[HealthService, Depends(_health_service)],
    limit: int = Query(10, ge=1, le=100),
) -> list[dict]:
    """List the latest persisted health scores."""
    return service.latest_scores(current.id, limit=limit)

