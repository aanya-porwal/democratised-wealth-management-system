"""Profile endpoints — user profile, financial profile, behavioral
profile and risk assessment (drives the engine).
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_db
from app.models.user import User
from app.schemas.user import (
    BehavioralProfileCreate,
    BehavioralProfileOut,
    FinancialProfileCreate,
    FinancialProfileOut,
    UserProfileCreate,
    UserProfileOut,
)
from app.services.profile_service import ProfileService

router = APIRouter()


def _profile_service(session: Annotated[Session, Depends(get_db)]) -> ProfileService:
    return ProfileService(session)


@router.get(
    "",
    response_model=dict,
    summary="Get the current user's full profile",
    description="Returns the demographic, financial and behavioral profiles "
    "plus the engine risk assessment in one call.",
)
def get_full_profile(
    current: Annotated[User, Depends(get_current_user)],
    service: Annotated[ProfileService, Depends(_profile_service)],
) -> dict:
    """Return every profile component for the authenticated user."""
    out: dict = {"user_id": str(current.id)}
    try:
        out["profile"] = UserProfileOut.model_validate(service.get_user_profile(current.id)).model_dump()
    except Exception:
        out["profile"] = None
    try:
        out["financial_profile"] = FinancialProfileOut.model_validate(
            service.get_financial_profile(current.id)
        ).model_dump()
    except Exception:
        out["financial_profile"] = None
    try:
        out["behavioral_profile"] = BehavioralProfileOut.model_validate(
            service.get_behavioral_profile(current.id)
        ).model_dump()
    except Exception:
        out["behavioral_profile"] = None
    out["risk"] = service.assess_risk(current)
    return out


@router.get(
    "/user",
    response_model=UserProfileOut,
    summary="Get demographic profile",
    description="Returns the demographic profile for the current user.",
)
def get_user_profile(
    current: Annotated[User, Depends(get_current_user)],
    service: Annotated[ProfileService, Depends(_profile_service)],
) -> UserProfileOut:
    """Fetch the demographic profile."""
    return UserProfileOut.model_validate(service.get_user_profile(current.id))


@router.put(
    "/user",
    response_model=UserProfileOut,
    summary="Create or update demographic profile",
    description="Upserts the demographic profile for the current user.",
)
def upsert_user_profile(
    payload: UserProfileCreate,
    current: Annotated[User, Depends(get_current_user)],
    service: Annotated[ProfileService, Depends(_profile_service)],
) -> UserProfileOut:
    """Create or update the demographic profile."""
    profile = service.upsert_user_profile(current, payload)
    service.session.commit()
    return UserProfileOut.model_validate(profile)


@router.get(
    "/financial",
    response_model=FinancialProfileOut,
    summary="Get financial profile",
    description="Returns the financial inputs used by the planning engine.",
)
def get_financial_profile(
    current: Annotated[User, Depends(get_current_user)],
    service: Annotated[ProfileService, Depends(_profile_service)],
) -> FinancialProfileOut:
    """Fetch the financial profile."""
    return FinancialProfileOut.model_validate(service.get_financial_profile(current.id))


@router.put(
    "/financial",
    response_model=FinancialProfileOut,
    summary="Create or update financial profile",
    description="Upserts the financial inputs (income, expenses, assets, debt, tax).",
)
def upsert_financial_profile(
    payload: FinancialProfileCreate,
    current: Annotated[User, Depends(get_current_user)],
    service: Annotated[ProfileService, Depends(_profile_service)],
) -> FinancialProfileOut:
    """Create or update the financial profile."""
    profile = service.upsert_financial_profile(current, payload)
    service.session.commit()
    return FinancialProfileOut.model_validate(profile)


@router.get(
    "/behavioral",
    response_model=BehavioralProfileOut,
    summary="Get behavioral profile",
    description="Returns the behavioral / risk-tolerance inputs.",
)
def get_behavioral_profile(
    current: Annotated[User, Depends(get_current_user)],
    service: Annotated[ProfileService, Depends(_profile_service)],
) -> BehavioralProfileOut:
    """Fetch the behavioral profile."""
    return BehavioralProfileOut.model_validate(service.get_behavioral_profile(current.id))


@router.put(
    "/behavioral",
    response_model=BehavioralProfileOut,
    summary="Create or update behavioral profile",
    description="Upserts the behavioral inputs (risk tolerance, experience, literacy).",
)
def upsert_behavioral_profile(
    payload: BehavioralProfileCreate,
    current: Annotated[User, Depends(get_current_user)],
    service: Annotated[ProfileService, Depends(_profile_service)],
) -> BehavioralProfileOut:
    """Create or update the behavioral profile."""
    profile = service.upsert_behavioral_profile(current, payload)
    service.session.commit()
    return BehavioralProfileOut.model_validate(profile)


@router.get(
    "/risk",
    response_model=dict,
    summary="Assess investment risk",
    description="Runs the risk engine (capacity + tolerance) for the current user.",
)
def risk_assessment(
    current: Annotated[User, Depends(get_current_user)],
    service: Annotated[ProfileService, Depends(_profile_service)],
) -> dict:
    """Return the engine's risk assessment for the current user."""
    return service.assess_risk(current)

