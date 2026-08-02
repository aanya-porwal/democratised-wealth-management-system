"""Allocation endpoints — strategic target allocation via the engine."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_db
from app.models.user import User
from app.schemas.allocation import AllocationOut, AllocationRequest
from app.services.portfolio_service import PortfolioService

router = APIRouter()


def _portfolio_service(session: Annotated[Session, Depends(get_db)]) -> PortfolioService:
    return PortfolioService(session)


@router.post(
    "",
    response_model=AllocationOut,
    summary="Compute strategic allocation",
    description="Runs the allocation engine for the current user and returns "
    "target weights across equity/debt/gold/cash/ELSS/PPF/EPF/NPS buckets "
    "with the underlying risk score and a plain-language explanation.",
)
def compute_allocation(
    payload: AllocationRequest,
    current: Annotated[User, Depends(get_current_user)],
    service: Annotated[PortfolioService, Depends(_portfolio_service)],
) -> AllocationOut:
    """Compute the strategic target allocation for the current user."""
    result = service.get_allocation(current, payload)
    return AllocationOut(**result)

