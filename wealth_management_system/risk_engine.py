"""Risk scoring and assessment engine.

Every function in this module is concerned with measuring how much risk a
user *can* take (capacity) and how much they are *willing* to take
(tolerance), and combining the two into a single ``RiskAssessment``.

The final score treats **capacity as a ceiling** — a user can never take
more risk than they can financially absorb.
"""

from wealth_management_system.models import (
    BehavioralProfile,
    EmploymentType,
    RiskAssessment,
    RiskToleranceLevel,
    UserProfile,
)

# ─────────────────────────────────────────────────────────────────────
# Individual capacity factors
# ─────────────────────────────────────────────────────────────────────


def score_income_stability(
    employment_type: EmploymentType, income_stability: float
) -> float:
    """Score income stability on a 0.0–1.0 scale.

    Starts from a base score implied by the employment type and blends it
    with the user-stated stability figure (both are trusted equally).
    """
    base_scores = {
        EmploymentType.SALARIED_GOVT: 1.0,
        EmploymentType.SALARIED_PRIVATE: 0.8,  # layoffs? highly replaceable
        EmploymentType.BUSINESS_OWNER: 0.6,
        EmploymentType.SELF_EMPLOYED: 0.55,
        EmploymentType.FREELANCER: 0.45,
        EmploymentType.STUDENT: 0.2,
        EmploymentType.RETIRED: 0.7,  # pension/fixed income
        EmploymentType.UNEMPLOYED: 0.0,
    }
    base = base_scores[employment_type]
    return (base + income_stability) / 2


def score_emergency_fund(emergency_fund_months: float) -> float:
    """Score emergency-fund readiness on a 0.0–1.0 scale.

    The emergency fund is the #1 prerequisite for any investment — without
    it, any market dip forces premature withdrawal.
    """
    if emergency_fund_months >= 6:
        return 1.0
    elif emergency_fund_months >= 3:
        return 0.7
    elif emergency_fund_months >= 1:
        return 0.4
    else:
        return 0.1


def score_debt_burden(debt_to_income: float) -> float:
    """Score debt burden on a 0.0–1.0 scale.

    High EMI obligations reduce investable surplus *and* increase
    vulnerability to income shocks.
    """
    if debt_to_income == 0:
        return 1.0
    elif debt_to_income <= 0.1:
        return 0.9
    elif debt_to_income <= 0.2:
        return 0.75
    elif debt_to_income <= 0.35:
        return 0.5
    elif debt_to_income <= 0.5:
        return 0.25
    else:
        return 0.1  # dangerously over-leveraged


def score_surplus_ratio(monthly_surplus: float, monthly_income: float) -> float:
    """Score investable-surplus ratio on a 0.0–1.0 scale.

    Measures what fraction of income is actually free to invest — a low
    surplus means low capacity even if income is high.
    """
    if monthly_income == 0:
        return 0.0
    ratio = monthly_surplus / monthly_income
    if ratio >= 0.4:
        return 1.0
    elif ratio >= 0.25:
        return 0.8
    elif ratio >= 0.15:
        return 0.6
    elif ratio >= 0.05:
        return 0.35
    else:
        return 0.1


def score_dependents(dependents: int, age: int) -> float:
    """Score dependents burden on a 0.0–1.0 scale.

    More dependents means more financial obligations. Age matters too —
    dependents at 28 vs 50 are very different situations.
    """
    if dependents == 0:
        return 1.0
    elif dependents == 1:
        return 0.8
    elif dependents == 2:
        return 0.65
    elif dependents == 3:
        return 0.45
    else:
        return 0.3


# ─────────────────────────────────────────────────────────────────────
# Risk capacity & tolerance
# ─────────────────────────────────────────────────────────────────────


def calculate_risk_capacity(profile: UserProfile) -> float:
    """Weighted combination of all capacity factors (0.0–1.0).

    Weights reflect real-world importance:

    - Emergency fund is the foundation — highest weight
    - Income stability determines ability to stay invested
    - Debt burden directly competes with investments
    - Surplus ratio is the practical constraint
    - Dependents add obligation risk
    """
    financial = profile.financial

    scores = {
        "emergency_fund": score_emergency_fund(financial.emergency_fund_months),
        "income_stability": score_income_stability(
            financial.employment_type, financial.income_stability
        ),
        "debt_burden": score_debt_burden(financial.debt_to_income_ratio()),
        "surplus_ratio": score_surplus_ratio(
            financial.monthly_surplus(), financial.monthly_income
        ),
        "dependents": score_dependents(profile.dependents, profile.age),
    }

    weights = {
        "emergency_fund": 0.30,
        "income_stability": 0.25,
        "debt_burden": 0.20,
        "surplus_ratio": 0.15,
        "dependents": 0.10,
    }

    capacity_score = sum(scores[key] * weights[key] for key in scores)
    return round(capacity_score, 4)


def calculate_risk_tolerance(profile: UserProfile) -> float:
    """Behavioural / psychological risk tolerance (0.0–1.0)."""
    behavioural: BehavioralProfile = profile.behavioral

    # Stated tolerance (from the enum)
    tolerance_map = {
        RiskToleranceLevel.VERY_CONSERVATIVE: 0.1,
        RiskToleranceLevel.CONSERVATIVE: 0.3,
        RiskToleranceLevel.MODERATE: 0.5,
        RiskToleranceLevel.AGGRESSIVE: 0.75,
        RiskToleranceLevel.VERY_AGGRESSIVE: 1.0,
    }
    stated = tolerance_map[behavioural.risk_tolerance]

    # Drawdown reaction (1 = panic sell, 5 = buy more)
    drawdown = (behavioural.drawdown_reaction_score - 1) / 4  # normalise to 0-1

    # Experience modifiers
    experience_bonus = 0.0
    if behavioural.has_invested_before:
        experience_bonus += 0.05
    if behavioural.has_experienced_market_crash:
        experience_bonus += 0.05  # survived a crash = more realistic

    # Loss aversion penalty (5 = very loss averse)
    loss_aversion_penalty = (behavioural.loss_aversion_score - 1) / 4 * 0.1

    # Financial literacy — more literate = better calibrated
    literacy_bonus = (behavioural.financial_literacy_score - 1) / 4 * 0.05

    tolerance_score = (
        stated * 0.40
        + drawdown * 0.40
        + experience_bonus
        + literacy_bonus
        - loss_aversion_penalty
    )

    return round(min(max(tolerance_score, 0.0), 1.0), 4)  # clamp to 0-1


# ─────────────────────────────────────────────────────────────────────
# Final assessment
# ─────────────────────────────────────────────────────────────────────


def categorise_risk(score: float) -> str:
    """Map a 0.0–1.0 risk score to a human-readable category."""
    if score < 0.2:
        return "Very Conservative"
    elif score < 0.4:
        return "Conservative"
    elif score < 0.6:
        return "Moderate"
    elif score < 0.75:
        return "Aggressive"
    else:
        return "Very Aggressive"


def assess_risk(profile: UserProfile) -> RiskAssessment:
    """Produce the full risk assessment for a user.

    Capacity acts as a ceiling — a user can never take more risk than
    they can financially absorb.
    """
    capacity = calculate_risk_capacity(profile)
    tolerance = calculate_risk_tolerance(profile)

    raw_final = tolerance * 0.45 + capacity * 0.55
    final = min(raw_final, capacity)  # the ceiling

    capacity_was_binding = final < raw_final

    return RiskAssessment(
        capacity_score=capacity,
        tolerance_score=tolerance,
        final_score=round(final, 4),
        final_score_100=int(final * 100),
        risk_category=categorise_risk(final),
        capacity_was_binding=capacity_was_binding,
        breakdown={
            "capacity": capacity,
            "tolerance": tolerance,
            "raw_combined": round(raw_final, 4),
            "capacity_ceiling_applied": capacity_was_binding,
        },
    )

