"""Fallback provider — chains providers in configured order.

Tries each enabled provider for a given identity until one succeeds.
Integrates with the :class:`CacheLayer`: cached (possibly stale) data is
served before hitting the network when the cache says it is acceptable.
"""

from __future__ import annotations

import logging
from datetime import date
from typing import Any, Dict, List, Optional

from security_selection.cache.engine import CacheLayer
from security_selection.config import ProviderConfig, get_config
from security_selection.models.data import ProviderPayload, SecurityIdentity
from security_selection.providers.base import BaseDataProvider, ProviderException

logger = logging.getLogger(__name__)


class FallbackProvider(BaseDataProvider):
    """Aggregates providers into a single ordered, resilient interface."""

    name = None  # type: ignore[assignment]

    def __init__(
        self,
        providers: List[BaseDataProvider],
        cache: CacheLayer | None = None,
        config: Optional[ProviderConfig] = None,
    ) -> None:
        super().__init__(enabled=True)
        self._providers = providers
        self._cache = cache or CacheLayer()
        self._config = config or get_config().providers

    def supports(self, identity: SecurityIdentity) -> bool:
        return any(p.supports(identity) for p in self._providers)

    # ── snapshot ────────────────────────────────────────────────────

    def fetch_snapshot(self, identity: SecurityIdentity) -> ProviderPayload:
        key = f"{identity.key}:snapshot"
        cached = self._cache.get(key)
        if cached is not None:
            return self._from_cache(cached.data, identity)
        for provider in self._providers:
            if not provider.enabled or not provider.supports(identity):
                continue
            try:
                payload = provider.fetch_snapshot(identity)
                if payload.success:
                    self._cache.set(key, payload, kind="snapshot")
                    return payload
                logger.debug("provider %s failed snapshot for %s: %s",
                             provider.name, identity.symbol, payload.error)
            except Exception as exc:
                logger.debug("provider %s raised on snapshot for %s: %s",
                             provider.name, identity.symbol, exc)
        # cache fallback (stale but within tolerance)
        stale = self._cache.get_stale(key)
        if stale is not None:
            logger.info("serving stale snapshot for %s", identity.symbol)
            payload = self._from_cache(stale.data, identity)
            return payload
        return ProviderPayload(
            provider=provider_placeholder(),
            identity=identity,
            success=False,
            error="all providers failed for snapshot",
        )

    # ── history ─────────────────────────────────────────────────────

    def fetch_history(
        self,
        identity: SecurityIdentity,
        start: date | None = None,
        end: date | None = None,
    ) -> ProviderPayload:
        key = f"{identity.key}:history"
        cached = self._cache.get(key)
        if cached is not None:
            return self._from_cache(cached.data, identity)
        for provider in self._providers:
            if not provider.enabled or not provider.supports(identity):
                continue
            try:
                payload = provider.fetch_history(identity, start, end)
                if payload.success and payload.history and not payload.history.is_empty():
                    self._cache.set(key, payload, kind="history")
                    return payload
                logger.debug("provider %s failed history for %s: %s",
                             provider.name, identity.symbol, payload.error)
            except Exception as exc:
                logger.debug("provider %s raised on history for %s: %s",
                             provider.name, identity.symbol, exc)
        stale = self._cache.get_stale(key)
        if stale is not None:
            logger.info("serving stale history for %s", identity.symbol)
            return self._from_cache(stale.data, identity)
        return ProviderPayload(
            provider=provider_placeholder(),
            identity=identity,
            success=False,
            error="all providers failed for history",
        )

    # ── search ──────────────────────────────────────────────────────

    def search(self, query: str, **kwargs: Any) -> List[SecurityIdentity]:
        out: List[SecurityIdentity] = []
        seen = set()
        for provider in self._providers:
            if not provider.enabled:
                continue
            try:
                for identity in provider.search(query, **kwargs):
                    if identity.symbol not in seen:
                        out.append(identity)
                        seen.add(identity.symbol)
            except Exception as exc:
                logger.debug("provider %s search failed: %s", provider.name, exc)
        return out

    # ── metric hooks (first provider that returns non-empty) ────────

    def fetch_metrics(self, identity: SecurityIdentity) -> Dict[str, Any]:
        for provider in self._providers:
            if not provider.enabled or not provider.supports(identity):
                continue
            try:
                metrics = provider.fetch_metrics(identity)
                if metrics:
                    return metrics
            except Exception:
                continue
        return {}

    def fetch_holdings(self, identity: SecurityIdentity) -> List[Dict[str, Any]]:
        for provider in self._providers:
            if not provider.enabled or not provider.supports(identity):
                continue
            try:
                holdings = provider.fetch_holdings(identity)
                if holdings:
                    return holdings
            except Exception:
                continue
        return []

    def fetch_sector_allocations(self, identity: SecurityIdentity) -> Dict[str, float]:
        for provider in self._providers:
            if not provider.enabled or not provider.supports(identity):
                continue
            try:
                sectors = provider.fetch_sector_allocations(identity)
                if sectors:
                    return sectors
            except Exception:
                continue
        return {}

    def fetch_country_allocations(self, identity: SecurityIdentity) -> Dict[str, float]:
        for provider in self._providers:
            if not provider.enabled or not provider.supports(identity):
                continue
            try:
                countries = provider.fetch_country_allocations(identity)
                if countries:
                    return countries
            except Exception:
                continue
        return {}

    # ── helpers ─────────────────────────────────────────────────────

    @staticmethod
    def _from_cache(data: Dict[str, Any], identity: SecurityIdentity) -> ProviderPayload:
        """Rebuild a ProviderPayload from cached serialized data."""
        from security_selection.models.data import (
            DataPoint,
            HistoricalSeries,
            MarketSnapshot,
        )
        from security_selection.models.enums import DataSource, ProviderName

        ident = identity
        snap_raw = data.get("snapshot") or {}
        snapshot = None
        if snap_raw:
            snapshot = MarketSnapshot(
                identity=ident,
                current_price=snap_raw.get("current_price"),
                nav=snap_raw.get("nav"),
                as_of=_parse_dt(snap_raw.get("as_of")),
                currency=snap_raw.get("currency", "INR"),
                volume=snap_raw.get("volume"),
                average_volume=snap_raw.get("average_volume"),
                market_cap=snap_raw.get("market_cap"),
                aum=snap_raw.get("aum"),
                extra=snap_raw.get("extra") or {},
            )
        hist_raw = data.get("history")
        history = None
        if hist_raw:
            points = [
                DataPoint(date=_parse_date(p.get("date")), value=p.get("value"))
                for p in hist_raw.get("points", [])
                if _parse_date(p.get("date")) is not None and p.get("value") is not None
            ]
            bench = [
                DataPoint(date=_parse_date(p.get("date")), value=p.get("value"))
                for p in hist_raw.get("benchmark", [])
                if _parse_date(p.get("date")) is not None and p.get("value") is not None
            ]
            history = HistoricalSeries(
                points=points,
                benchmark=bench,
                currency=hist_raw.get("currency", "INR"),
                source=DataSource(hist_raw.get("source", "cache")),
            )
        try:
            provider = ProviderName(data.get("provider", "cache"))
        except ValueError:
            provider = ProviderName.CACHE
        return ProviderPayload(
            provider=provider,
            identity=ident,
            snapshot=snapshot,
            history=history,
            metrics=data.get("metrics") or {},
            holdings=data.get("holdings") or [],
            sector_allocations=data.get("sector_allocations") or {},
            country_allocations=data.get("country_allocations") or {},
            success=data.get("success", True),
            error=data.get("error"),
        )


def provider_placeholder():
    from security_selection.models.enums import ProviderName

    return ProviderName.CACHE


def _parse_date(raw: Any):
    from datetime import date

    if not raw:
        return None
    try:
        return date.fromisoformat(str(raw)[:10])
    except ValueError:
        return None


def _parse_dt(raw: Any):
    from datetime import datetime

    if not raw:
        return None
    try:
        return datetime.fromisoformat(raw)
    except ValueError:
        return None

