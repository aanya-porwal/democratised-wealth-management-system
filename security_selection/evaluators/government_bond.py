"""Government bond evaluator — discovers, fetches and evaluates government bonds (G-Secs).

Government bonds are sovereign-guaranteed debt securities issued by the
Government of India. Uses the static data provider for bond metadata
and yfinance for G-sec yield tracking.
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


class GovernmentBondEvaluator(BaseEvaluator):
    """Evaluator for government bonds (G-Secs, State Development Loans).

    Government bonds are the safest debt instruments. They are evaluated
    on yield, duration, maturity, and liquidity.
    """

    kind: SecurityKind = SecurityKind.GOVERNMENT_BOND
    target: TargetAssetClass = TargetAssetClass.GOVERNMENT_BONDS
    bucket: AssetClassBucket = AssetClassBucket.DEBT

    def __init__(
        self,
        providers: BaseProviderSet,
        *,
        target: TargetAssetClass | None = None,
    ) -> None:
        super().__init__(providers, target=target)
        self._eval_config = self._config.evaluator_config(self.target)

    def discover(self, selection_input: SelectionInput) -> List[SecurityIdentity]:
        universe = self._eval_config.universe if self._eval_config else []
        if not universe:
            return self._data.search("", kind=SecurityKind.GOVERNMENT_BOND)
        identities: List[SecurityIdentity] = []
        for symbol in universe:
            identities.append(
                SecurityIdentity(
                    symbol=symbol,
                    name=symbol,
                    currency=default_currency(self.target),
                    kind=SecurityKind.GOVERNMENT_BOND,
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
            history_years=None,
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
                    "Govt bond %s failed quality: %s",
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
            payloads, self.target, kind=SecurityKind.GOVERNMENT_BOND
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
            profile = self._normalize_govt_bond(candidate)
            candidate.profile = profile
        return candidates

    def _normalize_govt_bond(self, candidate: CandidateSecurity) -> NormalizedProfile:
        m = candidate.metrics
        avail: Dict[NormalizationAxis, bool] = {}

        ytm = m.get("interest_rate") or m.get("yield_to_maturity")
        if ytm is not None and isinstance(ytm, (int, float)):
            expected_return = _minmax_scale(float(ytm), 0.0, 0.12)
            avail[NormalizationAxis.EXPECTED_RETURN] = True
        else:
            expected_return = 0.5
            avail[NormalizationAxis.EXPECTED_RETURN] = False

        # Risk (sovereign = near-zero default risk)
        risk = 0.95
        avail[NormalizationAxis.RISK] = True

        liquidity = 0.5
        avail[NormalizationAxis.LIQUIDITY] = True

        diversification = 0.2
        avail[NormalizationAxis.DIVERSIFICATION] = True

        tax_efficiency = 0.3
        avail[NormalizationAxis.TAX_EFFICIENCY] = True

        cost = 0.7
        avail[NormalizationAxis.COST] = True

        tracking_quality = 0.5
        avail[NormalizationAxis.TRACKING_QUALITY] = False

        quality = 0.95  # sovereign guaranteed
        avail[NormalizationAxis.QUALITY] = True

        market_exposure = 0.5
        avail[NormalizationAxis.MARKET_EXPOSURE] = True

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
