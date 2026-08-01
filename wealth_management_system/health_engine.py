"""financial health engine — one score, plain-language signals.

a single number is useless without knowing what is driving it. this
engine produces both: a 0-100 health score and a list of human-readable
signals, each with severity, so the recommendation layer can explain
*why* the score is what it is.

health is built on foundations, not returns:
1. savings rate (are they living below their means?)
2. emergency fund (can they survive a shock?)
3. debt burden (are obligations under control?)
4. surplus (is there money left to act?)
5. protection (are dependents covered?)
"""

from dataclasses import dataclass, field
from typing import List

from wealth_management_system.cashflow_engine import (
    build_cashflow_snapshot,
    emergency_fund_target,
)
from wealth_management_system.models import UserProfile

# thresholds are deliberately conservative — better to under-promise
GOOD_SAVINGS_RATE: float = 0.20
GOOD_EMERGENCY_MONTHS: float = 6.0
GOOD_DEBT_TO_INCOME: float = 0.30
GOOD_SURPLUS_RATIO: float = 0.15

# the emergency fund is the foundation, so it caps the grade. you cannot
# be financially excellent while your shock absorber is incomplete.
#   missing  -> cannot score above 39 (poor)
#   building -> cannot score above 69 (good)
#   ready    -> no cap
EF_MISSING_CAP: int = 39
EF_BUILDING_CAP: int = 69


@dataclass
class HealthSignal:
    """a single plain-language finding about financial health."""

    severity: str  # critical / warning / good
    message: str


@dataclass
class FinancialHealth:
    """aggregate health result: score plus explainable signals."""

    score: int  # 0-100
    grade: str  # excellent / good / fair / poor / critical
    signals: List[HealthSignal] = field(default_factory=list)

    def critical_signals(self) -> List[HealthSignal]:
        """signals that must be addressed before investing."""
        return [s for s in self.signals if s.severity == "critical"]


def _grade(score: int) -> str:
    """map a 0-100 score to a plain-language grade."""
    if score >= 80:
        return "excellent"
    if score >= 60:
        return "good"
    if score >= 40:
        return "fair"
    if score >= 20:
        return "poor"
    return "critical"


def assess_health(user: UserProfile) -> FinancialHealth:
    """score financial health and generate explainable signals."""
    financial = user.financial
    cash = build_cashflow_snapshot(user)

    signals: List[HealthSignal] = []
    score = 0.0
    weights = 0.0

    # 1. savings rate — the single strongest predictor of future wealth
    weights += 0.30
    if cash.savings_rate >= GOOD_SAVINGS_RATE:
        score += 30
        signals.append(
            HealthSignal("good", f"savings rate of {cash.savings_rate:.0%} is solid")
        )
    elif cash.savings_rate >= 0.10:
        score += 18
        signals.append(
            HealthSignal(
                "warning",
                f"only {cash.savings_rate:.0%} of income is saved — target 20%+",
            )
        )
    else:
        score += 6
        signals.append(
            HealthSignal(
                "critical",
                f"barely any surplus ({cash.savings_rate:.0%} savings rate) — "
                "expenses are eating the income",
            )
        )

    # 2. emergency fund — the shock absorber
    weights += 0.25
    want = emergency_fund_target(financial)
    if cash.emergency_fund_priority == "ready":
        score += 25
        signals.append(
            HealthSignal(
                "good",
                f"emergency fund covers {cash.emergency_fund_months:.0f} months",
            )
        )
    elif cash.emergency_fund_priority == "building":
        score += 15
        signals.append(
            HealthSignal(
                "warning",
                f"emergency fund covers {cash.emergency_fund_months:.0f} of "
                f"{want:.0f} months — keep building before heavy investing",
            )
        )
    else:
        score += 3
        signals.append(
            HealthSignal(
                "critical",
                "no emergency fund — a single shock could force debt or "
                "premature investment withdrawal",
            )
        )

    # 3. debt burden — debt competes with future goals
    weights += 0.20
    dti = financial.debt_to_income_ratio()
    if dti <= 0.10:
        score += 20
        signals.append(HealthSignal("good", "debt is under control"))
    elif dti <= GOOD_DEBT_TO_INCOME:
        score += 12
        signals.append(
            HealthSignal("warning", f"debt eats {dti:.0%} of income — manageable but rising")
        )
    else:
        score += 4
        signals.append(
            HealthSignal(
                "critical",
                f"debt consumes {dti:.0%} of income — clear the expensive "
                "loans before investing aggressively",
            )
        )

    # 4. surplus — money left to actually act on any plan
    weights += 0.15
    surplus_ratio = cash.monthly_surplus / cash.monthly_income if cash.monthly_income > 0 else 0.0
    if surplus_ratio >= GOOD_SURPLUS_RATIO:
        score += 15
        signals.append(
            HealthSignal(
                "good",
                f"₹{cash.monthly_surplus:,.0f} surplus each month to work with",
            )
        )
    elif surplus_ratio > 0:
        score += 8
        signals.append(
            HealthSignal(
                "warning",
                "surplus is thin — every rupee needs to be prioritised carefully",
            )
        )
    else:
        score += 2
        signals.append(
            HealthSignal("critical", "spending exceeds income — the plan starts with the budget, not investing")
        )

    # 5. protection — life + health insurance for dependents
    weights += 0.10
    protection_ok = financial.has_health_insurance and (
        user.dependents == 0 or financial.has_term_life_insurance
    )
    if protection_ok:
        score += 10
        signals.append(HealthSignal("good", "protection basics are in place"))
    else:
        needs = []
        if not financial.has_health_insurance:
            needs.append("health insurance")
        if user.dependents > 0 and not financial.has_term_life_insurance:
            needs.append("term life cover for your dependents")
        score += 3
        signals.append(
            HealthSignal(
                "warning" if user.dependents == 0 else "critical",
                "missing " + " and ".join(needs),
            )
        )

    total = round(score)
    # the emergency fund caps the grade — foundations always come first
    if cash.emergency_fund_priority == "missing":
        total = min(total, EF_MISSING_CAP)
    elif cash.emergency_fund_priority == "building":
        total = min(total, EF_BUILDING_CAP)

    return FinancialHealth(
        score=total,
        grade=_grade(total),
        signals=signals,
    )

