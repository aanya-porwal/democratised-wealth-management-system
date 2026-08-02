"""Financial health score models.

These complement the root-level ``health_engine.FinancialHealth`` with a
richer per-factor breakdown, strengths/weaknesses lists and improvement
suggestions.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class HealthFactorScore:
    """One factor's contribution to the overall health score.

    Attributes
    ----------
    name:
        Factor key (e.g. ``"emergency_fund"``).
    score:
        Points earned for this factor (0..max_points).
    max_points:
        The maximum points available for this factor.
    severity:
        ``"good"``, ``"warning"`` or ``"critical"``.
    message:
        Plain-language explanation of the factor's score.
    """

    name: str
    score: float
    max_points: float
    severity: str
    message: str

    @property
    def percentage(self) -> float:
        """Fraction of the available points earned (0..1)."""
        if self.max_points <= 0:
            return 0.0
        return min(self.score / self.max_points, 1.0)


@dataclass
class HealthScoreResult:
    """The complete 0-100 health assessment with explanations.

    Attributes
    ----------
    score:
        Overall score (0..100).
    grade:
        ``excellent`` / ``good`` / ``fair`` / ``poor`` / ``critical``.
    factors:
        Per-factor breakdown used for explainability.
    strengths:
        Human-readable list of what the user is doing well.
    weaknesses:
        Human-readable list of what needs attention.
    suggestions:
        Actionable improvement suggestions.
    """

    score: int
    grade: str
    factors: list[HealthFactorScore] = field(default_factory=list)
    strengths: list[str] = field(default_factory=list)
    weaknesses: list[str] = field(default_factory=list)
    suggestions: list[str] = field(default_factory=list)
