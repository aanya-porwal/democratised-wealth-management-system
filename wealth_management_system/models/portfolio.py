"""Portfolio holding and trade models.

These describe the *current state* of a user's portfolio (what they
actually own) and the *trades* required to move it to a target. They are
pure data records — the logic that builds them lives in the allocation
and rebalancing engines.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from wealth_management_system.models import AssetClass
from wealth_management_system.models import AssetClass as _AssetClass  # noqa: F401  (re-export)

# Re-export AssetClass so callers can reference the enum via models.portfolio
AssetClass = _AssetClass


@dataclass(frozen=True)
class Holding:
    """One position in a portfolio.

    Attributes
    ----------
    asset_class:
        The instrument (from the root ``AssetClass`` enum).
    market_value:
        Current rupee value of the position.
    cost_basis:
        Original rupee cost of the position (used for capital-gains
        estimation on rebalance). Defaults to ``market_value`` when
        unknown, which implies no unrealised gain.
    quantity:
        Optional number of units/shares.
    """

    asset_class: AssetClass
    market_value: float
    cost_basis: float = 0.0
    quantity: Optional[float] = None

    def __post_init__(self) -> None:
        """Sanitise and validate the holding."""
        if self.market_value < 0:
            raise ValueError("market_value cannot be negative")
        if self.cost_basis < 0:
            raise ValueError("cost_basis cannot be negative")
        object.__setattr__(self, "market_value", round(self.market_value, 2))
        object.__setattr__(self, "cost_basis", round(self.cost_basis, 2))

    def unrealised_gain(self) -> float:
        """Rupees of unrealised capital gain (positive) or loss."""
        return self.market_value - self.cost_basis

    def weight_of(self, total_value: float) -> float:
        """Fraction of the portfolio this holding represents."""
        if total_value <= 0:
            return 0.0
        return self.market_value / total_value


@dataclass
class PortfolioHoldings:
    """The full set of positions a user currently owns."""

    holdings: list[Holding] = field(default_factory=list)

    def total_value(self) -> float:
        """Sum of every position's market value."""
        return round(sum(h.market_value for h in self.holdings), 2)

    def value_of(self, asset_class: AssetClass) -> float:
        """Market value held in a specific asset class."""
        return sum(h.market_value for h in self.holdings if h.asset_class == asset_class)

    def weight_of(self, asset_class: AssetClass) -> float:
        """Portfolio weight (0..1) of a specific asset class."""
        total = self.total_value()
        if total <= 0:
            return 0.0
        return round(self.value_of(asset_class) / total, 6)

    def bucket_values(self, bucket_map: dict[str, list[AssetClass]]) -> dict[str, float]:
        """Aggregate market values by logical bucket.

        Parameters
        ----------
        bucket_map:
            Mapping of bucket name (e.g. ``"equity"``) to the list of
            asset classes that belong to it.

        Returns
        -------
        dict[str, float]
            Total rupee value per bucket (only non-zero buckets included).
        """
        result: dict[str, float] = {}
        for bucket, classes in bucket_map.items():
            value = sum(self.value_of(ac) for ac in classes)
            if value > 0:
                result[bucket] = round(value, 2)
        return result

    def add(self, holding: Holding) -> None:
        """Add a holding, merging duplicates by summing market value."""
        for existing in self.holdings:
            if existing.asset_class == holding.asset_class:
                merged = Holding(
                    asset_class=existing.asset_class,
                    market_value=existing.market_value + holding.market_value,
                    cost_basis=existing.cost_basis + holding.cost_basis,
                    quantity=(
                        (existing.quantity or 0.0) + (holding.quantity or 0.0)
                        if existing.quantity is not None or holding.quantity is not None
                        else None
                    ),
                )
                self.holdings.remove(existing)
                self.holdings.append(merged)
                return
        self.holdings.append(holding)


@dataclass(frozen=True)
class Trade:
    """A single buy or sell order implied by rebalancing.

    Attributes
    ----------
    asset_class:
        The instrument being traded.
    amount:
        Positive = buy, negative = sell (rupees of notional).
    reason:
        Plain-language justification.
    estimated_tax_impact:
        Rupees of capital-gains tax if this is a sale (0 for buys).
    estimated_transaction_cost:
        Rupees of transaction cost for this trade.
    """

    asset_class: AssetClass
    amount: float  # positive buy / negative sell
    reason: str = ""
    estimated_tax_impact: float = 0.0
    estimated_transaction_cost: float = 0.0

    def is_buy(self) -> bool:
        """Whether this trade is a purchase."""
        return self.amount > 0

    def is_sell(self) -> bool:
        """Whether this trade is a sale."""
        return self.amount < 0

    @property
    def absolute_amount(self) -> float:
        """Absolute rupee notional of the trade."""
        return abs(self.amount)
