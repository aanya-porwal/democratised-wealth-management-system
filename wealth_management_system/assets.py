"""Investment product database and asset-allocation building blocks.

This module owns everything related to *investment products*:

* ``AssetClassProfile`` — the dataclass describing a single instrument
  (defined in :mod:`models`).
* ``ASSET_PROFILES`` — the curated database of every supported instrument.
* ``effective_return_after_tax`` / ``elss_effective_return`` — the
  after-tax return computations used by the recommendation engine.
"""

from typing import Dict

from wealth_management_system.models import (
    AssetCategory,
    AssetClass,
    AssetClassProfile,
    DeductionBenefit,
    TaxTreatment,
)
from wealth_management_system.utils import (
    EQUITY_LTCG_RATE,
    SGB_INTEREST_RATE,
    elss_irr,
)

ASSET_PROFILES: Dict[AssetClass, AssetClassProfile] = {
    # ── CASH & LIQUID ─────────────────────────────────────────────
    AssetClass.SAVINGS_ACCOUNT: AssetClassProfile(
        asset_class=AssetClass.SAVINGS_ACCOUNT,
        category=AssetCategory.CASH_AND_LIQUID,
        expected_annual_return=0.035,
        annual_volatility=0.0,
        min_horizon_years=0.0,
        max_horizon_years=1.0,
        liquidity_score=1.0,
        lock_in_years=0,
        risk_level=1,
        tax_treatment=TaxTreatment.SAVINGS_INTEREST,
        deduction_benefit=DeductionBenefit.NONE,
        min_investment=0,
        sip_possible=True,
        description="Regular savings account. 80TTA: first ₹10K interest exempt.",
    ),
    AssetClass.LIQUID_FUND: AssetClassProfile(
        asset_class=AssetClass.LIQUID_FUND,
        category=AssetCategory.CASH_AND_LIQUID,
        expected_annual_return=0.068,
        annual_volatility=0.003,
        min_horizon_years=0.0,
        max_horizon_years=1.0,
        liquidity_score=0.95,
        lock_in_years=0,
        risk_level=1,
        tax_treatment=TaxTreatment.DEBT_SLAB,
        deduction_benefit=DeductionBenefit.NONE,
        min_investment=500,
        sip_possible=True,
        description="Liquid mutual funds. Better than savings account. T+1 redemption.",
    ),
    AssetClass.OVERNIGHT_FUND: AssetClassProfile(
        asset_class=AssetClass.OVERNIGHT_FUND,
        category=AssetCategory.CASH_AND_LIQUID,
        expected_annual_return=0.065,
        annual_volatility=0.001,
        min_horizon_years=0.0,
        max_horizon_years=0.25,
        liquidity_score=1.0,
        lock_in_years=0,
        risk_level=1,
        tax_treatment=TaxTreatment.DEBT_SLAB,
        deduction_benefit=DeductionBenefit.NONE,
        min_investment=500,
        sip_possible=False,
        description="Overnight funds. Safest mutual fund category. For parking money.",
    ),
    AssetClass.MONEY_MARKET_FUND: AssetClassProfile(
        asset_class=AssetClass.MONEY_MARKET_FUND,
        category=AssetCategory.CASH_AND_LIQUID,
        expected_annual_return=0.072,
        annual_volatility=0.005,
        min_horizon_years=0.25,
        max_horizon_years=1.0,
        liquidity_score=0.9,
        lock_in_years=0,
        risk_level=2,
        tax_treatment=TaxTreatment.DEBT_SLAB,
        deduction_benefit=DeductionBenefit.NONE,
        min_investment=500,
        sip_possible=True,
        description="Money market funds. Up to 1yr maturity instruments.",
    ),
    # ── DEBT ──────────────────────────────────────────────────────
    AssetClass.ULTRA_SHORT_FUND: AssetClassProfile(
        asset_class=AssetClass.ULTRA_SHORT_FUND,
        category=AssetCategory.DEBT,
        expected_annual_return=0.073,
        annual_volatility=0.008,
        min_horizon_years=0.25,
        max_horizon_years=1.0,
        liquidity_score=0.9,
        lock_in_years=0,
        risk_level=2,
        tax_treatment=TaxTreatment.DEBT_SLAB,
        deduction_benefit=DeductionBenefit.NONE,
        min_investment=500,
        sip_possible=True,
        description="3-6 month horizon debt funds.",
    ),
    AssetClass.LOW_DURATION_FUND: AssetClassProfile(
        asset_class=AssetClass.LOW_DURATION_FUND,
        category=AssetCategory.DEBT,
        expected_annual_return=0.076,
        annual_volatility=0.012,
        min_horizon_years=0.5,
        max_horizon_years=2.0,
        liquidity_score=0.88,
        lock_in_years=0,
        risk_level=2,
        tax_treatment=TaxTreatment.DEBT_SLAB,
        deduction_benefit=DeductionBenefit.NONE,
        min_investment=500,
        sip_possible=True,
        description="6-12 month horizon debt funds.",
    ),
    AssetClass.SHORT_DURATION_FUND: AssetClassProfile(
        asset_class=AssetClass.SHORT_DURATION_FUND,
        category=AssetCategory.DEBT,
        expected_annual_return=0.078,
        annual_volatility=0.018,
        min_horizon_years=1.0,
        max_horizon_years=3.0,
        liquidity_score=0.85,
        lock_in_years=0,
        risk_level=3,
        tax_treatment=TaxTreatment.DEBT_SLAB,
        deduction_benefit=DeductionBenefit.NONE,
        min_investment=500,
        sip_possible=True,
        description="1-3 year horizon debt funds.",
    ),
    AssetClass.CORPORATE_BOND_FUND: AssetClassProfile(
        asset_class=AssetClass.CORPORATE_BOND_FUND,
        category=AssetCategory.DEBT,
        expected_annual_return=0.082,
        annual_volatility=0.025,
        min_horizon_years=2.0,
        max_horizon_years=5.0,
        liquidity_score=0.82,
        lock_in_years=0,
        risk_level=3,
        tax_treatment=TaxTreatment.DEBT_SLAB,
        deduction_benefit=DeductionBenefit.NONE,
        min_investment=500,
        sip_possible=True,
        description="AA+ rated corporate bond funds. Higher yield, minimal credit risk.",
    ),
    AssetClass.BANKING_PSU_FUND: AssetClassProfile(
        asset_class=AssetClass.BANKING_PSU_FUND,
        category=AssetCategory.DEBT,
        expected_annual_return=0.079,
        annual_volatility=0.020,
        min_horizon_years=1.0,
        max_horizon_years=4.0,
        liquidity_score=0.85,
        lock_in_years=0,
        risk_level=2,
        tax_treatment=TaxTreatment.DEBT_SLAB,
        deduction_benefit=DeductionBenefit.NONE,
        min_investment=500,
        sip_possible=True,
        description="Banking and PSU debt funds. Very low credit risk.",
    ),
    AssetClass.MEDIUM_DURATION_FUND: AssetClassProfile(
        asset_class=AssetClass.MEDIUM_DURATION_FUND,
        category=AssetCategory.DEBT,
        expected_annual_return=0.083,
        annual_volatility=0.035,
        min_horizon_years=3.0,
        max_horizon_years=5.0,
        liquidity_score=0.80,
        lock_in_years=0,
        risk_level=3,
        tax_treatment=TaxTreatment.DEBT_SLAB,
        deduction_benefit=DeductionBenefit.NONE,
        min_investment=500,
        sip_possible=True,
        description="3-4 year Macaulay duration debt funds.",
    ),
    AssetClass.GILT_FUND: AssetClassProfile(
        asset_class=AssetClass.GILT_FUND,
        category=AssetCategory.DEBT,
        expected_annual_return=0.087,
        annual_volatility=0.055,
        min_horizon_years=5.0,
        max_horizon_years=None,
        liquidity_score=0.78,
        lock_in_years=0,
        risk_level=4,
        tax_treatment=TaxTreatment.DEBT_SLAB,
        deduction_benefit=DeductionBenefit.NONE,
        min_investment=500,
        sip_possible=True,
        description="Long duration government securities. Interest rate sensitive.",
    ),
    AssetClass.FIXED_DEPOSIT: AssetClassProfile(
        asset_class=AssetClass.FIXED_DEPOSIT,
        category=AssetCategory.DEBT,
        expected_annual_return=0.074,
        annual_volatility=0.0,
        min_horizon_years=0.25,
        max_horizon_years=5.0,
        liquidity_score=0.70,
        lock_in_years=0,  # technically breakable with penalty
        risk_level=1,
        tax_treatment=TaxTreatment.DEBT_SLAB,
        deduction_benefit=DeductionBenefit.NONE,
        min_investment=1000,
        sip_possible=False,
        description=(
            "Bank FDs. DICGC insured up to ₹5L. Guaranteed returns. "
            "Premature withdrawal with penalty. Very popular in tier 2/3."
        ),
    ),
    AssetClass.RECURRING_DEPOSIT: AssetClassProfile(
        asset_class=AssetClass.RECURRING_DEPOSIT,
        category=AssetCategory.DEBT,
        expected_annual_return=0.072,
        annual_volatility=0.0,
        min_horizon_years=0.5,
        max_horizon_years=5.0,
        liquidity_score=0.65,
        lock_in_years=0,
        risk_level=1,
        tax_treatment=TaxTreatment.DEBT_SLAB,
        deduction_benefit=DeductionBenefit.NONE,
        min_investment=100,
        sip_possible=True,  # IS a SIP by nature
        description=(
            "Recurring deposit. Monthly fixed contribution. "
            "Familiar to tier 2/3 users. Safe and guaranteed."
        ),
    ),
    AssetClass.POST_OFFICE_MIS: AssetClassProfile(
        asset_class=AssetClass.POST_OFFICE_MIS,
        category=AssetCategory.DEBT,
        expected_annual_return=0.077,
        annual_volatility=0.0,
        min_horizon_years=5.0,
        max_horizon_years=5.0,
        liquidity_score=0.50,
        lock_in_years=5,
        risk_level=1,
        tax_treatment=TaxTreatment.DEBT_SLAB,
        deduction_benefit=DeductionBenefit.NONE,
        min_investment=1000,
        sip_possible=False,
        description=(
            "Post Office Monthly Income Scheme. Govt guaranteed. "
            "Monthly income payout. Max ₹9L single, ₹15L joint. "
            "Extremely trusted in tier 2/3 India."
        ),
    ),
    AssetClass.POST_OFFICE_NSC: AssetClassProfile(
        asset_class=AssetClass.POST_OFFICE_NSC,
        category=AssetCategory.DEBT,
        expected_annual_return=0.077,
        annual_volatility=0.0,
        min_horizon_years=5.0,
        max_horizon_years=5.0,
        liquidity_score=0.30,
        lock_in_years=5,
        risk_level=1,
        tax_treatment=TaxTreatment.DEBT_SLAB,
        deduction_benefit=DeductionBenefit.SECTION_80C,
        min_investment=1000,
        sip_possible=False,
        description=(
            "National Savings Certificate. 80C eligible. 5yr lock-in. "
            "Govt guaranteed. Accrued interest reinvested counts as 80C."
        ),
    ),
    AssetClass.POST_OFFICE_SCSS: AssetClassProfile(
        asset_class=AssetClass.POST_OFFICE_SCSS,
        category=AssetCategory.DEBT,
        expected_annual_return=0.082,
        annual_volatility=0.0,
        min_horizon_years=5.0,
        max_horizon_years=5.0,
        liquidity_score=0.40,
        lock_in_years=5,
        risk_level=1,
        tax_treatment=TaxTreatment.DEBT_SLAB,
        deduction_benefit=DeductionBenefit.SECTION_80C,
        min_investment=1000,
        sip_possible=False,
        description=(
            "Senior Citizen Savings Scheme. Age 60+. 8.2% rate. "
            "80C eligible. Max ₹30L. Highest safe return for retirees."
        ),
    ),
    AssetClass.RBI_FLOATING_BOND: AssetClassProfile(
        asset_class=AssetClass.RBI_FLOATING_BOND,
        category=AssetCategory.DEBT,
        expected_annual_return=0.082,
        annual_volatility=0.0,
        min_horizon_years=7.0,
        max_horizon_years=7.0,
        liquidity_score=0.20,
        lock_in_years=7,
        risk_level=1,
        tax_treatment=TaxTreatment.DEBT_SLAB,
        deduction_benefit=DeductionBenefit.NONE,
        min_investment=1000,
        sip_possible=False,
        description=(
            "RBI Floating Rate Savings Bonds. 7yr lock-in. "
            "Rate linked to NSC + 35bps. Sovereign guarantee."
        ),
    ),
    AssetClass.GSEC_RETAIL_DIRECT: AssetClassProfile(
        asset_class=AssetClass.GSEC_RETAIL_DIRECT,
        category=AssetCategory.DEBT,
        expected_annual_return=0.073,
        annual_volatility=0.04,
        min_horizon_years=1.0,
        max_horizon_years=None,
        liquidity_score=0.65,
        lock_in_years=0,
        risk_level=2,
        tax_treatment=TaxTreatment.DEBT_SLAB,
        deduction_benefit=DeductionBenefit.NONE,
        min_investment=10000,
        sip_possible=False,
        description=(
            "G-Secs via RBI Retail Direct. Sovereign. "
            "Interest rate risk if sold before maturity."
        ),
    ),
    # ── HYBRID ────────────────────────────────────────────────────
    AssetClass.CONSERVATIVE_HYBRID: AssetClassProfile(
        asset_class=AssetClass.CONSERVATIVE_HYBRID,
        category=AssetCategory.HYBRID,
        expected_annual_return=0.090,
        annual_volatility=0.08,
        min_horizon_years=2.0,
        max_horizon_years=None,
        liquidity_score=0.85,
        lock_in_years=0,
        risk_level=3,
        tax_treatment=TaxTreatment.DEBT_SLAB,  # <65% equity = debt taxation
        deduction_benefit=DeductionBenefit.NONE,
        min_investment=500,
        sip_possible=True,
        description=(
            "75% debt / 25% equity. Stable with mild growth. "
            "Good for conservative users who want slight equity kicker."
        ),
    ),
    AssetClass.AGGRESSIVE_HYBRID: AssetClassProfile(
        asset_class=AssetClass.AGGRESSIVE_HYBRID,
        category=AssetCategory.HYBRID,
        expected_annual_return=0.118,
        annual_volatility=0.155,
        min_horizon_years=3.0,
        max_horizon_years=None,
        liquidity_score=0.85,
        lock_in_years=0,
        risk_level=5,
        tax_treatment=TaxTreatment.EQUITY_LTCG,  # >65% equity = equity taxation
        deduction_benefit=DeductionBenefit.NONE,
        min_investment=500,
        sip_possible=True,
        description=(
            "75% equity / 25% debt. Equity taxation. "
            "Good moderate-risk product."
        ),
    ),
    AssetClass.BALANCED_ADVANTAGE: AssetClassProfile(
        asset_class=AssetClass.BALANCED_ADVANTAGE,
        category=AssetCategory.HYBRID,
        expected_annual_return=0.110,
        annual_volatility=0.120,
        min_horizon_years=3.0,
        max_horizon_years=None,
        liquidity_score=0.85,
        lock_in_years=0,
        risk_level=4,
        tax_treatment=TaxTreatment.EQUITY_LTCG,
        deduction_benefit=DeductionBenefit.NONE,
        min_investment=500,
        sip_possible=True,
        description=(
            "Dynamic asset allocation. Fund manager shifts equity/debt "
            "based on valuations. Good for market-timing-averse investors."
        ),
    ),
    AssetClass.ARBITRAGE_FUND: AssetClassProfile(
        asset_class=AssetClass.ARBITRAGE_FUND,
        category=AssetCategory.HYBRID,
        expected_annual_return=0.068,
        annual_volatility=0.005,
        min_horizon_years=0.25,
        max_horizon_years=None,
        liquidity_score=0.88,
        lock_in_years=0,
        risk_level=2,
        tax_treatment=TaxTreatment.EQUITY_LTCG,  # key advantage
        deduction_benefit=DeductionBenefit.NONE,
        min_investment=500,
        sip_possible=True,
        description=(
            "Near-zero risk but taxed as equity after 1yr holding. "
            "Rolling strategy: invest, hold 12+ months, redeem at LTCG rate. "
            "For 30%+ bracket: beats FDs and most debt funds on after-tax basis. "
            "Ideal for parking 1yr+ money for high bracket investors."
        ),
    ),
    # ── EQUITY ────────────────────────────────────────────────────
    AssetClass.EQUITY_INDEX_LARGECAP: AssetClassProfile(
        asset_class=AssetClass.EQUITY_INDEX_LARGECAP,
        category=AssetCategory.EQUITY,
        expected_annual_return=0.120,
        annual_volatility=0.175,
        min_horizon_years=5.0,
        max_horizon_years=None,
        liquidity_score=0.92,
        lock_in_years=0,
        risk_level=5,
        tax_treatment=TaxTreatment.EQUITY_LTCG,
        deduction_benefit=DeductionBenefit.NONE,
        min_investment=500,
        sip_possible=True,
        description=(
            "Nifty 50 / Sensex index funds. Lowest cost equity exposure. "
            "Recommended as core equity holding for most investors."
        ),
    ),
    AssetClass.EQUITY_LARGE_CAP: AssetClassProfile(
        asset_class=AssetClass.EQUITY_LARGE_CAP,
        category=AssetCategory.EQUITY,
        expected_annual_return=0.122,
        annual_volatility=0.180,
        min_horizon_years=5.0,
        max_horizon_years=None,
        liquidity_score=0.90,
        lock_in_years=0,
        risk_level=5,
        tax_treatment=TaxTreatment.EQUITY_LTCG,
        deduction_benefit=DeductionBenefit.NONE,
        min_investment=500,
        sip_possible=True,
        description=(
            "Actively managed large cap funds. "
            "Prefer index funds unless strong alpha track record."
        ),
    ),
    AssetClass.EQUITY_FLEXI_CAP: AssetClassProfile(
        asset_class=AssetClass.EQUITY_FLEXI_CAP,
        category=AssetCategory.EQUITY,
        expected_annual_return=0.130,
        annual_volatility=0.200,
        min_horizon_years=5.0,
        max_horizon_years=None,
        liquidity_score=0.88,
        lock_in_years=0,
        risk_level=6,
        tax_treatment=TaxTreatment.EQUITY_LTCG,
        deduction_benefit=DeductionBenefit.NONE,
        min_investment=500,
        sip_possible=True,
        description=(
            "Fund manager allocates freely across large/mid/small. "
            "Good single-fund equity exposure."
        ),
    ),
    AssetClass.EQUITY_MID_CAP: AssetClassProfile(
        asset_class=AssetClass.EQUITY_MID_CAP,
        category=AssetCategory.EQUITY,
        expected_annual_return=0.145,
        annual_volatility=0.240,
        min_horizon_years=7.0,
        max_horizon_years=None,
        liquidity_score=0.85,
        lock_in_years=0,
        risk_level=7,
        tax_treatment=TaxTreatment.EQUITY_LTCG,
        deduction_benefit=DeductionBenefit.NONE,
        min_investment=500,
        sip_possible=True,
        description="Mid cap mutual funds. Higher return potential, higher volatility.",
    ),
    AssetClass.EQUITY_SMALL_CAP: AssetClassProfile(
        asset_class=AssetClass.EQUITY_SMALL_CAP,
        category=AssetCategory.EQUITY,
        expected_annual_return=0.160,
        annual_volatility=0.300,
        min_horizon_years=7.0,
        max_horizon_years=None,
        liquidity_score=0.80,
        lock_in_years=0,
        risk_level=8,
        tax_treatment=TaxTreatment.EQUITY_LTCG,
        deduction_benefit=DeductionBenefit.NONE,
        min_investment=500,
        sip_possible=True,
        description=(
            "Small cap funds. High risk, high reward. "
            "Only for long horizon aggressive investors."
        ),
    ),
    AssetClass.EQUITY_DIVIDEND_YIELD: AssetClassProfile(
        asset_class=AssetClass.EQUITY_DIVIDEND_YIELD,
        category=AssetCategory.EQUITY,
        expected_annual_return=0.115,
        annual_volatility=0.145,
        min_horizon_years=5.0,
        max_horizon_years=None,
        liquidity_score=0.88,
        lock_in_years=0,
        risk_level=4,
        tax_treatment=TaxTreatment.EQUITY_LTCG,
        deduction_benefit=DeductionBenefit.NONE,
        min_investment=500,
        sip_possible=True,
        description=(
            "Dividend yield funds. Lower volatility equity. "
            "Good for pre-retirees wanting equity with stability."
        ),
    ),
    AssetClass.EQUITY_SECTORAL: AssetClassProfile(
        asset_class=AssetClass.EQUITY_SECTORAL,
        category=AssetCategory.EQUITY,
        expected_annual_return=0.150,
        annual_volatility=0.280,
        min_horizon_years=7.0,
        max_horizon_years=None,
        liquidity_score=0.80,
        lock_in_years=0,
        risk_level=9,
        tax_treatment=TaxTreatment.EQUITY_LTCG,
        deduction_benefit=DeductionBenefit.NONE,
        min_investment=500,
        sip_possible=True,
        description=(
            "Sectoral / thematic funds. Concentrated risk. "
            "Only for users with strong conviction on a sector."
        ),
    ),
    AssetClass.EQUITY_ELSS: AssetClassProfile(
        asset_class=AssetClass.EQUITY_ELSS,
        category=AssetCategory.EQUITY,
        expected_annual_return=0.128,
        annual_volatility=0.195,
        min_horizon_years=3.0,
        max_horizon_years=None,
        liquidity_score=0.60,
        lock_in_years=3,
        risk_level=6,
        tax_treatment=TaxTreatment.EQUITY_LTCG,
        deduction_benefit=DeductionBenefit.SECTION_80C,
        min_investment=500,
        sip_possible=True,
        description=(
            "Equity Linked Savings Scheme. 80C deduction up to ₹1.5L. "
            "3yr lock-in (shortest among 80C options). "
            "Should be first equity choice if 80C headroom exists."
        ),
    ),
    AssetClass.INTERNATIONAL_FUND: AssetClassProfile(
        asset_class=AssetClass.INTERNATIONAL_FUND,
        category=AssetCategory.EQUITY,
        expected_annual_return=0.110,
        annual_volatility=0.200,
        min_horizon_years=5.0,
        max_horizon_years=None,
        liquidity_score=0.80,
        lock_in_years=0,
        risk_level=6,
        tax_treatment=TaxTreatment.DEBT_SLAB,  # taxed as debt post 2023
        deduction_benefit=DeductionBenefit.NONE,
        min_investment=500,
        sip_possible=True,
        description=(
            "US / global index funds. Currency + market diversification. "
            "Now taxed at slab rate — reduces attractiveness for 30% bracket."
        ),
    ),
    # ── GOLD & COMMODITIES ────────────────────────────────────────
    AssetClass.GOLD_ETF: AssetClassProfile(
        asset_class=AssetClass.GOLD_ETF,
        category=AssetCategory.GOLD_AND_COMMODITIES,
        expected_annual_return=0.090,
        annual_volatility=0.150,
        min_horizon_years=3.0,
        max_horizon_years=None,
        liquidity_score=0.88,
        lock_in_years=0,
        risk_level=4,
        tax_treatment=TaxTreatment.DEBT_SLAB,  # taxed as debt post 2023
        deduction_benefit=DeductionBenefit.NONE,
        min_investment=500,
        sip_possible=True,
        description=(
            "Gold ETFs. Real-time pricing. No making charges. "
            "Taxed at slab rate now. Better than physical gold for purity/storage."
        ),
    ),
    AssetClass.SOVEREIGN_GOLD_BOND: AssetClassProfile(
        asset_class=AssetClass.SOVEREIGN_GOLD_BOND,
        category=AssetCategory.GOLD_AND_COMMODITIES,
        expected_annual_return=0.115,  # gold price + 2.5% interest
        annual_volatility=0.150,
        min_horizon_years=5.0,
        max_horizon_years=8.0,
        liquidity_score=0.40,
        lock_in_years=5,  # early exit from yr 5, full maturity yr 8
        risk_level=4,
        tax_treatment=TaxTreatment.SGB_MATURITY,
        deduction_benefit=DeductionBenefit.NONE,
        min_investment=5000,
        sip_possible=False,
        description=(
            "Sovereign Gold Bonds. RBI issued. 2.5% annual interest. "
            "ZERO capital gains tax at 8yr maturity. "
            "Best gold instrument for long-term holders by a wide margin."
        ),
    ),
    # ── REAL ASSETS ───────────────────────────────────────────────
    AssetClass.REIT: AssetClassProfile(
        asset_class=AssetClass.REIT,
        category=AssetCategory.REAL_ASSETS,
        expected_annual_return=0.105,
        annual_volatility=0.160,
        min_horizon_years=5.0,
        max_horizon_years=None,
        liquidity_score=0.75,
        lock_in_years=0,
        risk_level=5,
        tax_treatment=TaxTreatment.REIT_INVIT,
        deduction_benefit=DeductionBenefit.NONE,
        min_investment=10000,
        sip_possible=False,
        description=(
            "Real Estate Investment Trusts. Regular dividend income + "
            "capital appreciation. Nifty REITs index available. "
            "Good for real estate exposure without buying property."
        ),
    ),
    AssetClass.INVIT: AssetClassProfile(
        asset_class=AssetClass.INVIT,
        category=AssetCategory.REAL_ASSETS,
        expected_annual_return=0.110,
        annual_volatility=0.140,
        min_horizon_years=5.0,
        max_horizon_years=None,
        liquidity_score=0.65,
        lock_in_years=0,
        risk_level=5,
        tax_treatment=TaxTreatment.REIT_INVIT,
        deduction_benefit=DeductionBenefit.NONE,
        min_investment=10000,
        sip_possible=False,
        description=(
            "Infrastructure Investment Trusts. Roads, power, telecom. "
            "High dividend yield. Less liquid than REITs."
        ),
    ),
    # ── TAX ADVANTAGED ────────────────────────────────────────────
    AssetClass.PPF: AssetClassProfile(
        asset_class=AssetClass.PPF,
        category=AssetCategory.TAX_ADVANTAGED,
        expected_annual_return=0.071,
        annual_volatility=0.0,
        min_horizon_years=15.0,
        max_horizon_years=None,
        liquidity_score=0.25,
        lock_in_years=15,
        risk_level=1,
        tax_treatment=TaxTreatment.EEE,
        deduction_benefit=DeductionBenefit.SECTION_80C,
        min_investment=500,
        sip_possible=True,
        description=(
            "Public Provident Fund. EEE status. 80C eligible. "
            "Govt guaranteed. 15yr lock-in with partial withdrawal from yr 7. "
            "Max ₹1.5L/year. Best risk-free long-term instrument."
        ),
    ),
    AssetClass.EPF: AssetClassProfile(
        asset_class=AssetClass.EPF,
        category=AssetCategory.TAX_ADVANTAGED,
        expected_annual_return=0.082,
        annual_volatility=0.0,
        min_horizon_years=0.0,  # technically till retirement but we track it
        max_horizon_years=None,
        liquidity_score=0.15,
        lock_in_years=0,  # withdrawable under conditions
        risk_level=1,
        tax_treatment=TaxTreatment.EEE,
        deduction_benefit=DeductionBenefit.SECTION_80C,
        min_investment=0,
        sip_possible=False,  # employer-driven
        description=(
            "Employee Provident Fund. EEE status. Employer matches. "
            "8.25% current rate. Counted as existing asset, not new investment."
        ),
    ),
    AssetClass.NPS_TIER1: AssetClassProfile(
        asset_class=AssetClass.NPS_TIER1,
        category=AssetCategory.TAX_ADVANTAGED,
        expected_annual_return=0.105,  # blended equity+debt NPS portfolio
        annual_volatility=0.120,
        min_horizon_years=10.0,
        max_horizon_years=None,
        liquidity_score=0.10,
        lock_in_years=0,  # locked till 60
        risk_level=4,
        tax_treatment=TaxTreatment.EET,
        deduction_benefit=DeductionBenefit.BOTH_80C_80CCD,
        min_investment=500,
        sip_possible=True,
        description=(
            "National Pension System Tier 1. Locked till age 60. "
            "80C + additional 80CCD(1B) ₹50K deduction. "
            "60% lump sum tax-free at exit, 40% mandatory annuity. "
            "For 30% bracket: ₹50K extra deduction = ₹15K tax saved annually."
        ),
    ),
    AssetClass.NPS_TIER2: AssetClassProfile(
        asset_class=AssetClass.NPS_TIER2,
        category=AssetCategory.TAX_ADVANTAGED,
        expected_annual_return=0.105,
        annual_volatility=0.120,
        min_horizon_years=0.0,
        max_horizon_years=None,
        liquidity_score=0.80,
        lock_in_years=0,
        risk_level=4,
        tax_treatment=TaxTreatment.DEBT_SLAB,  # no special tax benefit
        deduction_benefit=DeductionBenefit.NONE,
        min_investment=500,
        sip_possible=True,
        description=(
            "NPS Tier 2. No lock-in, no tax benefit. "
            "Liquid NPS with good fund management. "
            "Only useful if you want NPS fund managers without lock-in."
        ),
    ),
}


def effective_return_after_tax(
    profile: AssetClassProfile,
    tax_bracket: float,
    holding_years: float,
    has_80c_headroom: bool = False,
) -> float:
    """Estimate the real after-tax annual return of an asset profile.

    Parameters
    ----------
    profile:
        The asset profile to evaluate.
    tax_bracket:
        User's marginal tax rate as a fraction (0.0, 0.05, ..., 0.30).
    holding_years:
        How long the money will stay invested.
    has_80c_headroom:
        ``True`` if the user hasn't used their full ₹1.5L 80C limit.

    Returns
    -------
    float
        Approximate after-tax annual return.
    """
    r = profile.expected_annual_return

    if profile.tax_treatment == TaxTreatment.EEE:
        return r  # no tax at any stage

    elif profile.tax_treatment == TaxTreatment.EET:
        # NPS: deduction on entry, taxed on exit.
        # Approximate: tax saved upfront amortised over years.
        # 60% lump sum at exit is tax free, 40% annuity taxed.
        annuity_tax_drag = 0.40 * tax_bracket * r
        return r - annuity_tax_drag

    elif profile.tax_treatment == TaxTreatment.EQUITY_LTCG:
        if holding_years >= 1:
            # 10% on gains above 1L — approximation ignores the 1L exemption
            return r * (1 - EQUITY_LTCG_RATE)
        else:
            return r * (1 - 0.15)  # STCG

    elif profile.tax_treatment == TaxTreatment.EQUITY_STCG:
        return r * (1 - 0.15)

    elif profile.tax_treatment == TaxTreatment.DEBT_SLAB:
        return r * (1 - tax_bracket)

    elif profile.tax_treatment == TaxTreatment.SGB_MATURITY:
        if holding_years >= 8:
            # interest taxed at slab, but zero CGT — very efficient
            price_appreciation = r - SGB_INTEREST_RATE
            after_tax_interest = SGB_INTEREST_RATE * (1 - tax_bracket)
            return price_appreciation + after_tax_interest
        else:
            return r * (1 - tax_bracket)

    elif profile.tax_treatment == TaxTreatment.SAVINGS_INTEREST:
        # 80TTA: first 10K interest exempt, rest at slab
        return r * (1 - tax_bracket * 0.7)  # approximate

    else:
        return r * (1 - tax_bracket)


def elss_effective_return(
    profile: AssetClassProfile,
    tax_bracket: float,
    monthly_investment: float,
    has_80c_headroom: bool,
) -> float:
    """Effective return of an ELSS SIP using an IRR calculation.

    Uses IRR because it is the only correct way to model a one-time
    entry benefit (Section 80C deduction) spread over a multi-year
    holding period.
    """
    return elss_irr(
        gross_annual_return=profile.expected_annual_return,
        tax_bracket=tax_bracket,
        monthly_sip=monthly_investment,
        has_80c_headroom=has_80c_headroom,
        years=3.0,
    )

