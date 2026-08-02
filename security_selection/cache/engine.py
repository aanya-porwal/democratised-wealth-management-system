"""Provider-independent cache layer.

The cache stores raw provider payloads keyed by a canonical security key.
It is intentionally independent of any provider: evaluators ask the
cache for a security key, and providers never see it. Freshness is
tracked with fetch timestamps + TTLs; stale-but-within-limit data can be
served as a fallback (controlled by the quality engine).
"""

from __future__ import annotations

import logging
import threading
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from security_selection.config import CacheConfig, get_config
from security_selection.models.data import CachedPayload, ProviderPayload
from security_selection.models.enums import ProviderName

logger = logging.getLogger(__name__)


class CacheLayer:
    """An in-process TTL cache with optional Redis backing.

    The default backend is a dict (works everywhere, including tests).
    When a Redis client is supplied, entries are mirrored there so the
    cache survives across processes.
    """

    def __init__(self, config: Optional[CacheConfig] = None, redis_client: Any | None = None) -> None:
        self._config = config or get_config().cache
        self._store: Dict[str, CachedPayload] = {}
        self._lock = threading.RLock()
        self._redis = redis_client

    # ── public API ──────────────────────────────────────────────────

    def get(self, key: str) -> CachedPayload | None:
        """Return the cached payload if present and not expired.

        Expired entries are evicted lazily. None when absent/expired.
        """
        with self._lock:
            cached = self._store.get(key)
            if cached is None:
                cached = self._redis_get(key)
                if cached is not None:
                    self._store[key] = cached
            if cached is None:
                return None
            if cached.is_expired():
                self._store.pop(key, None)
                self._redis_delete(key)
                return None
            return cached

    def get_stale(self, key: str, max_staleness_seconds: Optional[int] = None) -> CachedPayload | None:
        """Return cached data even if expired, within staleness tolerance."""
        limit = max_staleness_seconds or self._config.max_staleness_seconds
        with self._lock:
            cached = self._store.get(key)
            if cached is None:
                cached = self._redis_get(key)
                if cached is not None:
                    self._store[key] = cached
            if cached is None:
                return None
            if cached.age_seconds() > limit:
                return None
            return cached

    def set(
        self,
        key: str,
        payload: ProviderPayload,
        ttl_seconds: Optional[int] = None,
        kind: str = "default",
    ) -> None:
        """Store a payload under the canonical key."""
        ttl = ttl_seconds or self._ttl_for(kind)
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=ttl)
        cached = CachedPayload(
            key=key,
            data=self._serialize(payload),
            fetched_at=datetime.now(timezone.utc),
            expires_at=expires_at,
            source=payload.provider,
        )
        with self._lock:
            self._store[key] = cached
            self._redis_set(key, cached)

    def refresh(self, key: str, ttl_seconds: Optional[int] = None, kind: str = "default") -> bool:
        """Extend the TTL of an existing entry (no data refetch)."""
        ttl = ttl_seconds or self._ttl_for(kind)
        with self._lock:
            cached = self._store.get(key)
            if cached is None:
                cached = self._redis_get(key)
            if cached is None:
                return False
            refreshed = CachedPayload(
                key=key,
                data=cached.data,
                fetched_at=datetime.now(timezone.utc),
                expires_at=datetime.now(timezone.utc) + timedelta(seconds=ttl),
                source=cached.source,
            )
            self._store[key] = refreshed
            self._redis_set(key, refreshed)
            return True

    def delete(self, key: str) -> None:
        with self._lock:
            self._store.pop(key, None)
            self._redis_delete(key)

    def purge_expired(self) -> int:
        """Remove all expired entries; return how many were removed."""
        now = datetime.now(timezone.utc)
        with self._lock:
            expired = [k for k, v in self._store.items() if v.is_expired(now)]
            for k in expired:
                self._store.pop(k, None)
                self._redis_delete(k)
            return len(expired)

    def clear(self) -> None:
        with self._lock:
            self._store.clear()
            if self._redis is not None:
                try:
                    self._redis.flushdb()
                except Exception:  # pragma: no cover
                    pass

    def stats(self) -> Dict[str, Any]:
        """Basic cache statistics for monitoring."""
        with self._lock:
            return {
                "entries": len(self._store),
                "keys": sorted(self._store.keys())[:100],
            }

    def cleanup_older_than(self, days: Optional[int] = None) -> int:
        """Remove entries fetched more than ``days`` ago."""
        days = days or self._config.cleanup_older_than_days
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        with self._lock:
            old = [k for k, v in self._store.items() if v.fetched_at < cutoff]
            for k in old:
                self._store.pop(k, None)
                self._redis_delete(k)
            return len(old)

    # ── helpers ─────────────────────────────────────────────────────

    def _ttl_for(self, kind: str) -> int:
        mapping = {
            "price": self._config.price_ttl_seconds,
            "nav": self._config.nav_ttl_seconds,
            "history": self._config.history_ttl_seconds,
            "snapshot": self._config.snapshot_ttl_seconds,
        }
        return mapping.get(kind, self._config.default_ttl_seconds)

    @staticmethod
    def _serialize(payload: ProviderPayload) -> Dict[str, Any]:
        """Flatten a provider payload into a JSON-safe dict."""
        return {
            "provider": payload.provider.value,
            "identity": {
                "symbol": payload.identity.symbol,
                "name": payload.identity.name,
                "exchange": payload.identity.exchange,
                "isin": payload.identity.isin,
                "scheme_code": payload.identity.scheme_code,
                "currency": payload.identity.currency,
            },
            "snapshot": _snapshot_to_dict(payload.snapshot),
            "history": _history_to_dict(payload.history),
            "metrics": payload.metrics,
            "holdings": payload.holdings,
            "sector_allocations": payload.sector_allocations,
            "country_allocations": payload.country_allocations,
            "success": payload.success,
            "error": payload.error,
        }

    def _redis_get(self, key: str) -> CachedPayload | None:
        if self._redis is None:
            return None
        try:
            raw = self._redis.get(f"ss:{key}")
            if not raw:
                return None
            import json

            data = json.loads(raw)
            return CachedPayload(
                key=key,
                data=data.get("data", {}),
                fetched_at=datetime.fromisoformat(data["fetched_at"]),
                expires_at=(
                    datetime.fromisoformat(data["expires_at"])
                    if data.get("expires_at")
                    else None
                ),
                source=ProviderName(data.get("source", "cache")),
            )
        except Exception as exc:  # pragma: no cover
            logger.warning("redis get failed for %s: %s", key, exc)
            return None

    def _redis_set(self, key: str, cached: CachedPayload) -> None:
        if self._redis is None:
            return
        try:
            import json

            self._redis.set(
                f"ss:{key}",
                json.dumps(
                    {
                        "data": cached.data,
                        "fetched_at": cached.fetched_at.isoformat(),
                        "expires_at": (
                            cached.expires_at.isoformat() if cached.expires_at else None
                        ),
                        "source": cached.source.value,
                    },
                    default=str,
                ),
                ex=self._config.default_ttl_seconds,
            )
        except Exception as exc:  # pragma: no cover
            logger.warning("redis set failed for %s: %s", key, exc)

    def _redis_delete(self, key: str) -> None:
        if self._redis is None:
            return
        try:
            self._redis.delete(f"ss:{key}")
        except Exception:  # pragma: no cover
            pass


# ── serialization helpers ────────────────────────────────────────────


def _snapshot_to_dict(snapshot) -> Dict[str, Any]:
    if snapshot is None:
        return {}
    return {
        "current_price": snapshot.current_price,
        "nav": snapshot.nav,
        "as_of": snapshot.as_of.isoformat() if snapshot.as_of else None,
        "currency": snapshot.currency,
        "volume": snapshot.volume,
        "average_volume": snapshot.average_volume,
        "market_cap": snapshot.market_cap,
        "aum": snapshot.aum,
        "extra": snapshot.extra,
    }


def _history_to_dict(history) -> Dict[str, Any]:
    if history is None:
        return None
    return {
        "points": [{"date": p.date.isoformat(), "value": p.value} for p in history.points],
        "benchmark": [{"date": p.date.isoformat(), "value": p.value} for p in history.benchmark],
        "currency": history.currency,
        "source": history.source.value,
    }

