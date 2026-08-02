"""Stock evaluator — discovers, fetches and evaluates individual stocks.

Stocks are discovered via the config universe or by ticker symbol search.
Uses yfinance as the primary provider for price data and fundamentals.
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


class StockEvaluator(BaseEvaluator):
    """Evaluator for individual stocks (equity shares).

    Discovers stocks from the config universe, fetches live data via
    yfinance, computes metrics, normalizes, and passes through the
    shared pipeline stages.
    """

    kind: SecurityKind = SecurityKind.STOCK
    target: TargetAssetClass = TargetAssetClass.STOCKS
    bucket: AssetClassBucket = AssetClassBucket.EQUITY

    def __init__(
        self,
        providers: BaseProviderSet,
        *,
        target: TargetAssetClass | None = None,
    ) -> None:
        super().__init__(providers, target=target)
        self._eval_config = self._config.evaluator_config(self.target)

    def discover(self, selection_input: SelectionInput) -> List[SecurityIdentity]:
        """Discover stocks from the config universe or search query."""
        universe = self._eval_config.universe if self._eval_config else []
        # If no static universe, try to search via providers
        if not universe and selection_input.filter_overrides.get("search_query"):
            query = selection_input.filter_overrides["search_query"]
            identities = self._data.search(query, kind=SecurityKind.STOCK)
            limit = self._eval_config.max_candidates if self._eval_config else 30
            if selection_input.candidate_limit:
                limit = min(limit, selection_input.candidate_limit)
            return identities[:limit]

        identities: List[SecurityIdentity] = []
        for symbol in universe:
            identities.append(
                SecurityIdentity(
                    symbol=symbol,
                    name=symbol,
                    currency=default_currency(self.target),
                    kind=SecurityKind.STOCK,
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
        valid: List[ProviderPayload] = []
        for payload in payloads:
            report = self._quality.validate_payload(payload)
            if report.is_usable:
                valid.append(payload)
            else:
                logger.warning(
                    "Stock %s failed quality: %s",
                    payload.identity.symbol,
                    report.summary(),
                )
        return valid

    def calculate_metrics(
        self,
        payloads: List[ProviderPayload],
        selection_input: SelectionInput,
    ) -> List[CandidateSecurity]:
        candidates = build_candidates_from_payloads(
            payloads, self.target, kind=SecurityKind.STOCK
        )
        for candidate in candidates:
            enrich_candidate_from_metrics(candidate, self._metrics, self._config)
        return candidates

    def normalize(
        self,
        candidates: List[CandidateSecurity],
        selection_input: SelectionInput,
    ) -> List[CandidateSecurity]:
        for candidate in candidates:
            profile = self._normalize_stock(candidate)
            candidate.profile = profile
        return candidates

    def _normalize_stock(self, candidate: CandidateSecurity) -> NormalizedProfile:
        m = candidate.metrics
        avail: Dict[NormalizationAxis, bool] = {}

        # Return
        returns = [m.get("cagr_1y"), m.get("cagr_3y"), m.get("cagr_5y")]
        valid_returns = [r for r in returns if r is not None and isinstance(r, (int, float))]
        if valid_returns:
            expected_return = _minmax_scale(
                sum(valid_returns) / len(valid_returns), -0.20, 0.40
            )
            avail[NormalizationAxis.EXPECTED_RETURN] = True
        else:
            expected_return = 0.5
            avail[NormalizationAxis.EXPECTED_RETURN] = False

        # Risk
        vol = m.get("annual_volatility")
        if vol is not None and isinstance(vol, (int, float)) and vol > 0:
            risk = _minmax_scale(1.0 / (1.0 + vol), 0.0, 1.0)
            avail[NormalizationAxis.RISK] = True
        else:
            risk = 0.5
            avail[NormalizationAxis.RISK] = False

        # Liquidity (avg volume)
        avg_vol = m.get("average_volume_30d")
        if avg_vol is not None and isinstance(avg_vol, (int, float)):
            liquidity = _minmax_scale(float(avg_vol), 0, 10_000_000)
            avail[NormalizationAxis.LIQUIDITY] = True
        else:
            liquidity = 0.5
            avail[NormalizationAxis.LIQUIDITY] = False

        # Diversification (stocks are single-issuer)
        diversification = 0.2
        avail[NormalizationAxis.DIVERSIFICATION] = True

        # Tax efficiency
        tax_efficiency = 0.7
        avail[NormalizationAxis.TAX_EFFICIENCY] = True

        # Cost (no expense ratio for stocks; brokerage is near-zero)
        cost = 0.9
        avail[NormalizationAxis.COST] = True

        # Tracking quality (N/A for stocks)
        tracking_quality = 0.5
        avail[NormalizationAxis.TRACKING_QUALITY] = False

        # Quality (PE, ROE, Sharpe)
        sharpe = m.get("sharpe_ratio")
        if sharpe is not None and isinstance(sharpe, (int, float)):
            quality = _minmax_scale(float(sharpe), -1.0, 3.0)
            avail[NormalizationAxis.QUALITY] = True
        else:
            quality = 0.5
            avail[NormalizationAxis.QUALITY] = False

        # Market exposure (market cap)
        mcap = m.get("market_cap")
        if mcap is not None and isinstance(mcap, (int, float)):
            market_exposure = _minmax_scale(float(mcap), 0, 20_000_000_000_000)
            avail[NormalizationAxis.MARKET_EXPOSURE] = True
        else:
            market_exposure = 0.5
            avail[NormalizationAxis.MARKET_EXPOSURE] = False

        available_count = sum(1 for v in avail.values() if v)
        confidence = available_count / len(NormalizationAxis)

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
    if max_val <= min_val:
        return 0.5
    scaled = (value - min_val) / (max_val - min_val)
    return max(0.0, min(1.0, scaled))
