"""tests for the asset universe and core data models."""

from wealth_management_system.assets import (
    ASSET_PROFILES,
    effective_return_after_tax,
)
from wealth_management_system.models import (
    AssetCategory,
    AssetClass,
    TaxTreatment,
)
from wealth_management_system.sample_users import ravi


def test_every_asset_class_has_a_profile():
    """the database must cover the entire enum, no gaps."""
    missing = set(AssetClass) - set(ASSET_PROFILES.keys())
    assert not missing


def test_asset_profiles_are_sensible():
    """returns and risk levels must be internally consistent."""
    for ac, p in ASSET_PROFILES.items():
        assert p.expected_annual_return >= 0.0
        assert p.annual_volatility >= 0.0
        assert 1 <= p.risk_level <= 10
        assert p.liquidity_score <= 1.0
        # cash must never carry equity-level risk
        if p.category == AssetCategory.CASH_AND_LIQUID:
            assert p.risk_level <= 2


def test_tax_treatment_reduces_return():
    """after-tax return must never exceed the gross return for taxed assets."""
    for ac, p in ASSET_PROFILES.items():
        if p.tax_treatment in (TaxTreatment.EEE,):
            continue  # fully exempt — no drag
        after_tax = effective_return_after_tax(p, tax_bracket=0.30, holding_years=5)
        assert after_tax <= p.expected_annual_return + 1e-9


def test_elss_gets_80c_bonus():
    """ELSS with 80C headroom must beat plain equity for a high bracket user."""
    elss = ASSET_PROFILES[AssetClass.EQUITY_ELSS]
    index = ASSET_PROFILES[AssetClass.EQUITY_INDEX_LARGECAP]
    eff_elss = effective_return_after_tax(elss, tax_bracket=0.30, holding_years=3, has_80c_headroom=True)
    eff_index = effective_return_after_tax(index, tax_bracket=0.30, holding_years=3)
    assert eff_elss > eff_index


def test_goal_model_derived_properties():
    """years_to_goal and amount_remaining must be correct."""
    goal = ravi.goals[0]
    assert goal.amount_remaining() >= 0
    assert goal.years_to_goal() >= 0

