"""ETF evaluator — discovers, fetches and evaluates equity ETFs.

Serves multiple :class:`TargetAssetClass` values (large_cap, mid_cap,
small_cap, flexi_cap) via the ``target`` constructor parameter.
Each target maps to a curated universe of ETF symbols in the config.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from security_selection.base.evaluator import BaseEvaluator
from security_selection.base.provider import BaseProviderSet
from security_selection.evaluators._common import (
    build_candidates_from_payloads,
    default_benchmark_symbol,
    default_currency,
    enrich_candidate_from_metrics,
)
from security_selection.models.data import ProviderPayload, SecurityIdentity
from security_selection.models.enums import (
    AssetClassBucket,
    Confidence,
    NormalizationAxis,
    SecurityKind,
    TargetAssetClass,
)
from security_selection.models.pipeline import (
    CandidateSecurity,
    NormalizedProfile,
    SelectionInput,
)

logger = logging.getLogger(__name__)


class ETFEvaluator(BaseEvaluator):
    """Evaluator for equity ETFs (large, mid, small, flexi cap).

    Class attributes
    ----------------
    kind:
        :attr:`SecurityKind.ETF`
    target:
        Defaults to :attr:`TargetAssetClass.LARGE_CAP_EQUITY`; override
        via constructor to serve mid/small/flexi.
    bucket:
        :attr:`AssetClassBucket.EQUITY`
    """

    kind: SecurityKind = SecurityKind.ETF
    target: TargetAssetClass = TargetAssetClass.LARGE_CAP_EQUITY
    bucket: AssetClassBucket = AssetClassBucket.EQUITY

    def __init__(
        self,
        providers: BaseProviderSet,
        *,
        target: TargetAssetClass | None = None,
    ) -> None:
        super().__init__(providers, target=target)
        # Resolve the evaluator config for this target
        self._eval_config = self._config.evaluator_config(self.target)

    # ── Pipeline stages ─────────────────────────────────────────────

    def discover(self, selection_input: SelectionInput) -> List[SecurityIdentity]:
        """Discover ETFs from the config universe for this target."""
        universe = self._eval_config.universe if self._eval_config else []
        if not universe:
            logger.warning("No ETF universe configured for %s", self.target.value)
            return []
        identities: List[SecurityIdentity] = []
        for symbol in universe:
            identities.append(
                SecurityIdentity(
                    symbol=symbol,
                    name=symbol,
                    currency=default_currency(self.target),
                    kind=SecurityKind.ETF,
                )
            )
        limit = self._eval_config.max_candidates if self._eval_config else 30
        if selection_input.candidate_limit:
            limit = min(limit, selection_input.candidate_limit)
        return identities[:limit]

    def fetch_data(
        self,
        identities: List[SecurityIdentity],
        selection_input: SelectionInput,
    ) -> List[ProviderPayload]:
        """Fetch ETF data from the provider chain."""
        return self._data.fetch_multi(
            identities=identities,
            history_years=5,
            use_cache=selection_input.use_cache,
        )

    def validate(
        self,
        payloads: List[ProviderPayload],
        selection_input: SelectionInput,
    ) -> List[ProviderPayload]:
        """Run quality checks; drop failed payloads."""
        valid: List[ProviderPayload] = []
        for payload in payloads:
            report = self._quality.validate_payload(payload)
            if report.is_usable:
                valid.append(payload)
            else:
                logger.warning(
                    "ETF %s failed quality: %s",
                    payload.identity.symbol,
                    report.summary(),
                )
        return valid

    def calculate_metrics(
        self,
        payloads: List[ProviderPayload],
        selection_input: SelectionInput,
    ) -> List[CandidateSecurity]:
        """Compute metrics and build candidates."""
        candidates = build_candidates_from_payloads(
            payloads, self.target, kind=SecurityKind.ETF
        )
        for candidate in candidates:
            enrich_candidate_from_metrics(candidate, self._metrics, self._config)
        return candidates

    def normalize(
        self,
        candidates: List[CandidateSecurity],
        selection_input: SelectionInput,
    ) -> List[CandidateSecurity]:
        """Normalize each ETF candidate to the common profile."""
        for candidate in candidates:
            profile = self._normalize_etf(candidate)
            candidate.profile = profile
        return candidates

    # ── Normalization logic ─────────────────────────────────────────

    def _normalize_etf(self, candidate: CandidateSecurity) -> NormalizedProfile:
        """Build a normalized 0..1 profile for an ETF."""
        m = candidate.metrics
        avail: Dict[NormalizationAxis, bool] = {}

        # Expected return (1y, 3y, 5y CAGR weighted)
        returns = [
            m.get("cagr_1y"),
            m.get("cagr_3y"),
            m.get("cagr_5y"),
        ]
        valid_returns = [r for r in returns if r is not None and isinstance(r, (int, float))]
        if valid_returns:
            expected_return = _minmax_scale(
                sum(valid_returns) / len(valid_returns),
                -0.15, 0.30,
            )
            avail[NormalizationAxis.EXPECTED_RETURN] = True
        else:
            expected_return = 0.5
            avail[NormalizationAxis.EXPECTED_RETURN] = False

        # Risk (inverse volatility: lower vol = higher score)
        vol = m.get("annual_volatility")
        if vol is not None and isinstance(vol, (int, float)) and vol > 0:
            risk = _minmax_scale(1.0 / (1.0 + vol), 0.0, 1.0)
            avail[NormalizationAxis.RISK] = True
        else:
            risk = 0.5
            avail[NormalizationAxis.RISK] = False

        # Liquidity (average volume / AUM)
        avg_vol = m.get("average_volume_30d")
        aum = m.get("aum_crore")
        if avg_vol is not None and aum is not None and aum > 0:
            turnover_ratio = float(avg_vol) / float(aum)
            liquidity = _minmax_scale(turnover_ratio, 0.0, 0.5)
            avail[NormalizationAxis.LIQUIDITY] = True
        else:
            liquidity = 0.5
            avail[NormalizationAxis.LIQUIDITY] = False

        # Diversification (holdings count)
        holdings_count = m.get("holdings_count")
        if holdings_count is not None and isinstance(holdings_count, (int, float)):
            diversification = _minmax_scale(float(holdings_count), 10, 200)
            avail[NormalizationAxis.DIVERSIFICATION] = True
        else:
            diversification = 0.5
            avail[NormalizationAxis.DIVERSIFICATION] = False

        # Tax efficiency (equity LTCG = good)
        tax_efficiency = 0.7
        avail[NormalizationAxis.TAX_EFFICIENCY] = True

        # Cost (inverse expense ratio)
        er = m.get("expense_ratio")
        if er is not None and isinstance(er, (int, float)):
            cost = _minmax_scale(1.0 - float(er) * 100, 0.0, 1.0)
            avail[NormalizationAxis.COST] = True
        else:
            cost = 0.5
            avail[NormalizationAxis.COST] = False

        # Tracking quality (inverse tracking error)
        te = m.get("tracking_error")
        if te is not None and isinstance(te, (int, float)):
            tracking_quality = _minmax_scale(1.0 / (1.0 + float(te) * 100), 0.0, 1.0)
            avail[NormalizationAxis.TRACKING_QUALITY] = True
        else:
            tracking_quality = 0.5
            avail[NormalizationAxis.TRACKING_QUALITY] = False

        # Quality (Sharpe ratio + data quality)
        sharpe = m.get("sharpe_ratio")
        if sharpe is not None and isinstance(sharpe, (int, float)):
            quality = _minmax_scale(float(sharpe), -1.0, 3.0)
            avail[NormalizationAxis.QUALITY] = True
        else:
            quality = 0.5
            avail[NormalizationAxis.QUALITY] = False

        # Market exposure (AUM as proxy for market cap exposure)
        if aum is not None and isinstance(aum, (int, float)):
            market_exposure = _minmax_scale(float(aum), 0, 50000)
            avail[NormalizationAxis.MARKET_EXPOSURE] = True
        else:
            market_exposure = 0.5
            avail[NormalizationAxis.MARKET_EXPOSURE] = False

        # Overall confidence
        available_count = sum(1 for v in avail.values() if v)
        total_axes = len(NormalizationAxis)
        confidence = available_count / total_axes

        return NormalizedProfile(
            security_key=candidate.key,
            expected_return=expected_return,
            risk=risk,
            liquidity=liquidity,
            diversification=diversification,
            tax_efficiency=tax_efficiency,
            cost=cost,
            tracking_quality=tracking_quality,
            quality=quality,
            market_exposure=market_exposure,
            confidence=confidence,
            available=avail,
        )


def _minmax_scale(value: float, min_val: float, max_val: float) -> float:
    """Scale a value to 0..1 using min-max normalisation, clamped."""
    if max_val <= min_val:
        return 0.5
    scaled = (value - min_val) / (max_val - min_val)
    return max(0.0, min(1.0, scaled))
