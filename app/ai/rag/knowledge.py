"""Knowledge corpus — educational content for RAG.

Contains curated financial education content covering SEBI regulations,
RBI policies, Income Tax, mutual fund concepts, and general financial
planning. The AI never calculates — it retrieves and explains.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class KnowledgeDocument:
    """A single document in the knowledge corpus."""

    title: str
    content: str
    source: str = "manual"
    category: str = "education"
    metadata: dict = field(default_factory=dict)


class KnowledgeCorpus:
    """The curated knowledge corpus.

    Documents are grouped by category and returned as flat lists for
    embedding and indexing. The corpus is static (defined in code) so it
    works with zero setup. Users can add documents via the API.
    """

    # ── SEBI / Regulatory ──────────────────────────────────────────

    SEBI_DISCLAIMER = KnowledgeDocument(
        title="SEBI Registration and Disclaimer",
        category="sebi",
        source="sebi",
        content=(
            "SEBI (Securities and Exchange Board of India) is the regulatory "
            "body for the securities market in India. All investment advisers "
            "must be registered with SEBI. This AI system is a financial "
            "education and planning tool, NOT a SEBI-registered investment "
            "adviser. It does not provide personalised investment advice, "
            "stock recommendations, or portfolio management services. "
            "Always consult a SEBI-registered investment adviser before "
            "making any investment decision."
        ),
    )

    SEBI_MUTUAL_FUND_RULES = KnowledgeDocument(
        title="SEBI Mutual Fund Regulations",
        category="sebi",
        source="sebi",
        content=(
            "SEBI regulates mutual funds through the SEBI (Mutual Funds) "
            "Regulations, 1996. Key requirements: (1) All mutual funds must "
            "be registered with SEBI. (2) Each scheme must have a Scheme "
            "Information Document (SID) and a Statement of Additional "
            "Information (SAI). (3) Asset Management Companies (AMCs) must "
            "maintain a minimum net worth of Rs. 50 crore. (4) Total Expense "
            "Ratio (TER) is capped at 2.25% for equity funds and 2.00% for "
            "debt funds. (5) Mutual funds must disclose their portfolio "
            "monthly. (6) Exit load cannot exceed 1% of redemption value."
        ),
    )

    # ── RBI / Fixed Income ─────────────────────────────────────────

    RBI_PPF_RULES = KnowledgeDocument(
        title="Public Provident Fund (PPF) Rules",
        category="rbi",
        source="rbi",
        content=(
            "The Public Provident Fund (PPF) is a government-backed savings "
            "scheme under the Public Provident Fund Act, 1968. Key features: "
            "(1) Minimum annual deposit: Rs. 500. Maximum: Rs. 1.5 lakh. "
            "(2) Lock-in period: 15 years (extendable in blocks of 5 years). "
            "(3) Interest rate is set quarterly by the government (currently "
            "around 7.1% p.a., compounded annually). (4) Deposits qualify "
            "for tax deduction under Section 80C. (5) Interest earned and "
            "maturity amount are tax-free (EEE status). (6) Partial "
            "withdrawals allowed from the 7th financial year. (7) Loans "
            "available from the 3rd to the 6th year."
        ),
    )

    RBI_NPS_RULES = KnowledgeDocument(
        title="National Pension System (NPS) Rules",
        category="rbi",
        source="rbi",
        content=(
            "The National Pension System (NPS) is a government-sponsored "
            "retirement savings scheme regulated by PFRDA. Key features: "
            "(1) Any Indian citizen aged 18-70 can open an NPS account. "
            "(2) Tier I account: mandatory, minimum contribution Rs. 500 "
            "per year. (3) Tier II account: voluntary savings, no lock-in. "
            "(4) Tax benefits: Section 80CCD(1) up to Rs. 1.5 lakh, "
            "Section 80CCD(1B) additional Rs. 50,000. (5) Employer "
            "contributions under Section 80CCD(2) up to 14% of salary "
            "(central government) or 10% (others). (6) At maturity (60 years), "
            "60% can be withdrawn tax-free; 40% must buy an annuity. "
            "(7) Partial withdrawals allowed after 10 years for specified "
            "purposes."
        ),
    )

    # ── Income Tax ─────────────────────────────────────────────────

    TAX_SECTION_80C = KnowledgeDocument(
        title="Income Tax Section 80C Deductions",
        category="tax",
        source="income_tax",
        content=(
            "Section 80C of the Income Tax Act allows deductions up to "
            "Rs. 1.5 lakh per financial year. Eligible investments include: "
            "(1) Employee Provident Fund (EPF). (2) Public Provident Fund "
            "(PPF). (3) Equity-Linked Savings Scheme (ELSS) — 3-year "
            "lock-in. (4) National Savings Certificate (NSC) — 5-year lock-in. "
            "(5) Tax-saving Fixed Deposits (5-year lock-in). (6) Life "
            "Insurance Premiums. (7) Tuition fees for children. (8) "
            "Principal repayment on home loan. (9) Senior Citizens Savings "
            "Scheme. (10) Sukanya Samriddhi Yojana."
        ),
    )

    TAX_CAPITAL_GAINS = KnowledgeDocument(
        title="Capital Gains Tax on Investments",
        category="tax",
        source="income_tax",
        content=(
            "Capital gains tax in India: (1) Equity mutual funds/listed "
            "shares: LTCG (>1 year) at 10% over Rs. 1 lakh; STCG at 15%. "
            "(2) Debt mutual funds: LTCG (>3 years) at 20% with indexation; "
            "STCG at slab rate. (3) Real estate: LTCG (>2 years) at 20% "
            "with indexation; STCG at slab rate. (4) Gold: LTCG (>3 years) "
            "at 20% with indexation; STCG at slab rate. (5) Sovereign Gold "
            "Bonds: LTCG at 20% with indexation if held till maturity (8 "
            "years) — tax-free if held to maturity. Indexation adjusts the "
            "purchase price for inflation using the Cost Inflation Index (CII)."
        ),
    )

    # ── Mutual Fund Education ──────────────────────────────────────

    MF_EXPENSE_RATIO = KnowledgeDocument(
        title="Understanding Mutual Fund Expense Ratios",
        category="mutual_fund",
        source="education",
        content=(
            "The Expense Ratio is the annual fee charged by a mutual fund "
            "to manage your investment. It is expressed as a percentage of "
            "the fund's average assets under management (AUM). SEBI limits "
            "expense ratios: (1) Equity funds: up to 2.25% of AUM. "
            "(2) Debt funds: up to 2.00% of AUM. (3) Index funds/ETFs: "
            "typically 0.10% to 1.00%. A higher expense ratio directly "
            "reduces your returns. For example, a 1% expense ratio on a "
            "Rs. 10 lakh investment over 20 years costs approximately "
            "Rs. 3.5 lakh in lost compounding. Always compare expense "
            "ratios when choosing between similar funds. Direct plans "
            "have lower expense ratios than regular plans."
        ),
    )

    MF_SIP_VS_LUMPSUM = KnowledgeDocument(
        title="SIP vs Lump Sum Investing",
        category="mutual_fund",
        source="education",
        content=(
            "Systematic Investment Plan (SIP) and Lump Sum are two ways "
            "to invest in mutual funds. SIP: Invest a fixed amount "
            "regularly (monthly/quarterly). Benefits rupee cost averaging — "
            "you buy more units when prices are low and fewer when prices "
            "are high. Reduces the impact of market timing. Requires "
            "discipline but is suitable for salaried investors. Lump Sum: "
            "Invest a large amount at once. Works best when the market is "
            "undervalued or when you have a large windfall. Requires good "
            "market timing. For most retail investors, a combination of "
            "SIP for regular income and lump sum for bonuses works best. "
            "Historically, lump sum outperforms SIP in rising markets, "
            "while SIP reduces risk in volatile markets."
        ),
    )

    MF_ACTIVE_VS_PASSIVE = KnowledgeDocument(
        title="Active vs Passive Mutual Funds",
        category="mutual_fund",
        source="education",
        content=(
            "Active funds: Fund managers actively select stocks to beat a "
            "benchmark index. Higher expense ratios (1.0% to 2.25%). "
            "Potential to outperform, but most active funds fail to beat "
            "their benchmark over long periods. Passive funds (Index "
            "funds/ETFs): Track a market index (Nifty 50, Sensex, etc.). "
            "Lower expense ratios (0.10% to 1.0%). Guaranteed to match "
            "market returns (minus fees). Lower risk of underperformance. "
            "For retail investors, a core portfolio of passive funds with "
            "selective active funds in less efficient categories (mid-cap, "
            "small-cap) is a common strategy."
        ),
    )

    # ── Financial Planning ─────────────────────────────────────────

    EMERGENCY_FUND = KnowledgeDocument(
        title="Emergency Fund Guidelines",
        category="financial_planning",
        source="education",
        content=(
            "An emergency fund is money set aside for unexpected expenses "
            "(job loss, medical emergency, urgent home repair). Guideline: "
            "3 to 6 months of essential expenses. For single-income "
            "households or irregular income, 6 to 12 months. Where to keep: "
            "Savings account (immediate access), liquid funds, or sweep "
            "fixed deposits. The emergency fund should be kept separate "
            "from your regular account. It should not be invested in "
            "equity or long-term instruments. The goal is preservation and "
            "liquidity, not growth."
        ),
    )

    RETIREMENT_PLANNING = KnowledgeDocument(
        title="Retirement Planning Basics",
        category="financial_planning",
        source="education",
        content=(
            "Retirement planning ensures you have enough money to maintain "
            "your lifestyle after you stop working. Key steps: (1) Estimate "
            "your retirement corpus — typically 25-30 times your annual "
            "expenses. (2) Factor in inflation (6% average). (3) Use the "
            "4% rule: you can withdraw 4% of your corpus annually without "
            "running out of money for 30 years. (4) Start early — the "
            "power of compounding means Rs. 5,000/month invested from age "
            "25 grows to Rs. 2.5 crore by 60 (assuming 12% returns). "
            "(5) Diversify across asset classes: equity for growth, debt "
            "for stability, gold for hedge. (6) Review and rebalance "
            "annually."
        ),
    )

    # ── Risk Management ────────────────────────────────────────────

    RISK_PROFILING = KnowledgeDocument(
        title="Understanding Investment Risk Profiles",
        category="risk_management",
        source="education",
        content=(
            "Risk profiling categorises an investor's ability and "
            "willingness to take investment risk. The five common profiles: "
            "(1) Very Conservative: Prefer capital preservation over growth. "
            "Allocate 80-100% to debt. (2) Conservative: Accept small "
            "fluctuations for slightly higher returns. Allocate 60-80% "
            "debt, 20-40% equity. (3) Moderate: Balanced approach. "
            "Allocate 40-60% equity, 40-60% debt. (4) Aggressive: "
            "Comfortable with significant short-term volatility for higher "
            "long-term returns. Allocate 60-80% equity, 20-40% debt. "
            "(5) Very Aggressive: Seeks maximum returns, accepts high "
            "volatility. Allocate 80-100% equity. Risk capacity depends "
            "on age, income stability, dependents, and net worth."
        ),
    )

    # ── All categories ─────────────────────────────────────────────

    _ALL_DOCUMENTS: list[KnowledgeDocument] = [
        SEBI_DISCLAIMER,
        SEBI_MUTUAL_FUND_RULES,
        RBI_PPF_RULES,
        RBI_NPS_RULES,
        TAX_SECTION_80C,
        TAX_CAPITAL_GAINS,
        MF_EXPENSE_RATIO,
        MF_SIP_VS_LUMPSUM,
        MF_ACTIVE_VS_PASSIVE,
        EMERGENCY_FUND,
        RETIREMENT_PLANNING,
        RISK_PROFILING,
    ]

    @classmethod
    def documents(cls) -> list[KnowledgeDocument]:
        """Return all documents in the corpus."""
        return list(cls._ALL_DOCUMENTS)

    @classmethod
    def by_category(cls, category: str) -> list[KnowledgeDocument]:
        """Return documents filtered by category."""
        return [d for d in cls._ALL_DOCUMENTS if d.category == category]

    @classmethod
    def categories(cls) -> list[str]:
        """Return the list of unique categories."""
        return list({d.category for d in cls._ALL_DOCUMENTS})

    @classmethod
    def count(cls) -> int:
        return len(cls._ALL_DOCUMENTS)
