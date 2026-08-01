"""Demo users and life-stage archetypes.

Every engine test, demo and sanity check draws from here. Each user is a
realistic Indian profile so the financial intelligence actually has
something to reason about — from a student to a retiree, from high debt
to high net worth.

Importing this module has no side effects.
"""

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

# ─────────────────────────────────────────────────────────────────────
# Core demo users
# ─────────────────────────────────────────────────────────────────────

# ravi — 28, software engineer, mumbai. good income, thin emergency fund,
# some debt, aggressive on paper. classic "investing before foundations" case.
ravi = UserProfile(
    user_id="u001",
    name="Ravi Shankar",
    age=28,
    date_of_birth=date(1996, 3, 15),
    dependents=0,
    financial=FinancialProfile(
        monthly_income=85000,
        employment_type=EmploymentType.SALARIED_PRIVATE,
        income_stability=0.85,
        monthly_fixed_expenses=35000,  # rent + EMI
        monthly_variable_expenses=20000,
        emergency_fund_months=1.5,
        existing_investments=80000,
        provident_fund_balance=45000,
        total_debt=200000,
        monthly_emi_total=8000,
        tax_bracket_percent=20,
        has_term_life_insurance=False,
        has_health_insurance=True,
    ),
    behavioral=BehavioralProfile(
        risk_tolerance=RiskToleranceLevel.AGGRESSIVE,
        drawdown_reaction_score=4,
        has_invested_before=True,
        has_experienced_market_crash=False,
        financial_literacy_score=3,
        loss_aversion_score=2,
    ),
    goals=[
        Goal(
            goal_type=GoalType.EMERGENCY_FUND,
            priority=GoalPriority.CRITICAL,
            target_amount=180000,  # 6 months expenses
            target_date=date(2026, 12, 31),
            current_savings_for_goal=52500,  # 1.5 months already saved
        ),
        Goal(
            goal_type=GoalType.WEALTH_CREATION,
            priority=GoalPriority.HIGH,
            target_amount=1_00_00_000,
            target_date=date(2040, 1, 1),
        ),
    ],
)

# meena — 44, tier 3 city, small business owner, 2 kids. low income
# stability, thin emergency fund, but owns gold. classic "protect first" case.
meena = UserProfile(
    user_id="u002",
    name="Meena Devi",
    age=44,
    date_of_birth=date(1980, 6, 20),
    dependents=2,
    financial=FinancialProfile(
        monthly_income=35000,
        employment_type=EmploymentType.BUSINESS_OWNER,
        income_stability=0.55,
        monthly_fixed_expenses=18000,
        monthly_variable_expenses=10000,
        emergency_fund_months=1.0,
        existing_investments=120000,
        provident_fund_balance=0,
        gold_value=200000,
        total_debt=150000,
        monthly_emi_total=5000,
        tax_bracket_percent=5,
        has_term_life_insurance=False,
        has_health_insurance=True,
    ),
    behavioral=BehavioralProfile(
        risk_tolerance=RiskToleranceLevel.MODERATE,
        drawdown_reaction_score=2,
        has_invested_before=True,
        has_experienced_market_crash=False,
        financial_literacy_score=2,
        loss_aversion_score=4,
    ),
    goals=[
        Goal(
            goal_type=GoalType.EDUCATION_CHILD,
            priority=GoalPriority.CRITICAL,
            target_amount=800000,
            target_date=date(2030, 6, 1),
            current_savings_for_goal=0,
        ),
        Goal(
            goal_type=GoalType.RETIREMENT,
            priority=GoalPriority.HIGH,
            target_amount=1_50_00_000,
            target_date=date(2045, 1, 1),
        ),
    ],
)

# ─────────────────────────────────────────────────────────────────────
# Life-stage / financial archetypes
# ─────────────────────────────────────────────────────────────────────


def _student() -> UserProfile:
    """student — no income, tiny savings, first job soon."""
    return UserProfile(
        user_id="u101",
        name="Aarav Student",
        age=21,
        date_of_birth=date(2004, 6, 10),
        dependents=0,
        financial=FinancialProfile(
            monthly_income=5000,  # pocket money / part time
            employment_type=EmploymentType.STUDENT,
            income_stability=0.2,
            monthly_fixed_expenses=3000,
            monthly_variable_expenses=4000,
            emergency_fund_months=0.0,
            existing_investments=0,
            tax_bracket_percent=0,
        ),
        behavioral=BehavioralProfile(
            risk_tolerance=RiskToleranceLevel.AGGRESSIVE,
            drawdown_reaction_score=4,
            has_invested_before=False,
            financial_literacy_score=2,
        ),
        goals=[
            Goal(
                goal_type=GoalType.EMERGENCY_FUND,
                priority=GoalPriority.CRITICAL,
                target_amount=14000,  # 2 months of expenses
                target_date=date(2027, 1, 1),
            ),
            Goal(
                goal_type=GoalType.EDUCATION_SELF,
                priority=GoalPriority.HIGH,
                target_amount=300000,
                target_date=date(2028, 6, 1),
            ),
        ],
    )


def _retiree() -> UserProfile:
    """retiree — fixed pension, capital preservation first."""
    return UserProfile(
        user_id="u102",
        name="Sharma Retiree",
        age=65,
        date_of_birth=date(1960, 2, 2),
        dependents=0,
        financial=FinancialProfile(
            monthly_income=40000,  # pension + rent
            employment_type=EmploymentType.RETIRED,
            income_stability=0.95,
            monthly_fixed_expenses=15000,
            monthly_variable_expenses=12000,
            emergency_fund_months=12.0,
            existing_investments=2500000,
            provident_fund_balance=0,
            real_estate_value=4000000,
            gold_value=300000,
            total_debt=0,
            monthly_emi_total=0,
            tax_bracket_percent=10,
            has_term_life_insurance=False,
            has_health_insurance=True,
        ),
        behavioral=BehavioralProfile(
            risk_tolerance=RiskToleranceLevel.CONSERVATIVE,
            drawdown_reaction_score=1,
            has_invested_before=True,
            has_experienced_market_crash=True,
            financial_literacy_score=2,
            loss_aversion_score=5,
        ),
        goals=[
            Goal(
                goal_type=GoalType.RETIREMENT,
                priority=GoalPriority.CRITICAL,
                target_amount=6000000,  # 15+ years of expenses
                target_date=date(2035, 1, 1),
                current_savings_for_goal=2800000,
            ),
        ],
    )


def _high_debt_professional() -> UserProfile:
    """high-debt professional — good income, over-leveraged, investing too early."""
    return UserProfile(
        user_id="u103",
        name="Karan HighDebt",
        age=31,
        date_of_birth=date(1994, 8, 8),
        dependents=1,
        financial=FinancialProfile(
            monthly_income=120000,
            employment_type=EmploymentType.SALARIED_PRIVATE,
            income_stability=0.8,
            monthly_fixed_expenses=65000,  # rent + car + personal loan EMIs
            monthly_variable_expenses=30000,
            emergency_fund_months=0.5,
            existing_investments=200000,  # investing despite the debt
            provident_fund_balance=60000,
            total_debt=1200000,
            monthly_emi_total=42000,
            tax_bracket_percent=30,
            has_term_life_insurance=True,
            has_health_insurance=True,
        ),
        behavioral=BehavioralProfile(
            risk_tolerance=RiskToleranceLevel.VERY_AGGRESSIVE,
            drawdown_reaction_score=5,
            has_invested_before=True,
            has_experienced_market_crash=False,
            financial_literacy_score=3,
            loss_aversion_score=1,
        ),
        goals=[
            Goal(
                goal_type=GoalType.EMERGENCY_FUND,
                priority=GoalPriority.CRITICAL,
                target_amount=285000,  # 3 months of expenses
                target_date=date(2026, 12, 31),
                current_savings_for_goal=47500,
            ),
            Goal(
                goal_type=GoalType.HOME_PURCHASE,
                priority=GoalPriority.HIGH,
                target_amount=3000000,
                target_date=date(2031, 1, 1),
            ),
        ],
    )


def _working_parent() -> UserProfile:
    """working parent — two incomes, family, multiple goals, decent health."""
    return UserProfile(
        user_id="u104",
        name="Priya Parent",
        age=38,
        date_of_birth=date(1987, 5, 5),
        dependents=2,
        financial=FinancialProfile(
            monthly_income=95000,
            employment_type=EmploymentType.SALARIED_GOVT,
            income_stability=0.95,
            monthly_fixed_expenses=38000,
            monthly_variable_expenses=25000,
            emergency_fund_months=6.0,
            existing_investments=600000,
            provident_fund_balance=400000,
            real_estate_value=0,
            gold_value=150000,
            total_debt=400000,  # home loan
            monthly_emi_total=12000,
            tax_bracket_percent=20,
            has_term_life_insurance=True,
            has_health_insurance=True,
        ),
        behavioral=BehavioralProfile(
            risk_tolerance=RiskToleranceLevel.MODERATE,
            drawdown_reaction_score=3,
            has_invested_before=True,
            has_experienced_market_crash=True,
            financial_literacy_score=4,
            loss_aversion_score=3,
        ),
        goals=[
            Goal(
                goal_type=GoalType.EMERGENCY_FUND,
                priority=GoalPriority.CRITICAL,
                target_amount=378000,  # 6 months of expenses
                target_date=date(2027, 1, 1),
                current_savings_for_goal=378000,  # already complete
            ),
            Goal(
                goal_type=GoalType.EDUCATION_CHILD,
                priority=GoalPriority.CRITICAL,
                target_amount=1500000,
                target_date=date(2035, 6, 1),
                current_savings_for_goal=300000,
                current_monthly_contribution=5000,
            ),
            Goal(
                goal_type=GoalType.RETIREMENT,
                priority=GoalPriority.HIGH,
                target_amount=20000000,
                target_date=date(2047, 1, 1),
                current_savings_for_goal=1000000,
                current_monthly_contribution=15000,
            ),
            Goal(
                goal_type=GoalType.TRAVEL,
                priority=GoalPriority.ASPIRATIONAL,
                target_amount=300000,
                target_date=date(2028, 12, 1),
                current_savings_for_goal=50000,
            ),
        ],
    )


def _hnw() -> UserProfile:
    """high net worth — plenty of cash, conflicting goals, poor structure."""
    return UserProfile(
        user_id="u105",
        name="Vikram HNW",
        age=45,
        date_of_birth=date(1980, 1, 1),
        dependents=3,
        financial=FinancialProfile(
            monthly_income=500000,
            employment_type=EmploymentType.BUSINESS_OWNER,
            income_stability=0.6,
            monthly_fixed_expenses=180000,
            monthly_variable_expenses=100000,
            emergency_fund_months=18.0,  # idle cash beyond the need
            existing_investments=500000,
            provident_fund_balance=0,
            real_estate_value=15000000,
            gold_value=2000000,
            total_debt=0,
            monthly_emi_total=0,
            tax_bracket_percent=30,
            has_term_life_insurance=False,  # under-insured for 3 dependents
            has_health_insurance=True,
        ),
        behavioral=BehavioralProfile(
            risk_tolerance=RiskToleranceLevel.VERY_AGGRESSIVE,
            drawdown_reaction_score=5,
            has_invested_before=True,
            has_experienced_market_crash=True,
            financial_literacy_score=3,
            loss_aversion_score=2,
        ),
        goals=[
            Goal(
                goal_type=GoalType.RETIREMENT,
                priority=GoalPriority.CRITICAL,
                target_amount=30000000,
                target_date=date(2040, 1, 1),
                current_savings_for_goal=5000000,
            ),
            Goal(
                goal_type=GoalType.WEALTH_CREATION,
                priority=GoalPriority.HIGH,
                target_amount=50000000,
                target_date=date(2045, 1, 1),
                current_savings_for_goal=2000000,
            ),
            Goal(
                goal_type=GoalType.HOME_PURCHASE,
                priority=GoalPriority.HIGH,
                target_amount=20000000,  # conflicting with retirement
                target_date=date(2032, 1, 1),
            ),
        ],
    )


# all archetypes keyed by short id for the test suite
ARCHETYPES = {
    "student": _student,
    "retiree": _retiree,
    "high_debt": _high_debt_professional,
    "working_parent": _working_parent,
    "hnw": _hnw,
}


def build_all_sample_users() -> list:
    """Return ravi, meena and every archetype as a flat list."""
    return [ravi, meena] + [builder() for builder in ARCHETYPES.values()]

