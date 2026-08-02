"""Redis client wrapper.

Used for session/blacklist storage, response caching, rate-limit
counters and — later — AI conversation memory. The wrapper degrades
gracefully: if Redis is unreachable in a non-critical path, calls return
defaults instead of crashing the API.
"""

from __future__ import annotations

import json
import logging
from typing import Any

import redis

from app.config import settings

logger = logging.getLogger(__name__)


class CacheClient:
    """Thin, type-tolerant Redis cache with graceful degradation."""

    def __init__(self, url: str | None = None) -> None:
        self._url = url or settings.REDIS_URL
        self._client: redis.Redis | None = None
        self._available: bool | None = None

    def connect(self) -> None:
        try:
            self._client = redis.Redis.from_url(self._url, decode_responses=True)
            self._client.ping()
            self._available = True
            logger.info("Redis connected at %s", self._url)
        except Exception as exc:  # pragma: no cover - depends on infra
            self._available = False
            logger.warning("Redis unavailable (%s); cache disabled", exc)

    def close(self) -> None:
        if self._client is not None:
            self._client.close()

    @property
    def available(self) -> bool:
        return bool(self._available and self._client)

    # ── value helpers ───────────────────────────────────────────────

    def set_json(self, key: str, value: Any, ttl_seconds: int | None = None) -> None:
        if not self.available:
            return
        try:
            self._client.set(key, json.dumps(value, default=str), ex=ttl_seconds)
        except Exception as exc:  # pragma: no cover
            logger.warning("Redis set failed for %s: %s", key, exc)

    def get_json(self, key: str) -> Any | None:
        if not self.available:
            return None
        try:
            raw = self._client.get(key)
            return json.loads(raw) if raw else None
        except Exception as exc:  # pragma: no cover
            logger.warning("Redis get failed for %s: %s", key, exc)
            return None

    def delete(self, *keys: str) -> None:
        if not self.available:
            return
        try:
            self._client.delete(*keys)
        except Exception as exc:  # pragma: no cover
            logger.warning("Redis delete failed: %s", exc)

    def exists(self, key: str) -> bool:
        if not self.available:
            return False
        try:
            return bool(self._client.exists(key))
        except Exception as exc:  # pragma: no cover
            logger.warning("Redis exists failed: %s", exc)
            return False

    def ttl(self, key: str) -> int:
        """Remaining TTL in seconds (-1 = persists, -2 = missing)."""
        if not self.available:
            return -2
        try:
            return int(self._client.ttl(key))
        except Exception as exc:  # pragma: no cover
            logger.warning("Redis ttl failed: %s", exc)
            return -2

    # ── session / rate-limit helpers ────────────────────────────────

    def blacklist_jwt(self, jti: str, expires_in_seconds: int) -> None:
        """Store a revoked token id so it cannot be reused after logout."""
        self.set_json(f"jwt:blacklist:{jti}", {"revoked": True}, ttl_seconds=expires_in_seconds)

    def is_jwt_blacklisted(self, jti: str) -> bool:
        return self.exists(f"jwt:blacklist:{jti}")

    def blacklist_access_jti(self, jti: str) -> None:
        """Revoke an access token for its remaining lifetime (via TTL)."""
        self.blacklist_jwt(jti, settings.access_token_expire_seconds)


# Process-wide singleton.
cache = CacheClient()

