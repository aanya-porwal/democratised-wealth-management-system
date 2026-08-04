"""Shared domain models for the ML platform.

These are the canonical data structures that flow through the entire
platform: synthetic population generation, the Digital Twin engine, the
feature engineering layer and the ML pipeline. They are deliberately
plain dataclasses (no ORM, no network) so the platform stays independent
of the FastAPI backend and can be imported anywhere.

The structures mirror the domain vocabulary in the existing engine
(``wealth_management_system.models.base``) so that the ML layer can
*consume* the same concepts without touching the deterministic engine.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from typing import Dict, List, Optional, Tuple

# ─────────────────────────────────────────────────────────────────────
# Enums
# ─────────────────────────────────────────────────────────────────────


class CityTier(str, Enum):
    TIER1 = "tier1"
    TIER2 = "tier2"
    TIER3 = "tier3"


class Gender(str, Enum):
    MALE = "male"
    FEMALE = "female"


class EducationLevel(str, Enum):
    NO_FORMAL = "no_formal"
    SCHOOL = "school"
    HIGH_SCHOOL = "high_school"
    UNDERGRAD = "undergrad"
    POSTGRAD = "postgrad"
    DOCTORATE = "doctorate"


class Occupation(str, Enum):
    STUDENT = "student"
    SOFTWARE_ENGINEER = "software_engineer"
    DOCTOR = "doctor"
    GOVERNMENT_EMPLOYEE = "government_employee"
    BUSINESS_OWNER = "business_owner"
    CONSULTANT = "consultant"
    RETIRED = "retired"
    HOMEMAKER = "homemaker"
    FREELANCER = "freelancer"
    STARTUP_FOUNDER = "startup_founder"
    TEACHER = "teacher"
    CA = "ca"
    LAWYER = "lawyer"
    NURSE = "nurse"
    FARMER = "farmer"
    RETAIL_OWNER = "retail_owner"
    OTHER = "other"


class Industry(str, Enum):
    TECHNOLOGY = "technology"
    HEALTHCARE = "healthcare"
    EDUCATION = "education"
    FINANCE = "finance"
    GOVERNMENT = "government"
    AGRICULTURE = "agriculture"
    RETAIL = "retail"
    MANUFACTURING = "manufacturing"
    CONSTRUCTION = "construction"
    TRANSPORT = "transport"
    ENERGY = "energy"
    MEDIA = "media"
    LEGAL = "legal"
    OTHER = "other"


class RiskTolerance(str, Enum):
    VERY_CONSERVATIVE = "very_conservative"
    CONSERVATIVE = "conservative"
    MODERATE = "moderate"
    AGGRESSIVE = "aggressive"
    VERY_AGGRESSIVE = "very_aggressive"


class FinancialLiteracy(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class MaritalStatus(str, Enum):
    SINGLE = "single"
    MARRIED = "married"
    DIVORCED = "divorced"
    WIDOWED = "widowed"


class TaxStatus(str, Enum):
    NEW_REGIME = "new_regime"
    OLD_REGIME = "old_regime"


class PersonaName(str, Enum):
    """Canonical list of persona archetypes (50+)."""

    # ── base archetypes ──────────────────────────────────────────
    STUDENT = "student"
    SOFTWARE_ENGINEER = "software_engineer"
    DOCTOR = "doctor"
    GOVERNMENT_EMPLOYEE = "government_employee"
    BUSINESS_OWNER = "business_owner"
    CONSULTANT = "consultant"
    RETIRED = "retired"
    HOMEMAKER = "homemaker"
    FREELANCER = "freelancer"
    STARTUP_FOUNDER = "startup_founder"
    TEACHER = "teacher"
    CA = "ca"
    NURSE = "nurse"
    RETAIL_OWNER = "retail_owner"
    FARMER = "farmer"
    LAWYER = "lawyer"
    OTHER = "other"

    # ── derived / specialised archetypes ──────────────────────────
    SENIOR_SOFTWARE_ENGINEER = "senior_software_engineer"
    TIER1_DOCTOR = "tier1_doctor"
    TIER3_DOCTOR = "tier3_doctor"
    HOME_LOAN_BUSINESS_OWNER = "home_loan_business_owner"
    TEACHER_TIER2 = "teacher_tier2"
    AGRICULTURE_OWNER = "agriculture_owner"
    NURSE_TIER2 = "nurse_tier2"
    RETIRED_PROFESSIONAL = "retired_professional"
    FREELANCER_EXPERIENCED = "freelancer_experienced"
    STARTUP_FOUNDER_SCALEUP = "startup_founder_scaleup"
    CONSULTANT_SENIOR = "consultant_senior"
    GOVERNMENT_EMPLOYEE_SENIOR = "government_employee_senior"
    LAWYER_CORPORATE = "lawyer_corporate"
    CA_CONSULTANT = "ca_consultant"
    HOMEMAKER_URBAN = "homemaker_urban"
    RETAIL_OWNER_URBAN = "retail_owner_urban"
    FARMER_PROGRESSIVE = "farmer_progressive"
    STUDENT_POSTGRAD = "student_postgrad"
    SOFTWARE_ENGINEER_TIER2 = "software_engineer_tier2"
    DOCTOR_PUBLIC_SECTOR = "doctor_public_sector"
    RETIRED_GOVERNMENT = "retired_government"

    # ── additional tier-2/3 variants ──────────────────────────────
    MANUFACTURING_ENGINEER = "manufacturing_engineer"
    TRANSPORT_OPERATOR = "transport_operator"
    ENERGY_SECTOR_EMPLOYEE = "energy_sector_employee"
    CONSTRUCTION_OWNER = "construction_owner"
    MEDIA_PROFESSIONAL = "media_professional"
    FINANCE_ANALYST = "finance_analyst"
    PHARMA_REP = "pharma_rep"
    IT_CONSULTANT_TIER2 = "it_consultant_tier2"
    BANK_EMPLOYEE = "bank_employee"
    INSURANCE_AGENT = "insurance_agent"
    HEALTHCARE_WORKER = "healthcare_worker"
    RETIRED_TEACHER = "retired_teacher"
    RETIRED_DOCTOR = "retired_doctor"
    HOMEMAKER_TIER3 = "homemaker_tier3"
    FREELANCER_DESIGNER = "freelancer_designer"
    STARTUP_EMPLOYEE = "startup_employee"
    CHIEF_TECHNOLOGY_OFFICER = "chief_technology_officer"
    SENIOR_MANAGER = "senior_manager"
    SCHOOL_PRINCIPAL = "school_principal"
    FARMER_LANDOWNER = "farmer_landowner"
    RETAIL_CHAIN_OWNER = "retail_chain_owner"
    LAWYER_FAMILY_PRACTICE = "lawyer_family_practice"
    CA_FIRM_PARTNER = "ca_firm_partner"
    RESEARCHER = "researcher"
    NRE_EMPLOYEE = "nre_employee"
    GOVERNMENT_TEACHER_PUBLIC = "government_teacher_public"
    RETAIL_EMPLOYEE = "retail_employee"
    HOMEMAKER_WEALTHY = "homemaker_wealthy"
    RETIRED_ENTREPRENEUR = "retired_entrepreneur"
    PROFESSIONAL_SPORTS = "professional_sports"


# ─────────────────────────────────────────────────────────────────────
# Behaviour traits
# ─────────────────────────────────────────────────────────────────────


@dataclass
class BehaviourTraits:
    """Psychological / behavioural traits of a person.

    All scores are on a 0..1 scale (higher = more of that trait) unless
    otherwise noted. These influence investment decisions in the
    behavioural simulation.
    """

    loss_aversion: float = 0.5
    discipline: float = 0.5
    financial_literacy: float = 0.5
    overconfidence: float = 0.5
    panic_selling: float = 0.5
    long_term_thinking: float = 0.5
    impulse_spending: float = 0.5
    investment_consistency: float = 0.5

    # risk tolerance proxy (0 conservative .. 1 aggressive)
    risk_appetite: float = 0.5

    @classmethod
    def default(cls) -> "BehaviourTraits":
        return cls()

    def to_dict(self) -> Dict[str, float]:
        return {
            "loss_aversion": self.loss_aversion,
            "discipline": self.discipline,
            "financial_literacy": self.financial_literacy,
            "overconfidence": self.overconfidence,
            "panic_selling": self.panic_selling,
            "long_term_thinking": self.long_term_thinking,
            "impulse_spending": self.impulse_spending,
            "investment_consistency": self.investment_consistency,
            "risk_appetite": self.risk_appetite,
        }


# ─────────────────────────────────────────────────────────────────────
# Financial profile (synthetic)
# ─────────────────────────────────────────────────────────────────────


@dataclass
class FinancialTwinProfile:
    """A complete description of a synthetic person's finances.

    This is the single source of truth for a person at a point in time.
    It is *not* a random bag of values — every field is produced by the
    statistical population generator with an explicit correlation
    structure.
    """

    # Identity
    person_id: str
    age: int
    gender: Gender
    city_tier: CityTier
    occupation: Occupation
    industry: Industry
    education: EducationLevel
    marital_status: MaritalStatus = MaritalStatus.SINGLE
    dependents: int = 0

    # Income
    monthly_income: float = 0.0
    salary_growth_rate: float = 0.06
    secondary_income: float = 0.0

    # Expenses / savings
    monthly_expenses: float = 0.0
    monthly_savings: float = 0.0
    emergency_fund_months: float = 3.0

    # Investments / portfolio
    existing_investments: float = 0.0
    portfolio: Dict[str, float] = field(default_factory=dict)  # asset_class -> value

    # Insurance / loans
    has_term_life_insurance: bool = False
    has_health_insurance: bool = False
    total_debt: float = 0.0
    monthly_emi_total: float = 0.0

    # Credit behaviour
    credit_score: float = 700.0

    # Risk
    risk_profile: RiskTolerance = RiskTolerance.MODERATE
    financial_literacy: FinancialLiteracy = FinancialLiteracy.MEDIUM

    # Goals
    goals: List[Dict[str, object]] = field(default_factory=list)

    # Tax / retirement
    tax_status: TaxStatus = TaxStatus.NEW_REGIME
    tax_bracket_percent: float = 0.0
    retirement_age: int = 60

    # Behaviour
    behaviour: BehaviourTraits = field(default_factory=BehaviourTraits)

    # Investment preferences
    investment_preferences: List[str] = field(default_factory=list)

    # Metadata
    persona_name: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)

    @property
    def net_worth(self) -> float:
        assets = (
            self.existing_investments
            + sum(self.portfolio.values())
            + self.emergency_fund_months * self.monthly_expenses
        )
        return assets - self.total_debt

    @property
    def debt_to_income_ratio(self) -> float:
        if self.monthly_income == 0:
            return 0.0
        return self.monthly_emi_total / self.monthly_income

    def to_dict(self) -> Dict[str, object]:
        return {
            "person_id": self.person_id,
            "age": self.age,
            "gender": self.gender.value,
            "city_tier": self.city_tier.value,
            "occupation": self.occupation.value,
            "industry": self.industry.value,
            "education": self.education.value,
            "marital_status": self.marital_status.value,
            "dependents": self.dependents,
            "monthly_income": self.monthly_income,
            "salary_growth_rate": self.salary_growth_rate,
            "secondary_income": self.secondary_income,
            "monthly_expenses": self.monthly_expenses,
            "monthly_savings": self.monthly_savings,
            "emergency_fund_months": self.emergency_fund_months,
            "existing_investments": self.existing_investments,
            "portfolio": self.portfolio,
            "has_term_life_insurance": self.has_term_life_insurance,
            "has_health_insurance": self.has_health_insurance,
            "total_debt": self.total_debt,
            "monthly_emi_total": self.monthly_emi_total,
            "credit_score": self.credit_score,
            "risk_profile": self.risk_profile.value,
            "financial_literacy": self.financial_literacy.value,
            "goals": self.goals,
            "tax_status": self.tax_status.value,
            "tax_bracket_percent": self.tax_bracket_percent,
            "retirement_age": self.retirement_age,
            "behaviour": self.behaviour.to_dict(),
            "investment_preferences": self.investment_preferences,
            "persona_name": self.persona_name,
        }


@dataclass
class Persona:
    """A named archetype defining a distribution over profile traits.

    A persona is a *template*; the population generator adds noise to
    produce thousands of realistic variations of each archetype.
    """

    name: PersonaName
    occupation: Occupation
    industry: Industry
    education_floor: EducationLevel
    income_range: Tuple[float, float]  # (min, max) monthly INR
    age_range: Tuple[int, int]
    city_tier_dist: Dict[str, float]  # tier -> weight
    behaviour_centers: Dict[str, float]  # trait -> center
    investment_preferences: List[str] = field(default_factory=list)
    risk_center: float = 0.5
    literacy_center: float = 0.5
    retirement_age: int = 60

    def to_dict(self) -> Dict[str, object]:
        return {
            "name": self.name.value,
            "occupation": self.occupation.value,
            "industry": self.industry.value,
            "education_floor": self.education_floor.value,
            "income_range": self.income_range,
            "age_range": self.age_range,
            "city_tier_dist": self.city_tier_dist,
            "behaviour_centers": self.behaviour_centers,
            "investment_preferences": self.investment_preferences,
            "risk_center": self.risk_center,
            "literacy_center": self.literacy_center,
            "retirement_age": self.retirement_age,
        }

