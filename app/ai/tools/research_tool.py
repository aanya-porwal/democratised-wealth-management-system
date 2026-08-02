"""Research tool — security research via the Security Selection Engine."""

from __future__ import annotations

from typing import Any

from app.ai.tools.base import BaseTool, ToolError


class ResearchTool(BaseTool):
    """Research securities (funds, ETFs, stocks, bonds) using the Security Selection Engine."""

    name: str = "research_tool"
    description: str = "Research securities using the Security Selection Engine"
    requires_confirmation: bool = False

    def execute(self, **kwargs: Any) -> dict[str, Any]:
        query = kwargs.get("query", "")
        asset_class = kwargs.get("asset_class")
        if not query and not asset_class:
            raise ToolError("query or asset_class is required")
        # For now, return a placeholder indicating the engine is available
        # In production, this would call the security_selection evaluator registry
        return {
            "research": {
                "query": query,
                "asset_class": asset_class,
                "message": "Security Selection Engine query. Use the /research endpoint for full reports.",
            }
        }

    def validate_input(self, **kwargs: Any) -> list[str]:
        errors = []
        if "query" not in kwargs and "asset_class" not in kwargs:
            errors.append("query or asset_class is required")
        return errors
