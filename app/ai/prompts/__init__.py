"""Prompt management — versioned YAML templates separated from code.

Templates are stored in ``prompts/templates/`` as YAML files with
versioning support. The manager loads, renders, and caches templates.
"""

from __future__ import annotations

from app.ai.prompts.manager import PromptManager, get_prompt

__all__ = ["PromptManager", "get_prompt"]
