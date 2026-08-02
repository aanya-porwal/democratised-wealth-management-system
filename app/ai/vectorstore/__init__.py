"""Vector store layer — local, free.

Provides a provider-independent vector-store interface. Defaults to FAISS
(local files); an in-memory numpy fallback is available. No paid vector
databases.
"""

from __future__ import annotations

from app.ai.vectorstore.base import (
    ScoredChunk,
    VectorChunk,
    VectorStoreError,
    BaseVectorStore,
)
from app.ai.vectorstore.factory import (
    build_vector_store,
    get_vector_store,
    reset_vector_store_cache,
)

__all__ = [
    "ScoredChunk",
    "VectorChunk",
    "VectorStoreError",
    "BaseVectorStore",
    "build_vector_store",
    "get_vector_store",
    "reset_vector_store_cache",
]

