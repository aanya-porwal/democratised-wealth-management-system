"""Market data tool — retrieves cached market data."""

from __future__ import annotations

from typing import Any

from app.ai.tools.base import BaseTool
from app.core.cache import cache


class MarketDataTool(BaseTool):
    """Retrieve cached market data (indices, asset prices, assumptions)."""

    name: str = "market_data_tool"
    description: str = "Retrieve cached market data"
    requires_confirmation: bool = False

    def execute(self, **kwargs: Any) -> dict[str, Any]:
        symbol = kwargs.get("symbol", "")
        if symbol:
            data = cache.get_json(f"market_data:{symbol}")
            if data:
                return {"market_data": data}
            return {"market_data": {"symbol": symbol, "message": "No cached data for this symbol"}}
        refresh = cache.get_json("system:market_data:last_refresh")
        return {"market_data": refresh or {"message": "No market data cached"}}

    def validate_input(self, **kwargs: Any) -> list[str]:
        return []
