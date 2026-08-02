"""ConversationManager — maintains conversation history, context, memory retrieval, agent routing, session state."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from app.ai.schemas import (
    AgentName,
    AgentPlan,
    ChatMessage,
    ChatResponse,
    MessageRole,
    PlannerAction,
)
from app.ai.agents.registry import AgentRegistry
from app.ai.config import ai_settings
from app.ai.memory.store import MemoryStore
from app.ai.rag.retriever import RAGRetriever
from app.ai.prompts.manager import PromptManager
from app.ai.providers.factory import get_llm_provider


class ConversationManager:
    """Orchestrates the conversation: plan → execute agents → respond."""

    def __init__(self) -> None:
        self._memory = MemoryStore()
        self._rag = RAGRetriever()
        self._provider = None

    @property
    def provider(self):
        if self._provider is None:
            self._provider = get_llm_provider()
        return self._provider

    def process_message(
        self,
        user_id: uuid.UUID,
        session_id: uuid.UUID,
        message: str,
        context: dict[str, Any] | None = None,
    ) -> ChatResponse:
        ctx = context or {}
        ctx["user_id"] = str(user_id)
        ctx["session_id"] = str(session_id)

        # Store the user message in memory
        if ai_settings.memory_enabled:
            self._memory.store(
                user_id=user_id,
                memory_type="conversation",
                content=message,
                metadata={"role": "user", "session_id": str(session_id)},
                session_id=session_id,
            )

        # Retrieve relevant memories
        memories = []
        if ai_settings.memory_enabled:
            memories = self._memory.retrieve(user_id, message, top_k=3)

        # Retrieve relevant knowledge documents
        documents = []
        if ai_settings.rag_enabled:
            documents = self._rag.retrieve(message, top_k=3)

        # Get the planner agent and create a plan
        planner = AgentRegistry.get(AgentName.PLANNER)
        plan_result = planner.run(message, ctx)
        plan_data = plan_result.output.get("plan", {})
        plan = AgentPlan(**plan_data) if isinstance(plan_data, dict) else AgentPlan()

        # Execute each action in the plan
        all_tool_calls: list[dict[str, Any]] = []
        agents_used: list[str] = []
        response_parts: list[str] = []

        for action in plan.actions:
            agent_name = action.agent
            try:
                agent = AgentRegistry.get(agent_name)
                agent_result = agent.run(
                    f"{action.description}: {message}",
                    {**ctx, **action.input},
                )
                agents_used.append(agent_name.value)
                if agent_result.output:
                    response_parts.append(str(agent_result.output))
            except Exception as exc:
                response_parts.append(f"Note: {agent_name.value} analysis unavailable ({exc})")

        # Final response composition
        reply = self._compose_response(message, response_parts, documents, memories, plan)

        if ai_settings.memory_enabled:
            self._memory.store(
                user_id=user_id,
                memory_type="conversation",
                content=reply,
                metadata={"role": "assistant", "session_id": str(session_id)},
                session_id=session_id,
            )

        return ChatResponse(
            session_id=session_id,
            reply=reply,
            tool_calls=all_tool_calls,
            agents_used=agents_used,
            memories_retrieved=len(memories),
            documents_retrieved=len(documents),
            provider=ai_settings.llm_provider.value,
            model=ai_settings.llm_model,
            requires_followup=plan.requires_followup,
            followup_questions=plan.followup_questions,
        )

    def _compose_response(
        self,
        message: str,
        parts: list[str],
        documents: list[Any],
        memories: list[Any],
        plan: AgentPlan,
    ) -> str:
        lines: list[str] = []
        lines.append(plan.summary or "I'll help you with that.")
        if parts:
            lines.append("")
            lines.extend(parts[:3])
        if documents:
            lines.append("")
            lines.append("📚 **Relevant resources:**")
            for doc in documents[:2]:
                lines.append(f"- {doc.title}")
        if not parts and not documents:
            lines.append("")
            lines.append("I understand you're asking about financial planning. Could you please provide more details so I can help you better?")
        lines.append("")
        lines.append("---")
        lines.append(
            "*This response is for educational purposes only and is not "
            "investment, legal or tax advice. Please consult a SEBI-registered "
            "investment adviser before making any investment decision.*"
        )
        return "\n".join(lines)
