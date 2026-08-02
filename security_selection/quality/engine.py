"""Data Quality Engine.

Detects and reports data-quality problems before a security is allowed
into the candidate universe:

* missing values / incomplete datasets
* duplicate securities / duplicate points
* stale prices (last observation too old)
* outliers (z-score or single-day return jumps)
* invalid NAVs (zero / negative / absurdly small)
* API failures (fallback to cached data when permitted)

The engine is provider-independent and returns a :class:`QualityReport`.
"""

from __future__ import annotations

import logging
from datetime import date, datetime, timezone
from typing import Dict, List, Optional

from security_selection.config import QualityConfig, get_config
from security_selection.models.data import (
    DataPoint,
    HistoricalSeries,
    MarketSnapshot,
    ProviderPayload,
    QualityReport,
)
from security_selection.utils.math import safe_float

logger = logging.getLogger(__name__)


class DataQualityEngine:
    """Runs data-quality checks on provider payloads."""

    def __init__(self, config: Optional[QualityConfig] = None) -> None:
        self._config = config or get_config().quality

    # ── public API ──────────────────────────────────────────────────

    def validate_payload(self, payload: ProviderPayload) -> QualityReport:
        """Validate one provider payload."""
        issues: List[str] = []
        used_cache_fallback = False

        if not payload.success:
            issues.append(f"provider failure: {payload.error or 'unknown error'}")

        identity = payload.identity
        history = payload.history
        snapshot = payload.snapshot

        # missing data detection
        missing_fraction = 0.0
        if history is None or history.is_empty():
            missing_fraction = 1.0
            issues.append("no historical series available")
        else:
            missing_fraction = self._missing_fraction(history)
            if missing_fraction > self._config.max_missing_fraction:
                issues.append(
                    f"missing data fraction {missing_fraction:.0%} exceeds "
                    f"limit {self._config.max_missing_fraction:.0%}"
                )

        # duplicate points
        duplicates = 0
        if history and history.points:
            dates = [p.date for p in history.points]
            duplicates = len(dates) - len(set(dates))
            if duplicates:
                issues.append(f"{duplicates} duplicate date points in series")

        # stale price
        stale_days: Optional[int] = None
        if history and history.points:
            stale_days = (date.today() - history.points[-1].date).days
            if stale_days > self._config.stale_price_days:
                issues.append(f"price/NAV is {stale_days} days stale")

        # invalid NAVs / prices
        invalid_count = 0
        if history and history.points:
            invalid_count = self._count_invalid_values(history.points)
            if invalid_count:
                issues.append(f"{invalid_count} invalid (<=0) values in series")

        # outliers
        outlier_count = 0
        if history and history.points:
            values = [p.value for p in history.points if p.value > 0]
            outlier_count = self._count_outliers(values)
            if outlier_count:
                issues.append(f"{outlier_count} outlier observations detected")

        # snapshot sanity
        if snapshot is not None:
            price = snapshot.price
            if price is None or price <= 0:
                issues.append("snapshot has no positive price/NAV")

        # API failures fallback
        api_failures = 0
        if not payload.success:
            api_failures = 1
            if self._config.allow_cache_fallback:
                used_cache_fallback = True
                issues.append("falling back to cached data (cache fallback enabled)")

        passed = len(issues) == 0
        quality_score = self._quality_score(
            missing_fraction=missing_fraction,
            duplicate_count=duplicates,
            stale_days=stale_days,
            outlier_count=outlier_count,
            invalid_count=invalid_count,
            api_failures=api_failures,
        )

        return QualityReport(
            security_key=identity.key,
            passed=passed,
            issues=issues,
            missing_fraction=round(missing_fraction, 4),
            duplicate_count=duplicates,
            stale_days=stale_days,
            outlier_count=outlier_count,
            api_failures=api_failures,
            used_cache_fallback=used_cache_fallback,
            quality_score=round(quality_score, 4),
        )

    def validate_series(self, history: HistoricalSeries) -> QualityReport:
        """Validate a bare series (synthetic payload for tests)."""
        payload = ProviderPayload(
            provider=payload_provider_placeholder(),
            identity=SecurityIdentityPlaceholder(history),
            history=history,
        )
        return self.validate_payload(payload)

    # ── internals ───────────────────────────────────────────────────

    def _missing_fraction(self, history: HistoricalSeries) -> float:
        """Estimate missing fraction using gaps > 1 trading day."""
        if not history.points:
            return 1.0
        from datetime import timedelta

        dates = [p.date for p in history.points]
        expected = (dates[-1] - dates[0]).days + 1
        if expected <= 0:
            return 0.0
        return 1.0 - (len(set(dates)) / expected)

    def _count_invalid_values(self, points: List[DataPoint]) -> int:
        return sum(1 for p in points if safe_float(p.value, 0.0) is not None and p.value <= 0)

    def _count_outliers(self, values: List[float]) -> int:
        """Count values beyond ``outlier_zscore`` standard deviations."""
        if len(values) < 4:
            return 0
        import statistics

        mean = statistics.fmean(values)
        std = statistics.pstdev(values)
        if std == 0:
            return 0
        z = self._config.outlier_zscore
        return sum(1 for v in values if abs((v - mean) / std) > z)

    def _quality_score(
        self,
        *,
        missing_fraction: float,
        duplicate_count: int,
        stale_days: Optional[int],
        outlier_count: int,
        invalid_count: int,
        api_failures: int,
    ) -> float:
        """0..1 composite quality score."""
        score = 1.0
        score -= missing_fraction * 0.5
        score -= min(duplicate_count / 50.0, 0.1)
        if stale_days is not None and stale_days > self._config.stale_price_days:
            score -= min(stale_days / 365.0, 0.15)
        score -= min(outlier_count / 100.0, 0.1)
        score -= min(invalid_count / 100.0, 0.1)
        score -= api_failures * 0.2
        return max(0.0, score)


# ── local helpers (avoid circular imports) ───────────────────────────

def payload_provider_placeholder():
    """Return a placeholder provider name for synthetic payloads."""
    from security_selection.models.enums import ProviderName

    return ProviderName.MOCK


def SecurityIdentityPlaceholder(history: HistoricalSeries):
    """Build a minimal identity for a bare series."""
    from security_selection.models.data import SecurityIdentity

    return SecurityIdentity(symbol="synthetic")

