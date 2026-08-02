"""MFAPI provider — free Indian mutual-fund scheme + NAV data.

Uses the free public AMFI mirror ``https://api.mfapi.in``. Provides
scheme search, NAV snapshots and daily NAV history for Indian mutual
funds. Requires the ``requests`` package.
"""

from __future__ import annotations

import logging
from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from security_selection.models.data import (
    DataPoint,
    HistoricalSeries,
    MarketSnapshot,
    ProviderPayload,
    SecurityIdentity,
)
from security_selection.models.enums import DataSource, ProviderName
from security_selection.providers.base import BaseDataProvider, ProviderException
from security_selection.utils.math import safe_float

logger = logging.getLogger(__name__)

try:
    import requests as _requests

    _HAS_REQUESTS = True
except Exception:  # pragma: no cover
    _requests = None
    _HAS_REQUESTS = False

_BASE_URL = "https://api.mfapi.in"

# Indian mutual fund kinds served by MFAPI
_SUPPORTED_KINDS = {"mutual_fund", "international_fund"}


class MFAPIProvider(BaseDataProvider):
    """Free Indian mutual fund data via api.mfapi.in."""

    name = ProviderName.MFAPI

    def __init__(self, **config: Any) -> None:
        super().__init__(**config)
        self._base_url = str(config.get("base_url") or _BASE_URL)

    def supports(self, identity: SecurityIdentity) -> bool:
        if not _HAS_REQUESTS:
            return False
        if not self.enabled:
            return False
        kind = identity.kind.value if identity.kind else ""
        if kind not in _SUPPORTED_KINDS:
            return False
        return bool(identity.scheme_code or identity.symbol)

    # ── snapshot ────────────────────────────────────────────────────

    def fetch_snapshot(self, identity: SecurityIdentity) -> ProviderPayload:
        code = identity.scheme_code or identity.symbol
        if not code:
            return self._error_payload(identity, "no scheme code")
        try:
            resp = _requests.get(f"{self._base_url}/mf/{code}", timeout=self._timeout())
            resp.raise_for_status()
            data = resp.json()
            nav_data = data.get("data") or []
            if not nav_data:
                return self._error_payload(identity, "empty NAV payload")
            latest = nav_data[-1]
            nav = safe_float(latest.get("nav"))
            snapshot = MarketSnapshot(
                identity=identity,
                nav=nav,
                as_of=_parse_mfapi_date(latest.get("date")),
                currency="INR",
                extra={
                    "scheme_name": data.get("meta", {}).get("scheme_name", ""),
                    "scheme_category": data.get("meta", {}).get("scheme_category", ""),
                    "fund_house": data.get("meta", {}).get("fund_house", ""),
                    "scheme_code": data.get("meta", {}).get("scheme_code", ""),
                },
            )
            return ProviderPayload(
                provider=self.name,
                identity=identity,
                snapshot=snapshot,
                metrics={
                    "fund_house": data.get("meta", {}).get("fund_house", ""),
                    "scheme_category": data.get("meta", {}).get("scheme_category", ""),
                },
                success=True,
            )
        except Exception as exc:  # pragma: no cover
            logger.warning("MFAPI snapshot failed for %s: %s", code, exc)
            return self._error_payload(identity, str(exc))

    # ── history ─────────────────────────────────────────────────────

    def fetch_history(
        self,
        identity: SecurityIdentity,
        start: date | None = None,
        end: date | None = None,
    ) -> ProviderPayload:
        code = identity.scheme_code or identity.symbol
        if not code:
            return self._error_payload(identity, "no scheme code")
        try:
            resp = _requests.get(f"{self._base_url}/mf/{code}", timeout=self._timeout())
            resp.raise_for_status()
            data = resp.json()
            nav_data = data.get("data") or []
            if not nav_data:
                return self._error_payload(identity, "empty NAV payload")

            start = start or (date.today() - timedelta(days=365 * 10))
            end = end or date.today()
            points: List[DataPoint] = []
            for row in nav_data:
                d = _parse_mfapi_date(row.get("date"))
                value = safe_float(row.get("nav"))
                if d is None or value is None:
                    continue
                if start <= d <= end:
                    points.append(DataPoint(date=d, value=value))

            series = HistoricalSeries(points=_dedupe(points), source=DataSource.LIVE, currency="INR")
            return ProviderPayload(
                provider=self.name,
                identity=identity,
                history=series,
                success=True,
            )
        except Exception as exc:  # pragma: no cover
            logger.warning("MFAPI history failed for %s: %s", code, exc)
            return self._error_payload(identity, str(exc))

    # ── search ──────────────────────────────────────────────────────

    def search(self, query: str, **kwargs: Any) -> List[SecurityIdentity]:
        if not _HAS_REQUESTS:
            return []
        try:
            resp = _requests.get(f"{self._base_url}/mf/search", params={"q": query}, timeout=self._timeout())
            resp.raise_for_status()
            rows = resp.json() or []
            out: List[SecurityIdentity] = []
            for row in rows:
                code = row.get("schemeCode")
                name = row.get("schemeName", "")
                if not code:
                    continue
                out.append(
                    SecurityIdentity(
                        symbol=str(code),
                        scheme_code=str(code),
                        name=str(name),
                        currency="INR",
                        kind=None,
                    )
                )
            return out
        except Exception as exc:  # pragma: no cover
            logger.warning("MFAPI search failed for %r: %s", query, exc)
            return []

    # ── helpers ─────────────────────────────────────────────────────

    def _timeout(self) -> int:
        return int(self._config.get("timeout_seconds", 15))

    def _error_payload(self, identity: SecurityIdentity, error: str) -> ProviderPayload:
        return ProviderPayload(
            provider=self.name,
            identity=identity,
            success=False,
            error=error,
        )


def _parse_mfapi_date(raw: Any) -> date | None:
    if not raw:
        return None
    try:
        if isinstance(raw, datetime):
            return raw.date()
        if isinstance(raw, date):
            return raw
        return date.fromisoformat(str(raw)[:10])
    except ValueError:
        return None


def _dedupe(points: List[DataPoint]) -> List[DataPoint]:
    seen: Dict[date, float] = {}
    for p in points:
        seen[p.date] = p.value
    return [DataPoint(date=d, value=v) for d, v in sorted(seen.items())]

