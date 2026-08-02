"""Typed Pydantic v2 contracts for the AI layer.

These schemas are the strongly-typed boundary between the FastAPI routes,
the ConversationManager, the PlannerAgent and the tool/agent registries.
Every object crossing a layer boundary is validated here so the AI layer
remains strongly typed, testable and safe against malformed LLM output.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from app.ai.config import LLMProviderName


# ─────────────────────────────────────────────────────────────────────
# Roles / intents
# ─────────────────────────────────────────────────────────────────────


class MessageRole(str, Enum):
    """Conversation message roles."""

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


class AgentName(str, Enum):
    """Identifiers for every agent in the registry."""

    PLANNER = "planner"
    PROFILE = "profile"
    GOAL = "goal"
    PORTFOLIO = "portfolio"
    RESEARCH = "research"
    SCENARIO = "scenario"
    COACH = "coach"
    MEMORY = "memory"
    EXPLAINABILITY = "explainability"
    CRITIC = "critic"
    COMPLIANCE = "compliance"
    DATA_VALIDATION = "data_validation"


class ToolName(str, Enum):
    """Identifiers for every tool in the registry."""

    RISK = "risk_tool"
    GOAL = "goal_tool"
    ALLOCATION = "allocation_tool"
    SECURITY = "security_tool"
    PORTFOLIO = "portfolio_tool"
    SIMULATION = "simulation_tool"
    SCENARIO = "scenario_tool"
    RESEARCH = "research_tool"
    DATABASE = "database_tool"
    MARKET_DATA = "market_data_tool"
    HEALTH_SCORE = "health_score_tool"
    COMPARISON = "comparison_tool"
    PROFILE = "profile_tool"


# ─────────────────────────────────────────────────────────────────────
# Messages & chat
# ─────────────────────────────────────────────────────────────────────


class ChatMessage(BaseModel):
    """A single conversational message."""

    model_config = ConfigDict(use_enum_values=True)

    role: MessageRole
    content: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    tool_name: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ChatRequest(BaseModel):
    """POST /chat payload."""

    model_config = ConfigDict(use_enum_values=True)

    session_id: uuid.UUID | None = None
    message: str = Field(..., min_length=1, max_length=20_000)
    context: dict[str, Any] = Field(default_factory=dict)


class ChatResponse(BaseModel):
    """POST /chat response."""

    model_config = ConfigDict(use_enum_values=True)

    session_id: uuid.UUID
    reply: str
    tool_calls: list[dict[str, Any]] = Field(default_factory=list)
    agents_used: list[str] = Field(default_factory=list)
    memories_retrieved: int = 0
    documents_retrieved: int = 0
    provider: str = LLMProviderName.OLLAMA.value
    model: str = "llama3"
    requires_followup: bool = False
    followup_questions: list[str] = Field(default_factory=list)
    disclaimer: str = (
        "This response is for educational purposes only and is not "
        "investment, legal or tax advice. Please consult a SEBI-registered "
        "investment adviser before making any investment decision."
    )
    metadata: dict[str, Any] = Field(default_factory=dict)


# ─────────────────────────────────────────────────────────────────────
# Planner output
# ─────────────────────────────────────────────────────────────────────


class PlannerAction(BaseModel):
    """One unit of work the planner decomposes a request into."""

    model_config = ConfigDict(use_enum_values=True)

    agent: AgentName
    tool: ToolName | None = None
    input: dict[str, Any] = Field(default_factory=dict)
    description: str = ""
    requires_followup: bool = False
    followup_question: str | None = None


class AgentPlan(BaseModel):
    """The typed plan produced by the PlannerAgent.

    ``actions`` is an ordered list of subtasks. The ConversationManager
    executes them in order and assembles the final response.
    """

    model_config = ConfigDict(use_enum_values=True)

    intent: str = ""
    summary: str = ""
    actions: list[PlannerAction] = Field(default_factory=list)
    confidence: float = Field(0.5, ge=0.0, le=1.0)
    requires_followup: bool = False
    followup_questions: list[str] = Field(default_factory=list)


# ─────────────────────────────────────────────────────────────────────
# Tool execution
# ─────────────────────────────────────────────────────────────────────


class ToolCall(BaseModel):
    """A tool invocation (LLM requested or planner-mandated)."""

    model_config = ConfigDict(use_enum_values=True)

    name: ToolName
    arguments: dict[str, Any] = Field(default_factory=dict)
    agent: AgentName | None = None
    requires_confirmation: bool = False


class ToolResult(BaseModel):
    """The typed result of a tool execution."""

    model_config = ConfigDict(use_enum_values=True)

    ok: bool = True
    tool: str
    data: dict[str, Any] = Field(default_factory=dict)
    error: str | None = None
    warning: str | None = None
    latency_ms: float = 0.0
    executed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    confirmed: bool = True


# ─────────────────────────────────────────────────────────────────────
# Agent results
# ─────────────────────────────────────────────────────────────────────


class AgentResult(BaseModel):
    """The typed result of an agent execution."""

    model_config = ConfigDict(use_enum_values=True)

    agent: AgentName
    status: Literal["success", "needs_followup", "failed"] = "success"
    output: dict[str, Any] = Field(default_factory=dict)
    message: str = ""
    tool_results: list[ToolResult] = Field(default_factory=list)
    followup_questions: list[str] = Field(default_factory=list)
    latency_ms: float = 0.0
    memory_written: bool = False
    warnings: list[str] = Field(default_factory=list)


class AgentRunRecord(BaseModel):
    """Observability record of one agent execution."""

    model_config = ConfigDict(use_enum_values=True)

    id: uuid.UUID | None = None
    user_id: uuid.UUID | None = None
    session_id: uuid.UUID | None = None
    agent: AgentName
    status: str = "success"
    input_summary: str = ""
    output_summary: str = ""
    tool_names: list[str] = Field(default_factory=list)
    latency_ms: float = 0.0
    error: str | None = None
    prompt_version: str = "1.0.0"
    model: str = "llama3"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ─────────────────────────────────────────────────────────────────────
# RAG / memory
# ─────────────────────────────────────────────────────────────────────


class RetrievedDocument(BaseModel):
    """A document retrieved by the RAG retriever."""

    model_config = ConfigDict(use_enum_values=True)

    id: str = ""
    title: str = ""
    content: str = ""
    source: str = ""
    category: str = ""
    score: float = 0.0
    chunk_index: int = 0


class RetrievedMemory(BaseModel):
    """A memory row retrieved by the memory store."""

    model_config = ConfigDict(use_enum_values=True)

    id: str = ""
    memory_type: str = ""
    content: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)
    score: float = 0.0
    created_at: datetime | None = None


class KnowledgeDocumentCreate(BaseModel):
    """Create a knowledge document (for the RAG corpus)."""

    title: str = Field(..., min_length=1, max_length=512)
    content: str = Field(..., min_length=1)
    source: str = Field("manual", max_length=255)
    category: str = Field("education", max_length=64)
    metadata: dict[str, Any] = Field(default_factory=dict)


class MemoryCreate(BaseModel):
    """Write a memory row."""

    memory_type: str = Field(..., max_length=64)
    content: str = Field(..., min_length=1)
    metadata: dict[str, Any] = Field(default_factory=dict)


# ─────────────────────────────────────────────────────────────────────
# Research / scenario / tools API payloads
# ─────────────────────────────────────────────────────────────────────


class ResearchRequest(BaseModel):
    """POST /research payload."""

    query: str = Field(..., min_length=1, max_length=10_000)
    asset_class: str | None = None
    symbols: list[str] = Field(default_factory=list)
    context: dict[str, Any] = Field(default_factory=dict)


class ScenarioAgentRequest(BaseModel):
    """POST /scenario (agent path) payload."""

    scenario_type: str = Field(..., min_length=1, max_length=64)
    description: str | None = None
    parameters: dict[str, Any] = Field(default_factory=dict)


class ToolInvokeRequest(BaseModel):
    """POST /tools/{name} payload."""

    model_config = ConfigDict(use_enum_values=True)

    arguments: dict[str, Any] = Field(default_factory=dict)
    confirm: bool = False


class AgentListResponse(BaseModel):
    """GET /agents payload."""

    agents: list[dict[str, Any]] = Field(default_factory=list)

