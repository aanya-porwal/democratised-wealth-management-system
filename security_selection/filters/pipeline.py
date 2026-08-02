"""Filter pipeline — applies a chain of filters to candidates."""

from __future__ import annotations

import logging
from typing import Any, Dict, List

from security_selection.config import FilterDefaultsConfig
from security_selection.filters.base import BaseFilter
from security_selection.filters.standard import build_standard_filters
from security_selection.models.pipeline import CandidateSecurity

logger = logging.getLogger(__name__)


class FilterPipeline:
    """Runs an ordered set of filters over the candidate universe.

    A candidate passes only if every filter passes. Rejected candidates
    carry the filter reason in ``meta["rejection_reason"]`` so the report
    can explain why a security was excluded.
    """

    def __init__(
        self,
        defaults: FilterDefaultsConfig,
        filters: List[BaseFilter] | None = None,
    ) -> None:
        self._defaults = defaults
        self._filters = filters or build_standard_filters(defaults)

    def apply(
        self,
        candidates: List[CandidateSecurity],
        overrides: Dict[str, Any] | None = None,
    ) -> List[CandidateSecurity]:
        overrides = overrides or {}
        passed: List[CandidateSecurity] = []
        for candidate in candidates:
            rejected_for: List[str] = []
            ok = True
            for filt in self._filters:
                result = filt.check(candidate, overrides)
                if not result.passed:
                    ok = False
                    rejected_for.append(result.reason or filt.name)
                    if len(rejected_for) >= 3:
                        break
            if ok:
                passed.append(candidate)
            else:
                candidate.meta["rejected"] = True
                candidate.meta["rejection_reason"] = "; ".join(rejected_for)
        return passed

    def describe(self) -> List[str]:
        """Return the active filter names for reporting."""
        return [f.name for f in self._filters]

