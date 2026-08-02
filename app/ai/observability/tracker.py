"""AgentRunTracker — logs agent executions, tool calls, latency, and failures to PostgreSQL."""

from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from app.ai.config import ai_settings
from app.ai.schemas import AgentName, AgentRunRecord
from app.database.session import SessionLocal

logger = logging.getLogger(__name__)


class AgentRunTracker:
    """Tracks and persists agent run logs for observability."""

    @staticmethod
    def log(
        user_id: uuid.UUID | None,
        session_id: uuid.UUID | None,
        agent: AgentName,
        status: str,
        input_summary: str = "",
        output_summary: str = "",
        tool_names: list[str] | None = None,
        latency_ms: float = 0.0,
        error: str | None = None,
        prompt_version: str = "1.0.0",
        model: str = "",
    ) -> uuid.UUID | None:
        """Persist an agent run log entry."""
        if not ai_settings.observability_enabled:
            return None
        record_id = uuid.uuid4()
        try:
            from app.models.ai import AgentRunLog
            db = SessionLocal()
            try:
                entry = AgentRunLog(
                    id=record_id,
                    user_id=user_id,
                    session_id=session_id,
                    agent=agent.value,
                    status=status,
                    input_summary=input_summary[:500],
                    output_summary=output_summary[:500],
                    tool_names=tool_names or [],
                    latency_ms=latency_ms,
                    error=error,
                    prompt_version=prompt_version,
                    model=model or ai_settings.llm_model,
                )
                db.add(entry)
                db.commit()
                return record_id
            except Exception as exc:
                db.rollback()
                logger.warning("failed to log agent run: %s", exc)
                return None
            finally:
                db.close()
        except Exception as exc:
            logger.warning("observability logging failed: %s", exc)
            return None

    @staticmethod
    def to_record(entry: Any) -> AgentRunRecord:
        """Convert an ORM AgentRunLog to an AgentRunRecord."""
        return AgentRunRecord(
            id=entry.id,
            user_id=entry.user_id,
            session_id=entry.session_id,
            agent=AgentName(entry.agent) if entry.agent else AgentName.PLANNER,
            status=entry.status,
            input_summary=entry.input_summary or "",
            output_summary=entry.output_summary or "",
            tool_names=entry.tool_names or [],
            latency_ms=entry.latency_ms or 0.0,
            error=entry.error,
            prompt_version=entry.prompt_version or "1.0.0",
            model=entry.model or "",
            created_at=entry.created_at if entry.created_at else datetime.now(timezone.utc),
        )
