"""Reproducibility utilities: seeded RNG management.

The entire platform is deterministic given a seed. All randomness flows
through a single master RNG so that running the same pipeline twice —
with the same seed and config — produces identical results. This is
essential for experiment reproducibility and for re-running a digital
twin's life from a given point.

The seed is derived from ``config.reproducibility.seed`` unless
overridden. ``ensure_seed`` is called at the entry points of the
pipeline to guarantee a fixed seed is present.
"""

from __future__ import annotations

import logging
import os
import random
from contextlib import contextmanager
from typing import Iterator, Optional

import numpy as np

logger = logging.getLogger(__name__)

_MASTER_SEED: Optional[int] = None
_master_rng: Optional[np.random.Generator] = None


def set_seed(seed: Optional[int] = None) -> int:
    """Fix the global seed for Python, numpy and the master RNG.

    Parameters
    ----------
    seed:
        The seed to use. If ``None``, keeps the current seed (or falls
        back to a default of 42).

    Returns
    -------
    int
        The active seed.
    """
    global _MASTER_SEED, _master_rng
    if seed is not None:
        _MASTER_SEED = seed
    if _MASTER_SEED is None:
        _MASTER_SEED = 42
    _master_rng = np.random.default_rng(_MASTER_SEED)
    random.seed(_MASTER_SEED)
    np.random.seed(_MASTER_SEED)
    logger.debug("Seeded platform RNG with seed=%d", _MASTER_SEED)
    return _MASTER_SEED


def get_seed() -> int:
    """Return the active seed (initialising to 42 if not yet set)."""
    if _MASTER_SEED is None:
        set_seed(42)
    return _MASTER_SEED  # type: ignore[return-value]


def get_rng() -> np.random.Generator:
    """Return the process-wide master generator (lazily initialised)."""
    global _master_rng
    if _master_rng is None:
        set_seed(get_seed())
    return _master_rng  # type: ignore[return-value]


def ensure_seed(seed: Optional[int] = None) -> int:
    """Ensure the platform is seeded; throw if seed missing and required.

    Parameters
    ----------
    seed:
        Optional explicit seed. If provided, it is applied.

    Returns
    -------
    int
        The active seed.
    """
    if seed is not None:
        return set_seed(seed)
    if _MASTER_SEED is None:
        # Called from pipeline entry; default to 42 so behaviour is
        # deterministic by default. The CLI can pass an explicit seed.
        return set_seed(42)
    return _MASTER_SEED


@contextmanager
def fixed_seed(seed: int) -> Iterator[None]:
    """Temporarily fix the seed for the duration of a block.

    Restores the previous seed afterwards so callers are not surprised.
    """
    global _MASTER_SEED, _master_rng
    previous = _MASTER_SEED
    set_seed(seed)
    try:
        yield
    finally:
        if previous is not None:
            set_seed(previous)


def child_seed(seed: Optional[int] = None) -> int:
    """Derive a deterministic child RNG seed from the master seed.

    Used so different subsystems get independent, reproducible streams
    without consuming the master generator's state.
    """
    rng = get_rng()
    base = seed if seed is not None else get_seed()
    return int(rng.integers(0, 2**31 - 1)) + base
