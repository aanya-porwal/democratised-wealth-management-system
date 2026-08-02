"""Base tool interface — every tool inherits from BaseTool.

Tools are the ONLY bridge between AI agents and financial engines.
Each tool calls existing services (which route through EngineAdapter).
The AI never performs calculations.
"""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from typing import Any

from app.ai.schemas import ToolResult


class ToolError(Exception):
    """Raised when a tool execution fails."""


class BaseTool(ABC):
    """Abstract tool that exposes execute/validate_input/validate_output."""

    name: str = "base_tool"
    description: str = "Base tool"
    requires_confirmation: bool = False
    requires_db: bool = True

    def __init__(self) -> None:
        self._last_result: ToolResult | None = None

    @abstractmethod
    def execute(self, **kwargs: Any) -> dict[str, Any]:
        """Execute the tool with the given arguments.

        Calls the existing service layer (which routes through EngineAdapter).
        Never performs calculations itself.
        """

    def validate_input(self, **kwargs: Any) -> list[str]:
        """Validate input arguments. Return list of error messages (empty = valid)."""
        errors: list[str] = []
        return errors

    def validate_output(self, result: dict[str, Any]) -> list[str]:
        """Validate the output. Return list of error messages (empty = valid)."""
        errors: list[str] = []
        return errors

    def run(self, **kwargs: Any) -> ToolResult:
        """Full lifecycle: validate → execute → validate_output."""
        start = time.perf_counter()
        input_errors = self.validate_input(**kwargs)
        if input_errors:
            return ToolResult(
                ok=False,
                tool=self.name,
                data={},
                error="; ".join(input_errors),
                latency_ms=0.0,
            )
        try:
            data = self.execute(**kwargs)
        except ToolError as exc:
            return ToolResult(
                ok=False,
                tool=self.name,
                data={},
                error=str(exc),
                latency_ms=(time.perf_counter() - start) * 1000.0,
            )
        output_errors = self.validate_output(data)
        if output_errors:
            return ToolResult(
                ok=False,
                tool=self.name,
                data=data,
                error="; ".join(output_errors),
                warning="Output validation failed",
                latency_ms=(time.perf_counter() - start) * 1000.0,
            )
        return ToolResult(
            ok=True,
            tool=self.name,
            data=data,
            latency_ms=(time.perf_counter() - start) * 1000.0,
        )
