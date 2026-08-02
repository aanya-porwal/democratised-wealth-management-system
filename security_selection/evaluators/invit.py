"""InvIT evaluator — discovers, fetches and evaluates Infrastructure Investment Trusts.

InvITs invest in infrastructure projects (roads, power, telecom). They
are listed on stock exchanges and provide stable dividend income.
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


class InvITEvaluator(BaseEvaluator):
    """Evaluator for Infrastructure Investment Trusts.

    InvITs are evaluated on dividend yield, project pipeline, and cash
    flow stability. Similar to REITs but for infrastructure assets.
    """

    kind: SecurityKind = SecurityKind.INVIT
    target: TargetAssetClass = TargetAssetClass.INVIT
    bucket: AssetClassBucket = AssetClassBucket.REAL_ASSETS

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
            logger.warning("No InvIT universe configured")
            return []
        identities: List[SecurityIdentity] = []
        for symbol in universe:
            identities.append(
                SecurityIdentity(
                    symbol=symbol,
                    name=symbol,
                    currency=default_currency(self.target),
                    kind=SecurityKind.INVIT,
                )
            )
        limit = self._eval_config.max_candidates if self._eval_config else 20
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
                    "InvIT %s failed quality: %s",
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
            payloads, self.target, kind=SecurityKind.INVIT
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
            profile = self._normalize_invit(candidate)
            candidate.profile = profile
        return candidates

    def _normalize_invit(self, candidate: CandidateSecurity) -> NormalizedProfile:
        m = candidate.metrics
        avail: Dict[NormalizationAxis, bool] = {}

        returns = [m.get("cagr_1y"), m.get("cagr_3y")]
        valid_returns = [r for r in returns if r is not None and isinstance(r, (int, float))]
        if valid_returns:
            expected_return = _minmax_scale(
                sum(valid_returns) / len(valid_returns), -0.15, 0.25
            )
            avail[NormalizationAxis.EXPECTED_RETURN] = True
        else:
            expected_return = 0.5
            avail[NormalizationAxis.EXPECTED_RETURN] = False

        vol = m.get("annual_volatility")
        if vol is not None and isinstance(vol, (int, float)) and vol > 0:
            risk = _minmax_scale(1.0 / (1.0 + vol), 0.0, 1.0)
            avail[NormalizationAxis.RISK] = True
        else:
            risk = 0.5
            avail[NormalizationAxis.RISK] = False

        liquidity = 0.4  # less liquid than REITs
        avail[NormalizationAxis.LIQUIDITY] = True

        diversification = 0.4
        avail[NormalizationAxis.DIVERSIFICATION] = True

        tax_efficiency = 0.5
        avail[NormalizationAxis.TAX_EFFICIENCY] = True

        cost = 0.7
        avail[NormalizationAxis.COST] = True

        tracking_quality = 0.5
        avail[NormalizationAxis.TRACKING_QUALITY] = False

        sharpe = m.get("sharpe_ratio")
        if sharpe is not None and isinstance(sharpe, (int, float)):
            quality = _minmax_scale(float(sharpe), -1.0, 3.0)
            avail[NormalizationAxis.QUALITY] = True
        else:
            quality = 0.5
            avail[NormalizationAxis.QUALITY] = False

        aum = m.get("aum_crore")
        if aum is not None and isinstance(aum, (int, float)):
            market_exposure = _minmax_scale(float(aum), 0, 50000)
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
