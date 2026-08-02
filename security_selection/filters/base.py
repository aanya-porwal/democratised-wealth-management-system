"""Base filter interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict

from security_selection.models.pipeline import CandidateSecurity


@dataclass(frozen=True)
class FilterResult:
    """The outcome of one filter for one candidate."""

    passed: bool
    reason: str | None = None


class BaseFilter(ABC):
    """A single configurable filter over candidates.

    Filters are pure: given a candidate and an overrides dict they return
    a :class:`FilterResult`. Overrides let users relax/tighten limits.
    """

    name: str = "base"

    def __init__(self, defaults: Any) -> None:
        self._defaults = defaults

    @abstractmethod
    def check(
        self, candidate: CandidateSecurity, overrides: Dict[str, Any]
    ) -> FilterResult:
        """Check a candidate against this filter's configured limits."""

    # ── helper ──────────────────────────────────────────────────────

    def _limit(
        self, overrides: Dict[str, Any], key: str, default: Any
    ) -> Any:
        """Return the user override when provided, else the configured default."""
        return overrides.get(key, default)

    def _metric(self, candidate: CandidateSecurity, name: str) -> Any:
        return candidate.metrics.get(name)

    def _profile(self, candidate: CandidateSecurity, attr: str) -> Any:
        profile = candidate.profile
        if profile is None:
            return None
        return getattr(profile, attr, None)

