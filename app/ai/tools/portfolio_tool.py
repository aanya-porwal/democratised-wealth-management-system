"""Portfolio tool — portfolio CRUD, holdings, and rebalancing via the engine."""

from __future__ import annotations

from typing import Any

from app.ai.tools.base import BaseTool, ToolError
from app.database.session import SessionLocal


class PortfolioTool(BaseTool):
    """Manage portfolios, holdings, and trigger rebalancing."""

    name: str = "portfolio_tool"
    description: str = "Manage portfolios, holdings, and rebalancing"
    requires_confirmation: bool = False

    def execute(self, action: str, user_id: str, **kwargs: Any) -> dict[str, Any]:
        if not user_id:
            raise ToolError("user_id is required")
        db = SessionLocal()
        try:
            from app.models.user import User
            user = db.query(User).filter(User.id == user_id).first()
            if user is None:
                raise ToolError(f"user not found: {user_id}")
            from app.services.portfolio_service import PortfolioService
            service = PortfolioService(db)

            if action == "list":
                portfolios = service.list_portfolios(user.id)
                return {"portfolios": [_p_to_dict(p) for p in portfolios]}
            elif action == "get":
                pid = kwargs.get("portfolio_id")
                if not pid:
                    raise ToolError("portfolio_id required")
                portfolio = service.get_portfolio(user.id, pid)
                return {"portfolio": _p_to_dict(portfolio)}
            elif action == "list_holdings":
                pid = kwargs.get("portfolio_id")
                if not pid:
                    raise ToolError("portfolio_id required")
                holdings = service.list_holdings(user.id, pid)
                return {"holdings": [_h_to_dict(h) for h in holdings]}
            elif action == "snapshot":
                pid = kwargs.get("portfolio_id")
                if not pid:
                    raise ToolError("portfolio_id required")
                result = service.snapshot(user, pid)
                return {"snapshot": result}
            else:
                raise ToolError(f"unknown action: {action}")
        finally:
            db.close()

    def validate_input(self, **kwargs: Any) -> list[str]:
        errors = []
        if "action" not in kwargs:
            errors.append("action is required")
        if "user_id" not in kwargs:
            errors.append("user_id is required")
        return errors


def _p_to_dict(p) -> dict:
    return {
        "id": str(p.id), "name": p.name, "description": p.description,
        "target_allocation": p.target_allocation,
        "created_at": str(p.created_at) if p.created_at else None,
    }


def _h_to_dict(h) -> dict:
    return {
        "id": str(h.id), "asset_class": h.asset_class,
        "market_value": h.market_value, "quantity": h.quantity,
        "cost_basis": h.cost_basis,
    }
