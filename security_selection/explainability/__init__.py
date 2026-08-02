"""Centralized explainability engine.

Evaluators NEVER hand-write explanations. All reasons, strengths,
weaknesses and confidence levels are produced here.
"""

from security_selection.explainability.engine import ExplanationEngine

__all__ = ["ExplanationEngine"]

