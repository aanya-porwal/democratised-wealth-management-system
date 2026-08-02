"""Pagination, sorting, filtering and searching helpers.

Used by every list endpoint so the API is consistent: ``?page=2``,
``?size=20``, ``?sort=-created_at``, ``?q=text``. The helper returns a
paginated result object that routers turn into a standard envelope.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Generic, TypeVar

from fastapi import Query
from pydantic import BaseModel
from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

T = TypeVar("T")


class PageParams(BaseModel):
    """Query parameters accepted by every list endpoint."""

    page: int = Query(1, ge=1, description="Page number, 1-based")
    size: int = Query(20, ge=1, le=100, description="Page size (1-100)")
    sort: str | None = Query(
        None, description='Sort field, prefix with "-" for descending, e.g. "-created_at"'
    )
    q: str | None = Query(None, description="Free-text search term")

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.size


@dataclass
class Page(Generic[T]):
    """A single page of results with total counts."""

    items: list[T]
    total: int
    page: int
    size: int

    @property
    def pages(self) -> int:
        return max(1, -(-self.total // self.size)) if self.size else 1

    @property
    def has_next(self) -> bool:
        return self.page < self.pages


def paginate_query(
    session: Session,
    statement: Select[Any],
    *,
    page_params: PageParams,
    sortable_fields: set[str] | None = None,
    search_fields: list[str] | None = None,
) -> Page[Any]:
    """Execute a select with pagination, optional sorting and searching.

    Parameters
    ----------
    session:
        Active DB session.
    statement:
        The base ``select(...)`` to page.
    page_params:
        Page/size/sort/q parameters.
    sortable_fields:
        Whitelist of columns that may be sorted on (prevents SQL
        injection through the ``sort`` parameter).
    search_fields:
        Columns to ``ILIKE``-search when ``q`` is provided.

    Returns
    -------
    Page
        A :class:`Page` with the requested slice.
    """
    model = statement.column_descriptions[0]["entity"]

    # search
    if page_params.q and search_fields:
        from sqlalchemy import or_

        term = f"%{page_params.q.strip()}%"
        criteria = [getattr(model, f).ilike(term) for f in search_fields if hasattr(model, f)]
        if criteria:
            statement = statement.where(or_(*criteria))

    # total count
    count_stmt = select(func.count()).select_from(statement.order_by(None).subquery())
    total = int(session.execute(count_stmt).scalar_one())

    # sort (whitelisted)
    if page_params.sort and sortable_fields:
        field = page_params.sort
        descending = field.startswith("-")
        field = field.lstrip("-")
        if field in sortable_fields and hasattr(model, field):
            column = getattr(model, field)
            statement = statement.order_by(column.desc() if descending else column.asc())

    # fallback deterministic ordering
    if not statement._order_by_clauses:
        statement = statement.order_by(model.created_at.desc())

    items = session.execute(statement.offset(page_params.offset).limit(page_params.size)).scalars().all()
    return Page(items=list(items), total=total, page=page_params.page, size=page_params.size)

