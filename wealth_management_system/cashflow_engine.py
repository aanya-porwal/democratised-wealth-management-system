"""cashflow engine — surplus, savings rate and emergency fund.

before recommending any investment we need to know how much money the
user actually has to work with each month. this engine answers that:

* true monthly surplus (after committed sip already deducted)
* savings rate as a fraction of income
* how many months the emergency fund covers, and how far it is from the
  recommended target

the emergency fund is the foundation. every other engine depends on the
surplus it computes here.
"""

from dataclasses import dataclass

from wealth_management_system.models import UserProfile

# emergency fund should cover 6 months of fixed + variable expenses
# for a salaried user, more for an irregular income. conservative default.
RECOMMENDED_EMERGENCY_FUND_MONTHS: float = 6.0
# irregular earners (freelancer, business owner) need a thicker buffer
IRREGULAR_INCOME_BUFFER_MONTHS: float = 9.0

# income types with unpredictable cash flow — plan for a bigger cushion
_IRREGULAR_EMPLOYMENT = {"freelancer", "business_owner", "self_employed"}


@dataclass
class CashflowSnapshot:
    """the monthly cashflow picture for a user."""

    monthly_income: float
    monthly_expenses: float
    monthly_surplus: float
    committed_sip: float
    discretionary_surplus: float  # surplus left after existing sip
    savings_rate: float  # 0.0 to 1.0, surplus / income
    emergency_fund_months: float  # current coverage
    emergency_fund_target_months: float  # recommended coverage
    emergency_fund_gap_months: float  # how many months short
    emergency_fund_amount_needed: float  # rupees to reach the target
    emergency_fund_priority: str  # ready / building / missing


def emergency_fund_target(profile) -> float:
    """recommended emergency fund buffer in months.

    irregular income earns a bigger cushion because a bad month is more
    likely to turn into an emergency.
    """
    emp = profile.employment_type.value
    if emp in _IRREGULAR_EMPLOYMENT:
        return IRREGULAR_INCOME_BUFFER_MONTHS
    return RECOMMENDED_EMERGENCY_FUND_MONTHS


def emergency_fund_status(months_have: float, months_want: float) -> str:
    """classify emergency fund readiness.

    ready — already there, stop adding
    building — partial buffer, keep prioritising until full
    missing — nothing saved, this comes before any investing
    """
    if months_have >= months_want:
        return "ready"
    if months_have >= 1:
        return "building"
    return "missing"


def build_cashflow_snapshot(user: UserProfile) -> CashflowSnapshot:
    """compute the full monthly cashflow picture for a user."""
    financial = user.financial

    income = financial.monthly_income + financial.secondary_monthly_income
    expenses = financial.monthly_fixed_expenses + financial.monthly_variable_expenses
    surplus = financial.monthly_surplus()

    # committed sip already eats into surplus — that money is spoken for
    committed = financial.existing_monthly_sip
    discretionary = max(0.0, surplus - committed)

    savings_rate = surplus / income if income > 0 else 0.0

    months_have = financial.emergency_fund_months
    months_want = emergency_fund_target(financial)
    gap_months = max(0.0, months_want - months_have)

    monthly_expense_burn = expenses / 12 if expenses > 0 else 0.0
    # expenses here are monthly already (fixed + variable are monthly),
    # so the "amount needed" is gap_months * monthly expenses
    amount_needed = max(0.0, gap_months * (expenses or 0.0))

    return CashflowSnapshot(
        monthly_income=income,
        monthly_expenses=expenses,
        monthly_surplus=surplus,
        committed_sip=committed,
        discretionary_surplus=discretionary,
        savings_rate=round(min(max(savings_rate, 0.0), 1.0), 4),
        emergency_fund_months=months_have,
        emergency_fund_target_months=months_want,
        emergency_fund_gap_months=round(gap_months, 2),
        emergency_fund_amount_needed=round(amount_needed),
        emergency_fund_priority=emergency_fund_status(months_have, months_want),
    )


def emergency_fund_allocation(
    user: UserProfile, snapshot: CashflowSnapshot | None = None
) -> float:
    """monthly rupees that should go to the emergency fund first.

    when the fund is missing or building, the planner holds back a share
    of discretionary surplus. once ready, the whole surplus frees up for
    goals. never lets the emergency fund starve other goals forever.
    """
    if snapshot is None:
        snapshot = build_cashflow_snapshot(user)

    if snapshot.emergency_fund_priority == "ready":
        return 0.0

    # conservative: devote up to 80% of discretionary surplus while the
    # fund is being built, so the user still has a little to live on.
    if snapshot.emergency_fund_priority == "missing":
        return snapshot.discretionary_surplus * 0.8
    return snapshot.discretionary_surplus * 0.5  # building

