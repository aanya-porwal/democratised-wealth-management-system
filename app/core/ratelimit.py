"""Redis-backed rate limiting with an in-memory fallback.

A fixed-window counter per key (default key = client IP) stored in Redis
so limits hold across multiple workers. When Redis is unavailable the
limiter falls back to a local dictionary — still correct within a single
process, which is enough for dev and tests.
"""

from __future__ import annotations

import logging
import time
from collections import defaultdict
from threading import Lock

from fastapi import Request
from fastapi.responses import JSONResponse

from app.config import settings
from app.core import cache
from app.core.exceptions import RateLimitError

logger = logging.getLogger(__name__)

_local: dict[str, tuple[int, float]] = {}
_local_lock = Lock()


def _parse_spec(spec: str) -> tuple[int, int]:
    """Parse ``"60/minute"`` -> (limit, window_seconds)."""
    count_str, unit = spec.strip().split("/")
    count = int(count_str)
    window = {"second": 1, "minute": 60, "hour": 3600, "day": 86400}[unit]
    return count, window


def check_rate_limit(
    request: Request,
    *,
    key_prefix: str = "rl",
    spec: str | None = None,
) -> None:
    """Increment the counter for the client and raise if over the limit."""
    if not settings.RATE_LIMIT_ENABLED:
        return
    limit, window = _parse_spec(spec or settings.RATE_LIMIT_DEFAULT)
    client = request.client.host if request.client else "unknown"
    key = f"{key_prefix}:{client}"

    if cache.cache.available:
        bucket = int(time.time() // window)
        redis_key = f"{key}:{bucket}"
        try:
            count = cache.cache._client.incr(redis_key)  # type: ignore[union-attr]
            if count == 1:
                cache.cache._client.expire(redis_key, window)
            if count > limit:
                raise RateLimitError(
                    f"Rate limit exceeded ({limit} per {window}s)",
                    code="rate_limit_exceeded",
                )
            return
        except RateLimitError:
            raise
        except Exception as exc:  # pragma: no cover
            logger.warning("Redis rate-limit failed, falling back to local: %s", exc)

    # In-memory fallback (single process).
    now = time.time()
    with _local_lock:
        current_window = int(now // window)
        prev_count, prev_window = _local.get(key, (0, current_window))
        if prev_window != current_window:
            _local[key] = (0, current_window)
            prev_count, _ = _local[key]
        if prev_count >= limit:
            raise RateLimitError(
                f"Rate limit exceeded ({limit} per {window}s)",
                code="rate_limit_exceeded",
            )
        _local[key] = (prev_count + 1, current_window)


def rate_limited_response(exc: RateLimitError) -> JSONResponse:
    return JSONResponse(status_code=429, content=exc.to_dict())

