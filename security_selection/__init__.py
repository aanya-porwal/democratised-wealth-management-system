"""Security Selection & Investment Research Platform.

A plugin-based, provider-independent, asset-class-agnostic engine that
operates AFTER the strategic asset-allocation step. It discovers
eligible securities for a target asset class, retrieves live data from
free public sources, validates/normalizes it, computes metrics, applies
factor scoring, ranks candidates, constructs a single- or multi-security
portfolio, generates an institutional research report and persists the
decision for reproducibility.

The package is deliberately independent:
  * no imports from ``app`` (the FastAPI backend)
  * no SQLAlchemy / network at import time
  * providers are injected and can be mocked in tests
  * every tunable constant lives in ``config/config.yaml``

New asset classes are added by implementing a new :class:`BaseEvaluator`
subclass and registering it — the core engine never changes.
"""

from __future__ import annotations

__version__ = "1.0.0"

