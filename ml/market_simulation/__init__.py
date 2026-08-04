"""Market Simulation (PART 5).

Applies synthetic users to real historical market data. Supports:

* **Data source**: real historical data (via ``yfinance`` if available)
  with a built-in deterministic static seed for offline environments.
* **Assets**: Nifty, Sensex, Gold, Bond Yields, FD Rates, Inflation,
  Repo Rate, International ETFs.
* **Regime detection**: identify bull / bear / sideways / crisis
  regimes from return series (for feature engineering & scenario
  analysis).
* **Return sampling**: generate correlated return paths for synthetic
  portfolios.

This module never replaces the deterministic investment engine — it
*feeds* realistic market paths into the recommendation simulation,
portfolio evolution and dataset builder.
"""

from ml.market_simulation.market_data import (  # noqa: F401
    MarketDataProvider,
    StaticMarketDataProvider,
    get_static_config,
    compute_historical_returns,
)
from ml.market_simulation.regimes import (  # noqa: F401
    MarketRegime,
    RegimeDetector,
    detect_regime,
    regime_from_return_series,
)
from ml.market_simulation.sampler import (  # noqa: F401
    MarketReturnSampler,
    sample_monthly_returns,
)

__all__ = [
    "MarketDataProvider",
    "StaticMarketDataProvider",
    "get_static_config",
    "compute_historical_returns",
    "MarketRegime",
    "RegimeDetector",
    "detect_regime",
    "regime_from_return_series",
    "MarketReturnSampler",
    "sample_monthly_returns",
]
