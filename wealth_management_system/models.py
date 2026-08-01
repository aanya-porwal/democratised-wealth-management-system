"""Data models for the AI-powered wealth management system.

This module contains only *data definitions*: enums, dataclasses and the
domain objects that describe a user, their goals, the risk-assessment
output, and the investable asset universe.

It deliberately contains no business logic — risk scoring, tax
optimisation and recommendation algorithms live in the dedicated engine
modules (``risk_engine``, ``assets``, ``recommendation_engine``). The only
methods allowed here are simple derived properties that belong to the
model itself (e.g. surplus, net worth, years-to-goal).
"""

from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from typing import List, Optional

# ─────────────────────────────────────────────────────────────────────
# User & goal models
# ─────────────────────────────────────────────────────────────────────


class EmploymentType(Enum):
    """Primary employment situation of the user."""

    SALARIED_PRIVATE = "salaried_private"
    SALARIED_GOVT = "salaried_govt"
    SELF_EMPLOYED = "self_employed"
    BUSINESS_OWNER = "business_owner"
    FREELANCER = "freelancer"
    STUDENT = "student"
    RETIRED = "retired"
    UNEMPLOYED = "unemployed"


class GoalType(Enum):
    """What the money is being saved for."""

    EMERGENCY_FUND = "emergency_fund"
    HOME_PURCHASE = "home_purchase"
    VEHICLE = "vehicle"
    EDUCATION_SELF = "education_self"
    EDUCATION_CHILD = "education_child"
    WEDDING = "wedding"
    TRAVEL = "travel"
    RETIREMENT = "retirement"
    WEALTH_CREATION = "wealth_creation"  # no specific target, just grow
    OTHER = "other"


class GoalPriority(Enum):
    """Importance of a goal — determines order of funding."""

    CRITICAL = "critical"  # non-negotiable. retirement, emergency fund
    HIGH = "high"  # important but some flexibility
    ASPIRATIONAL = "aspirational"  # nice to have, first to sacrifice


@dataclass
class Goal:
    """A single financial goal with a target date and amount."""

    goal_type: GoalType
    priority: GoalPriority
    target_amount: float  # in rupees
    target_date: date  # when do they need this money
    current_savings_for_goal: float = 0.0  # already saved towards this
    current_monthly_contribution: float = 0.0  # what they already put in monthly
    notes: str = ""

    def years_to_goal(self) -> float:
        """Number of years remaining until the target date."""
        today = date.today()
        delta = self.target_date - today
        return delta.days / 365.25

    def months_to_goal(self) -> int:
        """Months remaining until the target date (min 1)."""
        today = date.today()
        months = round(self.years_to_goal() * 12)
        return max(1, months)

    def amount_remaining(self) -> float:
        """How much more money is still needed for this goal."""
        return self.target_amount - self.current_savings_for_goal


@dataclass
class FinancialProfile:
    """Income, expenses, assets and liabilities of the user."""

    # Income
    monthly_income: float
    employment_type: EmploymentType
    income_stability: float  # 0.0 to 1.0. govt salary = 1.0, freelancer = 0.4

    # Expenses & obligations
    monthly_fixed_expenses: float  # rent, EMIs, insurance premiums
    monthly_variable_expenses: float  # food, transport, lifestyle

    has_secondary_income: bool = False
    secondary_monthly_income: float = 0.0

    # Existing assets
    emergency_fund_months: float = 0.0  # how many months of expenses saved
    existing_investments: float = 0.0  # current portfolio value
    provident_fund_balance: float = 0.0
    real_estate_value: float = 0.0
    gold_value: float = 0.0

    # Liabilities
    total_debt: float = 0.0
    monthly_emi_total: float = 0.0

    # Tax
    tax_bracket_percent: float = 0.0  # 0, 5, 10, 15, 20, 30

    # Protection (insurance). None = unknown; we default to False so the
    # health engine flags under-insurance rather than assuming it's handled.
    has_term_life_insurance: bool = False
    has_health_insurance: bool = False

    # Cashflow visibility
    existing_monthly_sip: float = 0.0  # already committed monthly investments

    def monthly_surplus(self) -> float:
        """Cash left over each month after all expenses."""
        return (
            self.monthly_income
            + self.secondary_monthly_income
            - self.monthly_fixed_expenses
            - self.monthly_variable_expenses
        )

    def debt_to_income_ratio(self) -> float:
        """EMI obligations as a fraction of monthly income."""
        if self.monthly_income == 0:
            return 0
        return self.monthly_emi_total / self.monthly_income

    def net_worth(self) -> float:
        """Total assets minus total liabilities."""
        total_assets = (
            self.existing_investments
            + self.provident_fund_balance
            + self.real_estate_value
            + self.gold_value
        )
        return total_assets - self.total_debt


class RiskToleranceLevel(Enum):
    """User-stated tolerance for investment risk."""

    VERY_CONSERVATIVE = 1
    CONSERVATIVE = 2
    MODERATE = 3
    AGGRESSIVE = 4
    VERY_AGGRESSIVE = 5


@dataclass
class BehavioralProfile:
    """Psychological / behavioural traits collected during onboarding."""

    risk_tolerance: RiskToleranceLevel

    # How would they react if the portfolio drops 20%?
    # 1 = sell everything, 5 = buy more
    drawdown_reaction_score: int  # 1 to 5

    # Investment experience
    has_invested_before: bool = False
    has_experienced_market_crash: bool = False

    # Financial literacy score (assessed during onboarding)
    financial_literacy_score: int = 1  # 1 to 5

    # Emotional relationship with money
    loss_aversion_score: int = 3  # 1 (not bothered) to 5 (very loss averse)


@dataclass
class UserProfile:
    """Aggregate user record tying together identity, finance and goals."""

    # Identity
    user_id: str
    name: str
    age: int
    date_of_birth: date
    dependents: int = 0  # number of financial dependents

    # Core profiles
    financial: Optional["FinancialProfile"] = None
    behavioral: Optional["BehavioralProfile"] = None
    goals: List[Goal] = field(default_factory=list)

    # Metadata
    profile_created: date = field(default_factory=date.today)
    last_updated: date = field(default_factory=date.today)

    def investable_surplus(self) -> float:
        """What can realistically be invested monthly.

        Keeps a 10% liquidity buffer so the user does not invest 100% of
        their surplus.
        """
        surplus = self.financial.monthly_surplus()
        return max(0, surplus * 0.9)

    def years_to_retirement(self, retirement_age: int = 60) -> float:
        """Years remaining until the assumed retirement age."""
        return max(0, retirement_age - self.age)

    def life_stage(self) -> str:
        """Coarse life-stage bucket derived from age."""
        if self.age < 25:
            return "early_career"
        elif self.age < 35:
            return "wealth_building"
        elif self.age < 50:
            return "peak_earning"
        elif self.age < 60:
            return "pre_retirement"
        else:
            return "retirement"


# ─────────────────────────────────────────────────────────────────────
# Risk assessment output
# ─────────────────────────────────────────────────────────────────────


@dataclass
class RiskAssessment:
    """Result of combining risk capacity and risk tolerance."""

    capacity_score: float  # 0 to 1
    tolerance_score: float  # 0 to 1
    final_score: float  # 0 to 1
    final_score_100: int  # 0 to 100, for display
    risk_category: str  # human readable
    capacity_was_binding: bool  # did capacity override tolerance?
    breakdown: dict  # for explainability


# ─────────────────────────────────────────────────────────────────────
# Asset universe
# ─────────────────────────────────────────────────────────────────────


class AssetCategory(Enum):
    """Level-1 broad buckets of investable assets."""

    CASH_AND_LIQUID = "cash_and_liquid"
    DEBT = "debt"
    HYBRID = "hybrid"
    EQUITY = "equity"
    GOLD_AND_COMMODITIES = "gold_and_commodities"
    REAL_ASSETS = "real_assets"
    TAX_ADVANTAGED = "tax_advantaged"  # PPF, NPS, EPF — lock-in but EEE/EET


class AssetClass(Enum):
    """Level-2 specific investment instruments within a category."""

    # CASH & LIQUID
    SAVINGS_ACCOUNT = "savings_account"
    LIQUID_FUND = "liquid_fund"
    OVERNIGHT_FUND = "overnight_fund"
    MONEY_MARKET_FUND = "money_market_fund"

    # DEBT
    ULTRA_SHORT_FUND = "ultra_short_fund"  # 3-6 months
    LOW_DURATION_FUND = "low_duration_fund"  # 6-12 months
    SHORT_DURATION_FUND = "short_duration_fund"  # 1-3 years
    CORPORATE_BOND_FUND = "corporate_bond_fund"
    BANKING_PSU_FUND = "banking_psu_fund"
    MEDIUM_DURATION_FUND = "medium_duration_fund"  # 3-4 years
    GILT_FUND = "gilt_fund"  # long duration govt
    FIXED_DEPOSIT = "fixed_deposit"  # bank FD
    RECURRING_DEPOSIT = "recurring_deposit"  # bank RD
    POST_OFFICE_MIS = "post_office_mis"  # monthly income scheme
    POST_OFFICE_NSC = "post_office_nsc"  # national savings cert
    POST_OFFICE_SCSS = "post_office_scss"  # senior citizen scheme
    RBI_FLOATING_BOND = "rbi_floating_bond"
    GSEC_RETAIL_DIRECT = "gsec_retail_direct"  # RBI retail direct

    # HYBRID
    CONSERVATIVE_HYBRID = "conservative_hybrid"  # ~25% equity
    AGGRESSIVE_HYBRID = "aggressive_hybrid"  # ~75% equity
    BALANCED_ADVANTAGE = "balanced_advantage"  # dynamic allocation
    ARBITRAGE_FUND = "arbitrage_fund"  # equity taxation, debt risk

    # EQUITY
    EQUITY_INDEX_LARGECAP = "equity_index_largecap"  # Nifty 50, Sensex
    EQUITY_LARGE_CAP = "equity_large_cap"
    EQUITY_FLEXI_CAP = "equity_flexi_cap"
    EQUITY_MID_CAP = "equity_mid_cap"
    EQUITY_SMALL_CAP = "equity_small_cap"
    EQUITY_DIVIDEND_YIELD = "equity_dividend_yield"
    EQUITY_SECTORAL = "equity_sectoral"
    EQUITY_ELSS = "equity_elss"  # 80C, 3yr lock-in
    INTERNATIONAL_FUND = "international_fund"

    # GOLD & COMMODITIES
    GOLD_ETF = "gold_etf"
    SOVEREIGN_GOLD_BOND = "sovereign_gold_bond"  # 8yr, 2.5% interest, zero CGT

    # REAL ASSETS
    REIT = "reit"
    INVIT = "invit"

    # TAX ADVANTAGED (separate category — lock-in changes behaviour)
    PPF = "ppf"  # EEE, 15yr lock-in (partial withdrawal allowed)
    EPF = "epf"  # EEE, till retirement
    NPS_TIER1 = "nps_tier1"  # EET, locked till 60
    NPS_TIER2 = "nps_tier2"  # no lock-in, no extra tax benefit


class TaxTreatment(Enum):
    """How each instrument is taxed in India."""

    EEE = "eee"  # exempt-exempt-exempt (PPF, EPF)
    EET = "eet"  # exempt-exempt-taxed (NPS)
    EQUITY_LTCG = "equity_ltcg"  # 10% above 1L after 1yr
    EQUITY_STCG = "equity_stcg"  # 15% under 1yr
    DEBT_SLAB = "debt_slab"  # added to income, taxed at slab rate
    SGB_MATURITY = "sgb_maturity"  # zero CGT at 8yr maturity; interest at slab
    REIT_INVIT = "reit_invit"  # mixed: dividend + LTCG components
    SAVINGS_INTEREST = "savings_interest"  # slab rate, 80TTA exemption up to 10K


class DeductionBenefit(Enum):
    """Tax-deduction benefit available on the instrument."""

    NONE = "none"
    SECTION_80C = "80c"  # up to 1.5L combined limit
    SECTION_80CCD_1B = "80ccd_1b"  # additional 50K for NPS only
    BOTH_80C_80CCD = "both"  # NPS Tier 1 gets both


@dataclass
class AssetClassProfile:
    """Static metadata describing a single investable asset class.

    This is a pure data record. Tax/return computations that act on it
    live in :mod:`assets` (see ``effective_return_after_tax`` and
    ``elss_effective_return``).
    """

    asset_class: AssetClass
    category: AssetCategory

    # Returns & risk
    expected_annual_return: float  # gross, pre-tax
    annual_volatility: float
    min_horizon_years: float
    max_horizon_years: Optional[float]  # None means no upper limit

    # Liquidity
    liquidity_score: float  # 1.0 = instant, 0.0 = fully locked
    lock_in_years: float  # 0 if no lock-in

    # Risk
    risk_level: int  # 1 (safest) to 10 (riskiest)

    # Tax
    tax_treatment: TaxTreatment
    deduction_benefit: DeductionBenefit

    # Accessibility
    min_investment: float  # minimum in rupees
    sip_possible: bool  # can invest monthly

    description: str

