"""Synthetic Population Generator (PART 1) — core implementation.

Generates 100,000+ realistic Indian household financial profiles. Every
profile is built from *statistical distributions and correlations* —
never from flat random values. The generator:

1. Draws a persona (archetype) for each person from the persona registry.
2. Draws correlated latent variables (age, education, income, savings,
   risk tolerance) via a Gaussian copula so the traits are correlated.
3. Maps those latent variables to concrete, realistic profile values
   (income bands, expense ratios, savings rates, debt levels, portfolio
   weights, insurance take-up, behaviour traits, goals, tax status).
4. Composes the result into a :class:`~ml.models.FinancialTwinProfile`.

The output is deterministic given a seed (see ``ml.utils.seeding``).
"""

from __future__ import annotations

import logging
from typing import Dict, List, Optional

import numpy as np

from ml.config import get_config
from ml.models import (
    BehaviourTraits,
    CityTier,
    EducationLevel,
    FinancialLiteracy,
    FinancialTwinProfile,
    Gender,
    Industry,
    MaritalStatus,
    Occupation,
    RiskTolerance,
    TaxStatus,
)
from ml.synthetic_population.personas import PERSONA_REGISTRY, get_persona
from ml.utils.copula import build_correlation_matrix, sample_gaussian_copula
from ml.utils.seeding import ensure_seed, get_rng

logger = logging.getLogger(__name__)

# ── Asset classes used in synthetic portfolios ─────────────────────
_ASSET_CLASSES = [
    "equity",
    "index_funds",
    "mutual_funds",
    "fixed_deposits",
    "gold",
    "ppf",
    "nps",
    "bond_yields",
    "real_estate",
    "international_etf",
    "savings",
]

# ── Education mapping from latent rank ─────────────────────────────
_EDUCATION_LEVELS = [
    EducationLevel.NO_FORMAL,
    EducationLevel.SCHOOL,
    EducationLevel.HIGH_SCHOOL,
    EducationLevel.UNDERGRAD,
    EducationLevel.POSTGRAD,
    EducationLevel.DOCTORATE,
]

# ── Risk tolerance mapping from latent rank ────────────────────────
_RISK_LEVELS = [
    RiskTolerance.VERY_CONSERVATIVE,
    RiskTolerance.CONSERVATIVE,
    RiskTolerance.MODERATE,
    RiskTolerance.AGGRESSIVE,
    RiskTolerance.VERY_AGGRESSIVE,
]


def _clamp(value: float, lo: float, hi: float) -> float:
    """Clamp a value to ``[lo, hi]``."""
    return max(lo, min(hi, value))


def _pick_enum(items: List, u: float) -> object:
    """Pick an enum member from a list using a uniform rank ``u``."""
    idx = int(_clamp(u * len(items), 0, len(items) - 1))
    return items[idx]


class PopulationGenerator:
    """Generate a realistic synthetic Indian population.

    Parameters
    ----------
    size:
        Number of profiles to generate.
    seed:
        Optional seed. Defaults to the config seed.
    """

    def __init__(self, size: int = 100000, seed: Optional[int] = None) -> None:
        self.size = size
        self.seed = ensure_seed(seed)
        self.rng = get_rng()
        self.config = get_config()
        self._build_copula()

    # ── correlation structure ──────────────────────────────────────
    def _build_copula(self) -> None:
        """Build the Gaussian copula from the config correlation matrix."""
        corr_cfg = self.config.population.correlation
        variables = list(corr_cfg.variables) or ["age", "education", "income", "savings", "risk"]
        matrix = [list(row) for row in (corr_cfg.matrix or [])]
        if not matrix:
            # Default 5x5 correlation matrix.
            matrix = [
                [1.0, 0.40, 0.55, 0.45, 0.20],
                [0.40, 1.0, 0.60, 0.50, 0.30],
                [0.55, 0.60, 1.0, 0.70, 0.25],
                [0.45, 0.50, 0.70, 1.0, 0.35],
                [0.20, 0.30, 0.25, 0.35, 1.0],
            ]
        self.corr_variables = variables
        self.corr_matrix = build_correlation_matrix(variables, matrix)

    # ── main entry ─────────────────────────────────────────────────
    def generate(self) -> List[FinancialTwinProfile]:
        """Generate the full population of synthetic profiles."""
        n = self.size
        profiles: List[FinancialTwinProfile] = []

        # Sample correlated latent variables (each column ~ Uniform(0,1)).
        uniforms = sample_gaussian_copula(self.corr_matrix, n, self.rng)
        age_u = uniforms[:, 0]
        edu_u = uniforms[:, 1]
        income_u = uniforms[:, 2]
        savings_u = uniforms[:, 3]
        risk_u = uniforms[:, 4]

        persona_names = [p.name.value for p in PERSONA_REGISTRY]
        persona_idx = self.rng.integers(0, len(persona_names), size=n)

        for i in range(n):
            persona = get_persona(persona_names[int(persona_idx[i])])
            if persona is None:
                persona = PERSONA_REGISTRY[0]
            profile = self._build_one(
                persona=persona,
                age_u=float(age_u[i]),
                edu_u=float(edu_u[i]),
                income_u=float(income_u[i]),
                savings_u=float(savings_u[i]),
                risk_u=float(risk_u[i]),
                person_id=i,
            )
            profiles.append(profile)

        return profiles

    # ── single profile construction ────────────────────────────────
    def _build_one(
        self,
        persona,
        age_u: float,
        edu_u: float,
        income_u: float,
        savings_u: float,
        risk_u: float,
        person_id: int,
    ) -> FinancialTwinProfile:
        """Construct one realistic profile from latent ranks."""
        cfg = self.config.population
        income_cfg = cfg.income

        # ── age ────────────────────────────────────────────────────
        age_lo, age_hi = persona.age_range
        age = int(round(age_lo + (age_hi - age_lo) * age_u))
        age = _clamp(age, *cfg.age_range)

        # ── gender ─────────────────────────────────────────────────
        gender = Gender.FEMALE if self.rng.random() < cfg.gender_share_female else Gender.MALE

        # ── city tier ──────────────────────────────────────────────
        tiers = list(persona.city_tier_dist.keys())
        weights = np.array([persona.city_tier_dist[t] for t in tiers], dtype=float)
        weights = weights / weights.sum()
        city_tier = CityTier(self.rng.choice(tiers, p=weights))

        # ── education (respect persona floor) ──────────────────────
        floor_idx = _EDUCATION_LEVELS.index(persona.education_floor)
        edu_idx = floor_idx + int(_clamp(edu_u * (len(_EDUCATION_LEVELS) - floor_idx), 0, len(_EDUCATION_LEVELS) - 1 - floor_idx))
        education = _EDUCATION_LEVELS[edu_idx]

        # ── income (lognormal within persona band) ─────────────────
        lo, hi = persona.income_range
        # Use the persona band as the mode of a lognormal draw clipped to
        # the band, scaled by the latent income rank.
        log_lo, log_hi = np.log(max(lo, 1.0)), np.log(max(hi, 1.0))
        log_income = log_lo + (log_hi - log_lo) * income_u
        # Add realistic dispersion around the persona centre.
        dispersion = np.random.lognormal(0, 0.25)
        monthly_income = float(np.exp(log_income) * dispersion)
        monthly_income = _clamp(monthly_income, max(lo, income_cfg.min_monthly), max(hi, income_cfg.min_monthly))
        monthly_income = _clamp(monthly_income, income_cfg.min_monthly, income_cfg.max_monthly)

        # ── expenses / savings ─────────────────────────────────────
        # Expense ratio depends on income and age; higher income → lower
        # expense ratio. Savings is the residual.
        expense_ratio = _clamp(
            0.85 - 0.25 * (monthly_income / 500000) - 0.05 * min(age / 60, 1.0),
            0.4,
            0.95,
        )
        monthly_expenses = monthly_income * expense_ratio
        monthly_savings = monthly_income - monthly_expenses

        # ── emergency fund ─────────────────────────────────────────
        emergency_months = _clamp(2.0 + 6.0 * savings_u, 0.0, 12.0)

        # ── risk profile & behaviour ───────────────────────────────
        risk_rank = _clamp(risk_u * 0.6 + persona.risk_center * 0.4, 0.0, 1.0)
        risk_profile = _pick_enum(_RISK_LEVELS, risk_rank)
        behaviour = self._build_behaviour(persona, risk_rank, age)

        # ── financial literacy ─────────────────────────────────────
        lit_rank = _clamp(edu_u * 0.5 + persona.literacy_center * 0.5, 0.0, 1.0)
        if lit_rank < 0.33:
            literacy = FinancialLiteracy.LOW
        elif lit_rank < 0.66:
            literacy = FinancialLiteracy.MEDIUM
        else:
            literacy = FinancialLiteracy.HIGH

        # ── existing investments / portfolio ───────────────────────
        invest_ratio = _clamp(0.1 + 0.5 * savings_u * (1.0 - expense_ratio), 0.0, 0.6)
        existing_investments = monthly_income * invest_ratio * 12.0
        portfolio = self._build_portfolio(monthly_income, risk_rank, persona)

        # ── insurance / debt ───────────────────────────────────────
        has_term = self.rng.random() < _clamp(0.3 + 0.2 * age / 60, 0.0, 0.8)
        has_health = self.rng.random() < _clamp(0.4 + 0.2 * age / 60, 0.0, 0.9)
        debt_ratio = _clamp(0.05 + 0.3 * (1.0 - savings_u) * (1.0 - persona.risk_center), 0.0, 0.5)
        total_debt = monthly_income * debt_ratio * 24.0
        monthly_emi = monthly_income * _clamp(0.05 + 0.2 * (1.0 - savings_u), 0.0, 0.35)

        # ── credit score ───────────────────────────────────────────
        credit_score = float(_clamp(600 + 250 * savings_u + 50 * min(age / 60, 1.0), 350, 900))

        # ── marital status & dependents ────────────────────────────
        marital, dependents = self._marital_and_dependents(age)

        # ── goals ──────────────────────────────────────────────────
        goals = self._build_goals(age, monthly_income, risk_profile)

        # ── tax / retirement ───────────────────────────────────────
        tax_status = TaxStatus.NEW_REGIME if self.rng.random() < 0.6 else TaxStatus.OLD_REGIME
        tax_bracket = _clamp(0.05 + 0.25 * (monthly_income / 500000), 0.0, 0.5)
        retirement_age = persona.retirement_age

        return FinancialTwinProfile(
            person_id=f"person_{person_id:06d}",
            age=age,
            gender=gender,
            city_tier=city_tier,
            occupation=persona.occupation,
            industry=persona.industry,
            education=education,
            marital_status=marital,
            dependents=dependents,
            monthly_income=round(monthly_income, 2),
            salary_growth_rate=round(_clamp(0.03 + 0.05 * (1 - age / 80), 0.02, 0.15), 4),
            secondary_income=round(monthly_income * 0.1 if self.rng.random() < 0.2 else 0.0, 2),
            monthly_expenses=round(monthly_expenses, 2),
            monthly_savings=round(monthly_savings, 2),
            emergency_fund_months=round(emergency_months, 1),
            existing_investments=round(existing_investments, 2),
            portfolio=portfolio,
            has_term_life_insurance=has_term,
            has_health_insurance=has_health,
            total_debt=round(total_debt, 2),
            monthly_emi_total=round(monthly_emi, 2),
            credit_score=round(credit_score, 1),
            risk_profile=risk_profile,
            financial_literacy=literacy,
            goals=goals,
            tax_status=tax_status,
            tax_bracket_percent=round(tax_bracket, 4),
            retirement_age=retirement_age,
            behaviour=behaviour,
            investment_preferences=list(persona.investment_preferences),
            persona_name=persona.name.value,
        )

    # ── behaviour ──────────────────────────────────────────────────
    def _build_behaviour(self, persona, risk_rank: float, age: int) -> BehaviourTraits:
        """Derive behaviour traits from persona centres + noise."""
        centers = persona.behaviour_centers
        noise = self.rng.normal(0, 0.12)
        return BehaviourTraits(
            loss_aversion=_clamp(centers.get("loss_aversion", 0.5) + noise, 0.0, 1.0),
            discipline=_clamp(centers.get("discipline", 0.5) + noise, 0.0, 1.0),
            financial_literacy=_clamp(centers.get("financial_literacy", 0.5) + noise, 0.0, 1.0),
            overconfidence=_clamp(centers.get("overconfidence", 0.5) + noise, 0.0, 1.0),
            panic_selling=_clamp(centers.get("panic_selling", 0.5) + noise, 0.0, 1.0),
            long_term_thinking=_clamp(centers.get("long_term_thinking", 0.5) + noise, 0.0, 1.0),
            impulse_spending=_clamp(centers.get("impulse_spending", 0.5) + noise, 0.0, 1.0),
            investment_consistency=_clamp(centers.get("investment_consistency", 0.5) + noise, 0.0, 1.0),
            risk_appetite=risk_rank,
        )

    # ── portfolio ──────────────────────────────────────────────────
    def _build_portfolio(self, monthly_income: float, risk_rank: float, persona) -> Dict[str, float]:
        """Build a target portfolio allocation based on risk and income."""
        # Risk-proportional equity weight.
        equity_weight = _clamp(0.2 + 0.5 * risk_rank, 0.1, 0.7)
        # Remaining split across defensive assets.
        defensive = 1.0 - equity_weight
        weights = {
            "equity": equity_weight,
            "index_funds": equity_weight * 0.3,
            "mutual_funds": equity_weight * 0.3,
            "fixed_deposits": defensive * 0.3,
            "gold": defensive * 0.15,
            "ppf": defensive * 0.15,
            "nps": defensive * 0.1,
            "bond_yields": defensive * 0.1,
            "real_estate": defensive * 0.1,
            "international_etf": equity_weight * 0.1,
            "savings": defensive * 0.1,
        }
        # Normalise and scale by investable base.
        total = sum(weights.values())
        investable = monthly_income * 12.0 * _clamp(0.1 + 0.4 * risk_rank, 0.1, 0.5)
        portfolio = {k: round(v / total * investable, 2) for k, v in weights.items()}
        return portfolio

    # ── marital status & dependents ────────────────────────────────
    def _marital_and_dependents(self, age: int) -> tuple:
        """Determine marital status and dependent count from age."""
        if age < 24:
            return MaritalStatus.SINGLE, 0
        if age < 30:
            married = self.rng.random() < 0.4
            return MaritalStatus.MARRIED if married else MaritalStatus.SINGLE, 0
        # 30+ : mostly married, some dependents.
        if self.rng.random() < 0.85:
            dependents = int(self.rng.randint(0, 4))
            return MaritalStatus.MARRIED, dependents
        return MaritalStatus.SINGLE, 0

    # ── goals ──────────────────────────────────────────────────────
    def _build_goals(self, age: int, monthly_income: float, risk_profile: RiskTolerance) -> List[Dict]:
        """Build a realistic set of financial goals."""
        goals: List[Dict] = []
        # Retirement goal (always present).
        goals.append(self._goal("retirement", "corpus", monthly_income * 12.0 * 20))
        # Emergency fund goal.
        goals.append(self._goal("emergency_fund", "liquidity", monthly_income * 6.0))
        # House purchase — likely for 28+.
        if age >= 28 and self.rng.random() < 0.5:
            goals.append(self._goal("house_purchase", "corpus", monthly_income * 60.0))
        # Children education — likely for those with dependents.
        if age >= 30 and self.rng.random() < 0.4:
            goals.append(self._goal("child_education", "corpus", monthly_income * 36.0))
        # Wealth building for high risk.
        if risk_profile in (RiskTolerance.AGGRESSIVE, RiskTolerance.VERY_AGGRESSIVE):
            goals.append(self._goal("wealth_creation", "corpus", monthly_income * 120.0))
        return goals

    @staticmethod
    def _goal(name: str, kind: str, target: float) -> Dict:
        """Build a goal dict."""
        return {"name": name, "type": kind, "target_amount": round(target, 2)}


def generate_population(
    size: int = 100000,
    seed: Optional[int] = None,
) -> List[FinancialTwinProfile]:
    """Generate a synthetic population of `size` profiles.

    Parameters
    ----------
    size:
        Number of profiles.
    seed:
        Optional seed for reproducibility.

    Returns
    -------
    List[FinancialTwinProfile]
        The generated profiles.
    """
    generator = PopulationGenerator(size=size, seed=seed)
    return generator.generate()
