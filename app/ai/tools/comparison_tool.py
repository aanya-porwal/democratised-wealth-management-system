"""Comparison tool — compare securities using the Security Selection Engine."""

from __future__ import annotations

from typing import Any

from app.ai.tools.base import BaseTool


class ComparisonTool(BaseTool):
    """Compare securities (funds, ETFs, stocks, bonds) side by side."""

    name: str = "comparison_tool"
    description: str = "Compare securities (funds, ETFs, stocks, bonds) side by side"
    requires_confirmation: bool = False

    def execute(self, **kwargs: Any) -> dict[str, Any]:
        symbols = kwargs.get("symbols", [])
        if not symbols:
            return {"comparison": {"message": "No symbols provided for comparison"}}
        return {
            "comparison": {
                "symbols": symbols,
                "message": "Comparison engine available. Use the /research endpoint for detailed reports.",
            }
        }

    def validate_input(self, **kwargs: Any) -> list[str]:
        errors = []
        if "symbols" not in kwargs or not kwargs["symbols"]:
            errors.append("symbols is required (list of security symbols)")
        return errors
