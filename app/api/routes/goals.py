"""Goal endpoints — CRUD, engine analysis, and progress snapshots."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_db
from app.models.user import User
from app.schemas.common import MessageResponse
from app.schemas.goal import (
    GoalAnalysisOut,
    GoalCreate,
    GoalOut,
    GoalProgressOut,
    GoalUpdate,
)
from app.services.goal_service import GoalService

router = APIRouter()


def _goal_service(session: Annotated[Session, Depends(get_db)]) -> GoalService:
    return GoalService(session)


@router.post(
    "",
    response_model=GoalOut,
    status_code=201,
    summary="Create a goal",
    description="Adds a financial goal for the current user.",
)
def create_goal(
    payload: GoalCreate,
    current: Annotated[User, Depends(get_current_user)],
    service: Annotated[GoalService, Depends(_goal_service)],
) -> GoalOut:
    """Create a new goal."""
    goal = service.create_goal(current, payload)
    service.session.commit()
    return GoalOut.model_validate(goal)


@router.get(
    "",
    response_model=list[GoalOut],
    summary="List goals",
    description="Lists all goals for the current user.",
)
def list_goals(
    current: Annotated[User, Depends(get_current_user)],
    service: Annotated[GoalService, Depends(_goal_service)],
) -> list[GoalOut]:
    """List the current user's goals."""
    return [GoalOut.model_validate(g) for g in service.list_goals(current.id)]


@router.get(
    "/analysis",
    response_model=list[GoalAnalysisOut],
    summary="Analyse all goals",
    description="Runs the engine's goal-analysis for every goal and returns "
    "inflation-adjusted targets, required SIPs and success probabilities.",
)
def analyse_all_goals(
    current: Annotated[User, Depends(get_current_user)],
    service: Annotated[GoalService, Depends(_goal_service)],
) -> list[GoalAnalysisOut]:
    """Analyse every goal with the goal engine."""
    return [GoalAnalysisOut(**a) for a in service.analyse_all_goals(current)]


@router.get(
    "/{goal_id}",
    response_model=GoalOut,
    summary="Get a goal",
    description="Returns a single goal owned by the current user.",
)
def get_goal(
    goal_id: uuid.UUID,
    current: Annotated[User, Depends(get_current_user)],
    service: Annotated[GoalService, Depends(_goal_service)],
) -> GoalOut:
    """Fetch one goal."""
    return GoalOut.model_validate(service.get_goal(current.id, goal_id))


@router.patch(
    "/{goal_id}",
    response_model=GoalOut,
    summary="Update a goal",
    description="Partially updates goal fields (target amount, date, priority...).",
)
def update_goal(
    goal_id: uuid.UUID,
    payload: GoalUpdate,
    current: Annotated[User, Depends(get_current_user)],
    service: Annotated[GoalService, Depends(_goal_service)],
) -> GoalOut:
    """Update one goal."""
    goal = service.update_goal(current.id, goal_id, payload)
    service.session.commit()
    return GoalOut.model_validate(goal)


@router.delete(
    "/{goal_id}",
    response_model=MessageResponse,
    summary="Delete a goal",
    description="Soft-deletes a goal owned by the current user.",
)
def delete_goal(
    goal_id: uuid.UUID,
    current: Annotated[User, Depends(get_current_user)],
    service: Annotated[GoalService, Depends(_goal_service)],
) -> MessageResponse:
    """Delete (soft) one goal."""
    service.delete_goal(current.id, goal_id)
    service.session.commit()
    return MessageResponse(message="Goal deleted")


@router.get(
    "/{goal_id}/analysis",
    response_model=GoalAnalysisOut,
    summary="Analyse one goal",
    description="Runs the engine's goal-analysis for a single goal.",
)
def analyse_goal(
    goal_id: uuid.UUID,
    current: Annotated[User, Depends(get_current_user)],
    service: Annotated[GoalService, Depends(_goal_service)],
) -> GoalAnalysisOut:
    """Analyse one goal with the goal engine."""
    return GoalAnalysisOut(**service.analyse_goal(current.id, goal_id))


@router.post(
    "/{goal_id}/progress",
    response_model=GoalProgressOut,
    summary="Record goal progress",
    description="Computes and stores a progress snapshot for one goal.",
)
def record_progress(
    goal_id: uuid.UUID,
    current: Annotated[User, Depends(get_current_user)],
    service: Annotated[GoalService, Depends(_goal_service)],
) -> GoalProgressOut:
    """Record a goal-progress snapshot."""
    record = service.record_progress(current.id, goal_id)
    service.session.commit()
    return GoalProgressOut(**record)

