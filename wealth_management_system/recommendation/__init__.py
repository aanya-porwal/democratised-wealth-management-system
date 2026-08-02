"""Explainable recommendation engine.

Produces tax-aware, goal-aware instrument and allocation recommendations,
each with a confidence level and a list of plain-language reasons so the
user understands *why* a product was chosen.

The legacy ``recommendation_engine`` continues to power the raw
instrument ranking; this package adds the explainability layer on top.
"""

from wealth_management_system.recommendation.engine import RecommendationEngine

__all__ = ["RecommendationEngine"]

