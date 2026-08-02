"""Scoring engine — applies the configured scoring model to candidates.

The engine is model-agnostic: it uses whatever ``IScoringModel`` is
provided (default :class:`WeightedScoreModel`). This is the seam where a
future ML model plugs in without touching the evaluators or the pipeline.
"""

from __future__ import annotations

from typing import List, Optional

from security_selection.config import ScoringConfig
from security_selection.models.pipeline import CandidateSecurity
from security_selection.scoring.models import IScoringModel, WeightedScoreModel


class ScoringEngine:
    """Scores candidates using an :class:`IScoringModel`."""

    def __init__(
        self,
        config: ScoringConfig,
        model: Optional[IScoringModel] = None,
    ) -> None:
        self._config = config
        self._model = model or WeightedScoreModel(
            weights=dict(config.factor_weights),
            scale=config.score_scale,
        )

    @property
    def model(self) -> IScoringModel:
        return self._model

    def score(self, candidate: CandidateSecurity) -> tuple[list, float]:
        """Score one candidate; returns (factor_scores, overall)."""
        factor_scores, overall = self._model.score(candidate)
        return factor_scores, overall

