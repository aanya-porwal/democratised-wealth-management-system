"""AIOrchestratorService — main entry point for the AI layer.

Coordinates providers, memory, RAG, agents, conversation manager,
security, and observability into a single orchestrator.
"""

from __future__ import annotations

import uuid
from typing import Any

from app.ai.agents.registry import AgentRegistry
from app.ai.config import ai_settings
from app.ai.conversation.manager import ConversationManager
from app.ai.embeddings.factory import get_embedding_model
from app.ai.memory.store import MemoryStore
from app.ai.observability.tracker import AgentRunTracker
from app.ai.providers.factory import get_llm_provider
from app.ai.rag.retriever import RAGRetriever
from app.ai.schemas import (
    AgentName,
    AgentPlan,
    ChatRequest,
    ChatResponse,
    KnowledgeDocumentCreate,
    MemoryCreate,
    RetrievedDocument,
    RetrievedMemory,
    ToolResult,
)
from app.ai.security.input_guard import PromptInjectionGuard
from app.ai.security.output_sanitizer import OutputSanitizer
from app.ai.security.tool_policy import ToolPolicy
from app.ai.tools.registry import ToolRegistry
from app.ai.vectorstore.factory import get_vector_store


class AIOrchestratorService:
    """Main orchestrator for the AI layer.

    Usage:
        service = AIOrchestratorService()
        response = service.chat(ChatRequest(session_id=..., message="Hello"))
    """

    def __init__(self) -> None:
        self._conversation = ConversationManager()
        self._memory = MemoryStore()
        self._rag = RAGRetriever()
        self._provider = get_llm_provider()
        self._embeddings = get_embedding_model()
        self._vector_store = get_vector_store()

        # Initialize registries
        AgentRegistry.initialize_defaults()
        ToolRegistry.initialize_defaults()

    # ── chat ────────────────────────────────────────────────────────

    def chat(self, request: ChatRequest) -> ChatResponse:
        """Process a chat message through the full AI pipeline."""
        if not request.session_id:
            request.session_id = uuid.uuid4()

        # Security check
        safe, issues = PromptInjectionGuard.check(request.message)
        if not safe:
            return ChatResponse(
                session_id=request.session_id,
                reply="I cannot process that request as it appears to contain a prompt injection attempt.",
                metadata={"security_issues": issues},
            )

        # Process conversation
        response = self._conversation.process_message(
            user_id=request.context.get("user_id", uuid.uuid4()),
            session_id=request.session_id,
            message=request.message,
            context=request.context,
        )

        # Sanitize output
        response.reply = OutputSanitizer.sanitize(response.reply)

        # Log observability
        AgentRunTracker.log(
            user_id=request.context.get("user_id"),
            session_id=request.session_id,
            agent=AgentName.PLANNER,
            status="success",
            input_summary=request.message[:200],
            output_summary=response.reply[:200],
            tool_names=response.agents_used,
            latency_ms=0.0,
            model=ai_settings.llm_model,
        )

        return response

    # ── tools ───────────────────────────────────────────────────────

    def execute_tool(self, tool_name: str, arguments: dict[str, Any], confirm: bool = False) -> ToolResult:
        """Execute a tool by name."""
        allowed, reason = ToolPolicy.check(tool_name, user_confirmed=confirm)
        if not allowed:
            return ToolResult(ok=False, tool=tool_name, data={}, error=reason or "Tool not allowed")
        result = ToolRegistry.execute(tool_name, **arguments)
        return ToolResult(**result)

    # ── agents ──────────────────────────────────────────────────────

    def list_agents(self) -> list[dict[str, Any]]:
        """List all registered agents."""
        return AgentRegistry.list_agents()

    def list_tools(self) -> list[dict[str, Any]]:
        """List all registered tools with policy info."""
        return ToolRegistry.list_tools()

    # ── memory ──────────────────────────────────────────────────────

    def store_memory(self, user_id: uuid.UUID, data: MemoryCreate, session_id: uuid.UUID | None = None) -> uuid.UUID:
        """Store a memory."""
        return self._memory.store(
            user_id=user_id,
            memory_type=data.memory_type,
            content=data.content,
            metadata=data.metadata,
            session_id=session_id,
        )

    def retrieve_memories(self, user_id: uuid.UUID, query: str, top_k: int = 5) -> list[RetrievedMemory]:
        """Retrieve relevant memories."""
        return self._memory.retrieve(user_id, query, top_k=top_k)

    # ── RAG / knowledge ─────────────────────────────────────────────

    def retrieve_knowledge(self, query: str, top_k: int = 5) -> list[RetrievedDocument]:
        """Retrieve relevant knowledge documents."""
        return self._rag.retrieve(query, top_k=top_k)

    def add_knowledge_document(self, doc: KnowledgeDocumentCreate) -> str:
        """Add a document to the knowledge corpus."""
        from app.ai.rag.knowledge import KnowledgeDocument
        kd = KnowledgeDocument(
            title=doc.title, content=doc.content,
            source=doc.source, category=doc.category,
            metadata=doc.metadata,
        )
        return self._rag.add_document(kd)

    # ── health ──────────────────────────────────────────────────────

    def health(self) -> dict[str, Any]:
        """Return the health status of the AI layer."""
        return {
            "status": "healthy",
            "provider": ai_settings.llm_provider.value,
            "model": ai_settings.llm_model,
            "embedding": ai_settings.embedding_provider.value,
            "vector_store": ai_settings.vector_store.value,
            "rag_enabled": ai_settings.rag_enabled,
            "memory_enabled": ai_settings.memory_enabled,
            "critic_enabled": ai_settings.critic_enabled,
            "compliance_enabled": ai_settings.compliance_enabled,
            "data_validation_enabled": ai_settings.data_validation_enabled,
            "observability_enabled": ai_settings.observability_enabled,
            "agent_count": len(AgentRegistry.list_agents()),
            "tool_count": len(ToolRegistry.list_tools()),
        }
