"""AI Chat & Agent API endpoints.

Provides the conversational financial advisor interface, agent management,
memory operations, and research endpoints.
"""

from __future__ import annotations

import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.ai.schemas import (
    ChatRequest,
    ChatResponse,
    KnowledgeDocumentCreate,
    MemoryCreate,
    ToolResult,
)
from app.ai.service import AIOrchestratorService
from app.dependencies import get_current_user, get_db
from app.models.user import User
from app.schemas.common import MessageResponse

router = APIRouter()

# ── dependency ──────────────────────────────────────────────────────


def get_ai_service() -> AIOrchestratorService:
    """Return the singleton AI orchestrator."""
    return AIOrchestratorService()


# ── Chat ────────────────────────────────────────────────────────────


class ChatPayload(BaseModel):
    """Chat message payload."""

    session_id: uuid.UUID | None = None
    message: str = Field(..., min_length=1, max_length=10000)
    context: dict[str, Any] = Field(default_factory=dict)


@router.post(
    "/chat",
    response_model=ChatResponse,
    summary="Send a message to the AI Financial Advisor",
    description="Routes the message through the planner → agents → tools → engines pipeline.",
)
def chat(
    payload: ChatPayload,
    current: Annotated[User, Depends(get_current_user)],
    ai: Annotated[AIOrchestratorService, Depends(get_ai_service)],
) -> ChatResponse:
    """Process a chat message through the multi-agent AI pipeline."""
    request = ChatRequest(
        session_id=payload.session_id or uuid.uuid4(),
        message=payload.message,
        context={
            "user_id": str(current.id),
            "email": current.email,
            "full_name": current.full_name,
            **payload.context,
        },
    )
    return ai.chat(request)


@router.get(
    "/chat/history",
    summary="Retrieve recent chat history from memory",
)
def chat_history(
    current: Annotated[User, Depends(get_current_user)],
    ai: Annotated[AIOrchestratorService, Depends(get_ai_service)],
    limit: int = Query(20, ge=1, le=100),
) -> list[dict[str, Any]]:
    """Retrieve recent conversation memories."""
    memories = ai.retrieve_memories(current.id, "recent conversation", top_k=limit)
    return [
        {"id": str(m.id), "memory_type": m.memory_type, "content": m.content, "created_at": str(m.created_at)}
        for m in memories
    ]


@router.post(
    "/chat/reset",
    response_model=MessageResponse,
    summary="Reset the current chat session",
)
def reset_chat(
    current: Annotated[User, Depends(get_current_user)],
) -> MessageResponse:
    """Reset the chat session (placeholder)."""
    return MessageResponse(message="Chat session reset")


# ── Agents ──────────────────────────────────────────────────────────


@router.get(
    "/agents",
    summary="List all registered AI agents",
    description="Returns the list of available agents with their descriptions.",
)
def list_agents(
    ai: Annotated[AIOrchestratorService, Depends(get_ai_service)],
) -> list[dict[str, Any]]:
    """List all registered AI agents."""
    return ai.list_agents()


# ── Tools ───────────────────────────────────────────────────────────


class ToolExecutePayload(BaseModel):
    """Execute a tool."""

    tool_name: str = Field(..., min_length=1)
    arguments: dict[str, Any] = Field(default_factory=dict)
    confirm: bool = False


@router.post(
    "/tools/execute",
    response_model=ToolResult,
    summary="Execute a tool by name",
)
def execute_tool(
    payload: ToolExecutePayload,
    current: Annotated[User, Depends(get_current_user)],
    ai: Annotated[AIOrchestratorService, Depends(get_ai_service)],
) -> ToolResult:
    """Execute a tool with the given arguments."""
    return ai.execute_tool(payload.tool_name, payload.arguments, confirm=payload.confirm)


@router.get(
    "/tools",
    summary="List all registered tools",
    description="Returns the list of available tools with their descriptions and policies.",
)
def list_tools(
    ai: Annotated[AIOrchestratorService, Depends(get_ai_service)],
) -> list[dict[str, Any]]:
    """List all registered tools."""
    return ai.list_tools()


# ── Memory ──────────────────────────────────────────────────────────


class StoreMemoryPayload(BaseModel):
    """Store a memory."""

    memory_type: str = "conversation"
    content: str
    metadata: dict[str, Any] = Field(default_factory=dict)


@router.post(
    "/memory",
    summary="Store a memory for the current user",
)
def store_memory(
    payload: StoreMemoryPayload,
    current: Annotated[User, Depends(get_current_user)],
    ai: Annotated[AIOrchestratorService, Depends(get_ai_service)],
    session: Annotated[Session, Depends(get_db)],
) -> dict[str, str]:
    """Store a memory for the current user."""
    from app.ai.memory.store import MemoryStore

    store = MemoryStore()
    memory_id = store.store(
        user_id=current.id,
        memory_type=payload.memory_type,
        content=payload.content,
        metadata=payload.metadata,
    )
    return {"id": str(memory_id), "status": "stored"}


@router.get(
    "/memory",
    summary="Retrieve relevant memories for the current user",
)
def retrieve_memories(
    current: Annotated[User, Depends(get_current_user)],
    ai: Annotated[AIOrchestratorService, Depends(get_ai_service)],
    query: str = Query("", min_length=0),
    limit: int = Query(10, ge=1, le=50),
) -> list[dict[str, Any]]:
    """Retrieve relevant memories for the current user."""
    memories = ai.retrieve_memories(current.id, query, top_k=limit)
    return [
        {
            "id": str(m.id),
            "memory_type": m.memory_type,
            "content": m.content[:500],
            "created_at": str(m.created_at),
        }
        for m in memories
    ]


# ── Research ────────────────────────────────────────────────────────


class ResearchPayload(BaseModel):
    """Research request."""

    query: str = Field(..., min_length=1)
    asset_class: str | None = None


@router.post(
    "/research",
    summary="Research securities using the Security Selection Engine",
)
def research(
    payload: ResearchPayload,
    current: Annotated[User, Depends(get_current_user)],
    ai: Annotated[AIOrchestratorService, Depends(get_ai_service)],
) -> dict[str, Any]:
    """Research securities."""
    result = ai.execute_tool("research_tool", {"query": payload.query, "asset_class": payload.asset_class})
    return result.data


# ── Knowledge ───────────────────────────────────────────────────────


class AddKnowledgePayload(BaseModel):
    """Add a document to the knowledge base."""

    title: str
    content: str
    source: str = "manual"
    category: str = "general"
    metadata: dict[str, Any] = Field(default_factory=dict)


@router.post(
    "/knowledge",
    summary="Add a document to the knowledge base",
)
def add_knowledge(
    payload: AddKnowledgePayload,
    current: Annotated[User, Depends(get_current_user)],
    ai: Annotated[AIOrchestratorService, Depends(get_ai_service)],
) -> dict[str, str]:
    """Add a document to the knowledge corpus."""
    from app.ai.rag.knowledge import KnowledgeDocument
    from app.ai.rag.retriever import RAGRetriever

    doc = KnowledgeDocument(
        title=payload.title,
        content=payload.content,
        source=payload.source,
        category=payload.category,
        metadata=payload.metadata,
    )
    retriever = RAGRetriever()
    doc_id = retriever.add_document(doc)
    return {"id": doc_id, "status": "indexed"}


# ── Scenario ────────────────────────────────────────────────────────


class ScenarioPayload(BaseModel):
    """Run a scenario analysis."""

    scenario_type: str = "market_crash"
    user_id: uuid.UUID | None = None


@router.post(
    "/scenario",
    summary="Run a what-if scenario analysis",
)
def run_scenario(
    payload: ScenarioPayload,
    current: Annotated[User, Depends(get_current_user)],
    ai: Annotated[AIOrchestratorService, Depends(get_ai_service)],
) -> dict[str, Any]:
    """Run a what-if scenario analysis."""
    result = ai.execute_tool(
        "scenario_tool",
        {"user_id": str(current.id), "scenario_type": payload.scenario_type},
    )
    return result.data


# ── Health ──────────────────────────────────────────────────────────


@router.get(
    "/health",
    summary="AI layer health check",
)
def ai_health(
    ai: Annotated[AIOrchestratorService, Depends(get_ai_service)],
) -> dict[str, Any]:
    """Return the health status of the AI layer."""
    return ai.health()
