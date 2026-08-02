"""Embedding layer — free local models only.

Provides a provider-independent embedding interface. Defaults to
sentence-transformers (MiniLM / BAAI bge); Ollama embeddings and a
deterministic hash fallback are also available. No paid embedding APIs.
"""

from __future__ import annotations

from app.ai.embeddings.base import BaseEmbeddingModel
from app.ai.embeddings.factory import (
    build_embedding_model,
    get_embedding_model,
    reset_embedding_cache,
)

__all__ = [
    "BaseEmbeddingModel",
    "build_embedding_model",
    "get_embedding_model",
    "reset_embedding_cache",
]

