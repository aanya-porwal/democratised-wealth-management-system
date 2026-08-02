"""Shared schema types: pagination envelope, generic messages."""

from __future__ import annotations

from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class MessageResponse(BaseModel):
    """A simple success message."""

    message: str = Field(..., description="Human-readable success message")
    detail: dict | None = Field(None, description="Optional structured detail")


class PaginationMeta(BaseModel):
    """Pagination metadata embedded in every list response."""

    page: int = Field(..., ge=1)
    size: int = Field(..., ge=1)
    total: int = Field(..., ge=0)
    pages: int = Field(..., ge=1)
    has_next: bool = False
    has_prev: bool = False


class PageOut(BaseModel, Generic[T]):
    """Standard paginated response envelope."""

    items: list[T]
    pagination: PaginationMeta

