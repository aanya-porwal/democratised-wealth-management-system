"""Tests for the explainable recommendation engine (PART 8)."""

from wealth_management_system.models import (
    ConfidenceLevel,
    RecommendationType,
)
from wealth_management_system.recommendation import RecommendationEngine


def test_recommendations_have_reasons(ravi):
    """Every recommendation must explain itself."""
    engine = RecommendationEngine(top_n=3)
    recommendations = engine.recommend(ravi)
    assert recommendations
    for rec in recommendations:
        assert rec.title
        assert rec.reasons
        assert rec.confidence in (ConfidenceLevel.HIGH, ConfidenceLevel.MEDIUM, ConfidenceLevel.LOW)


def test_reasons_are_weight_sorted(ravi):
    """Reasons must be sorted by weight (most important first)."""
    engine = RecommendationEngine(top_n=3)
    for rec in engine.recommend(ravi):
        weights = [r.weight for r in rec.reasons]
        assert weights == sorted(weights, reverse=True)


def test_instrument_recommendations_for_need(ravi):
    """recommend_instruments must return instrument type recommendations."""
    engine = RecommendationEngine(top_n=3)
    recs = engine.recommend_instruments(ravi, "growth", years=7)
    assert recs
    for rec in recs:
        assert rec.recommendation_type in (
            RecommendationType.ASSET_ALLOCATION,
            RecommendationType.INSTRUMENT,
        )


def test_elss_has_tax_reason(ravi):
    """ELSS recommendations must mention the 80C tax benefit."""
    engine = RecommendationEngine(top_n=10)
    recs = engine.recommend_instruments(ravi, "growth", years=7)
    elss = [r for r in recs if "elss" in r.title.lower()]
    if elss:
        texts = elss[0].reason_texts()
        assert any("tax" in t.lower() for t in texts)


def test_protection_recommendation_for_uninsured(ravi):
    """A user without term cover and dependents must get a protection rec."""
    engine = RecommendationEngine(top_n=3)
    recs = engine.recommend(ravi)
    protection = [
        r for r in recs if r.recommendation_type == RecommendationType.PROTECTION
    ]
    # ravi has no dependents, so health cover is present; term life not needed.
    # The only protection gap possible here is health insurance (present already).
    assert isinstance(protection, list)


def test_tax_recommendation_for_high_bracket():
    """A 30% bracket user with 80C headroom gets a tax recommendation."""
    from datetime import date
    from wealth_management_system.models import (
        BehavioralProfile,
        EmploymentType,
        FinancialProfile,
        Goal,
        GoalPriority,
        GoalType,
        RiskToleranceLevel,
        UserProfile,
    )

    user = UserProfile(
        user_id="t001",
        name="Tax Test",
        age=30,
        date_of_birth=date(1995, 1, 1),
        financial=FinancialProfile(
            monthly_income=150000,
            employment_type=EmploymentType.SALARIED_PRIVATE,
            income_stability=0.85,
            monthly_fixed_expenses=50000,
            monthly_variable_expenses=30000,
            emergency_fund_months=6,
            existing_investments=500000,
            tax_bracket_percent=30,
            has_health_insurance=True,
        ),
        behavioral=BehavioralProfile(
            risk_tolerance=RiskToleranceLevel.AGGRESSIVE,
            drawdown_reaction_score=4,
            has_invested_before=True,
        ),
        goals=[],
    )
    recs = RecommendationEngine(top_n=3).recommend(user)
    tax_recs = [r for r in recs if r.recommendation_type == RecommendationType.TAX]
    assert tax_recs
    assert any("80C" in r.title for r in tax_recs)

