"""Evaluator registry — maps target asset classes to evaluators.

The core engine (``SelectionService``) only ever asks the registry for an
evaluator. Adding a new asset class means registering a new evaluator;
no core code changes.
"""

from __future__ import annotations

import logging
from typing import Dict, List, Type

from security_selection.base.evaluator import BaseEvaluator
from security_selection.models.enums import TargetAssetClass

logger = logging.getLogger(__name__)


class RegistryError(Exception):
    """Raised when no evaluator is registered for a target asset class."""


class EvaluatorRegistry:
    """A registry of evaluator instances keyed by :class:`TargetAssetClass`.

    Multiple evaluators may serve one target class (e.g. both an ETF
    evaluator and a mutual-fund evaluator serve ``LARGE_CAP_EQUITY``); the
    registry holds an ordered list per target.
    """

    def __init__(self) -> None:
        self._registry: Dict[TargetAssetClass, List[BaseEvaluator]] = {}

    def register(
        self,
        target: TargetAssetClass,
        evaluator: BaseEvaluator,
    ) -> None:
        """Register an evaluator instance for a target asset class."""
        self._registry.setdefault(target, []).append(evaluator)
        logger.info(
            "registered evaluator %s for target %s",
            type(evaluator).__name__,
            target.value,
        )

    def has(self, target: TargetAssetClass) -> bool:
        return target in self._registry and bool(self._registry[target])

    def get(self, target: TargetAssetClass) -> List[BaseEvaluator]:
        """Return the evaluator instances registered for a target class."""
        if not self.has(target):
            raise RegistryError(f"no evaluator registered for target asset class {target.value}")
        return list(self._registry[target])

    def first(self, target: TargetAssetClass) -> BaseEvaluator:
        """Return the primary evaluator instance for a target class."""
        instances = self.get(target)
        return instances[0]

    def targets(self) -> List[TargetAssetClass]:
        return sorted(self._registry.keys(), key=lambda t: t.value)

    def clear(self) -> None:
        self._registry.clear()

