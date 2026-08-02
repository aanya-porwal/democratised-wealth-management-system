"""API package — top-level router aggregation.

``api_router`` bundles every feature router under a single prefix. It is
mounted in :mod:`app.main` as ``app.include_router(api_router)``.

Importing this package has no side effects other than registering route
tables; the FastAPI application itself is created in :mod:`app.main`.
"""

from fastapi import APIRouter

from app.api.routes import (
    ai,
    allocation,
    auth,
    chat,
    goals,
    health,
    planner,
    portfolio,
    profile,
    rebalance,
    recommendations,
    scenarios,
    simulation,
    system,
    users,
)

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(profile.router, prefix="/profile", tags=["Profile"])
api_router.include_router(goals.router, prefix="/goals", tags=["Goals"])
api_router.include_router(portfolio.router, prefix="/portfolio", tags=["Portfolio"])
api_router.include_router(allocation.router, prefix="/allocation", tags=["Allocation"])
api_router.include_router(rebalance.router, prefix="/rebalance", tags=["Rebalancing"])
api_router.include_router(
    recommendations.router, prefix="/recommendations", tags=["Recommendations"]
)
api_router.include_router(simulation.router, prefix="/simulation", tags=["Simulation"])
api_router.include_router(scenarios.router, prefix="/scenarios", tags=["Scenarios"])
api_router.include_router(health.router, prefix="/health-score", tags=["Health Score"])
api_router.include_router(planner.router, prefix="/planner", tags=["Planner"])
api_router.include_router(chat.router, prefix="/chat", tags=["Chat"])
api_router.include_router(ai.router, prefix="/ai", tags=["AI"])
api_router.include_router(system.router, prefix="/system", tags=["System"])

__all__ = ["api_router"]

