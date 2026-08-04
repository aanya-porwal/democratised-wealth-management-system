"""Correlation-aware multivariate sampling via a Gaussian copula.

Generating realistic synthetic households requires *correlated* random
variables — e.g. income and education are positively correlated, age and
savings are correlated, risk tolerance correlates with age. Sampling
marginals independently would produce unrealistic profile combinations.

A Gaussian copula lets us:
1. Draw correlated standard-normal vectors (via Cholesky of the
   correlation matrix).
2. Push them through the standard-normal CDF to get uniform ``[0,1]``
   ranks.
3. Feed each uniform rank into the inverse CDF / quantile function of a
   chosen marginal distribution (lognormal, real-valued, etc.).

This preserves the rank correlation between variables while allowing
each to have its own arbitrary marginal distribution.
"""

from __future__ import annotations

from typing import Iterable, List, Sequence, Tuple

import numpy as np

from ml.utils.seeding import get_rng


def build_correlation_matrix(
    variables: Sequence[str],
    matrix: Sequence[Sequence[float]],
) -> np.ndarray:
    """Validate and build a symmetric correlation matrix.

    Parameters
    ----------
    variables:
        Names of the variables (length N).
    matrix:
        An NxN list of lists. Off-diagonal entries are the pairwise
        correlations; diagonals are expected to be 1.0.

    Returns
    -------
    np.ndarray
        A positive semi-definite correlation matrix (N, N).
    """
    n = len(variables)
    if len(matrix) != n:
        raise ValueError(f"correlation matrix must be {n}x{n}, got {len(matrix)} rows")
    arr = np.asarray(matrix, dtype=float)
    if arr.shape != (n, n):
        raise ValueError(f"correlation matrix must be {n}x{n}")
    # Symmetrise (average with transpose) to fix tiny asymmetries.
    arr = (arr + arr.T) / 2.0
    # Clip to diagonal = 1.0.
    np.fill_diagonal(arr, 1.0)
    # Ensure PSD (numerical safety).
    eigvals = np.linalg.eigvalsh(arr)
    if eigvals.min() < 0:
        arr += np.eye(n) * (abs(eigvals.min()) + 1e-6)
    return arr


def correlated_normal_samples(
    corr_matrix: np.ndarray,
    n: int,
    rng: np.random.Generator | None = None,
) -> np.ndarray:
    """Draw correlated standard-normal samples from a correlation matrix.

    Parameters
    ----------
    corr_matrix:
        The (N, N) correlation matrix.
    n:
        Number of samples to draw.
    rng:
        Optional RNG (defaults to the master generator).

    Returns
    -------
    np.ndarray
        Array of shape (n, N) with standard-normal columns correlated
        according to ``corr_matrix``.
    """
    rng = rng or get_rng()
    chol = np.linalg.cholesky(corr_matrix)
    z = rng.standard_normal((n, corr_matrix.shape[0]))
    return z @ chol.T


def sample_gaussian_copula(
    corr_matrix: np.ndarray,
    n: int,
    rng: np.random.Generator | None = None,
) -> np.ndarray:
    """Draw uniform ``[0,1]`` ranks from a Gaussian copula.

    Parameters
    ----------
    corr_matrix:
        The (N, N) correlation matrix.
    n:
        Number of samples to draw.
    rng:
        Optional RNG.

    Returns
    -------
    np.ndarray
        Array of shape (n, N) with each column ~ Uniform(0,1) while
        preserving the rank correlation between columns.
    """
    from scipy.stats import norm

    z = correlated_normal_samples(corr_matrix, n, rng)
    return norm.cdf(z)


def copula_to_marginal(
    uniforms: np.ndarray,
    inverse_cdfs: Sequence[callable],
) -> np.ndarray:
    """Map copula uniform ranks to arbitrary marginals via inverse CDFs.

    Parameters
    ----------
    uniforms:
        Array of shape (n, N) of uniform ranks from the copula.
    inverse_cdfs:
        A sequence of N callables, each ``f(u) -> value`` mapping a
        uniform ``[0,1]`` rank to the marginal's quantile.

    Returns
    -------
    np.ndarray
        The transformed samples, shape (n, N).
    """
    if uniforms.shape[1] != len(inverse_cdfs):
        raise ValueError("number of inverse CDFs must match the number of columns")
    result = np.empty_like(uniforms)
    for j, inv_cdf in enumerate(inverse_cdfs):
        result[:, j] = inv_cdf(uniforms[:, j])
    return result
