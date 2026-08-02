"""Chat session endpoints — future AI compatibility.

The schema is deliberately generic: chat sessions simply persist a title,
context and message history. No AI/LLM is wired in; this is the storage
layer a future conversational advisor can consume.
"""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_db
from app.models.system import ChatSession
from app.models.user import User
from app.schemas.common import MessageResponse

router = APIRouter()


class ChatSessionCreate(BaseModel):
    """Payload to create a chat session."""

    title: str = Field("New chat", max_length=255)
    context: dict | None = None


class ChatSessionOut(BaseModel):
    """Chat session response."""

    id: uuid.UUID
    title: str
    context: dict | None = None
    status: str
    messages: dict | None = None
    created_at: str | None = None
    updated_at: str | None = None


@router.post(
    "",
    response_model=ChatSessionOut,
    status_code=201,
    summary="Create a chat session",
    description="Creates a conversational session shell for the current user.",
)
def create_chat_session(
    payload: ChatSessionCreate,
    current: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_db)],
) -> ChatSessionOut:
    """Create a chat session (future AI memory)."""
    record = ChatSession(user_id=current.id, title=payload.title, context=payload.context)
    session.add(record)
    session.commit()
    return ChatSessionOut(
        id=record.id,
        title=record.title,
        context=record.context,
        status=record.status,
        messages=record.messages,
        created_at=record.created_at.isoformat() if record.created_at else None,
        updated_at=record.updated_at.isoformat() if record.updated_at else None,
    )


@router.get(
    "",
    response_model=list[ChatSessionOut],
    summary="List chat sessions",
    description="Lists the current user's chat sessions.",
)
def list_chat_sessions(
    current: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_db)],
) -> list[ChatSessionOut]:
    """List the current user's chat sessions."""
    records = (
        session.query(ChatSession)
        .filter(ChatSession.user_id == current.id, ChatSession.deleted_at.is_(None))
        .order_by(ChatSession.updated_at.desc())
        .all()
    )
    return [
        ChatSessionOut(
            id=r.id,
            title=r.title,
            context=r.context,
            status=r.status,
            messages=r.messages,
            created_at=r.created_at.isoformat() if r.created_at else None,
            updated_at=r.updated_at.isoformat() if r.updated_at else None,
        )
        for r in records
    ]


@router.get(
    "/{chat_id}",
    response_model=ChatSessionOut,
    summary="Get a chat session",
    description="Returns a single chat session owned by the current user.",
)
def get_chat_session(
    chat_id: uuid.UUID,
    current: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_db)],
) -> ChatSessionOut:
    """Fetch one chat session."""
    record = (
        session.query(ChatSession)
        .filter(ChatSession.id == chat_id, ChatSession.user_id == current.id)
        .first()
    )
    if record is None:
        from app.core.exceptions import NotFoundError

        raise NotFoundError("Chat session not found", code="chat_not_found")
    return ChatSessionOut(
        id=record.id,
        title=record.title,
        context=record.context,
        status=record.status,
        messages=record.messages,
        created_at=record.created_at.isoformat() if record.created_at else None,
        updated_at=record.updated_at.isoformat() if record.updated_at else None,
    )


@router.delete(
    "/{chat_id}",
    response_model=MessageResponse,
    summary="Delete a chat session",
    description="Soft-deletes a chat session owned by the current user.",
)
def delete_chat_session(
    chat_id: uuid.UUID,
    current: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_db)],
) -> MessageResponse:
    """Delete (soft) a chat session."""
    record = (
        session.query(ChatSession)
        .filter(ChatSession.id == chat_id, ChatSession.user_id == current.id)
        .first()
    )
    if record is None:
        from app.core.exceptions import NotFoundError

        raise NotFoundError("Chat session not found", code="chat_not_found")
    record.soft_delete()
    session.commit()
    return MessageResponse(message="Chat session deleted")

