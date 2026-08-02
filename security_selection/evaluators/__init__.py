"""Evaluators package — concrete asset-class evaluator implementations.

Every evaluator subclasses :class:`BaseEvaluator` and implements only
the asset-specific pipeline stages. The core engine never knows how an
ETF or a Bond works.

Adding a new asset class = create a new evaluator module + register it
in :func:`build_default_registry`. No core code changes.
"""

from __future__ import annotations

from security_selection.base.registry import EvaluatorRegistry
from security_selection.base.provider import BaseProviderSet
from security_selection.models.enums import TargetAssetClass

from security_selection.evaluators.mutual_fund import MutualFundEvaluator
from security_selection.evaluators.etf import ETFEvaluator
from security_selection.evaluators.stock import StockEvaluator
from security_selection.evaluators.gold_etf import GoldETFEvaluator
from security_selection.evaluators.sgb import SGBEvaluator
from security_selection.evaluators.international_etf import InternationalETFEvaluator
from security_selection.evaluators.international_fund import InternationalFundEvaluator
from security_selection.evaluators.corporate_bond import CorporateBondEvaluator
from security_selection.evaluators.government_bond import GovernmentBondEvaluator
from security_selection.evaluators.reit import REITEvaluator
from security_selection.evaluators.invit import InvITEvaluator
from security_selection.evaluators.fixed_deposit import FixedDepositEvaluator
from security_selection.evaluators.ppf import PPFEvaluator
from security_selection.evaluators.nps import NPSEvaluator

__all__ = [
    "MutualFundEvaluator",
    "ETFEvaluator",
    "StockEvaluator",
    "GoldETFEvaluator",
    "SGBEvaluator",
    "InternationalETFEvaluator",
    "InternationalFundEvaluator",
    "CorporateBondEvaluator",
    "GovernmentBondEvaluator",
    "REITEvaluator",
    "InvITEvaluator",
    "FixedDepositEvaluator",
    "PPFEvaluator",
    "NPSEvaluator",
    "build_default_registry",
]


def build_default_registry(providers: BaseProviderSet) -> EvaluatorRegistry:
    """Build the default evaluator registry with all built-in evaluators.

    Each :class:`TargetAssetClass` maps to one or more evaluator instances.
    The registry is used by the :class:`SelectionService` to dispatch
    selection requests to the correct evaluator(s).

    Parameters
    ----------
    providers:
        The provider set to inject into every evaluator.

    Returns
    -------
    EvaluatorRegistry
        A populated registry instance.
    """
    registry = EvaluatorRegistry()

    # ── Equity ETFs ────────────────────────────────────────────────
    registry.register(
        TargetAssetClass.LARGE_CAP_EQUITY,
        ETFEvaluator(providers, target=TargetAssetClass.LARGE_CAP_EQUITY),
    )
    registry.register(
        TargetAssetClass.MID_CAP_EQUITY,
        ETFEvaluator(providers, target=TargetAssetClass.MID_CAP_EQUITY),
    )
    registry.register(
        TargetAssetClass.SMALL_CAP_EQUITY,
        ETFEvaluator(providers, target=TargetAssetClass.SMALL_CAP_EQUITY),
    )
    registry.register(
        TargetAssetClass.FLEXI_CAP_EQUITY,
        ETFEvaluator(providers, target=TargetAssetClass.FLEXI_CAP_EQUITY),
    )

    # ── Mutual Funds ───────────────────────────────────────────────
    registry.register(
        TargetAssetClass.ELSS_EQUITY,
        MutualFundEvaluator(providers, target=TargetAssetClass.ELSS_EQUITY),
    )
    registry.register(
        TargetAssetClass.INTERNATIONAL_EQUITY,
        InternationalFundEvaluator(providers),
    )

    # ── Gold ───────────────────────────────────────────────────────
    registry.register(
        TargetAssetClass.GOLD_ETF,
        GoldETFEvaluator(providers),
    )
    registry.register(
        TargetAssetClass.SGB,
        SGBEvaluator(providers),
    )
    registry.register(
        TargetAssetClass.GOLD,
        GoldETFEvaluator(providers, target=TargetAssetClass.GOLD),
    )

    # ── Bonds ──────────────────────────────────────────────────────
    registry.register(
        TargetAssetClass.CORPORATE_BONDS,
        CorporateBondEvaluator(providers),
    )
    registry.register(
        TargetAssetClass.GOVERNMENT_BONDS,
        GovernmentBondEvaluator(providers),
    )
    registry.register(
        TargetAssetClass.DEBT,
        CorporateBondEvaluator(providers, target=TargetAssetClass.DEBT),
    )

    # ── Real Assets ────────────────────────────────────────────────
    registry.register(
        TargetAssetClass.REIT,
        REITEvaluator(providers),
    )
    registry.register(
        TargetAssetClass.INVIT,
        InvITEvaluator(providers),
    )

    # ── Fixed Income (defined-benefit) ─────────────────────────────
    registry.register(
        TargetAssetClass.FIXED_DEPOSIT,
        FixedDepositEvaluator(providers),
    )
    registry.register(
        TargetAssetClass.PPF,
        PPFEvaluator(providers),
    )
    registry.register(
        TargetAssetClass.NPS,
        NPSEvaluator(providers),
    )

    # ── Stocks ─────────────────────────────────────────────────────
    registry.register(
        TargetAssetClass.STOCKS,
        StockEvaluator(providers),
    )

    return registry
