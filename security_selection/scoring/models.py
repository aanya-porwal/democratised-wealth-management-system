"""Scoring models — the ML-ready prediction interface.

``IScoringModel`` is the interface both the default weighted model and
any future ML model implement. The pipeline never knows which model is
used; swapping the model is a configuration change, not a code change.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List

from security_selection.models.pipeline import CandidateSecurity, FactorScore
from security_selection.scoring.factors import BaseFactor, build_factors
from security_selection.utils.math import clamp


class IScoringModel(ABC):
    """Interface for computing an overall security score."""

    @abstractmethod
    def score(self, candidate: CandidateSecurity) -> tuple[List[FactorScore], float]:
        """Return (per-factor scores, overall score 0..100)."""


@dataclass
class WeightedScoreModel(IScoringModel):
    """Weighted linear factor model (the default).

    Weights come from configuration. Unknown factors are skipped; missing
    weights for registered factors are assigned a tiny epsilon so the sum
    still normalizes.
    """

    weights: Dict[str, float]
    factors: List[BaseFactor] | None = None
    scale: float = 100.0

    def __post_init__(self) -> None:
        if self.factors is None:
            self.factors = build_factors()
        # normalize weights to sum to 1.0
        total = sum(max(0.0, w) for w in self.weights.values())
        self._weights = (
            {k: max(0.0, v) / total for k, v in self.weights.items()}
            if total > 0
            else {}
        )

    def score(self, candidate: CandidateSecurity) -> tuple[List[FactorScore], float]:
        factor_scores: List[FactorScore] = []
        overall = 0.0
        for factor in self.factors:
            weight = self._weights.get(factor.name, 0.0)
            if weight <= 0:
                continue
            raw, details = factor.score(candidate)
            raw = clamp(raw, 0.0, 1.0)
            weighted = raw * weight
            factor_scores.append(
                FactorScore(
                    factor=factor.name,
                    score=round(raw, 4),
                    weight=round(weight, 4),
                    weighted=round(weighted, 4),
                    details=details,
                )
            )
            overall += weighted
        overall = round(overall * self.scale, 2)
        return factor_scores, overall


class FeatureBuilder:
    """Build feature dicts for candidates (ML dataset preparation)."""

    @staticmethod
    def build(candidate: CandidateSecurity) -> Dict[str, Any]:
        from security_selection.utils.feature_builder import FeatureBuilder as _FB

        return _FB.build(candidate)


class DatasetBuilder:
    """Build a flat dataset (list of rows) for ML training/inference."""

    @staticmethod
    def build(candidates: List[CandidateSecurity]) -> List[Dict[str, Any]]:
        from security_selection.utils.feature_builder import FeatureBuilder as _FB

        return _FB.build_matrix(candidates)

    @staticmethod
    def to_csv(candidates: List[CandidateSecurity], path: str) -> None:
        """Persist the dataset to CSV (feature engineering output)."""
        import csv

        rows = DatasetBuilder.build(candidates)
        if not rows:
            return
        with open(path, "w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)

