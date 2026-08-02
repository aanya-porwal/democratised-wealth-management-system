"""Configuration package for the backend.

Loads environment-specific settings via :mod:`pydantic_settings`.
Import :func:`get_settings` everywhere you need configuration; the value
is cached per process.
"""

from app.config.settings import get_settings, settings

__all__ = ["get_settings", "settings"]

