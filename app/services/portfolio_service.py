"""Portfolio service — portfolio, holdings, snapshots, allocation and
rebalancing via the engine.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError, ValidationError
from app.models import Portfolio, PortfolioHolding, User
from app.repositories.portfolio_repository import PortfolioRepository
from app.schemas.allocation import AllocationOut, AllocationRequest
from app.schemas.portfolio import PortfolioCreate, PortfolioOut
from app.schemas.rebalance import RebalanceOut
from app.services.engine_adapter import EngineAdapter

from engine import AllocationEngine, AllocationEngineInput, Holding, PortfolioHoldings, RebalancingEngine  # noqa: E402


class PortfolioService:
    """Business workflows around portfolios + engine integration."""

    def __init__(self, session: Session) -> None:
        self.session = session
        self.portfolios = PortfolioRepository(session)

    # ── portfolio CRUD ──────────────────────────────────────────────

    def create_portfolio(self, user: User, data: PortfolioCreate) -> Portfolio:
        if data.target_allocation:
            total = sum(data.target_allocation.values())
            if abs(total - 1.0) > 1e-6:
                raise ValidationError("target_allocation weights must sum to 1.0", code="bad_weights")
        return self.portfolios.create(
            user_id=user.id,
            name=data.name,
            description=data.description,
            target_allocation=data.target_allocation,
        )

    def get_portfolio(self, user_id: uuid.UUID, portfolio_id: uuid.UUID) -> Portfolio:
        portfolio = self.portfolios.get_for_user(portfolio_id, user_id)
        if portfolio is None:
            raise NotFoundError("Portfolio not found", code="portfolio_not_found")
        return portfolio

    def list_portfolios(self, user_id: uuid.UUID) -> list[Portfolio]:
        return self.portfolios.list_for_user(user_id)

    # ── holdings ────────────────────────────────────────────────────

    def add_holding(self, user_id: uuid.UUID, portfolio_id: uuid.UUID, **values) -> PortfolioHolding:
        portfolio = self.get_portfolio(user_id, portfolio_id)
        return self.portfolios.add_holding(
            portfolio_id=portfolio.id, user_id=user_id, **values
        )

    def list_holdings(self, user_id: uuid.UUID, portfolio_id: uuid.UUID) -> list[PortfolioHolding]:
        self.get_portfolio(user_id, portfolio_id)
        return self.portfolios.list_holdings(portfolio_id)

    def delete_holding(self, user_id: uuid.UUID, portfolio_id: uuid.UUID, holding_id: uuid.UUID) -> None:
        self.get_portfolio(user_id, portfolio_id)
        holding = self.portfolios.get_holding(holding_id, portfolio_id)
        if holding is None:
            raise NotFoundError("Holding not found", code="holding_not_found")
        self.portfolios.delete_holding(holding)

    # ── allocation (engine) ─────────────────────────────────────────

    def get_allocation(self, user: User, req: AllocationRequest) -> dict:
        """Build the engine user aggregate and compute the strategic
        allocation."""
        engine_user = self._engine_user(user)
        from engine import LiquidityNeed

        liquidity = None
        if req.liquidity_need:
            try:
                liquidity = LiquidityNeed(req.liquidity_need)
            except ValueError:
                liquidity = None

        result = AllocationEngine().build(
            AllocationEngineInput(
                user=engine_user,
                risk_score=req.risk_score,
                horizon_years=req.horizon_years,
                liquidity_need=liquidity,
                monthly_investment=req.monthly_investment,
            )
        )
        return EngineAdapter.allocation_to_dict(result)

    # ── rebalancing (engine) ────────────────────────────────────────

    def rebalance(self, user: User, portfolio_id: uuid.UUID, target: dict | None = None) -> dict:
        """Run the rebalancing engine against current holdings and the
        portfolio target allocation."""
        portfolio = self.get_portfolio(user.id, portfolio_id)
        holdings = self.portfolios.list_holdings(portfolio_id)
        if not holdings:
            raise ValidationError("Portfolio has no holdings to rebalance", code="no_holdings")

        engine_holdings = PortfolioHoldings(
            holdings=[
                Holding(
                    asset_class=h.asset_class,
                    market_value=h.market_value,
                    cost_basis=h.cost_basis,
                    quantity=h.quantity,
                )
                for h in holdings
            ]
        )
        target_allocation = target or portfolio.target_allocation
        if not target_allocation:
            raise ValidationError(
                "No target allocation configured — run /allocation first or pass a target",
                code="missing_target",
            )
        result = RebalancingEngine().analyse(
            holdings=engine_holdings, target_allocation=target_allocation
        )
        return EngineAdapter.rebalance_to_dict(result)

    # ── snapshots ───────────────────────────────────────────────────

    def snapshot(self, user: User, portfolio_id: uuid.UUID) -> dict:
        portfolio = self.get_portfolio(user.id, portfolio_id)
        holdings = self.portfolios.list_holdings(portfolio_id)
        total_value = sum(h.market_value for h in holdings)
        snapshot = self.portfolios.add_snapshot(
            portfolio_id=portfolio_id,
            user_id=user.id,
            captured_at=datetime.now(timezone.utc),
            total_value=total_value,
            weights={h.asset_class: h.market_value / total_value if total_value else 0 for h in holdings},
            cash_flow=None,
            notes="manual snapshot",
        )
        return {
            "id": str(snapshot.id),
            "portfolio_id": str(snapshot.portfolio_id),
            "captured_at": snapshot.captured_at.isoformat(),
            "total_value": snapshot.total_value,
            "weights": snapshot.weights,
        }

    # ── helpers ─────────────────────────────────────────────────────

    def _engine_user(self, user: User):
        from app.services.engine_adapter import load_engine_parts

        profile, financial, behavioral, goals = load_engine_parts(self.session, user)
        return EngineAdapter.to_engine_user(user, profile, financial, behavioral, goals)

