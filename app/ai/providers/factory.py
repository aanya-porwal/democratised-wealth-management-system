"""LLM provider registry + factory.

The application never imports a concrete provider directly. It asks the
factory for a :class:`BaseLLMProvider` by name and receives the right
implementation. Adding a provider = subclass + register here.
"""

from __future__ import annotations

import logging
from typing import Any, Callable, Type

from app.ai.config import AISettings, LLMProviderName
from app.ai.providers.base import BaseLLMProvider, LLMProviderError

logger = logging.getLogger(__name__)

ProviderFactory = Callable[[AISettings], BaseLLMProvider]

# Registered provider builders, keyed by LLMProviderName.
_BUILDERS: dict[LLMProviderName, ProviderFactory] = {}


def register_provider(name: LLMProviderName, builder: ProviderFactory) -> None:
    """Register (or replace) a provider builder."""
    _BUILDERS[name] = builder
    logger.debug("registered LLM provider %s", name.value)


def _default_builders() -> None:
    """Register the built-in providers if not already registered."""
    if _BUILDERS:
        return

    from app.ai.providers.anthropic import AnthropicLLMProvider
    from app.ai.providers.fallback import FallbackLLMProvider
    from app.ai.providers.gemini import GeminiLLMProvider
    from app.ai.providers.groq import GroqLLMProvider
    from app.ai.providers.lmstudio import LMStudioLLMProvider
    from app.ai.providers.ollama import OllamaLLMProvider
    from app.ai.providers.openai import OpenAILLMProvider

    def _ollama(cfg: AISettings) -> BaseLLMProvider:
        return OllamaLLMProvider(
            model=cfg.llm_model,
            base_url=cfg.llm_base_url,
            timeout_seconds=cfg.llm_timeout_seconds,
            max_tokens=cfg.llm_max_tokens,
            temperature=cfg.llm_temperature,
        )

    def _openai(cfg: AISettings) -> BaseLLMProvider:
        return OpenAILLMProvider(
            model=cfg.llm_model,
            base_url=cfg.llm_base_url,
            api_key=cfg.llm_api_key,
            timeout_seconds=cfg.llm_timeout_seconds,
            max_tokens=cfg.llm_max_tokens,
            temperature=cfg.llm_temperature,
        )

    def _anthropic(cfg: AISettings) -> BaseLLMProvider:
        return AnthropicLLMProvider(
            model=cfg.llm_model,
            base_url=cfg.llm_base_url,
            api_key=cfg.llm_api_key,
            timeout_seconds=cfg.llm_timeout_seconds,
            max_tokens=cfg.llm_max_tokens,
            temperature=cfg.llm_temperature,
        )

    def _gemini(cfg: AISettings) -> BaseLLMProvider:
        return GeminiLLMProvider(
            model=cfg.llm_model,
            base_url=cfg.llm_base_url,
            api_key=cfg.llm_api_key,
            timeout_seconds=cfg.llm_timeout_seconds,
            max_tokens=cfg.llm_max_tokens,
            temperature=cfg.llm_temperature,
        )

    def _groq(cfg: AISettings) -> BaseLLMProvider:
        return GroqLLMProvider(
            model=cfg.llm_model,
            base_url=cfg.llm_base_url,
            api_key=cfg.llm_api_key,
            timeout_seconds=cfg.llm_timeout_seconds,
            max_tokens=cfg.llm_max_tokens,
            temperature=cfg.llm_temperature,
        )

    def _lmstudio(cfg: AISettings) -> BaseLLMProvider:
        return LMStudioLLMProvider(
            model=cfg.llm_model,
            base_url=cfg.llm_base_url,
            timeout_seconds=cfg.llm_timeout_seconds,
            max_tokens=cfg.llm_max_tokens,
            temperature=cfg.llm_temperature,
        )

    def _fallback(cfg: AISettings) -> BaseLLMProvider:
        return FallbackLLMProvider()

    register_provider(LLMProviderName.OLLAMA, _ollama)
    register_provider(LLMProviderName.OPENAI, _openai)
    register_provider(LLMProviderName.ANTHROPIC, _anthropic)
    register_provider(LLMProviderName.GEMINI, _gemini)
    register_provider(LLMProviderName.GROQ, _groq)
    register_provider(LLMProviderName.LMSTUDIO, _lmstudio)
    register_provider(LLMProviderName.FALLBACK, _fallback)


def build_llm_provider(cfg: AISettings | None = None) -> BaseLLMProvider:
    """Build the LLM provider selected by the settings.

    If building the configured provider fails (e.g. missing API key), the
    fallback deterministic provider is returned so the system never
    crashes at startup.
    """
    settings = cfg or _current_settings()
    _default_builders()
    builder = _BUILDERS.get(settings.llm_provider)
    if builder is None:
        logger.warning("no builder for %s; using fallback", settings.llm_provider.value)
        settings = _current_settings(force_fallback=True)
        builder = _BUILDERS[LLMProviderName.FALLBACK]
    try:
        return builder(settings)
    except LLMProviderError as exc:
        logger.warning("provider %s unavailable (%s); using fallback", settings.llm_provider.value, exc)
        settings = _current_settings(force_fallback=True)
        return _BUILDERS[LLMProviderName.FALLBACK](settings)
    except Exception as exc:  # pragma: no cover - defensive
        logger.exception("unexpected provider build error: %s", exc)
        settings = _current_settings(force_fallback=True)
        return _BUILDERS[LLMProviderName.FALLBACK](settings)


# Process-wide cached provider instance.
_provider_cache: BaseLLMProvider | None = None


def get_llm_provider() -> BaseLLMProvider:
    """Return the process-wide cached provider instance."""
    global _provider_cache
    if _provider_cache is None:
        _provider_cache = build_llm_provider()
    return _provider_cache


def reset_llm_cache() -> None:
    """Drop the cached provider (mainly for tests / hot-swap)."""
    global _provider_cache
    if _provider_cache is not None:
        try:
            close = getattr(_provider_cache, "close", None)
            if close:
                close()
        except Exception:  # pragma: no cover
            pass
        _provider_cache = None


def _current_settings(force_fallback: bool = False) -> AISettings:
    from app.ai.config import ai_settings

    if not force_fallback:
        return ai_settings
    from dataclasses import replace

    from app.ai.config import LLMProviderName

    return replace(ai_settings, llm_provider=LLMProviderName.FALLBACK)

