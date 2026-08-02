"""Portfolio repository."""

from __future__ import annotations

import uuid

from sqlalchemy import select

from app.models.portfolio import Portfolio, PortfolioHolding, PortfolioSnapshot
from app.repositories.base import BaseRepository


class PortfolioRepository(BaseRepository[Portfolio]):
    """Persistence for portfolios, holdings and snapshots."""

    model = Portfolio

    def list_for_user(self, user_id: uuid.UUID) -> list[Portfolio]:
        stmt = select(Portfolio).where(Portfolio.user_id == user_id).order_by(Portfolio.created_at)
        return list(self.session.execute(stmt).scalars().all())

    def get_for_user(self, portfolio_id: uuid.UUID, user_id: uuid.UUID) -> Portfolio | None:
        stmt = select(Portfolio).where(Portfolio.id == portfolio_id, Portfolio.user_id == user_id)
        return self.session.execute(stmt).scalars().first()

    def get_primary_for_user(self, user_id: uuid.UUID) -> Portfolio | None:
        stmt = (
            select(Portfolio)
            .where(Portfolio.user_id == user_id, Portfolio.is_primary == True)  # noqa: E712
            .order_by(Portfolio.created_at)
            .limit(1)
        )
        return self.session.execute(stmt).scalars().first()

    # ── holdings ────────────────────────────────────────────────────

    def add_holding(self, *, portfolio_id: uuid.UUID, user_id: uuid.UUID, **values) -> PortfolioHolding:
        holding = PortfolioHolding(
            portfolio_id=portfolio_id, user_id=user_id, **values
        )
        self.session.add(holding)
        self.session.flush()
        return holding

    def list_holdings(self, portfolio_id: uuid.UUID) -> list[PortfolioHolding]:
        stmt = select(PortfolioHolding).where(PortfolioHolding.portfolio_id == portfolio_id)
        return list(self.session.execute(stmt).scalars().all())

    def get_holding(self, holding_id: uuid.UUID, portfolio_id: uuid.UUID) -> PortfolioHolding | None:
        stmt = select(PortfolioHolding).where(
            PortfolioHolding.id == holding_id,
            PortfolioHolding.portfolio_id == portfolio_id,
        )
        return self.session.execute(stmt).scalars().first()

    def delete_holding(self, holding: PortfolioHolding) -> None:
        self.session.delete(holding)
        self.session.flush()

    # ── snapshots ───────────────────────────────────────────────────

    def add_snapshot(self, *, portfolio_id: uuid.UUID, user_id: uuid.UUID, **values) -> PortfolioSnapshot:
        snap = PortfolioSnapshot(portfolio_id=portfolio_id, user_id=user_id, **values)
        self.session.add(snap)
        self.session.flush()
        return snap

    def list_snapshots(self, portfolio_id: uuid.UUID, limit: int = 30) -> list[PortfolioSnapshot]:
        stmt = (
            select(PortfolioSnapshot)
            .where(PortfolioSnapshot.portfolio_id == portfolio_id)
            .order_by(PortfolioSnapshot.captured_at.desc())
            .limit(limit)
        )
        return list(self.session.execute(stmt).scalars().all())

