"""Persona Engine (PART 2) — realistic Indian archetypes.

Defines 50–100 named archetypes (personas) covering the socio-economic
spectrum of Indian households. Each persona is a *template*: a
distribution over profile traits (income range, age range, education
floor, city-tier mix, behaviour centres, risk centre, literacy centre,
investment preferences). The population generator draws thousands of
variations around each persona using the seeded RNG and the Gaussian
copula, so the output is statistically realistic rather than a flat
random bag.

Personas are intentionally expressed as plain data (built by
``build_personas``) so the list can be extended or edited without
touching any engine code.
"""

from __future__ import annotations

from typing import Dict, List, Tuple

from ml.models import (
    EducationLevel,
    Industry,
    Occupation,
    Persona,
    PersonaName,
)

# ─────────────────────────────────────────────────────────────────────
# Persona table
#
# Each entry: (name, occupation, industry, education_floor, income_range,
# age_range, city_tier_dist, behaviour_centers, investment_preferences,
# risk_center, literacy_center, retirement_age)
# ─────────────────────────────────────────────────────────────────────


def _tier(weights: Dict[str, float]) -> Dict[str, float]:
    """Shortcut for a normalised city-tier distribution."""
    return weights


_PERSONA_SPECS: List[Tuple] = [
    # ── Students & early career ────────────────────────────────────
    ("student", Occupation.STUDENT, Industry.EDUCATION, EducationLevel.HIGH_SCHOOL,
     (0, 15000), (18, 26), _tier({"tier1": 0.4, "tier2": 0.4, "tier3": 0.2}),
     {"impulse_spending": 0.6, "financial_literacy": 0.3}, ["mutual_funds", "ppf"], 0.3, 0.3, 60),
    ("software_engineer", Occupation.SOFTWARE_ENGINEER, Industry.TECHNOLOGY, EducationLevel.UNDERGRAD,
     (60000, 400000), (22, 40), _tier({"tier1": 0.7, "tier2": 0.25, "tier3": 0.05}),
     {"overconfidence": 0.6, "loss_aversion": 0.3}, ["equity", "index_funds", "international_etf"], 0.7, 0.7, 60),
    ("doctor", Occupation.DOCTOR, Industry.HEALTHCARE, EducationLevel.POSTGRAD,
     (80000, 500000), (27, 60), _tier({"tier1": 0.5, "tier2": 0.35, "tier3": 0.15}),
     {"discipline": 0.7, "long_term_thinking": 0.7}, ["equity", "fixed_deposits", "insurance"], 0.5, 0.7, 62),
    ("government_employee", Occupation.GOVERNMENT_EMPLOYEE, Industry.GOVERNMENT, EducationLevel.UNDERGRAD,
     (35000, 200000), (25, 60), _tier({"tier1": 0.3, "tier2": 0.4, "tier3": 0.3}),
     {"discipline": 0.8, "loss_aversion": 0.6}, ["ppf", "nps", "fixed_deposits"], 0.3, 0.5, 60),
    ("teacher", Occupation.TEACHER, Industry.EDUCATION, EducationLevel.UNDERGRAD,
     (20000, 90000), (24, 58), _tier({"tier1": 0.2, "tier2": 0.4, "tier3": 0.4}),
     {"discipline": 0.7, "financial_literacy": 0.4}, ["ppf", "mutual_funds", "fixed_deposits"], 0.3, 0.5, 60),
    ("nurse", Occupation.NURSE, Industry.HEALTHCARE, EducationLevel.UNDERGRAD,
     (20000, 70000), (22, 55), _tier({"tier1": 0.3, "tier2": 0.4, "tier3": 0.3}),
     {"discipline": 0.6, "impulse_spending": 0.4}, ["ppf", "fixed_deposits", "insurance"], 0.3, 0.4, 60),
    ("ca", Occupation.CA, Industry.FINANCE, EducationLevel.POSTGRAD,
     (100000, 600000), (26, 60), _tier({"tier1": 0.7, "tier2": 0.25, "tier3": 0.05}),
     {"financial_literacy": 0.9, "discipline": 0.7}, ["equity", "direct_stocks", "tax_planning"], 0.6, 0.9, 62),
    ("lawyer", Occupation.LAWYER, Industry.LEGAL, EducationLevel.POSTGRAD,
     (60000, 400000), (28, 62), _tier({"tier1": 0.6, "tier2": 0.3, "tier3": 0.1}),
     {"financial_literacy": 0.7, "overconfidence": 0.5}, ["equity", "real_estate", "fixed_deposits"], 0.5, 0.7, 62),
    # ── Business & entrepreneurship ────────────────────────────────
    ("business_owner", Occupation.BUSINESS_OWNER, Industry.RETAIL, EducationLevel.HIGH_SCHOOL,
     (50000, 1500000), (30, 65), _tier({"tier1": 0.3, "tier2": 0.4, "tier3": 0.3}),
     {"overconfidence": 0.6, "impulse_spending": 0.5}, ["real_estate", "commodities", "fixed_deposits"], 0.5, 0.4, 60),
    ("retail_owner", Occupation.RETAIL_OWNER, Industry.RETAIL, EducationLevel.HIGH_SCHOOL,
     (30000, 400000), (28, 62), _tier({"tier1": 0.2, "tier2": 0.4, "tier3": 0.4}),
     {"impulse_spending": 0.5, "discipline": 0.5}, ["fixed_deposits", "gold", "real_estate"], 0.4, 0.3, 60),
    ("startup_founder", Occupation.STARTUP_FOUNDER, Industry.TECHNOLOGY, EducationLevel.UNDERGRAD,
     (0, 2000000), (24, 45), _tier({"tier1": 0.8, "tier2": 0.15, "tier3": 0.05}),
     {"overconfidence": 0.8, "risk_appetite": 0.9, "long_term_thinking": 0.6}, ["equity", "venture", "savings"], 0.8, 0.6, 60),
    ("consultant", Occupation.CONSULTANT, Industry.FINANCE, EducationLevel.POSTGRAD,
     (80000, 500000), (28, 58), _tier({"tier1": 0.7, "tier2": 0.25, "tier3": 0.05}),
     {"financial_literacy": 0.8, "overconfidence": 0.5}, ["equity", "index_funds", "international_etf"], 0.6, 0.8, 62),
    ("freelancer", Occupation.FREELANCER, Industry.TECHNOLOGY, EducationLevel.UNDERGRAD,
     (20000, 300000), (22, 55), _tier({"tier1": 0.5, "tier2": 0.35, "tier3": 0.15}),
     {"impulse_spending": 0.5, "financial_literacy": 0.5}, ["equity", "mutual_funds", "savings"], 0.5, 0.5, 60),
    # ── Agriculture & labour ───────────────────────────────────────
    ("farmer", Occupation.FARMER, Industry.AGRICULTURE, EducationLevel.NO_FORMAL,
     (10000, 60000), (25, 70), _tier({"tier1": 0.0, "tier2": 0.2, "tier3": 0.8}),
     {"impulse_spending": 0.4, "financial_literacy": 0.2}, ["gold", "fixed_deposits", "agriculture"], 0.2, 0.2, 65),
    # ── Homemaker & retired ────────────────────────────────────────
    ("homemaker", Occupation.HOMEMAKER, Industry.OTHER, EducationLevel.HIGH_SCHOOL,
     (0, 50000), (26, 60), _tier({"tier1": 0.3, "tier2": 0.4, "tier3": 0.3}),
     {"loss_aversion": 0.7, "discipline": 0.6}, ["gold", "fixed_deposits", "ppf"], 0.2, 0.3, 60),
    ("retired", Occupation.RETIRED, Industry.OTHER, EducationLevel.HIGH_SCHOOL,
     (20000, 150000), (60, 80), _tier({"tier1": 0.3, "tier2": 0.4, "tier3": 0.3}),
     {"loss_aversion": 0.8, "panic_selling": 0.5}, ["fixed_deposits", "bond_yields", "annuity"], 0.1, 0.4, 60),
    # ── Other / generic ────────────────────────────────────────────
    ("other", Occupation.OTHER, Industry.OTHER, EducationLevel.SCHOOL,
     (15000, 80000), (20, 65), _tier({"tier1": 0.2, "tier2": 0.4, "tier3": 0.4}),
     {"impulse_spending": 0.5, "financial_literacy": 0.3}, ["fixed_deposits", "gold", "ppf"], 0.3, 0.3, 60),
]

# Additional archetypes to reach the 50+ target. These are derived from
# the base definitions by adjusting income bands and behaviour centres,
# producing distinct clusters (e.g. "senior_software_engineer",
# "tier1_doctor", "home_loan_heavy_business_owner").
_EXTRA_SPECS: List[Tuple] = [
    ("senior_software_engineer", Occupation.SOFTWARE_ENGINEER, Industry.TECHNOLOGY, EducationLevel.POSTGRAD,
     (250000, 900000), (35, 50), _tier({"tier1": 0.8, "tier2": 0.2, "tier3": 0.0}),
     {"financial_literacy": 0.8, "long_term_thinking": 0.8}, ["equity", "index_funds", "real_estate"], 0.7, 0.8, 60),
    ("tier1_doctor", Occupation.DOCTOR, Industry.HEALTHCARE, EducationLevel.POSTGRAD,
     (150000, 600000), (32, 60), _tier({"tier1": 0.9, "tier2": 0.1, "tier3": 0.0}),
     {"discipline": 0.7, "long_term_thinking": 0.7}, ["equity", "fixed_deposits", "insurance"], 0.5, 0.7, 62),
    ("tier3_doctor", Occupation.DOCTOR, Industry.HEALTHCARE, EducationLevel.POSTGRAD,
     (40000, 150000), (28, 60), _tier({"tier1": 0.0, "tier2": 0.3, "tier3": 0.7}),
     {"discipline": 0.6, "loss_aversion": 0.5}, ["fixed_deposits", "ppf", "insurance"], 0.3, 0.5, 62),
    ("home_loan_business_owner", Occupation.BUSINESS_OWNER, Industry.CONSTRUCTION, EducationLevel.HIGH_SCHOOL,
     (60000, 1200000), (32, 60), _tier({"tier1": 0.3, "tier2": 0.4, "tier3": 0.3}),
     {"discipline": 0.5, "impulse_spending": 0.4}, ["real_estate", "fixed_deposits", "gold"], 0.4, 0.4, 60),
    ("teacher_tier2", Occupation.TEACHER, Industry.EDUCATION, EducationLevel.UNDERGRAD,
     (25000, 110000), (28, 58), _tier({"tier1": 0.1, "tier2": 0.6, "tier3": 0.3}),
     {"discipline": 0.7, "loss_aversion": 0.6}, ["ppf", "mutual_funds", "fixed_deposits"], 0.3, 0.5, 60),
    ("agriculture_owner", Occupation.FARMER, Industry.AGRICULTURE, EducationLevel.SCHOOL,
     (15000, 80000), (28, 65), _tier({"tier1": 0.0, "tier2": 0.2, "tier3": 0.8}),
     {"impulse_spending": 0.3, "financial_literacy": 0.2}, ["gold", "fixed_deposits", "agriculture"], 0.2, 0.2, 65),
    ("nurse_tier2", Occupation.NURSE, Industry.HEALTHCARE, EducationLevel.UNDERGRAD,
     (20000, 60000), (24, 55), _tier({"tier1": 0.1, "tier2": 0.5, "tier3": 0.4}),
     {"discipline": 0.6, "impulse_spending": 0.4}, ["ppf", "fixed_deposits", "insurance"], 0.3, 0.4, 60),
    ("retired_professional", Occupation.RETIRED, Industry.FINANCE, EducationLevel.POSTGRAD,
     (50000, 200000), (60, 80), _tier({"tier1": 0.5, "tier2": 0.3, "tier3": 0.2}),
     {"loss_aversion": 0.7, "financial_literacy": 0.6}, ["bond_yields", "fixed_deposits", "annuity"], 0.2, 0.6, 60),
    ("freelancer_experienced", Occupation.FREELANCER, Industry.TECHNOLOGY, EducationLevel.UNDERGRAD,
     (50000, 400000), (30, 50), _tier({"tier1": 0.5, "tier2": 0.35, "tier3": 0.15}),
     {"financial_literacy": 0.6, "discipline": 0.5}, ["equity", "mutual_funds", "savings"], 0.5, 0.6, 60),
    ("startup_founder_scaleup", Occupation.STARTUP_FOUNDER, Industry.TECHNOLOGY, EducationLevel.POSTGRAD,
     (500000, 3000000), (30, 45), _tier({"tier1": 0.9, "tier2": 0.1, "tier3": 0.0}),
     {"overconfidence": 0.7, "risk_appetite": 0.9, "long_term_thinking": 0.7}, ["equity", "venture", "real_estate"], 0.8, 0.7, 60),
    ("consultant_senior", Occupation.CONSULTANT, Industry.FINANCE, EducationLevel.POSTGRAD,
     (150000, 800000), (35, 60), _tier({"tier1": 0.8, "tier2": 0.2, "tier3": 0.0}),
     {"financial_literacy": 0.9, "overconfidence": 0.5}, ["equity", "index_funds", "international_etf"], 0.6, 0.9, 62),
    ("government_employee_senior", Occupation.GOVERNMENT_EMPLOYEE, Industry.GOVERNMENT, EducationLevel.POSTGRAD,
     (100000, 300000), (45, 60), _tier({"tier1": 0.3, "tier2": 0.4, "tier3": 0.3}),
     {"discipline": 0.8, "loss_aversion": 0.6}, ["ppf", "nps", "fixed_deposits"], 0.3, 0.6, 60),
    ("lawyer_corporate", Occupation.LAWYER, Industry.LEGAL, EducationLevel.POSTGRAD,
     (150000, 700000), (32, 60), _tier({"tier1": 0.8, "tier2": 0.2, "tier3": 0.0}),
     {"financial_literacy": 0.8, "overconfidence": 0.5}, ["equity", "real_estate", "fixed_deposits"], 0.5, 0.8, 62),
    ("ca_consultant", Occupation.CA, Industry.FINANCE, EducationLevel.POSTGRAD,
     (150000, 800000), (30, 60), _tier({"tier1": 0.8, "tier2": 0.2, "tier3": 0.0}),
     {"financial_literacy": 0.9, "discipline": 0.7}, ["equity", "direct_stocks", "tax_planning"], 0.6, 0.9, 62),
    ("homemaker_urban", Occupation.HOMEMAKER, Industry.OTHER, EducationLevel.HIGH_SCHOOL,
     (0, 80000), (28, 58), _tier({"tier1": 0.6, "tier2": 0.3, "tier3": 0.1}),
     {"loss_aversion": 0.6, "discipline": 0.6}, ["gold", "fixed_deposits", "ppf"], 0.2, 0.4, 60),
    ("retail_owner_urban", Occupation.RETAIL_OWNER, Industry.RETAIL, EducationLevel.HIGH_SCHOOL,
     (40000, 500000), (30, 60), _tier({"tier1": 0.5, "tier2": 0.3, "tier3": 0.2}),
     {"impulse_spending": 0.5, "discipline": 0.5}, ["fixed_deposits", "gold", "real_estate"], 0.4, 0.4, 60),
    ("farmer_progressive", Occupation.FARMER, Industry.AGRICULTURE, EducationLevel.SCHOOL,
     (20000, 100000), (30, 60), _tier({"tier1": 0.0, "tier2": 0.3, "tier3": 0.7}),
     {"impulse_spending": 0.3, "financial_literacy": 0.3}, ["gold", "fixed_deposits", "agriculture"], 0.2, 0.3, 65),
    ("student_postgrad", Occupation.STUDENT, Industry.EDUCATION, EducationLevel.POSTGRAD,
     (0, 25000), (22, 28), _tier({"tier1": 0.5, "tier2": 0.35, "tier3": 0.15}),
     {"impulse_spending": 0.5, "financial_literacy": 0.4}, ["mutual_funds", "ppf", "savings"], 0.4, 0.4, 60),
    ("software_engineer_tier2", Occupation.SOFTWARE_ENGINEER, Industry.TECHNOLOGY, EducationLevel.UNDERGRAD,
     (40000, 150000), (22, 40), _tier({"tier1": 0.2, "tier2": 0.6, "tier3": 0.2}),
     {"overconfidence": 0.5, "loss_aversion": 0.4}, ["equity", "index_funds", "mutual_funds"], 0.6, 0.6, 60),
    ("doctor_public_sector", Occupation.DOCTOR, Industry.HEALTHCARE, EducationLevel.POSTGRAD,
     (60000, 150000), (28, 60), _tier({"tier1": 0.2, "tier2": 0.4, "tier3": 0.4}),
     {"discipline": 0.7, "loss_aversion": 0.5}, ["fixed_deposits", "ppf", "insurance"], 0.3, 0.5, 62),
    ("retired_government", Occupation.RETIRED, Industry.GOVERNMENT, EducationLevel.UNDERGRAD,
     (25000, 80000), (60, 80), _tier({"tier1": 0.2, "tier2": 0.4, "tier3": 0.4}),
     {"loss_aversion": 0.8, "discipline": 0.7}, ["fixed_deposits", "ppf", "annuity"], 0.1, 0.5, 60),
    # ── Additional tier-2/3 variants to reach 50+ archetypes ───────
    ("manufacturing_engineer", Occupation.SOFTWARE_ENGINEER, Industry.MANUFACTURING, EducationLevel.UNDERGRAD,
     (30000, 120000), (23, 45), _tier({"tier1": 0.2, "tier2": 0.5, "tier3": 0.3}),
     {"discipline": 0.6, "financial_literacy": 0.4}, ["ppf", "mutual_funds", "fixed_deposits"], 0.4, 0.5, 60),
    ("transport_operator", Occupation.OTHER, Industry.TRANSPORT, EducationLevel.SCHOOL,
     (15000, 60000), (25, 60), _tier({"tier1": 0.0, "tier2": 0.3, "tier3": 0.7}),
     {"impulse_spending": 0.5, "discipline": 0.4}, ["gold", "fixed_deposits", "savings"], 0.3, 0.2, 60),
    ("energy_sector_employee", Occupation.GOVERNMENT_EMPLOYEE, Industry.ENERGY, EducationLevel.UNDERGRAD,
     (40000, 150000), (25, 58), _tier({"tier1": 0.3, "tier2": 0.4, "tier3": 0.3}),
     {"discipline": 0.7, "loss_aversion": 0.5}, ["ppf", "nps", "fixed_deposits"], 0.3, 0.5, 60),
    ("construction_owner", Occupation.BUSINESS_OWNER, Industry.CONSTRUCTION, EducationLevel.HIGH_SCHOOL,
     (40000, 800000), (30, 60), _tier({"tier1": 0.2, "tier2": 0.4, "tier3": 0.4}),
     {"overconfidence": 0.5, "impulse_spending": 0.4}, ["real_estate", "fixed_deposits", "gold"], 0.4, 0.3, 60),
    ("media_professional", Occupation.CONSULTANT, Industry.MEDIA, EducationLevel.UNDERGRAD,
     (30000, 150000), (24, 50), _tier({"tier1": 0.5, "tier2": 0.35, "tier3": 0.15}),
     {"impulse_spending": 0.6, "overconfidence": 0.5}, ["mutual_funds", "fixed_deposits", "savings"], 0.4, 0.5, 60),
    ("finance_analyst", Occupation.CONSULTANT, Industry.FINANCE, EducationLevel.POSTGRAD,
     (60000, 300000), (25, 50), _tier({"tier1": 0.7, "tier2": 0.25, "tier3": 0.05}),
     {"financial_literacy": 0.8, "overconfidence": 0.5}, ["equity", "index_funds", "direct_stocks"], 0.6, 0.8, 60),
    ("pharma_rep", Occupation.SOFTWARE_ENGINEER, Industry.HEALTHCARE, EducationLevel.UNDERGRAD,
     (25000, 90000), (24, 50), _tier({"tier1": 0.2, "tier2": 0.4, "tier3": 0.4}),
     {"discipline": 0.5, "impulse_spending": 0.5}, ["mutual_funds", "fixed_deposits", "insurance"], 0.4, 0.4, 60),
    ("it_consultant_tier2", Occupation.CONSULTANT, Industry.TECHNOLOGY, EducationLevel.UNDERGRAD,
     (50000, 250000), (25, 50), _tier({"tier1": 0.3, "tier2": 0.5, "tier3": 0.2}),
     {"financial_literacy": 0.7, "overconfidence": 0.5}, ["equity", "index_funds", "mutual_funds"], 0.6, 0.7, 60),
    ("bank_employee", Occupation.GOVERNMENT_EMPLOYEE, Industry.FINANCE, EducationLevel.UNDERGRAD,
     (35000, 150000), (24, 55), _tier({"tier1": 0.3, "tier2": 0.4, "tier3": 0.3}),
     {"discipline": 0.7, "financial_literacy": 0.6}, ["ppf", "fixed_deposits", "mutual_funds"], 0.3, 0.6, 60),
    ("insurance_agent", Occupation.OTHER, Industry.FINANCE, EducationLevel.UNDERGRAD,
     (20000, 100000), (25, 55), _tier({"tier1": 0.2, "tier2": 0.4, "tier3": 0.4}),
     {"overconfidence": 0.5, "impulse_spending": 0.5}, ["insurance", "fixed_deposits", "mutual_funds"], 0.4, 0.4, 60),
    ("healthcare_worker", Occupation.NURSE, Industry.HEALTHCARE, EducationLevel.HIGH_SCHOOL,
     (15000, 50000), (22, 55), _tier({"tier1": 0.1, "tier2": 0.3, "tier3": 0.6}),
     {"discipline": 0.5, "impulse_spending": 0.4}, ["ppf", "fixed_deposits", "insurance"], 0.3, 0.3, 60),
    ("retired_teacher", Occupation.RETIRED, Industry.EDUCATION, EducationLevel.UNDERGRAD,
     (20000, 60000), (60, 80), _tier({"tier1": 0.2, "tier2": 0.4, "tier3": 0.4}),
     {"loss_aversion": 0.8, "discipline": 0.7}, ["fixed_deposits", "ppf", "annuity"], 0.1, 0.5, 60),
    ("retired_doctor", Occupation.RETIRED, Industry.HEALTHCARE, EducationLevel.POSTGRAD,
     (50000, 200000), (60, 80), _tier({"tier1": 0.4, "tier2": 0.4, "tier3": 0.2}),
     {"loss_aversion": 0.7, "discipline": 0.7}, ["bond_yields", "fixed_deposits", "annuity"], 0.2, 0.6, 60),
    ("homemaker_tier3", Occupation.HOMEMAKER, Industry.OTHER, EducationLevel.SCHOOL,
     (0, 30000), (26, 60), _tier({"tier1": 0.0, "tier2": 0.3, "tier3": 0.7}),
     {"loss_aversion": 0.8, "discipline": 0.6}, ["gold", "fixed_deposits", "ppf"], 0.1, 0.2, 60),
    ("freelancer_designer", Occupation.FREELANCER, Industry.MEDIA, EducationLevel.UNDERGRAD,
     (20000, 150000), (22, 50), _tier({"tier1": 0.4, "tier2": 0.4, "tier3": 0.2}),
     {"impulse_spending": 0.6, "overconfidence": 0.4}, ["mutual_funds", "savings", "fixed_deposits"], 0.4, 0.4, 60),
    ("startup_employee", Occupation.SOFTWARE_ENGINEER, Industry.TECHNOLOGY, EducationLevel.UNDERGRAD,
     (40000, 200000), (23, 38), _tier({"tier1": 0.7, "tier2": 0.25, "tier3": 0.05}),
     {"overconfidence": 0.6, "risk_appetite": 0.7}, ["equity", "index_funds", "esop"], 0.7, 0.6, 60),
    ("chief_technology_officer", Occupation.SOFTWARE_ENGINEER, Industry.TECHNOLOGY, EducationLevel.POSTGRAD,
     (400000, 2000000), (35, 55), _tier({"tier1": 0.9, "tier2": 0.1, "tier3": 0.0}),
     {"financial_literacy": 0.9, "long_term_thinking": 0.8}, ["equity", "index_funds", "international_etf", "real_estate"], 0.7, 0.9, 60),
    ("senior_manager", Occupation.CONSULTANT, Industry.MANUFACTURING, EducationLevel.POSTGRAD,
     (150000, 600000), (35, 55), _tier({"tier1": 0.6, "tier2": 0.3, "tier3": 0.1}),
     {"discipline": 0.7, "long_term_thinking": 0.7}, ["equity", "mutual_funds", "real_estate"], 0.5, 0.7, 60),
    ("school_principal", Occupation.TEACHER, Industry.EDUCATION, EducationLevel.POSTGRAD,
     (60000, 200000), (40, 60), _tier({"tier1": 0.3, "tier2": 0.4, "tier3": 0.3}),
     {"discipline": 0.8, "loss_aversion": 0.5}, ["ppf", "mutual_funds", "fixed_deposits"], 0.3, 0.6, 60),
    ("farmer_landowner", Occupation.FARMER, Industry.AGRICULTURE, EducationLevel.HIGH_SCHOOL,
     (30000, 150000), (35, 65), _tier({"tier1": 0.0, "tier2": 0.3, "tier3": 0.7}),
     {"impulse_spending": 0.3, "discipline": 0.5}, ["gold", "real_estate", "fixed_deposits"], 0.3, 0.3, 65),
    ("retail_chain_owner", Occupation.RETAIL_OWNER, Industry.RETAIL, EducationLevel.HIGH_SCHOOL,
     (80000, 500000), (32, 60), _tier({"tier1": 0.4, "tier2": 0.4, "tier3": 0.2}),
     {"impulse_spending": 0.4, "discipline": 0.6}, ["real_estate", "fixed_deposits", "equity"], 0.5, 0.4, 60),
    ("lawyer_family_practice", Occupation.LAWYER, Industry.LEGAL, EducationLevel.POSTGRAD,
     (40000, 200000), (30, 60), _tier({"tier1": 0.3, "tier2": 0.4, "tier3": 0.3}),
     {"financial_literacy": 0.6, "overconfidence": 0.5}, ["equity", "real_estate", "fixed_deposits"], 0.5, 0.6, 60),
    ("ca_firm_partner", Occupation.CA, Industry.FINANCE, EducationLevel.POSTGRAD,
     (200000, 1000000), (35, 60), _tier({"tier1": 0.8, "tier2": 0.2, "tier3": 0.0}),
     {"financial_literacy": 0.9, "discipline": 0.8}, ["equity", "direct_stocks", "real_estate", "tax_planning"], 0.6, 0.9, 62),
    ("researcher", Occupation.DOCTOR, Industry.EDUCATION, EducationLevel.DOCTORATE,
     (40000, 150000), (28, 60), _tier({"tier1": 0.5, "tier2": 0.35, "tier3": 0.15}),
     {"discipline": 0.7, "long_term_thinking": 0.7}, ["ppf", "mutual_funds", "fixed_deposits"], 0.3, 0.7, 60),
    ("nre_employee", Occupation.CONSULTANT, Industry.TECHNOLOGY, EducationLevel.POSTGRAD,
     (100000, 500000), (30, 55), _tier({"tier1": 0.8, "tier2": 0.15, "tier3": 0.05}),
     {"financial_literacy": 0.8, "long_term_thinking": 0.7}, ["equity", "international_etf", "real_estate"], 0.6, 0.8, 60),
    ("government_teacher_public", Occupation.GOVERNMENT_EMPLOYEE, Industry.EDUCATION, EducationLevel.UNDERGRAD,
     (25000, 80000), (25, 58), _tier({"tier1": 0.1, "tier2": 0.4, "tier3": 0.5}),
     {"discipline": 0.7, "loss_aversion": 0.6}, ["ppf", "nps", "fixed_deposits"], 0.2, 0.4, 60),
    ("retail_employee", Occupation.OTHER, Industry.RETAIL, EducationLevel.HIGH_SCHOOL,
     (15000, 50000), (22, 55), _tier({"tier1": 0.2, "tier2": 0.4, "tier3": 0.4}),
     {"impulse_spending": 0.5, "discipline": 0.3}, ["ppf", "fixed_deposits", "savings"], 0.2, 0.2, 60),
    ("homemaker_wealthy", Occupation.HOMEMAKER, Industry.OTHER, EducationLevel.UNDERGRAD,
     (0, 200000), (35, 60), _tier({"tier1": 0.7, "tier2": 0.25, "tier3": 0.05}),
     {"loss_aversion": 0.5, "discipline": 0.7}, ["gold", "real_estate", "fixed_deposits", "equity"], 0.4, 0.5, 60),
    ("retired_entrepreneur", Occupation.RETIRED, Industry.RETAIL, EducationLevel.HIGH_SCHOOL,
     (50000, 300000), (60, 80), _tier({"tier1": 0.3, "tier2": 0.4, "tier3": 0.3}),
     {"loss_aversion": 0.6, "discipline": 0.6}, ["bond_yields", "fixed_deposits", "real_estate"], 0.2, 0.5, 60),
    ("professional_sports", Occupation.OTHER, Industry.MEDIA, EducationLevel.UNDERGRAD,
     (50000, 500000), (20, 35), _tier({"tier1": 0.5, "tier2": 0.3, "tier3": 0.2}),
     {"impulse_spending": 0.7, "overconfidence": 0.6}, ["fixed_deposits", "mutual_funds", "savings"], 0.4, 0.3, 55),
]


def build_personas() -> List[Persona]:
    """Build the full persona registry (50–100 archetypes).

    Returns a list of :class:`~ml.models.Persona` objects covering the
    Indian household socio-economic spectrum. The base and extra specs
    are combined to exceed the 50-archetype target, with each persona
    parameterised for the population generator.
    """
    personas: List[Persona] = []
    all_specs = _PERSONA_SPECS + _EXTRA_SPECS
    for spec in all_specs:
        (
            name,
            occupation,
            industry,
            edu_floor,
            income_range,
            age_range,
            city_tier_dist,
            behaviour_centers,
            prefs,
            risk,
            literacy,
            ret_age,
        ) = spec
        personas.append(
            Persona(
                name=PersonaName(name),
                occupation=occupation,
                industry=industry,
                education_floor=edu_floor,
                income_range=income_range,
                age_range=age_range,
                city_tier_dist=city_tier_dist,
                behaviour_centers=behaviour_centers,
                investment_preferences=prefs,
                risk_center=risk,
                literacy_center=literacy,
                retirement_age=ret_age,
            )
        )
    return personas


# Pre-built registry (module-level singleton).
PERSONA_REGISTRY: List[Persona] = build_personas()


def get_persona(name: str | PersonaName) -> Persona | None:
    """Return a persona by name (case-insensitive), or ``None``."""
    key = name.value if isinstance(name, PersonaName) else str(name).lower()
    for p in PERSONA_REGISTRY:
        if p.name.value == key:
            return p
    return None


def list_persona_names() -> List[str]:
    """Return the names of all registered personas."""
    return [p.name.value for p in PERSONA_REGISTRY]
