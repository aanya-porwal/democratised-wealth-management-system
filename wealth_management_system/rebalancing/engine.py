"""Portfolio rebalancing engine.

Monitors a portfolio against a target allocation and, when drift exceeds
configurable thresholds, produces concrete buy/sell instructions that are
aware of:

* taxes (capital-gains tax on realised gains from sales),
* transaction costs (a rate applied to every trade),
* long-term investing (small drifts are ignored — only meaningful
  deviations trigger action).

The engine operates on strategic buckets (equity, debt, gold, ...) and
decomposes bucket-level trades into instrument-level orders using the
bucket's suggested instrument list from the asset database.
"""

from __future__ import annotations

import logging
from typing import Dict, List, Optional

from wealth_management_system.config import RebalancingConfig, get_config
from wealth_management_system.exceptions import RebalancingError
from wealth_management_system.models import (
    AssetClass,
    Holding,
    PortfolioHoldings,
    RebalanceAction,
    RebalanceDirection,
    RebalanceResult,
    Trade,
)
from wealth_management_system.utilities import get_logger

logger: logging.Logger = get_logger(__name__)


class RebalancingEngine:
    """Detects drift and computes tax/cost-aware rebalancing trades.

    Parameters
    ----------
    config:
        Optional ``RebalancingConfig``. Defaults to the process config.
    bucket_map:
        Optional mapping of bucket name to the asset classes that belong
        to it. Defaults to a reasonable strategic mapping.
    """

    def __init__(
        self,
        config: Optional[RebalancingConfig] = None,
        bucket_map: Optional[Dict[str, List[AssetClass]]] = None,
    ) -> None:
        self._config = config or get_config().rebalancing
        self._bucket_map = bucket_map or _DEFAULT_BUCKET_MAP

    # ── public API ──────────────────────────────────────────────────

    def analyse(
        self,
        holdings: PortfolioHoldings,
        target_allocation: Dict[str, float],
        portfolio_value: Optional[float] = None,
    ) -> RebalanceResult:
        """Compare current holdings to the target and produce trades.

        Parameters
        ----------
        holdings:
            The user's current positions.
        target_allocation:
            Mapping of bucket name -> target weight (0..1). Must sum to
            ~1.0.
        portfolio_value:
            Optional total portfolio value override. Defaults to the sum
            of the holdings' market values.

        Returns
        -------
        RebalanceResult
            Whether a rebalance is required, the per-bucket actions and
            the instrument-level trades (with tax/cost estimates).

        Raises
        ------
        RebalancingError
            If the target allocation is empty, sums to ~0, or contains
            weights outside [0, 1].
        """
        self._validate_target(target_allocation)

        total_value = portfolio_value if portfolio_value is not None else holdings.total_value()
        if total_value <= 0:
            return RebalanceResult(
                rebalance_required=False,
                notes=["portfolio value is zero — nothing to rebalance"],
            )

        if total_value < self._config.min_portfolio_value:
            return RebalanceResult(
                rebalance_required=False,
                portfolio_value=total_value,
                notes=[
                    "portfolio value below the rebalancing minimum — "
                    "trades would cost more than they are worth"
                ],
            )

        # current bucket values from holdings
        current_values = holdings.bucket_values(self._bucket_map)
        target_values: Dict[str, float] = {}
        for bucket, weight in target_allocation.items():
            if weight > 0:
                target_values[bucket] = total_value * weight

        actions = self._bucket_actions(current_values, target_values, total_value)
        required = any(a.direction != RebalanceDirection.HOLD for a in actions)
        trades = self._trades_from_actions(actions, holdings)
        total_cost = round(sum(t.estimated_transaction_cost for t in trades), 2)
        total_tax = round(sum(t.estimated_tax_impact for t in trades), 2)

        notes: List[str] = []
        if not required:
            notes.append("no bucket drifted beyond the rebalancing threshold")

        return RebalanceResult(
            rebalance_required=required,
            actions=actions,
            trades=trades,
            total_transaction_cost=total_cost,
            total_tax_impact=total_tax,
            portfolio_value=round(total_value, 2),
            notes=notes,
        )

    # ── internals ───────────────────────────────────────────────────

    def _validate_target(self, target_allocation: Dict[str, float]) -> None:
        """Sanity-check the target allocation."""
        if not target_allocation:
            raise RebalancingError(
                "target allocation is empty",
                code="empty_target",
            )
        total = sum(target_allocation.values())
        if total <= 0:
            raise RebalancingError(
                "target allocation must sum to a positive value",
                code="invalid_target_total",
                details={"total": total},
            )
        for bucket, weight in target_allocation.items():
            if not (0.0 <= weight <= 1.0):
                raise RebalancingError(
                    f"target weight for '{bucket}' out of range",
                    code="invalid_weight",
                    details={"bucket": bucket, "weight": weight},
                )

    def _bucket_actions(
        self,
        current_values: Dict[str, float],
        target_values: Dict[str, float],
        total_value: float,
    ) -> List[RebalanceAction]:
        """Compute per-bucket drift and the action needed.

        A bucket needs action only when the *absolute* drift (current -
        target weight) exceeds the absolute threshold AND the *relative*
        drift exceeds the relative threshold — this keeps small, noisy
        movements from triggering trades.
        """
        cfg = self._config
        actions: List[RebalanceAction] = []
        all_buckets = set(current_values) | set(target_values)

        for bucket in sorted(all_buckets):
            current = current_values.get(bucket, 0.0) / total_value
            target = target_values.get(bucket, 0.0) / total_value
            drift = current - target
            abs_drift = abs(drift)

            # both absolute and relative thresholds must be exceeded
            relative = abs_drift / target if target > 0 else abs_drift
            if abs_drift < cfg.absolute_drift_threshold or relative < cfg.relative_drift_threshold:
                continue

            trade_amount = abs_drift * total_value
            if trade_amount / total_value < cfg.min_trade_fraction:
                continue

            if drift > 0:
                direction = RebalanceDirection.SELL
                reason = (
                    f"{bucket} is overweight (current {current:.1%} vs "
                    f"target {target:.1%})"
                )
            else:
                direction = RebalanceDirection.BUY
                reason = (
                    f"{bucket} is underweight (current {current:.1%} vs "
                    f"target {target:.1%})"
                )

            actions.append(
                RebalanceAction(
                    bucket=bucket,
                    direction=direction,
                    current_weight=round(current, 6),
                    target_weight=round(target, 6),
                    drift=round(drift, 6),
                    trade_amount=round(trade_amount, 2),
                    reason=reason,
                )
            )
        return actions

    def _trades_from_actions(
        self,
        actions: List[RebalanceAction],
        holdings: PortfolioHoldings,
    ) -> List[Trade]:
        """Convert bucket actions into instrument-level trades.

        Buys are allocated across the bucket's suggested instruments
        (pro-rata by liquidity, skipping locked instruments). Sells are
        allocated across the user's actual holdings in that bucket,
        which lets us estimate the capital-gains tax per sale.
        """
        cfg = self._config
        trades: List[Trade] = []

        for action in actions:
            bucket = action.bucket
            instruments = self._bucket_map.get(bucket, [])
            if not instruments:
                continue

            if action.direction == RebalanceDirection.SELL:
                # distribute the sell across the actual holdings in bucket
                sells = self._sell_trades(action, holdings, instruments, cfg)
                trades.extend(sells)
            elif action.direction == RebalanceDirection.BUY:
                buys = self._buy_trades(action, instruments, cfg)
                trades.extend(buys)

        return trades

    def _sell_trades(
        self,
        action: RebalanceAction,
        holdings: PortfolioHoldings,
        instruments: List[AssetClass],
        cfg: RebalancingConfig,
    ) -> List[Trade]:
        """Build sell trades from the user's actual holdings."""
        trades: List[Trade] = []
        # holdings in this bucket
        bucket_holdings = [
            h for h in holdings.holdings if h.asset_class in instruments
        ]
        if not bucket_holdings:
            return trades

        total_bucket_value = sum(h.market_value for h in bucket_holdings)
        if total_bucket_value <= 0:
            return trades

        # sell pro-rata by holding value
        remaining = action.trade_amount
        for h in sorted(bucket_holdings, key=lambda x: -x.market_value):
            if remaining <= 0:
                break
            share = min(h.market_value, remaining)
            gain = share / h.market_value * h.unrealised_gain() if h.market_value > 0 else 0.0
            tax = max(0.0, gain) * cfg.capital_gains_tax_rate
            cost = share * cfg.transaction_cost_rate
            trades.append(
                Trade(
                    asset_class=h.asset_class,
                    amount=-round(share, 2),
                    reason=action.reason,
                    estimated_tax_impact=round(tax, 2),
                    estimated_transaction_cost=round(cost, 2),
                )
            )
            remaining -= share
        return trades

    def _buy_trades(
        self,
        action: RebalanceAction,
        instruments: List[AssetClass],
        cfg: RebalancingConfig,
    ) -> List[Trade]:
        """Build buy trades across the bucket's suggested instruments."""
        from wealth_management_system.assets import ASSET_PROFILES

        trades: List[Trade] = []
        # prefer liquid, non-locked instruments first
        ranked = sorted(
            instruments,
            key=lambda ac: (
                -ASSET_PROFILES[ac].liquidity_score,
                ASSET_PROFILES[ac].lock_in_years,
            ),
        )
        count = max(1, min(2, len(ranked)))
        selected = ranked[:count]
        amount_each = action.trade_amount / count
        for ac in selected:
            cost = amount_each * cfg.transaction_cost_rate
            trades.append(
                Trade(
                    asset_class=ac,
                    amount=round(amount_each, 2),
                    reason=action.reason,
                    estimated_transaction_cost=round(cost, 2),
                )
            )
        return trades


# default strategic mapping of buckets to asset classes
_DEFAULT_BUCKET_MAP: Dict[str, List[AssetClass]] = {
    "equity": [
        AssetClass.EQUITY_INDEX_LARGECAP,
        AssetClass.EQUITY_LARGE_CAP,
        AssetClass.EQUITY_FLEXI_CAP,
        AssetClass.EQUITY_MID_CAP,
        AssetClass.EQUITY_SMALL_CAP,
    ],
    "debt": [
        AssetClass.SHORT_DURATION_FUND,
        AssetClass.CORPORATE_BOND_FUND,
        AssetClass.MEDIUM_DURATION_FUND,
        AssetClass.GILT_FUND,
    ],
    "gold": [AssetClass.GOLD_ETF, AssetClass.SOVEREIGN_GOLD_BOND],
    "international_equity": [AssetClass.INTERNATIONAL_FUND],
    "reits": [AssetClass.REIT, AssetClass.INVIT],
    "fixed_deposits": [AssetClass.FIXED_DEPOSIT, AssetClass.RECURRING_DEPOSIT],
    "cash": [AssetClass.SAVINGS_ACCOUNT, AssetClass.LIQUID_FUND, AssetClass.OVERNIGHT_FUND],
    "elss": [AssetClass.EQUITY_ELSS],
    "ppf": [AssetClass.PPF],
    "epf": [AssetClass.EPF],
    "nps": [AssetClass.NPS_TIER1, AssetClass.NPS_TIER2],
    "bonds": [
        AssetClass.GSEC_RETAIL_DIRECT,
        AssetClass.RBI_FLOATING_BOND,
        AssetClass.POST_OFFICE_NSC,
    ],
}

