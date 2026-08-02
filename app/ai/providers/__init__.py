"""LLM provider layer.

The application must NOT depend on a specific LLM. Providers implement the
:class:`BaseLLMProvider` contract and are selected through the factory. The
rest of the system never knows which provider is being used.
"""

from __future__ import annotations

from app.ai.providers.base import (
    BaseLLMProvider,
    LLMCompletion,
    LLMError,
    LLMMessage,
    LLMProviderError,
)
from app.ai.providers.fallback import FallbackLLMProvider
from app.ai.providers.factory import (
    build_llm_provider,
    get_llm_provider,
    register_provider,
    reset_llm_cache,
)

__all__ = [
    "BaseLLMProvider",
    "LLMCompletion",
    "LLMError",
    "LLMMessage",
    "LLMProviderError",
    "FallbackLLMProvider",
    "build_llm_provider",
    "get_llm_provider",
    "register_provider",
    "reset_llm_cache",
]

