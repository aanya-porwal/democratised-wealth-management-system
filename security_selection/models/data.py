"""Data-layer models for the Security Selection platform.

These are the provider-agnostic containers that flow between providers,
the cache, the quality engine and the evaluators. They deliberately
contain no business logic.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from typing import Any, Dict, List, Optional

from security_selection.models.enums import DataSource, ProviderName, SecurityKind


@dataclass(frozen=True)
class SecurityIdentity:
    """A stable, provider-independent security identifier.

    ``symbol`` is the canonical ticker; ``exchange`` is the listing venue;
    ``scheme_code`` is the AMFI code for Indian mutual funds.
    """

    symbol: str
    name: str = ""
    exchange: str | None = None
    isin: str | None = None
    scheme_code: str | None = None
    currency: str = "INR"
    kind: SecurityKind | None = None

    @property
    def key(self) -> str:
        """A stable cache key for this security."""
        parts = [self.symbol]
        if self.exchange:
            parts.append(self.exchange)
        if self.scheme_code:
            parts.append(self.scheme_code)
        return ".".join(parts)


@dataclass(frozen=True)
class DataPoint:
    """A single dated observation (price or NAV)."""

    date: date
    value: float


@dataclass(frozen=True)
class HistoricalSeries:
    """An ordered daily price/NAV series with optional benchmark."""

    points: List[DataPoint] = field(default_factory=list)
    benchmark: List[DataPoint] = field(default_factory=list)
    currency: str = "INR"
    source: DataSource = DataSource.LIVE

    def is_empty(self) -> bool:
        return len(self.points) == 0

    def as_dicts(self) -> List[Dict[str, Any]]:
        return [{"date": p.date.isoformat(), "value": p.value} for p in self.points]


@dataclass(frozen=True)
class MetricValue:
    """A single metric with availability and derivation metadata.

    ``value`` is ``None`` when the metric could not be derived; ``reason``
    explains why (never fabricate a number).
    """

    name: str
    value: float | None
    available: bool = True
    source: DataSource = DataSource.LIVE
    reason: str | None = None

    @staticmethod
    def unavailable(name: str, reason: str) -> "MetricValue":
        return MetricValue(name=name, value=None, available=False, reason=reason)


@dataclass(frozen=True)
class MarketSnapshot:
    """A point-in-time snapshot of a security's market data."""

    identity: SecurityIdentity
    current_price: float | None = None
    nav: float | None = None
    as_of: datetime | None = None
    currency: str = "INR"
    volume: float | None = None
    average_volume: float | None = None
    market_cap: float | None = None
    aum: float | None = None
    extra: Dict[str, Any] = field(default_factory=dict)

    @property
    def price(self) -> float | None:
        """Return the best current valuation (NAV for funds, price else)."""
        return self.current_price if self.current_price is not None else self.nav


@dataclass(frozen=True)
class AvailableMetric:
    """Metadata describing a metric an evaluator can produce."""

    name: str
    description: str
    unit: str = ""


@dataclass(frozen=True)
class QualityReport:
    """Result of the data-quality engine for one security."""

    security_key: str
    passed: bool
    issues: List[str] = field(default_factory=list)
    missing_fraction: float = 0.0
    duplicate_count: int = 0
    stale_days: int | None = None
    outlier_count: int = 0
    api_failures: int = 0
    used_cache_fallback: bool = False
    quality_score: float = 1.0


@dataclass(frozen=True)
class ProviderPayload:
    """Raw payload returned by a data provider before normalization."""

    provider: ProviderName
    identity: SecurityIdentity
    snapshot: MarketSnapshot | None = None
    history: HistoricalSeries | None = None
    metrics: Dict[str, Any] = field(default_factory=dict)
    holdings: List[Dict[str, Any]] = field(default_factory=list)
    sector_allocations: Dict[str, float] = field(default_factory=dict)
    country_allocations: Dict[str, float] = field(default_factory=dict)
    fetched_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    success: bool = True
    error: str | None = None


@dataclass(frozen=True)
class CachedPayload:
    """Payload stored in the cache layer with freshness metadata."""

    key: str
    data: Dict[str, Any]
    fetched_at: datetime
    expires_at: datetime | None = None
    source: ProviderName = ProviderName.CACHE

    def is_expired(self, now: datetime | None = None) -> bool:
        now = now or datetime.now(timezone.utc)
        if self.expires_at is None:
            return False
        return now > self.expires_at

    def age_seconds(self, now: datetime | None = None) -> float:
        now = now or datetime.now(timezone.utc)
        return (now - self.fetched_at).total_seconds()

