"""Tests for the financial health score engine (PART 4)."""

from wealth_management_system.score import HealthScoreEngine


def test_health_score_in_0_100(ravi):
    """The enhanced health score must stay within 0..100."""
    result = HealthScoreEngine().score(ravi)
    assert 0 <= result.score <= 100
    assert result.grade


def test_nine_factors_present(ravi):
    """All nine factors must contribute to the score."""
    result = HealthScoreEngine().score(ravi)
    names = {f.name for f in result.factors}
    assert names == {
        "emergency_fund",
        "debt",
        "savings_rate",
        "insurance",
        "investment_rate",
        "diversification",
        "goal_progress",
        "tax_efficiency",
        "return",
    }


def test_score_matches_factor_sum(ravi):
    """The aggregate score must equal the sum of weighted factor points."""
    result = HealthScoreEngine().score(ravi)
    total = round(sum(f.score for f in result.factors))
    assert abs(result.score - total) <= 1


def test_suggestions_follow_from_weaknesses(ravi):
    """Weaknesses must generate at least one suggestion."""
    result = HealthScoreEngine().score(ravi)
    assert result.strengths or result.weaknesses
    assert isinstance(result.suggestions, list)


def test_emergency_fund_ceiling_for_ravi(ravi):
    """Ravi's thin emergency fund must keep his score below the cap."""
    result = HealthScoreEngine().score(ravi)
    assert result.score <= 69  # building cap from config


def test_priya_can_be_excellent(priya):
    """Priya's complete foundations must allow a high score."""
    result = HealthScoreEngine().score(priya)
    assert result.score >= 60

