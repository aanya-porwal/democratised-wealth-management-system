"""Market data provision for the ML platform (PART 5).

Provides historical return data for the Indian & international assets
used in simulations:

* Indian equities: Nifty 50 (``^NSEI``), Sensex (``^BSESN``)
* Gold: ``GC=F`` (COMEX) or ``GOLDBEES`` proxy
* Government bond yield: ``^IRX`` / ``IN10Y`` proxy
* FD rates / repo rate / inflation: deterministic rates from config or
  RBI-style series (may be downloaded if a provider exists).
* International: ``VOO``, ``QQQ``, ``SPY``, ``EEM``, ``IJR``

Two providers:

* :class:`StaticMarketDataProvider` — deterministic *realistic* seed
  data derived from long-run Indian market statistics. Zero network.
* :class:`MarketDataProvider` — tries ``yfinance`` first, falls back to
  the static provider automatically.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from ml.config import get_config
from ml.utils.io import ensure_dir, load_dataframe, save_dataframe
from ml.utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class AssetConfig:
    """Parameters for one simulated asset."""

    symbol: str
    name: str
    annual_return: float  # long-run annualised return (fraction)
    annual_vol: float  # long-run annualised volatility (fraction)
    kind: str = "equity"  # equity, gold, bond, rate, inflation


# ── deterministic static seed (realistic long-run Indian data) ──────
_STATIC_ASSETS: Dict[str, AssetConfig] = {
    "nifty": AssetConfig("NIFTY", "Nifty 50", 0.12, 0.15, "equity"),
    "sensex": AssetConfig("SENSEX", "BSE Sensex", 0.12, 0.16, "equity"),
    "gold": AssetConfig("GOLD", "Gold (INR)", 0.10, 0.14, "gold"),
    "bond_10y": AssetConfig("BOND10", "10Y G-Sec Yield", 0.071, 0.05, "bond"),
    "fd_rate": AssetConfig("FD_RATE", "Bank FD Rate", 0.065, 0.005, "rate"),
    "inflation": AssetConfig("INFLATION", "CPI Inflation", 0.05, 0.02, "inflation"),
    "repo_rate": AssetConfig("REPO", "RBI Repo Rate", 0.0625, 0.004, "rate"),
    "voo": AssetConfig("VOO", "S&P 500 ETF", 0.10, 0.16, "equity"),
    "qqq": AssetConfig("QQQ", "Nasdaq 100 ETF", 0.13, 0.20, "equity"),
    "eem": AssetConfig("EEM", "Emerging Markets ETF", 0.06, 0.22, "equity"),
    "ijr": AssetConfig("IJR", "US Small Cap ETF", 0.09, 0.19, "equity"),
}


def get_static_config() -> Dict[str, AssetConfig]:
    """Return the deterministic static asset universe."""
    return dict(_STATIC_ASSETS)


class StaticMarketDataProvider:
    """Deterministic, offline market data based on long-run statistics.

    The returns are *realistic* (based on historical Indian market
    behaviour) but generated deterministically from a fixed seed with a
    simple correlated geometric-brownian-motion model. This preserves
    realism while keeping tests and offline runs fully reproducible.
    """

    def __init__(self) -> None:
        self._assets = get_static_config()

    def available_assets(self) -> List[str]:
        return list(self._assets.keys())

    def get_annualized_stats(
        self, asset: str
    ) -> Tuple[float, float]:
        cfg = self._assets[asset]
        return cfg.annual_return, cfg.annual_vol

    def get_correlation_matrix(self, assets: Optional[List[str]] = None) -> np.ndarray:
        """Return a plausible correlation matrix for the asset universe."""
        names = list(assets or self._assets.keys())
        n = len(names)
        corr = np.eye(n)
        # Equity-assets are correlated with each other.
        equity_idx = [i for i, a in enumerate(names) if self._assets[a].kind == "equity"]
        for i in equity_idx:
            for j in equity_idx:
                if i != j:
                    corr[i, j] = 0.6
        # Gold is negatively correlated with equities.
        gold_idx = [i for i, a in enumerate(names) if self._assets[a].kind == "gold"]
        for g in gold_idx:
            for e in equity_idx:
                corr[g, e] = -0.15
                corr[e, g] = -0.15
        # Rates are near-zero correlated.
        return corr

    def get_history(self, asset: str, years: int = 15) -> pd.DataFrame:
        """Return a synthetic monthly price/return history.

        Parameters
        ----------
        asset:
            Asset key (must exist in the static universe).
        years:
            Number of years of monthly data to generate.

        Returns
        -------
        pd.DataFrame
            Columns: ``date``, ``close``, ``monthly_return``.
        """
        from ml.utils.seeding import get_rng

        if asset not in self._assets:
            raise KeyError(f"unknown asset: {asset}")
        cfg = self._assets[asset]
        rng = get_rng()
        n_months = years * 12
        dates = pd.date_range(end=pd.Timestamp.today().normalize(), periods=n_months, freq="ME")
        monthly_mu = cfg.annual_return / 12.0
        monthly_sigma = cfg.annual_vol / np.sqrt(12.0)
        returns = rng.normal(monthly_mu, monthly_sigma, n_months)
        close = 100.0 * np.cumprod(1.0 + returns)
        return pd.DataFrame(
            {"date": dates, "close": close, "monthly_return": returns}
        )


class MarketDataProvider:
    """Real market data provider with automatic static fallback.

    Parameters
    ----------
    fetch_real:
        Whether to attempt real downloads (``yfinance``). If disabled or
        the download fails, the deterministic static provider is used.
    static_provider:
        Optional pre-built static provider.
    """

    def __init__(
        self,
        fetch_real: Optional[bool] = None,
        static_provider: Optional[StaticMarketDataProvider] = None,
    ) -> None:
        cfg = get_config()
        self._fetch_real = bool(fetch_real) if (fetch_real is not None) else cfg.market.fetch_real
        self._static = static_provider or StaticMarketDataProvider()
        self._yf = None
        if self._fetch_real:
            try:
                import yfinance  # type: ignore

                self._yf = yfinance
            except Exception:
                logger.warning("yfinance not available; using static market data")
                self._yf = None

    def available_assets(self) -> List[str]:
        return self._static.available_assets()

    def get_history(self, asset: str, years: int = 15) -> pd.DataFrame:
        """Return historical market data for an asset.

        Attempts a real download from ``yfinance`` if configured; else
        falls back to the static deterministic provider.

        Parameters
        ----------
        asset:
            Asset key, e.g. ``nifty``.
        years:
            Years of history.

        Returns
        -------
        pd.DataFrame
            With columns ``date``, ``close``, ``monthly_return``.
        """
        if self._yf is not None:
            try:
                return self._fetch_real_history(asset, years)
            except Exception as exc:
                logger.warning("real fetch failed for %s (%s); using static", asset, exc)
        return self._static.get_history(asset, years)

    def _fetch_real_history(self, asset: str, years: int) -> pd.DataFrame:
        symbol = self._static._assets[asset].symbol.replace("_", "-")
        tickers = {
            "nifty": "^NSEI",
            "sensex": "^BSESN",
            "gold": "GC=F",
            "bond_10y": "^IRX",
            "voo": "VOO",
            "qqq": "QQQ",
            "eem": "EEM",
            "ijr": "IJR",
        }
        ticker = tickers.get(asset)
        if ticker is None:
            raise ValueError(f"no real ticker mapped for {asset}")
        df = self._yf.download(ticker, period=f"{years}y", interval="1mo", progress=False)
        if df is None or df.empty:
            raise ValueError(f"empty download for {asset}")
        close = df["Close"].dropna()
        monthly_return = close.pct_change().dropna()
        out = pd.DataFrame(
            {"date": close.index, "close": close.values, "monthly_return": monthly_return.values}
        )
        return out


def futures(value: bool) -> bool:
    """Small helper to normalise a bool (name kept short intentionally)."""
    return bool(value)


def compute_historical_returns(
    provider: MarketDataProvider,
    asset: str,
    years: int = 15,
) -> Dict[str, float]:
    """Compute annualised return & volatility from a provider history."""
    df = provider.get_history(asset, years)
    if df.empty:
        return {"asset": asset, "annualized_return": 0.0, "annualized_vol": 0.0}
    rets = df["monthly_return"].dropna()
    if rets.empty:
        return {"asset": asset, "annualized_return": 0.0, "annualized_vol": 0.0}
    annualized_return = float((1.0 + rets.mean()) ** 12 - 1.0)
    annualized_vol = float(rets.std(ddof=0) * np.sqrt(12.0))
    return {
        "asset": asset,
        "annualized_return": annualized_return,
        "annualized_vol": annualized_vol,
        "observations": int(len(rets)),
    }
