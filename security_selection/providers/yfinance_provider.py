"""yfinance provider — free market data for stocks, ETFs, REITs, InvITs.

Uses the open-source ``yfinance`` package (Yahoo Finance data). When the
package is not installed, the provider degrades gracefully and reports
the security as unsupported rather than crashing the pipeline.
"""

from __future__ import annotations

import logging
from datetime import date, datetime, timezone
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

try:  # pragma: no cover - optional dependency
    import yfinance as _yf  # type: ignore

    _HAS_YFINANCE = True
except Exception:  # pragma: no cover
    _yf = None
    _HAS_YFINANCE = False

# security kinds yfinance can serve
_SUPPORTED_KINDS = {
    "etf",
    "stock",
    "gold_etf",
    "reit",
    "invit",
    "international_etf",
    "corporate_bond",
    "government_bond",
}


class YFinanceProvider(BaseDataProvider):
    """Free Yahoo Finance data via the yfinance package."""

    name = ProviderName.YFINANCE

    def __init__(self, **config: Any) -> None:
        super().__init__(**config)
        self._max_history_years = int(config.get("max_history_years", 10) or 10)

    def supports(self, identity: SecurityIdentity) -> bool:
        if not _HAS_YFINANCE:
            return False
        if not self.enabled:
            return False
        kind = identity.kind.value if identity.kind else ""
        if kind not in _SUPPORTED_KINDS:
            return False
        return bool(identity.symbol)

    # ── snapshot ────────────────────────────────────────────────────

    def fetch_snapshot(self, identity: SecurityIdentity) -> ProviderPayload:
        if not _HAS_YFINANCE:
            return self._error_payload(identity, "yfinance is not installed")
        try:
            ticker = _yf.Ticker(identity.symbol)
            info = ticker.info or {}
            hist = ticker.history(period="5d")
            last = None
            if hist is not None and not hist.empty:
                last = hist["Close"].iloc[-1]
            current = safe_float(info.get("currentPrice") or info.get("regularMarketPrice") or last)
            snapshot = MarketSnapshot(
                identity=identity,
                current_price=current,
                as_of=datetime.now(timezone.utc),
                currency=str(info.get("currency") or "INR"),
                volume=safe_float(info.get("volume")),
                average_volume=safe_float(info.get("averageVolume")),
                market_cap=safe_float(info.get("marketCap")),
                aum=safe_float(info.get("totalAssets")),
                extra={k: v for k, v in info.items() if isinstance(v, (int, float, str))},
            )
            return ProviderPayload(
                provider=self.name,
                identity=identity,
                snapshot=snapshot,
                metrics=self._extract_metrics(info),
                success=True,
            )
        except Exception as exc:  # pragma: no cover
            logger.warning("yfinance snapshot failed for %s: %s", identity.symbol, exc)
            return self._error_payload(identity, str(exc))

    # ── history ─────────────────────────────────────────────────────

    def fetch_history(
        self,
        identity: SecurityIdentity,
        start: date | None = None,
        end: date | None = None,
    ) -> ProviderPayload:
        if not _HAS_YFINANCE:
            return self._error_payload(identity, "yfinance is not installed")
        try:
            start = start or self.default_start()
            end = end or date.today()
            ticker = _yf.Ticker(identity.symbol)
            hist = ticker.history(start=start.isoformat(), end=end.isoformat())
            if hist is None or hist.empty:
                return self._error_payload(identity, "no price history returned")
            points = []
            for idx, row in hist.iterrows():
                value = safe_float(row.get("Close"))
                if value is None:
                    continue
                ts = idx
                if hasattr(ts, "date"):
                    d = ts.date() if isinstance(ts, datetime) else ts
                else:
                    d = date.fromisoformat(str(ts)[:10])
                points.append(DataPoint(date=d, value=value))
            points = _dedupe_points(points)
            series = HistoricalSeries(points=points, source=DataSource.LIVE, currency="INR")
            return ProviderPayload(
                provider=self.name,
                identity=identity,
                history=series,
                success=True,
            )
        except Exception as exc:  # pragma: no cover
            logger.warning("yfinance history failed for %s: %s", identity.symbol, exc)
            return self._error_payload(identity, str(exc))

    # ── search ──────────────────────────────────────────────────────

    def search(self, query: str, **kwargs: Any) -> List[SecurityIdentity]:
        if not _HAS_YFINANCE:
            return []
        try:
            results = _yf.Search(query, max_results=10, news_count=0)  # type: ignore
            quotes = getattr(results, "quotes", []) or []
            out: List[SecurityIdentity] = []
            for q in quotes:
                symbol = q.get("symbol") or q.get("shortname")
                if not symbol:
                    continue
                out.append(
                    SecurityIdentity(
                        symbol=str(symbol),
                        name=str(q.get("shortname") or q.get("longname") or ""),
                        exchange=q.get("exchange"),
                        kind=None,
                    )
                )
            return out
        except Exception as exc:  # pragma: no cover
            logger.warning("yfinance search failed for %r: %s", query, exc)
            return []

    # ── metrics ─────────────────────────────────────────────────────

    def fetch_metrics(self, identity: SecurityIdentity) -> Dict[str, Any]:
        if not _HAS_YFINANCE:
            return {}
        try:
            info = _yf.Ticker(identity.symbol).info or {}
            return self._extract_metrics(info)
        except Exception as exc:  # pragma: no cover
            logger.warning("yfinance metrics failed for %s: %s", identity.symbol, exc)
            return {}

    def fetch_holdings(self, identity: SecurityIdentity) -> List[Dict[str, Any]]:
        if not _HAS_YFINANCE:
            return []
        try:
            ticker = _yf.Ticker(identity.symbol)
            top = ticker.funds_data.top_holdings if hasattr(ticker, "funds_data") else None
            if top is None or top.empty:
                return []
            rows: List[Dict[str, Any]] = []
            for _, row in top.head(20).iterrows():
                rows.append(
                    {
                        "symbol": str(row.get("Symbol") or row.get("symbol") or ""),
                        "name": str(row.get("Holding") or row.get("name") or ""),
                        "weight": safe_float(row.get("% of Portfolio") or row.get("weight")),
                    }
                )
            return rows
        except Exception as exc:  # pragma: no cover
            logger.warning("yfinance holdings failed for %s: %s", identity.symbol, exc)
            return []

    def fetch_sector_allocations(self, identity: SecurityIdentity) -> Dict[str, float]:
        if not _HAS_YFINANCE:
            return {}
        try:
            ticker = _yf.Ticker(identity.symbol)
            sectors = ticker.funds_data.sector_weightings if hasattr(ticker, "funds_data") else None
            if sectors is None or sectors.empty:
                return {}
            out: Dict[str, float] = {}
            for name, value in sectors.items():
                flat = float(value) if isinstance(value, (int, float)) else None
                if flat is not None:
                    out[str(name)] = flat
            return out
        except Exception as exc:  # pragma: no cover
            logger.warning("yfinance sectors failed for %s: %s", identity.symbol, exc)
            return {}

    # ── helpers ─────────────────────────────────────────────────────

    @staticmethod
    def _extract_metrics(info: Dict[str, Any]) -> Dict[str, Any]:
        """Pull the most useful fields from a yfinance info dict."""
        keep = [
            "expenseRatio", "annualReportExpenseRatio", "fundFamily",
            "category", "navPrice", "totalAssets", "yield", "dividendYield",
            "trailingPE", "forwardPE", "priceToBook", "returnOnEquity",
            "debtToEquity", "beta", "sharesOutstanding", "bid", "ask",
        ]
        out: Dict[str, Any] = {}
        for key in keep:
            if key in info and info[key] is not None:
                out[key] = info[key]
        if "fundFamily" in out:
            out["fund_house"] = out.pop("fundFamily")
        if "expenseRatio" in out:
            out["expense_ratio"] = out.pop("expenseRatio")
        if "totalAssets" in out:
            # yfinance reports USD for US funds; convert to crore INR approx
            assets_usd = safe_float(out.pop("totalAssets"))
            out["aum_crore"] = round(assets_usd * 0.0001 * 83, 2) if assets_usd else None
        if "dividendYield" in out:
            out["dividend_yield"] = out.pop("dividendYield")
        return out


def _dedupe_points(points: List[DataPoint]) -> List[DataPoint]:
    """Remove duplicate dates keeping the latest value."""
    seen: Dict[date, float] = {}
    for p in points:
        seen[p.date] = p.value
    return [DataPoint(date=d, value=v) for d, v in sorted(seen.items())]

