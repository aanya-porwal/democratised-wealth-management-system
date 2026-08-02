"""Tool registry — maps tool names to tool instances."""

from __future__ import annotations

import logging
from typing import Any

from app.ai.tools.base import BaseTool, ToolError

logger = logging.getLogger(__name__)


class ToolRegistry:
    """Registry of available tools.

    Tools are registered by name and can be looked up, listed, and executed.
    The registry enforces the tool policy (allowed/denied tools).
    """

    _tools: dict[str, BaseTool] = {}
    _initialized = False

    @classmethod
    def register(cls, tool: BaseTool) -> None:
        """Register a tool instance."""
        cls._tools[tool.name] = tool
        logger.debug("registered tool: %s", tool.name)

    @classmethod
    def get(cls, name: str) -> BaseTool:
        """Look up a tool by name."""
        if name not in cls._tools:
            raise ToolError(f"tool not found: {name}")
        return cls._tools[name]

    @classmethod
    def list_tools(cls) -> list[dict[str, Any]]:
        """List all registered tools with metadata."""
        from app.ai.config import ai_settings

        return [
            {
                "name": tool.name,
                "description": tool.description,
                "requires_confirmation": tool.requires_confirmation,
                "allowed": tool.name in ai_settings.allowed_tools,
            }
            for tool in cls._tools.values()
        ]

    @classmethod
    def execute(cls, name: str, **kwargs: Any) -> dict[str, Any]:
        """Execute a tool by name with the given arguments."""
        from app.ai.config import ai_settings

        if name in ai_settings.denied_tools:
            raise ToolError(f"tool is denied: {name}")
        if name not in ai_settings.allowed_tools:
            raise ToolError(f"tool not allowed: {name}")

        tool = cls.get(name)
        result = tool.run(**kwargs)
        return result.model_dump()

    @classmethod
    def initialize_defaults(cls) -> None:
        """Register all default tools."""
        if cls._initialized:
            return

        from app.ai.tools.risk_tool import RiskTool
        from app.ai.tools.goal_tool import GoalTool
        from app.ai.tools.profile_tool import ProfileTool
        from app.ai.tools.portfolio_tool import PortfolioTool
        from app.ai.tools.simulation_tool import SimulationTool
        from app.ai.tools.scenario_tool import ScenarioTool
        from app.ai.tools.research_tool import ResearchTool
        from app.ai.tools.health_score_tool import HealthScoreTool
        from app.ai.tools.allocation_tool import AllocationTool
        from app.ai.tools.comparison_tool import ComparisonTool
        from app.ai.tools.database_tool import DatabaseTool
        from app.ai.tools.market_data_tool import MarketDataTool

        cls.register(RiskTool())
        cls.register(GoalTool())
        cls.register(ProfileTool())
        cls.register(PortfolioTool())
        cls.register(SimulationTool())
        cls.register(ScenarioTool())
        cls.register(ResearchTool())
        cls.register(HealthScoreTool())
        cls.register(AllocationTool())
        cls.register(ComparisonTool())
        cls.register(DatabaseTool())
        cls.register(MarketDataTool())

        cls._initialized = True
        logger.info("registered %d default tools", len(cls._tools))


def get_tool_registry() -> ToolRegistry:
    """Get the tool registry (initializes defaults on first call)."""
    ToolRegistry.initialize_defaults()
    return ToolRegistry
