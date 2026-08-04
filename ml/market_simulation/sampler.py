"""Correlated market-return sampling (PART 5 support).

Generates synthetic monthly return paths for a set of assets using the
correlation structure from :class:`StaticMarketDataProvider`. These
paths are used to evolve synthetic portfolios under realistic market
conditions without touching the deterministic engine.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence

import numpy as np
import pandas as pd

from ml.market_simulation.market_data import StaticMarketDataProvider
from ml.utils.seeding import get_rng


@dataclass
class MarketReturnSampler:
    """Sample correlated monthly returns for a universe of assets.

    Parameters
    ----------
    assets:
        Asset keys to sample. Defaults to the full static universe.
    provider:
        A :class:`StaticMarketDataProvider` (or anything exposing
        ``get_annualized_stats`` and ``get_correlation_matrix``).
    """

    assets: Optional[List[str]] = None
    provider: Optional[StaticMarketDataProvider] = None

    def __post_init__(self) -> None:
        self._provider = self.provider or StaticMarketDataProvider()
        if self.assets is None:
            self.assets = self._provider.available_assets()

    def sample(self, n_months: int) -> pd.DataFrame:
        """Sample ``n_months`` of correlated monthly returns.

        Returns
        -------
        pd.DataFrame
            Rows = months, columns = asset keys, values = monthly return.
        """
        rng = get_rng()
        names = self.assets or []
        if not names:
            raise ValueError("no assets to sample")

        means = np.array(
            [self._provider.get_annualized_stats(a)[0] / 12.0 for a in names]
        )
        vols = np.array(
            [self._provider.get_annualized_stats(a)[1] / np.sqrt(12.0) for a in names]
        )
        corr = self._provider.get_correlation_matrix(names)
        # Ensure the correlation matrix is PSD.
        corr = _nearest_psd(corr)
        normal = rng.multivariate_normal(np.zeros(len(names)), corr, size=n_months)
        monthly_returns = normal * vols + means
        return pd.DataFrame(monthly_returns, columns=names)

    def sample_trajectories(
        self, n_months: int, n_paths: int
    ) -> List[pd.DataFrame]:
        """Sample multiple independent return paths (for scenario use)."""
        return [self.sample(n_months) for _ in range(n_paths)]


def _nearest_psd(matrix: np.ndarray, eps: float = 1e-8) -> np.ndarray:
    """Return the nearest positive semi-definite matrix (eigen clipping)."""
    eigvals, eigvecs = np.linalg.eigh((matrix + matrix.T) / 2.0)
    eigvals = np.clip(eigvals, 0.0, None)
    rebuilt = (eigvecs * eigvals) @ eigvecs.T
    # Re-normalise diagonal to 1 (correlation matrix).
    d = np.sqrt(np.diag(rebuilt))
    d[d == 0] = 1.0
    rebuilt = rebuilt / np.outer(d, d)
    rebuilt = (rebuilt + rebuilt.T) / 2.0
    # Add jitter to keep strictly positive definite for sampling.
    return rebuilt + eps * np.eye(rebuilt.shape[0])


def sample_monthly_returns(
    assets: Optional[List[str]] = None,
    n_months: int = 120,
) -> pd.DataFrame:
    """Convenience wrapper for :meth:`MarketReturnSampler.sample`."""
    return MarketReturnSampler(assets=assets).sample(n_months)
