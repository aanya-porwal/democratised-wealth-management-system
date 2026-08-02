"""Audit log repository."""

from __future__ import annotations

import uuid

from sqlalchemy import select

from app.models.audit import AuditLog
from app.repositories.base import BaseRepository


class AuditRepository(BaseRepository[AuditLog]):
    """Persistence for audit log entries."""

    model = AuditLog

    def record(
        self,
        *,
        user_id: uuid.UUID | None,
        action: str,
        resource_type: str | None = None,
        resource_id: str | None = None,
        status: str = "success",
        ip_address: str | None = None,
        user_agent: str | None = None,
        metadata_: dict | None = None,
    ) -> AuditLog:
        entry = AuditLog(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=str(resource_id) if resource_id is not None else None,
            status=status,
            ip_address=ip_address,
            user_agent=user_agent,
            metadata_=metadata_,
        )
        self.session.add(entry)
        self.session.flush()
        return entry

    def list_for_user(
        self, user_id: uuid.UUID, skip: int = 0, limit: int = 50
    ) -> list[AuditLog]:
        stmt = (
            select(AuditLog)
            .where(AuditLog.user_id == user_id)
            .order_by(AuditLog.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(self.session.execute(stmt).scalars().all())

