"""Admin user-management endpoints — list users, get users, set roles."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.dependencies import get_db, require_roles
from app.models.user import Role, User
from app.schemas.common import MessageResponse, PageOut, PaginationMeta
from app.schemas.user import UserOut
from app.services.user_service import UserService

router = APIRouter()


def _user_service(session: Annotated[Session, Depends(get_db)]) -> UserService:
    return UserService(session)


@router.get(
    "",
    response_model=PageOut[UserOut],
    summary="List users (admin)",
    description="Paginated user listing with optional search and sorting.",
)
def list_users(
    _admin: Annotated[User, Depends(require_roles(Role.ADMIN))],
    service: Annotated[UserService, Depends(_user_service)],
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    q: str | None = Query(None, description="Search by email or name"),
) -> PageOut[UserOut]:
    """Paginated admin list of users."""
    skip = (page - 1) * size
    users = service.list_users(skip=skip, limit=size, search=q)
    total = service.count_users(search=q)
    return PageOut[UserOut](
        items=[UserOut.model_validate(u) for u in users],
        pagination=PaginationMeta(
            page=page,
            size=size,
            total=total,
            pages=max(1, (total + size - 1) // size),
            has_next=(page * size) < total,
            has_prev=page > 1,
        ),
    )


@router.get(
    "/{user_id}",
    response_model=UserOut,
    summary="Get a user (admin)",
    description="Returns a single user by UUID.",
)
def get_user(
    user_id: uuid.UUID,
    _admin: Annotated[User, Depends(require_roles(Role.ADMIN))],
    service: Annotated[UserService, Depends(_user_service)],
) -> UserOut:
    """Fetch one user (admin only)."""
    return UserOut.model_validate(service.get(user_id))


@router.patch(
    "/{user_id}/role",
    response_model=UserOut,
    summary="Set a user's role (admin)",
    description="Promotes/demotes a user between admin, advisor and user roles.",
)
def set_user_role(
    user_id: uuid.UUID,
    payload: dict,
    _admin: Annotated[User, Depends(require_roles(Role.ADMIN))],
    service: Annotated[UserService, Depends(_user_service)],
) -> UserOut:
    """Change a user's role."""
    role = payload.get("role")
    if not role:
        from app.core.exceptions import ValidationError

        raise ValidationError("role is required", code="missing_role")
    return UserOut.model_validate(service.set_role(user_id, role))


@router.delete(
    "/{user_id}",
    response_model=MessageResponse,
    summary="Soft-delete a user (admin)",
    description="Marks the user as deleted (soft delete).",
)
def delete_user(
    user_id: uuid.UUID,
    _admin: Annotated[User, Depends(require_roles(Role.ADMIN))],
    service: Annotated[UserService, Depends(_user_service)],
) -> MessageResponse:
    """Soft-delete a user (admin only)."""
    user = service.get(user_id)
    from app.database.base import SoftDeleteMixin

    assert isinstance(user, SoftDeleteMixin)
    user.soft_delete()
    service.session.commit()
    return MessageResponse(message="User deleted")

