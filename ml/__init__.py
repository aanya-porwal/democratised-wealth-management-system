"""Intelligent Learning & Simulation Platform.

A complete, modular ML platform for the Wealth Management System. It
generates realistic synthetic Indian households, simulates their entire
financial life via a persistent **Digital Twin** engine, augments real
market data, trains and evaluates a broad suite of ML models, tracks
experiments, registers champions, and safely deploys models in shadow
mode alongside the authoritative rule engine.

Design principles
-----------------
* **Deterministic calculations are never replaced.** The ML layer only
  *augments* recommendations, behaviour prediction, security ranking,
  user segmentation and recommendation timing. All deterministic
  financial mathematics live in ``wealth_management_system`` /
  ``engine`` and are untouched.
* **Event-sourced Digital Twins.** Every synthetic person becomes a
  persistent, replayable twin. Every change is an immutable, timestamped
  event; history is never overwritten.
* **Statistical realism.** Synthetic profiles are generated from
  statistical distributions with an explicit correlation structure
  (Gaussian copula), not random values.
* **Modular & replaceable.** Every component is independently
  replaceable and follows the ``get_config`` typed-config pattern used
  by ``security_selection`` and the core engine.
* **Graceful degradation.** Heavy ML libraries (xgboost, lightgbm,
  catboost, shap, mlflow) are optional and lazily imported, with pure
  scikit-learn / JSON fallbacks so the platform runs end-to-end even on
  a clean environment.
"""

from __future__ import annotations

__version__ = "1.0.0"
