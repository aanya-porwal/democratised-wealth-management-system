"""Custom exception hierarchy for the wealth management system.

Every engine raises domain-specific exceptions so callers can catch
precisely the failure they care about without depending on string
matching. All exceptions derive from a common :class:`WealthManagementError`
base, which itself subclasses ``ValueError`` so existing ``try/except
ValueError`` blocks in legacy code continue to work.
"""

from __future__ import annotations

from typing import Any, Optional


class WealthManagementError(ValueError):
    """Base class for every exception raised by this package."""

    def __init__(
        self,
        message: str,
        *,
        code: Optional[str] = None,
        details: Optional[dict[str, Any]] = None,
    ) -> None:
        """Initialise the error.

        Parameters
        ----------
        message:
            Human-readable description of the failure.
        code:
            Machine-readable error code (e.g. ``"invalid_goal"``).
        details:
            Optional structured context (e.g. the offending goal).
        """
        super().__init__(message)
        self.message = message
        self.code = code
        self.details = details or {}

    def __str__(self) -> str:  # pragma: no cover - trivial
        if self.code:
            return f"[{self.code}] {self.message}"
        return self.message


class ConfigurationError(WealthManagementError):
    """Raised when configuration cannot be loaded or is invalid."""

    code_default = "config_error"

    def __init__(self, message: str, **kwargs: Any) -> None:
        kwargs.setdefault("code", self.code_default)
        super().__init__(message, **kwargs)


class ValidationError(WealthManagementError):
    """Raised when inputs to an engine violate its invariants."""

    code_default = "validation_error"

    def __init__(self, message: str, **kwargs: Any) -> None:
        kwargs.setdefault("code", self.code_default)
        super().__init__(message, **kwargs)


class GoalError(WealthManagementError):
    """Raised for invalid goal definitions or unsupported goal math."""

    code_default = "goal_error"

    def __init__(self, message: str, **kwargs: Any) -> None:
        kwargs.setdefault("code", self.code_default)
        super().__init__(message, **kwargs)


class SimulationError(WealthManagementError):
    """Raised when a simulation request is invalid (e.g. too few paths)."""

    code_default = "simulation_error"

    def __init__(self, message: str, **kwargs: Any) -> None:
        kwargs.setdefault("code", self.code_default)
        super().__init__(message, **kwargs)


class OptimizationError(WealthManagementError):
    """Raised when an optimizer cannot find a feasible solution."""

    code_default = "optimization_error"

    def __init__(self, message: str, **kwargs: Any) -> None:
        kwargs.setdefault("code", self.code_default)
        super().__init__(message, **kwargs)


class AllocationError(WealthManagementError):
    """Raised when an allocation request cannot be satisfied."""

    code_default = "allocation_error"

    def __init__(self, message: str, **kwargs: Any) -> None:
        kwargs.setdefault("code", self.code_default)
        super().__init__(message, **kwargs)


class RebalancingError(WealthManagementError):
    """Raised when a rebalancing request is invalid."""

    code_default = "rebalancing_error"

    def __init__(self, message: str, **kwargs: Any) -> None:
        kwargs.setdefault("code", self.code_default)
        super().__init__(message, **kwargs)

