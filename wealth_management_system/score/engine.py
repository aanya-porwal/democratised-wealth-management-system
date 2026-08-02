"""Financial health score engine.

Produces a 0-100 financial health score across nine factors:

1. emergency fund
2. debt
3. savings rate
4. insurance
5. investment rate
6. diversification
7. goal progress
8. tax efficiency
9. return

Every factor contributes a weighted number of points and a plain-language
message. The aggregate result carries strengths, weaknesses and actionable
suggestions so the score is explainable, not just a number.

Design notes
------------
* Factor weights come from ``config.health`` (no magic numbers).
* Reuses the legacy ``cashflow_engine`` for surplus / savings-rate
  figures and the legacy ``risk_engine`` for the return factor so this
  engine always agrees with the rest of the pipeline.
* The emergency fund still acts as a ceiling on the total score, just
  like the legacy ``health_engine`` — foundations always come first.
"""

from __future__ import annotations

import logging
from typing import Dict, List, Optional

from wealth_management_system.cashflow_engine import build_cashflow_snapshot
from wealth_management_system.config import HealthConfig, get_config
from wealth_management_system.models import (
    HealthFactorScore,
    HealthScoreResult,
    UserProfile,
)
from wealth_management_system.risk_engine import assess_risk
from wealth_management_system.utilities import get_logger

logger: logging.Logger = get_logger(__name__)

# default factor weights (used if config.health.factor_weights is empty)
_DEFAULT_WEIGHTS: Dict[str, float] = {
    "emergency_fund": 0.15,
    "debt": 0.12,
    "savings_rate": 0.15,
    "insurance": 0.12,
    "investment_rate": 0.12,
    "diversification": 0.10,
    "goal_progress": 0.12,
    "tax_efficiency": 0.06,
    "return": 0.06,
}


class HealthScoreEngine:
    """Computes the explainable 0-100 financial health score.

    Parameters
    ----------
    config:
        Optional ``HealthConfig``. Defaults to the process-wide config.
    """

    def __init__(self, config: Optional[HealthConfig] = None) -> None:
        self._config = config or get_config().health
        weights = self._config.factor_weights or _DEFAULT_WEIGHTS
        total = sum(weights.values())
        # normalise so weights sum to 1.0 (defensive)
        self._weights: Dict[str, float] = (
            {k: v / total for k, v in weights.items()} if total > 0 else _DEFAULT_WEIGHTS
        )

    # ── public API ──────────────────────────────────────────────────

    def score(self, user: UserProfile) -> HealthScoreResult:
        """Compute the health score and explanations for a user.

        Parameters
        ----------
        user:
            The user to assess.

        Returns
        -------
        HealthScoreResult
            Score, grade, per-factor breakdown, strengths, weaknesses
            and suggestions.
        """
        factors = self._factor_scores(user)
        total = round(sum(f.score for f in factors))
        total = min(total, self._ceiling(user))

        strengths = self._strengths(factors)
        weaknesses = self._weaknesses(factors)
        suggestions = self._suggestions(factors)

        return HealthScoreResult(
            score=total,
            grade=self._grade(total),
            factors=factors,
            strengths=strengths,
            weaknesses=weaknesses,
            suggestions=suggestions,
        )

    # ── factor scoring ──────────────────────────────────────────────

    def _factor_scores(self, user: UserProfile) -> List[HealthFactorScore]:
        """Compute every factor's points and message."""
        financial = user.financial
        cash = build_cashflow_snapshot(user)

        scores: List[HealthFactorScore] = [
            self._emergency_fund(user),
            self._debt(user),
            self._savings_rate(cash.savings_rate),
            self._insurance(user),
            self._investment_rate(user),
            self._diversification(user),
            self._goal_progress(user),
            self._tax_efficiency(user),
            self._return_factor(user),
        ]

        # apply weights and cap each factor at its max_points
        weighted: List[HealthFactorScore] = []
        for factor, weight in self._weights.items():
            base = next((f for f in scores if f.name == factor), None)
            if base is None:
                continue
            max_points = round(weight * 100, 2)
            points = round(min(base.score / max(base.max_points, 1e-9), 1.0) * max_points, 2)
            weighted.append(
                HealthFactorScore(
                    name=factor,
                    score=points,
                    max_points=max_points,
                    severity=base.severity,
                    message=base.message,
                )
            )
        return weighted

    def _emergency_fund(self, user: UserProfile) -> HealthFactorScore:
        cash = build_cashflow_snapshot(user)
        if cash.emergency_fund_priority == "ready":
            return HealthFactorScore(
                "emergency_fund", 1.0, 1.0, "good",
                f"emergency fund covers {cash.emergency_fund_months:.0f} months",
            )
        if cash.emergency_fund_priority == "building":
            return HealthFactorScore(
                "emergency_fund", 0.5, 1.0, "warning",
                f"emergency fund covers only {cash.emergency_fund_months:.0f} months",
            )
        return HealthFactorScore(
            "emergency_fund", 0.1, 1.0, "critical",
            "no emergency fund — a single shock forces debt or early withdrawal",
        )

    def _debt(self, user: UserProfile) -> HealthFactorScore:
        dti = user.financial.debt_to_income_ratio()
        if dti <= 0.10:
            return HealthFactorScore("debt", 1.0, 1.0, "good", "debt is under control")
        if dti <= 0.30:
            return HealthFactorScore(
                "debt", 0.6, 1.0, "warning",
                f"debt consumes {dti:.0%} of income — manageable but rising",
            )
        return HealthFactorScore(
            "debt", 0.2, 1.0, "critical",
            f"debt consumes {dti:.0%} of income — clear expensive loans first",
        )

    def _savings_rate(self, rate: float) -> HealthFactorScore:
        if rate >= 0.20:
            return HealthFactorScore(
                "savings_rate", 1.0, 1.0, "good", f"savings rate of {rate:.0%} is solid"
            )
        if rate >= 0.10:
            return HealthFactorScore(
                "savings_rate", 0.55, 1.0, "warning",
                f"only {rate:.0%} of income is saved — target 20%+",
            )
        return HealthFactorScore(
            "savings_rate", 0.15, 1.0, "critical",
            f"barely any surplus ({rate:.0%}) — expenses are eating income",
        )

    def _insurance(self, user: UserProfile) -> HealthFactorScore:
        financial = user.financial
        ok = financial.has_health_insurance and (
            user.dependents == 0 or financial.has_term_life_insurance
        )
        if ok:
            return HealthFactorScore("insurance", 1.0, 1.0, "good", "protection basics in place")
        missing = []
        if not financial.has_health_insurance:
            missing.append("health insurance")
        if user.dependents > 0 and not financial.has_term_life_insurance:
            missing.append("term life cover")
        return HealthFactorScore(
            "insurance", 0.3, 1.0, "critical" if user.dependents > 0 else "warning",
            "missing " + " and ".join(missing),
        )

    def _investment_rate(self, user: UserProfile) -> HealthFactorScore:
        financial = user.financial
        surplus = financial.monthly_surplus()
        invested = financial.existing_monthly_sip
        rate = invested / surplus if surplus > 0 else 0.0
        if invested <= 0:
            return HealthFactorScore(
                "investment_rate", 0.15, 1.0, "warning",
                "no regular monthly investing yet — money may be sitting idle",
            )
        if rate >= 0.30:
            return HealthFactorScore(
                "investment_rate", 1.0, 1.0, "good",
                f"investing {rate:.0%} of surplus every month",
            )
        return HealthFactorScore(
            "investment_rate", 0.6, 1.0, "warning",
            f"investing {rate:.0%} of surplus — consider raising it toward 30%",
        )

    def _diversification(self, user: UserProfile) -> HealthFactorScore:
        financial = user.financial
        buckets = 0
        if financial.existing_investments > 0:
            buckets += 1
        if financial.gold_value > 0:
            buckets += 1
        if financial.real_estate_value > 0:
            buckets += 1
        if financial.provident_fund_balance > 0:
            buckets += 1
        if buckets >= 3:
            return HealthFactorScore(
                "diversification", 1.0, 1.0, "good",
                f"assets spread across {buckets} broad buckets",
            )
        if buckets >= 1:
            return HealthFactorScore(
                "diversification", 0.5, 1.0, "warning",
                f"only {buckets} asset buckets — consider diversifying",
            )
        return HealthFactorScore(
            "diversification", 0.1, 1.0, "critical", "no assets to diversify yet",
        )

    def _goal_progress(self, user: UserProfile) -> HealthFactorScore:
        if not user.goals:
            return HealthFactorScore(
                "goal_progress", 0.4, 1.0, "warning", "no financial goals defined yet"
            )
        progress_sum = 0.0
        for goal in user.goals:
            if goal.target_amount > 0:
                progress_sum += min(goal.current_savings_for_goal / goal.target_amount, 1.0)
        avg = progress_sum / len(user.goals)
        if avg >= 0.5:
            return HealthFactorScore(
                "goal_progress", 1.0, 1.0, "good", f"goals are {avg:.0%} funded on average"
            )
        if avg >= 0.2:
            return HealthFactorScore(
                "goal_progress", 0.5, 1.0, "warning",
                f"goals only {avg:.0%} funded on average",
            )
        return HealthFactorScore(
            "goal_progress", 0.2, 1.0, "critical",
            f"goals barely started ({avg:.0%} funded)",
        )

    def _tax_efficiency(self, user: UserProfile) -> HealthFactorScore:
        bracket = user.financial.tax_bracket_percent / 100
        if bracket >= 0.20:
            return HealthFactorScore(
                "tax_efficiency", 0.6, 1.0, "warning",
                f"at a {bracket:.0%} tax bracket — use 80C/80CCD to cut the bill",
            )
        if bracket > 0:
            return HealthFactorScore(
                "tax_efficiency", 0.8, 1.0, "good",
                f"moderate {bracket:.0%} bracket — tax is a minor drag",
            )
        return HealthFactorScore(
            "tax_efficiency", 1.0, 1.0, "good", "no tax burden — full compounding",
        )

    def _return_factor(self, user: UserProfile) -> HealthFactorScore:
        risk = assess_risk(user)
        if risk.final_score_100 >= 60:
            return HealthFactorScore(
                "return", 1.0, 1.0, "good",
                f"portfolio risk profile supports growth ({risk.final_score_100}/100)",
            )
        if risk.final_score_100 >= 40:
            return HealthFactorScore(
                "return", 0.6, 1.0, "warning",
                f"moderate risk capacity ({risk.final_score_100}/100) limits returns",
            )
        return HealthFactorScore(
            "return", 0.3, 1.0, "warning",
            f"low risk capacity ({risk.final_score_100}/100) — returns will be modest",
        )

    # ── aggregation ─────────────────────────────────────────────────

    def _ceiling(self, user: UserProfile) -> int:
        """Emergency-fund ceiling on the total score."""
        cash = build_cashflow_snapshot(user)
        if cash.emergency_fund_priority == "missing":
            return self._config.ef_missing_cap
        if cash.emergency_fund_priority == "building":
            return self._config.ef_building_cap
        return 100

    @staticmethod
    def _grade(score: int) -> str:
        if score >= 80:
            return "excellent"
        if score >= 60:
            return "good"
        if score >= 40:
            return "fair"
        if score >= 20:
            return "poor"
        return "critical"

    def _strengths(self, factors: List[HealthFactorScore]) -> List[str]:
        return [f.message for f in factors if f.severity == "good"]

    def _weaknesses(self, factors: List[HealthFactorScore]) -> List[str]:
        return [
            f.message for f in factors if f.severity in ("critical", "warning")
        ]

    def _suggestions(self, factors: List[HealthFactorScore]) -> List[str]:
        suggestions: List[str] = []
        by_name = {f.name: f for f in factors}
        if by_name.get("emergency_fund") and by_name["emergency_fund"].severity != "good":
            suggestions.append("complete the emergency fund to at least 6 months of expenses")
        if by_name.get("debt") and by_name["debt"].severity == "critical":
            suggestions.append("prioritise clearing high-interest debt before investing aggressively")
        if by_name.get("insurance") and by_name["insurance"].severity != "good":
            suggestions.append("close the insurance gap (health cover, term life if dependents)")
        if by_name.get("investment_rate") and by_name["investment_rate"].score < 0.6:
            suggestions.append("start or increase a monthly SIP from the surplus")
        if by_name.get("diversification") and by_name["diversification"].severity != "good":
            suggestions.append("add asset buckets — gold, debt or equity — to diversify")
        if by_name.get("goal_progress") and by_name["goal_progress"].severity != "good":
            suggestions.append("define concrete goals with target dates and fund them")
        if by_name.get("tax_efficiency") and by_name["tax_efficiency"].severity == "warning":
            suggestions.append("use Section 80C / 80CCD instruments to reduce the tax bill")
        return suggestions

