"""Prompt template manager — versioned, separated from code.

Templates are stored as YAML files and loaded on demand. The manager
supports versioning, rendering with variables, and caching.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from string import Template
from typing import Any

import yaml

logger = logging.getLogger(__name__)

_TEMPLATE_DIR = Path(__file__).resolve().parent / "templates"


class PromptManager:
    """Loads, caches, and renders prompt templates.

    Templates are stored as YAML files in ``templates/``. Each file
    contains one or more named templates with version metadata.
    """

    _cache: dict[str, dict[str, Any]] = {}

    @classmethod
    def get(
        cls,
        template_name: str,
        version: str = "1.0.0",
        **variables: Any,
    ) -> str:
        """Load a template, render it with variables, and return the string."""
        key = f"{template_name}:{version}"
        if key not in cls._cache:
            cls._load(template_name, version)
        template_data = cls._cache.get(key)
        if template_data is None:
            logger.warning("template %s not found; using fallback", key)
            return _fallback_template(template_name, **variables)
        template_str = template_data.get("template", "")
        if not template_str:
            return _fallback_template(template_name, **variables)
        # Render with string.Template
        try:
            return Template(template_str).safe_substitute(**variables)
        except Exception as exc:
            logger.warning("template rendering failed: %s", exc)
            return template_str

    @classmethod
    def _load(cls, template_name: str, version: str) -> None:
        """Load a template from disk."""
        filepath = _TEMPLATE_DIR / f"{template_name}.yaml"
        if not filepath.exists():
            logger.warning("template file not found: %s", filepath)
            return
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            if not isinstance(data, dict):
                return
            for key, entry in data.items():
                if isinstance(entry, dict):
                    ver = str(entry.get("version", "1.0.0"))
                    cache_key = f"{key}:{ver}"
                    cls._cache[cache_key] = entry
            logger.debug("loaded %d templates from %s", len(data), filepath)
        except Exception as exc:
            logger.warning("failed to load template %s: %s", filepath, exc)

    @classmethod
    def list_templates(cls) -> list[str]:
        """List available template names."""
        templates: list[str] = []
        for f in _TEMPLATE_DIR.glob("*.yaml"):
            try:
                with open(f, "r", encoding="utf-8") as fh:
                    data = yaml.safe_load(fh)
                if isinstance(data, dict):
                    templates.extend(data.keys())
            except Exception:
                continue
        return sorted(templates)

    @classmethod
    def clear_cache(cls) -> None:
        cls._cache.clear()


def get_prompt(template_name: str, **variables: Any) -> str:
    """Convenience: get a rendered prompt template."""
    return PromptManager.get(template_name, **variables)


def _fallback_template(name: str, **variables: Any) -> str:
    """Return a simple fallback when the template file is missing."""
    fallbacks = {
        "system": (
            "You are a financial advisory AI assistant. "
            "You help users understand their financial situation, "
            "set goals, and make informed decisions. "
            "You NEVER provide financial calculations or investment advice. "
            "You ALWAYS direct users to consult SEBI-registered professionals. "
            "Current date: ${date}"
        ),
        "planner": (
            "Analyze the user's request and break it into subtasks. "
            "User request: ${user_message}"
        ),
        "profile": (
            "You help users complete their financial profile. "
            "Ask for missing information and update the database."
        ),
        "goal": (
            "You help users define, modify, and track financial goals. "
            "Use the Goal Engine for analysis."
        ),
        "portfolio": (
            "You help users understand their portfolio, risk, and allocation. "
            "Use the Risk Engine, Allocation Engine, and Security Selection Engine."
        ),
        "compliance": (
            "Ensure all responses comply with SEBI regulations. "
            "Add disclaimers where appropriate. "
            "Never provide personalised investment advice."
        ),
    }
    template_str = fallbacks.get(name, "You are a helpful financial assistant.")
    try:
        from datetime import datetime, timezone
        variables.setdefault("date", datetime.now(timezone.utc).strftime("%Y-%m-%d"))
        return Template(template_str).safe_substitute(**variables)
    except Exception:
        return template_str
