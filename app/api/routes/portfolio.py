"""Portfolio endpoints — portfolio CRUD, holdings and snapshots."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_db
from app.models.user import User
from app.schemas.common import MessageResponse
from app.schemas.portfolio import (
    HoldingCreate,
    HoldingOut,
    PortfolioCreate,
    PortfolioOut,
    PortfolioSnapshotOut,
)
from app.services.portfolio_service import PortfolioService

router = APIRouter()


def _portfolio_service(session: Annotated[Session, Depends(get_db)]) -> PortfolioService:
    return PortfolioService(session)


@router.post(
    "",
    response_model=PortfolioOut,
    status_code=201,
    summary="Create a portfolio",
    description="Creates a named portfolio with an optional target allocation.",
)
def create_portfolio(
    payload: PortfolioCreate,
    current: Annotated[User, Depends(get_current_user)],
    service: Annotated[PortfolioService, Depends(_portfolio_service)],
) -> PortfolioOut:
    """Create a portfolio for the current user."""
    portfolio = service.create_portfolio(current, payload)
    service.session.commit()
    return PortfolioOut.model_validate(portfolio)


@router.get(
    "",
    response_model=list[PortfolioOut],
    summary="List portfolios",
    description="Lists all portfolios for the current user.",
)
def list_portfolios(
    current: Annotated[User, Depends(get_current_user)],
    service: Annotated[PortfolioService, Depends(_portfolio_service)],
) -> list[PortfolioOut]:
    """List the current user's portfolios."""
    return [PortfolioOut.model_validate(p) for p in service.list_portfolios(current.id)]


@router.get(
    "/{portfolio_id}",
    response_model=PortfolioOut,
    summary="Get a portfolio",
    description="Returns a single portfolio owned by the current user.",
)
def get_portfolio(
    portfolio_id: uuid.UUID,
    current: Annotated[User, Depends(get_current_user)],
    service: Annotated[PortfolioService, Depends(_portfolio_service)],
) -> PortfolioOut:
    """Fetch one portfolio."""
    return PortfolioOut.model_validate(service.get_portfolio(current.id, portfolio_id))


@router.post(
    "/{portfolio_id}/holdings",
    response_model=HoldingOut,
    status_code=201,
    summary="Add a holding",
    description="Adds a position (asset class, market value, cost basis) to a portfolio.",
)
def add_holding(
    portfolio_id: uuid.UUID,
    payload: HoldingCreate,
    current: Annotated[User, Depends(get_current_user)],
    service: Annotated[PortfolioService, Depends(_portfolio_service)],
) -> HoldingOut:
    """Add a holding to a portfolio."""
    holding = service.add_holding(current.id, portfolio_id, **payload.model_dump())
    service.session.commit()
    return HoldingOut.model_validate(holding)


@router.get(
    "/{portfolio_id}/holdings",
    response_model=list[HoldingOut],
    summary="List holdings",
    description="Lists the positions inside a portfolio.",
)
def list_holdings(
    portfolio_id: uuid.UUID,
    current: Annotated[User, Depends(get_current_user)],
    service: Annotated[PortfolioService, Depends(_portfolio_service)],
) -> list[HoldingOut]:
    """List the holdings in a portfolio."""
    holdings = service.list_holdings(current.id, portfolio_id)
    return [HoldingOut.model_validate(h) for h in holdings]


@router.delete(
    "/{portfolio_id}/holdings/{holding_id}",
    response_model=MessageResponse,
    summary="Delete a holding",
    description="Soft-deletes a holding from a portfolio.",
)
def delete_holding(
    portfolio_id: uuid.UUID,
    holding_id: uuid.UUID,
    current: Annotated[User, Depends(get_current_user)],
    service: Annotated[PortfolioService, Depends(_portfolio_service)],
) -> MessageResponse:
    """Delete a holding."""
    service.delete_holding(current.id, portfolio_id, holding_id)
    service.session.commit()
    return MessageResponse(message="Holding deleted")


@router.post(
    "/{portfolio_id}/snapshot",
    response_model=PortfolioSnapshotOut,
    summary="Capture a portfolio snapshot",
    description="Computes and stores a value/weights snapshot for a portfolio.",
)
def capture_snapshot(
    portfolio_id: uuid.UUID,
    current: Annotated[User, Depends(get_current_user)],
    service: Annotated[PortfolioService, Depends(_portfolio_service)],
) -> PortfolioSnapshotOut:
    """Capture a portfolio snapshot."""
    snapshot = service.snapshot(current, portfolio_id)
    service.session.commit()
    return PortfolioSnapshotOut(**snapshot)

