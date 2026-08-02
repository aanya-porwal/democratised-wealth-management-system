"""Portfolio optimization package.

Implements a pluggable optimization layer. The entry point is
:class:`Optimizer` which dispatches to a concrete strategy
(:class:`MeanVarianceOptimizer` is the first implementation). Additional
algorithms (Black-Litterman, risk-parity, ...) can be added without
touching the public API.
"""

from wealth_management_system.optimization.engine import (
    MeanVarianceOptimizer,
    Optimizer,
)

__all__ = ["Optimizer", "MeanVarianceOptimizer"]

