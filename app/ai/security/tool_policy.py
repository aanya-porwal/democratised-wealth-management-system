"""ToolPolicy — enforces allowed/denied tools and confirmation requirements."""

from __future__ import annotations

from typing import Any

from app.ai.config import ai_settings


class ToolPolicy:
    """Enforces tool usage policy: allowed, denied, and confirmation-required tools."""

    @classmethod
    def is_allowed(cls, tool_name: str) -> bool:
        """Check if a tool is allowed for execution."""
        if tool_name in ai_settings.denied_tools:
            return False
        if tool_name not in ai_settings.allowed_tools:
            return False
        return True

    @classmethod
    def requires_confirmation(cls, tool_name: str) -> bool:
        """Check if a tool requires user confirmation before execution."""
        return tool_name in ai_settings.require_confirmation_for

    @classmethod
    def check(cls, tool_name: str, user_confirmed: bool = False) -> tuple[bool, str | None]:
        """Check if a tool can be executed.

        Returns (allowed, reason_if_denied).
        """
        if not cls.is_allowed(tool_name):
            return False, f"Tool '{tool_name}' is not allowed"
        if cls.requires_confirmation(tool_name) and not user_confirmed:
            return False, f"Tool '{tool_name}' requires confirmation"
        return True, None
