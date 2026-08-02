"""Plotting helpers (optional matplotlib dependency).

These functions are kept completely separate from the simulation and
allocation engines so the core logic never requires matplotlib. Importing
this module fails gracefully if matplotlib is unavailable.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from wealth_management_system.models.simulation import SimulationResult

if TYPE_CHECKING:
    import matplotlib.pyplot as plt

try:  # pragma: no cover - depends on environment
    import matplotlib.pyplot as plt

    _HAS_MPL = True
except ImportError:  # pragma: no cover
    plt = None  # type: ignore[assignment]
    _HAS_MPL = False


def plot_simulation_histogram(
    result: SimulationResult,
    *,
    bins: int = 50,
    title: str = "Simulated Corpus Distribution",
    target_line: Optional[float] = None,
    show: bool = False,
) -> Optional["plt.Axes"]:
    """Plot a histogram of the simulated terminal corpus values.

    Parameters
    ----------
    result:
        The simulation result containing terminal values.
    bins:
        Number of histogram bins.
    title:
        Chart title.
    target_line:
        Optional goal target; drawn as a vertical line so the user can
        see how many paths clear it.
    show:
        Whether to call ``plt.show()`` (useful in notebooks). Defaults
        to False so callers control rendering.

    Returns
    -------
    Optional[plt.Axes]
        The matplotlib axes, or ``None`` if matplotlib is unavailable.

    Raises
    ------
    ImportError
        If matplotlib is not installed.
    """
    if not _HAS_MPL or plt is None:
        raise ImportError(
            "matplotlib is required for plotting; install it or use the "
            "engine's pure-data outputs instead"
        )

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.hist(result.terminal_values, bins=bins, color="#2563eb", alpha=0.75, edgecolor="white")
    if target_line is not None:
        ax.axvline(target_line, color="#dc2626", linestyle="--", linewidth=1.5,
                   label=f"Target ₹{target_line:,.0f}")
        ax.legend()
    ax.axvline(result.statistics.median, color="#16a34a", linestyle=":", linewidth=1.5,
               label=f"Median ₹{result.statistics.median:,.0f}")
    ax.legend()
    ax.set_title(title)
    ax.set_xlabel("Corpus at target date (₹)")
    ax.set_ylabel("Frequency")
    ax.grid(alpha=0.3)
    fig.tight_layout()
    if show:  # pragma: no cover - interactive
        plt.show()
    return ax


def plot_allocation(
    allocation: dict[str, float],
    *,
    title: str = "Target Asset Allocation",
    show: bool = False,
) -> Optional["plt.Axes"]:
    """Plot a target allocation as a pie chart.

    Parameters
    ----------
    allocation:
        Mapping of bucket name -> weight (0..1).
    title:
        Chart title.
    show:
        Whether to call ``plt.show()``.

    Returns
    -------
    Optional[plt.Axes]
        The matplotlib axes, or ``None`` if matplotlib is unavailable.
    """
    if not _HAS_MPL or plt is None:
        raise ImportError(
            "matplotlib is required for plotting; install it or use the "
            "engine's pure-data outputs instead"
        )

    labels = list(allocation.keys())
    sizes = [w * 100 for w in allocation.values()]
    fig, ax = plt.subplots(figsize=(8, 8))
    ax.pie(sizes, labels=labels, autopct="%1.0f%%", startangle=90,
           colors=plt.cm.Set3(range(len(labels))))
    ax.set_title(title)
    fig.tight_layout()
    if show:  # pragma: no cover - interactive
        plt.show()
    return ax
