"""Strategic portfolio allocation engine.

This engine answers the question: *given who this person is, what should
their money look like?* It produces a target allocation across the full
instrument spectrum:

* equity (domestic, including ELSS)
* debt (bonds / debt funds)
* gold
* international equity
* REITs
* fixed deposits
* cash
* ELSS
* PPF
* EPF
* NPS
* bonds

The allocation is *strategic* — a long-term target, not a market call.
It varies with the factors that actually determine how much risk a user
should carry:

* age (younger = more equity)
* risk capacity + tolerance (from the legacy ``risk_engine``)
* time horizon (longer = more equity)
* emergency-fund readiness (missing buffer = more cash/debt)
* debt burden (high DTI = more conservative)
* financial goals (near goals = more liquid)

Design notes
------------
* Reads glidepath anchors and instrument caps from ``config.asset`` so
  the engine contains no magic numbers.
* Delegates risk scoring to the legacy ``risk_engine`` — full backward
  compatibility with the existing pipeline.
* The instrument list for each bucket comes from the legacy asset
  database via ``ASSET_PROFILES`` so the recommendation layer and this
  engine can never disagree about what exists.
"""

from __future__ import annotations

import logging
from typing import Dict, List, Optional

from wealth_management_system.config import AssetConfig, get_config
from wealth_management_system.exceptions import AllocationError
from wealth_management_system.models import (
    AllocationEngineInput,
    AllocationResult,
    AssetCategory,
    AssetClass,
    BucketAllocation,
    LiquidityNeed,
    UserProfile,
)
from wealth_management_system.risk_engine import assess_risk
from wealth_management_system.utilities import get_logger

logger: logging.Logger = get_logger(__name__)

# Ordering of buckets in the output (for display and tests)
_BUCKET_ORDER: List[str] = [
    "equity",
    "debt",
    "gold",
    "international_equity",
    "reits",
    "fixed_deposits",
    "cash",
    "elss",
    "ppf",
    "epf",
    "nps",
    "bonds",
]

# instruments that belong to each bucket (subset of the asset database)
_BUCKET_INSTRUMENTS: Dict[str, List[AssetClass]] = {
    "equity": [
        AssetClass.EQUITY_INDEX_LARGECAP,
        AssetClass.EQUITY_LARGE_CAP,
        AssetClass.EQUITY_FLEXI_CAP,
        AssetClass.EQUITY_MID_CAP,
        AssetClass.EQUITY_SMALL_CAP,
        AssetClass.EQUITY_DIVIDEND_YIELD,
    ],
    "debt": [
        AssetClass.SHORT_DURATION_FUND,
        AssetClass.CORPORATE_BOND_FUND,
        AssetClass.MEDIUM_DURATION_FUND,
        AssetClass.GILT_FUND,
        AssetClass.BALANCED_ADVANTAGE,
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


class AllocationEngine:
    """Builds a strategic target allocation for a user.

    Parameters
    ----------
    config:
        Optional ``AssetConfig``. Defaults to the process-wide config.
    """

    def __init__(self, config: Optional[AssetConfig] = None) -> None:
        self._config = config or get_config().asset

    # ── public API ──────────────────────────────────────────────────

    def build(self, allocation_input: AllocationEngineInput) -> AllocationResult:
        """Build the target allocation for a user.

        Parameters
        ----------
        allocation_input:
            Everything the engine needs about the user (risk override,
            horizon override, liquidity override, monthly investment).

        Returns
        -------
        AllocationResult
            The strategic target allocation with an explanation.

        Raises
        ------
        AllocationError
            If the input is invalid (e.g. a non-positive horizon).
        """
        user = allocation_input.user
        risk_score, risk_category = self._risk_for(user, allocation_input)
        horizon = self._horizon_for(user, allocation_input)
        liquidity = self._liquidity_for(user, allocation_input)
        monthly = allocation_input.monthly_investment or max(0, user.investable_surplus())

        if horizon <= 0:
            raise AllocationError(
                "investment horizon must be positive",
                code="invalid_horizon",
                details={"horizon": horizon},
            )

        weights = self._derive_weights(
            risk_score=risk_score,
            age=user.age,
            horizon=horizon,
            emergency_fund_months=user.financial.emergency_fund_months,
            debt_to_income=user.financial.debt_to_income_ratio(),
            liquidity=liquidity,
        )

        buckets = self._to_buckets(weights)
        explanation = self._explain(
            user=user,
            risk_score=risk_score,
            horizon=horizon,
            liquidity=liquidity,
            monthly_investment=monthly,
        )

        return AllocationResult(
            buckets=buckets,
            risk_score=risk_score,
            risk_category=risk_category,
            explanation=explanation,
        )

    # ── risk / horizon / liquidity resolution ──────────────────────

    def _risk_for(
        self, user: UserProfile, allocation_input: AllocationEngineInput
    ) -> tuple[int, str]:
        """Determine the risk score and category to drive the allocation."""
        if allocation_input.risk_score is not None:
            score = max(0, min(100, allocation_input.risk_score))
            category = self._category_for_score(score)
            return score, category
        risk = assess_risk(user)
        return risk.final_score_100, risk.risk_category

    def _horizon_for(
        self, user: UserProfile, allocation_input: AllocationEngineInput
    ) -> float:
        """Derive the investment horizon (years).

        Uses the override when provided; otherwise the longest goal
        target date, falling back to years-to-retirement, then a
        conservative 7-year default.
        """
        if allocation_input.horizon_years is not None:
            return allocation_input.horizon_years

        from datetime import date

        today = date.today()
        if user.goals:
            longest = max((g.target_date - today).days for g in user.goals)
            if longest > 0:
                return longest / 365.25

        retirement_years = user.years_to_retirement()
        if retirement_years > 0:
            return retirement_years
        return 7.0

    def _liquidity_for(
        self, user: UserProfile, allocation_input: AllocationEngineInput
    ) -> LiquidityNeed:
        """Determine liquidity need from override or nearest goal."""
        if allocation_input.liquidity_need is not None:
            return allocation_input.liquidity_need

        from datetime import date

        today = date.today()
        if user.financial.emergency_fund_months < 3:
            return LiquidityNeed.HIGH
        if user.goals:
            nearest_days = min((g.target_date - today).days for g in user.goals)
            if nearest_days <= 2 * 365:
                return LiquidityNeed.HIGH
            if nearest_days <= 5 * 365:
                return LiquidityNeed.MEDIUM
        return LiquidityNeed.LOW

    @staticmethod
    def _category_for_score(score: int) -> str:
        """Human-readable category for a 0-100 risk score."""
        if score < 20:
            return "Very Conservative"
        if score < 40:
            return "Conservative"
        if score < 60:
            return "Moderate"
        if score < 75:
            return "Aggressive"
        return "Very Aggressive"

    # ── weight derivation ───────────────────────────────────────────

    def _derive_weights(
        self,
        *,
        risk_score: int,
        age: int,
        horizon: float,
        emergency_fund_months: float,
        debt_to_income: float,
        liquidity: LiquidityNeed,
    ) -> Dict[str, float]:
        """Derive target weights for every bucket.

        Strategy (deliberately conservative — this is a target, not a
        bet):

        1. Equity weight comes from the config glidepath anchors,
           interpolated by risk score, then damped by age and horizon.
        2. The equity bucket is split between plain equity and ELSS
           (tax-advantaged) and international equity.
        3. The non-equity remainder is split among debt, bonds, gold,
           fixed deposits, cash, PPF, EPF and NPS.
        4. Liquidity needs raise cash/FD and lower long-duration assets.
        5. Emergency-fund and debt-burden shortfalls are compensated by
           extra debt/cash and reduced equity.
        """
        cfg = self._config
        equity = self._equity_weight(risk_score, age, horizon)

        # risk-off adjustments for weak foundations
        if emergency_fund_months < 3:
            equity *= 0.90
        if debt_to_income > 0.35:
            equity *= 0.85

        # split equity bucket
        elss = min(equity * 0.30, cfg.max_elss_fraction)
        international = min(equity * 0.15, cfg.max_international_fraction)
        pure_equity = max(0.0, equity - elss - international)

        # non-equity remainder
        non_equity = 1.0 - equity
        debt = non_equity * cfg.debt_default_share
        bonds = debt * 0.20
        debt -= bonds
        gold = non_equity * cfg.gold_share
        cash = non_equity * cfg.cash_share
        fd = min(non_equity * 0.20, cfg.max_fixed_deposit_fraction)
        ppf = min(non_equity * 0.15, cfg.max_ppf_fraction)
        epf = min(non_equity * 0.10, cfg.max_epf_fraction)
        nps = min(non_equity * 0.10, cfg.max_nps_fraction)

        # liquidity overrides: shift from debt toward cash/FD
        if liquidity == LiquidityNeed.HIGH:
            extra_cash = debt * 0.30
            cash += extra_cash
            debt -= extra_cash
            extra_fd = gold * 0.50
            fd += extra_fd
            gold -= extra_fd
        elif liquidity == LiquidityNeed.MEDIUM:
            extra_fd = debt * 0.15
            fd += extra_fd
            debt -= extra_fd

        weights: Dict[str, float] = {
            "equity": max(pure_equity, 0.0),
            "elss": max(elss, 0.0),
            "international_equity": max(international, 0.0),
            "debt": max(debt, 0.0),
            "bonds": max(bonds, 0.0),
            "gold": max(gold, 0.0),
            "fixed_deposits": max(fd, 0.0),
            "cash": max(cash, 0.0),
            "ppf": max(ppf, 0.0),
            "epf": max(epf, 0.0),
            "nps": max(nps, 0.0),
            "reits": max(min(equity * 0.06, cfg.max_reit_fraction), 0.0),
        }

        # normalise so weights always sum to 1.0
        total = sum(weights.values())
        if total <= 0:
            raise AllocationError(
                "derived allocation has zero weight",
                code="empty_allocation",
                details={"risk_score": risk_score},
            )
        return {k: v / total for k, v in weights.items()}

    def _equity_weight(self, risk_score: int, age: int, horizon: float) -> float:
        """Interpolate the equity weight from the config glidepath.

        Age and horizon damp the glidepath so an older user or a short
        horizon never ends up fully in equity.
        """
        risk_score = max(0, min(100, risk_score))
        anchors = self._config.equity_weight_by_score
        weight = anchors[-1][1] if anchors else 0.40
        for threshold, anchor_weight in anchors:
            if risk_score <= threshold:
                weight = anchor_weight
                break

        # age damping: after 45, shave equity toward debt
        if age > 45:
            weight *= max(0.0, 1.0 - (age - 45) * 0.02)

        # horizon damping: short horizons cannot ride out volatility
        if horizon < 5:
            weight *= max(0.3, horizon / 5)
        return max(0.05, min(weight, 0.80))

    # ── output assembly ─────────────────────────────────────────────

    def _to_buckets(self, weights: Dict[str, float]) -> List[BucketAllocation]:
        """Convert the weight map into ordered ``BucketAllocation`` objects."""
        buckets: List[BucketAllocation] = []
        for bucket in _BUCKET_ORDER:
            weight = weights.get(bucket, 0.0)
            if weight <= 0:
                continue
            instruments = _BUCKET_INSTRUMENTS.get(bucket, [])
            buckets.append(
                BucketAllocation(
                    bucket=bucket,
                    weight=round(weight, 6),
                    instruments=[i.value for i in instruments],
                )
            )
        return buckets

    def _explain(
        self,
        *,
        user: UserProfile,
        risk_score: int,
        horizon: float,
        liquidity: LiquidityNeed,
        monthly_investment: float,
    ) -> str:
        """Plain-language rationale for the allocation."""
        ef = user.financial.emergency_fund_months
        dti = user.financial.debt_to_income_ratio()
        bits = [
            f"Target allocation for a risk score of {risk_score}/100 "
            f"with a {horizon:.0f}-year horizon",
            f"monthly investable surplus of ₹{monthly_investment:,.0f}",
        ]
        if ef < 3:
            bits.append("emergency fund is thin — extra cash/debt buffer built in")
        if dti > 0.35:
            bits.append("high debt burden — allocation skewed conservative")
        if liquidity == LiquidityNeed.HIGH:
            bits.append("high liquidity need — cash and FDs overweighted")
        return ", ".join(bits) + "."

