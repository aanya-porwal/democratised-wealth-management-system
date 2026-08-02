"""Recommendation endpoints — generate, list, get and dismiss engine
recommendations.
"""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_db
from app.models.user import User
from app.schemas.common import MessageResponse
from app.schemas.recommendation import RecommendationActionUpdate, RecommendationOut
from app.services.recommendation_service import RecommendationService

router = APIRouter()


def _recommendation_service(
    session: Annotated[Session, Depends(get_db)],
) -> RecommendationService:
    return RecommendationService(session)


@router.post(
    "/generate",
    response_model=list[RecommendationOut],
    status_code=201,
    summary="Generate recommendations",
    description="Runs the explainable recommendation engine and persists the "
    "resulting recommendations for the current user.",
)
def generate_recommendations(
    current: Annotated[User, Depends(get_current_user)],
    service: Annotated[RecommendationService, Depends(_recommendation_service)],
    hours_valid: float = Query(24.0, gt=0, le=720, description="Validity window in hours"),
) -> list[RecommendationOut]:
    """Generate and persist a fresh recommendation set."""
    records = service.generate(current, hours_valid=hours_valid)
    service.session.commit()
    return [RecommendationOut(**r) for r in records]


@router.get(
    "",
    response_model=list[RecommendationOut],
    summary="List recommendations",
    description="Lists the current user's persisted recommendations.",
)
def list_recommendations(
    current: Annotated[User, Depends(get_current_user)],
    service: Annotated[RecommendationService, Depends(_recommendation_service)],
    limit: int = Query(50, ge=1, le=200),
) -> list[RecommendationOut]:
    """List the current user's recommendations."""
    records = service.list_for_user(current.id, limit=limit)
    return [RecommendationOut(**r) for r in records]


@router.get(
    "/{recommendation_id}",
    response_model=RecommendationOut,
    summary="Get a recommendation",
    description="Returns a single recommendation owned by the current user.",
)
def get_recommendation(
    recommendation_id: uuid.UUID,
    current: Annotated[User, Depends(get_current_user)],
    service: Annotated[RecommendationService, Depends(_recommendation_service)],
) -> RecommendationOut:
    """Fetch one recommendation."""
    return RecommendationOut(**service.get(current.id, recommendation_id))


@router.patch(
    "/{recommendation_id}",
    response_model=RecommendationOut,
    summary="Update recommendation status",
    description="Marks a recommendation as accepted, dismissed or completed.",
)
def update_recommendation_status(
    recommendation_id: uuid.UUID,
    payload: RecommendationActionUpdate,
    current: Annotated[User, Depends(get_current_user)],
    service: Annotated[RecommendationService, Depends(_recommendation_service)],
) -> RecommendationOut:
    """Update a recommendation's status."""
    record = service.get(current.id, recommendation_id)
    from app.models.recommendation import Recommendation

    obj = service.recommendations.get_for_user(recommendation_id, current.id)
    assert isinstance(obj, Recommendation)
    obj.status = payload.status
    service.session.commit()
    return RecommendationOut(**service.get(current.id, recommendation_id))


@router.delete(
    "/{recommendation_id}",
    response_model=MessageResponse,
    summary="Dismiss a recommendation",
    description="Soft-deletes (dismisses) a recommendation.",
)
def dismiss_recommendation(
    recommendation_id: uuid.UUID,
    current: Annotated[User, Depends(get_current_user)],
    service: Annotated[RecommendationService, Depends(_recommendation_service)],
) -> MessageResponse:
    """Dismiss (soft-delete) a recommendation."""
    service.dismiss(current.id, recommendation_id)
    service.session.commit()
    return MessageResponse(message="Recommendation dismissed")

