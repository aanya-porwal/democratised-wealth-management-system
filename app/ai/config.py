"""AI layer configuration.

Loaded from environment variables (via ``app.config.settings``) with sane
free/local defaults. The default installation runs entirely on free and
open-source software:

* LLM provider: Ollama (models: llama3, mistral, qwen, deepseek, phi, gemma)
* Embeddings: sentence-transformers (MiniLM / BAAI bge) with a hash fallback
* Vector store: FAISS (local files) with an in-memory numpy fallback
* Memory: PostgreSQL (existing database)

Paid providers (OpenAI, Anthropic, Gemini, Groq) are optional plugins that
are only instantiated when explicitly configured.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class LLMProviderName(str, Enum):
    """Identifiers for LLM providers."""

    OLLAMA = "ollama"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GEMINI = "gemini"
    GROQ = "groq"
    LMSTUDIO = "lmstudio"
    FALLBACK = "fallback"


class EmbeddingProviderName(str, Enum):
    """Identifiers for embedding providers."""

    SENTENCE_TRANSFORMERS = "sentence_transformers"
    OLLAMA = "ollama"
    HASH = "hash"


class VectorStoreName(str, Enum):
    """Identifiers for vector stores."""

    FAISS = "faiss"
    NUMPY = "numpy"


@dataclass(frozen=True)
class AISettings:
    """Process-wide AI layer settings.

    Instances are built by :func:`load_ai_settings` from the application
    ``settings`` object so the AI layer stays environment-driven but is
    still unit-testable without mutating global state.
    """

    # ── LLM ────────────────────────────────────────────────────────
    llm_provider: LLMProviderName = LLMProviderName.OLLAMA
    llm_model: str = "llama3"
    llm_base_url: str = "http://localhost:11434"  # Ollama default
    llm_api_key: str | None = None
    llm_timeout_seconds: float = 120.0
    llm_max_tokens: int = 2048
    llm_temperature: float = 0.2
    llm_system_prompt_version: str = "1.0.0"

    # ── embeddings ─────────────────────────────────────────────────
    embedding_provider: EmbeddingProviderName = EmbeddingProviderName.SENTENCE_TRANSFORMERS
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    embedding_dimensions: int = 384
    embedding_batch_size: int = 32

    # ── vector store ───────────────────────────────────────────────
    vector_store: VectorStoreName = VectorStoreName.FAISS
    vector_index_dir: str = ".vector_index"

    # ── RAG ────────────────────────────────────────────────────────
    rag_enabled: bool = True
    rag_top_k: int = 5
    rag_min_score: float = 0.15

    # ── memory ─────────────────────────────────────────────────────
    memory_enabled: bool = True
    memory_top_k: int = 5
    memory_max_history_messages: int = 50
    memory_ttl_days: int = 365

    # ── conversation ───────────────────────────────────────────────
    conversation_max_turns: int = 20

    # ── observability ──────────────────────────────────────────────
    observability_enabled: bool = True

    # ── tool policy ────────────────────────────────────────────────
    allowed_tools: tuple[str, ...] = (
        "risk_tool",
        "goal_tool",
        "allocation_tool",
        "security_tool",
        "portfolio_tool",
        "simulation_tool",
        "scenario_tool",
        "research_tool",
        "database_tool",
        "market_data_tool",
        "health_score_tool",
        "comparison_tool",
        "profile_tool",
    )
    denied_tools: tuple[str, ...] = ()
    require_confirmation_for: tuple[str, ...] = (
        "database_tool",
    )

    # ── agent flags ────────────────────────────────────────────────
    critic_enabled: bool = True
    compliance_enabled: bool = True
    data_validation_enabled: bool = True

    # ── background tasks ───────────────────────────────────────────
    knowledge_reindex_hours: int = 24
    memory_cleanup_hours: int = 24

    # convenience helpers
    @property
    def llm_available(self) -> bool:
        return self.llm_provider != LLMProviderName.FALLBACK


def load_ai_settings() -> AISettings:
    """Build :class:`AISettings` from the application configuration.

    Reads ``app.config.settings`` (pydantic-settings, env-driven) using
    ``AI_`` prefixed values that default to free/local components.
    """
    from app.config import settings as app_settings

    provider_raw = str(getattr(app_settings, "AI_LLM_PROVIDER", "ollama")).lower()
    try:
        llm_provider = LLMProviderName(provider_raw)
    except ValueError:
        llm_provider = LLMProviderName.OLLAMA

    embedding_raw = str(
        getattr(app_settings, "AI_EMBEDDING_PROVIDER", "sentence_transformers")
    ).lower()
    try:
        embedding_provider = EmbeddingProviderName(embedding_raw)
    except ValueError:
        embedding_provider = EmbeddingProviderName.SENTENCE_TRANSFORMERS

    vector_raw = str(getattr(app_settings, "AI_VECTOR_STORE", "faiss")).lower()
    try:
        vector_store = VectorStoreName(vector_raw)
    except ValueError:
        vector_store = VectorStoreName.FAISS

    allowed_raw = str(getattr(app_settings, "AI_ALLOWED_TOOLS", ""))
    allowed = tuple(
        t.strip() for t in allowed_raw.split(",") if t.strip()
    ) or (
        "risk_tool",
        "goal_tool",
        "allocation_tool",
        "security_tool",
        "portfolio_tool",
        "simulation_tool",
        "scenario_tool",
        "research_tool",
        "database_tool",
        "market_data_tool",
        "health_score_tool",
        "comparison_tool",
        "profile_tool",
    )

    denied_raw = str(getattr(app_settings, "AI_DENIED_TOOLS", ""))
    denied = tuple(t.strip() for t in denied_raw.split(",") if t.strip())

    return AISettings(
        llm_provider=llm_provider,
        llm_model=str(getattr(app_settings, "AI_LLM_MODEL", "llama3")),
        llm_base_url=str(getattr(app_settings, "AI_LLM_BASE_URL", "http://localhost:11434")),
        llm_api_key=getattr(app_settings, "AI_LLM_API_KEY", None),
        llm_timeout_seconds=float(getattr(app_settings, "AI_LLM_TIMEOUT_SECONDS", 120)),
        llm_max_tokens=int(getattr(app_settings, "AI_LLM_MAX_TOKENS", 2048)),
        llm_temperature=float(getattr(app_settings, "AI_LLM_TEMPERATURE", 0.2)),
        llm_system_prompt_version=str(
            getattr(app_settings, "AI_SYSTEM_PROMPT_VERSION", "1.0.0")
        ),
        embedding_provider=embedding_provider,
        embedding_model=str(
            getattr(
                app_settings,
                "AI_EMBEDDING_MODEL",
                "sentence-transformers/all-MiniLM-L6-v2",
            )
        ),
        embedding_dimensions=int(getattr(app_settings, "AI_EMBEDDING_DIMENSIONS", 384)),
        embedding_batch_size=int(getattr(app_settings, "AI_EMBEDDING_BATCH_SIZE", 32)),
        vector_store=vector_store,
        vector_index_dir=str(getattr(app_settings, "AI_VECTOR_INDEX_DIR", ".vector_index")),
        rag_enabled=bool(getattr(app_settings, "AI_RAG_ENABLED", True)),
        rag_top_k=int(getattr(app_settings, "AI_RAG_TOP_K", 5)),
        rag_min_score=float(getattr(app_settings, "AI_RAG_MIN_SCORE", 0.15)),
        memory_enabled=bool(getattr(app_settings, "AI_MEMORY_ENABLED", True)),
        memory_top_k=int(getattr(app_settings, "AI_MEMORY_TOP_K", 5)),
        memory_max_history_messages=int(
            getattr(app_settings, "AI_MEMORY_MAX_HISTORY_MESSAGES", 50)
        ),
        memory_ttl_days=int(getattr(app_settings, "AI_MEMORY_TTL_DAYS", 365)),
        conversation_max_turns=int(getattr(app_settings, "AI_CONVERSATION_MAX_TURNS", 20)),
        observability_enabled=bool(getattr(app_settings, "AI_OBSERVABILITY_ENABLED", True)),
        allowed_tools=allowed,
        denied_tools=denied,
        require_confirmation_for=(
            "database_tool",
        ),
        critic_enabled=bool(getattr(app_settings, "AI_CRITIC_ENABLED", True)),
        compliance_enabled=bool(getattr(app_settings, "AI_COMPLIANCE_ENABLED", True)),
        data_validation_enabled=bool(
            getattr(app_settings, "AI_DATA_VALIDATION_ENABLED", True)
        ),
        knowledge_reindex_hours=int(getattr(app_settings, "AI_KNOWLEDGE_REINDEX_HOURS", 24)),
        memory_cleanup_hours=int(getattr(app_settings, "AI_MEMORY_CLEANUP_HOURS", 24)),
    )


# Process-wide default instance (mirrors ``app.config.settings`` pattern).
ai_settings = load_ai_settings()

