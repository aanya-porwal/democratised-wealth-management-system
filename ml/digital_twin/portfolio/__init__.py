"""Portfolio evolution for digital twins.

The twin's portfolio is a :class:`PortfolioState` that evolves as
market returns are applied, investments are added/withdrawn, or the
allocation is rebalanced. These helpers mutate the twin's portfolio
state and emit the corresponding immutable events into the timeline.
"""

from ml.digital_twin.portfolio.evolution import (  # noqa: F401
    add_investment,
    apply_market_returns,
    rebalance_to_weights,
    withdraw_investment,
)

__all__ = ["add_investment", "apply_market_returns", "rebalance_to_weights", "withdraw_investment"]
