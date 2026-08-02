"""Rebalancing endpoints — drift-aware rebalancing via the engine."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Body, Depends
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_db
from app.models.user import User
from app.schemas.rebalance import RebalanceOut
from app.services.portfolio_service import PortfolioService

router = APIRouter()


def _portfolio_service(session: Annotated[Session, Depends(get_db)]) -> PortfolioService:
    return PortfolioService(session)


@router.post(
    "/{portfolio_id}",
    response_model=RebalanceOut,
    summary="Rebalance a portfolio",
    description="Compares current holdings to the target allocation and returns "
    "per-bucket actions plus instrument-level trades with tax and "
    "transaction-cost estimates.",
)
def rebalance_portfolio(
    portfolio_id: uuid.UUID,
    current: Annotated[User, Depends(get_current_user)],
    service: Annotated[PortfolioService, Depends(_portfolio_service)],
    target: dict[str, float] | None = Body(
        None,
        description="Optional bucket->weight target map. Defaults to the "
        "portfolio's stored target allocation.",
    ),
) -> RebalanceOut:
    """Run the rebalancing engine for a portfolio."""
    result = service.rebalance(current, portfolio_id, target=target)
    return RebalanceOut(**result)

