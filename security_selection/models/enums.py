"""Enums for the Security Selection platform."""

from __future__ import annotations

from enum import Enum


class TargetAssetClass(str, Enum):
    """The strategic asset classes that flow out of the allocation engine.

    Each maps to one or more concrete evaluators. The core engine only
    ever works with these high-level buckets — it never knows how an ETF
    or a bond is implemented.
    """

    LARGE_CAP_EQUITY = "large_cap_equity"
    MID_CAP_EQUITY = "mid_cap_equity"
    SMALL_CAP_EQUITY = "small_cap_equity"
    FLEXI_CAP_EQUITY = "flexi_cap_equity"
    ELSS_EQUITY = "elss_equity"
    INTERNATIONAL_EQUITY = "international_equity"
    DEBT = "debt"
    CORPORATE_BONDS = "corporate_bonds"
    GOVERNMENT_BONDS = "government_bonds"
    GOLD = "gold"
    GOLD_ETF = "gold_etf"
    SGB = "sgb"
    REIT = "reit"
    INVIT = "invit"
    FIXED_DEPOSIT = "fixed_deposit"
    PPF = "ppf"
    NPS = "nps"
    STOCKS = "stocks"


class SecurityKind(str, Enum):
    """The concrete instrument kind produced by an evaluator."""

    MUTUAL_FUND = "mutual_fund"
    ETF = "etf"
    STOCK = "stock"
    CORPORATE_BOND = "corporate_bond"
    GOVERNMENT_BOND = "government_bond"
    GOLD_ETF = "gold_etf"
    SGB = "sgb"
    REIT = "reit"
    INVIT = "invit"
    FIXED_DEPOSIT = "fixed_deposit"
    PPF = "ppf"
    NPS = "nps"
    INTERNATIONAL_ETF = "international_etf"
    INTERNATIONAL_FUND = "international_fund"


class AssetClassBucket(str, Enum):
    """Broad allocation bucket a security belongs to (for reporting)."""

    EQUITY = "equity"
    DEBT = "debt"
    GOLD = "gold"
    INTERNATIONAL_EQUITY = "international_equity"
    REAL_ASSETS = "real_assets"
    FIXED_DEPOSITS = "fixed_deposits"
    TAX_ADVANTAGED = "tax_advantaged"
    CASH = "cash"


class ProviderName(str, Enum):
    """Identifiers for data providers."""

    YFINANCE = "yfinance"
    MFAPI = "mfapi"
    RBI = "rbi"
    STATIC = "static"
    CACHE = "cache"
    MOCK = "mock"


class DataSource(str, Enum):
    """Where a piece of data came from (for the research report)."""

    LIVE = "live"
    CACHE = "cache"
    STATIC = "static"
    DERIVED = "derived"
    UNAVAILABLE = "unavailable"


class Confidence(str, Enum):
    """Confidence levels for recommendations."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class RecommendationAction(str, Enum):
    """The suggested investment action."""

    INVEST = "invest"
    HOLD = "hold"
    AVOID = "avoid"
    WATCH = "watch"


class NormalizationAxis(str, Enum):
    """The common normalized interface every evaluator outputs.

    Each axis is a 0..1 score with an associated confidence and
    availability flag, enabling cross-asset-class comparisons.
    """

    EXPECTED_RETURN = "expected_return"
    RISK = "risk"
    LIQUIDITY = "liquidity"
    DIVERSIFICATION = "diversification"
    TAX_EFFICIENCY = "tax_efficiency"
    COST = "cost"
    TRACKING_QUALITY = "tracking_quality"
    QUALITY = "quality"
    MARKET_EXPOSURE = "market_exposure"


class FilterOperator(str, Enum):
    """Operators supported by configurable filters."""

    GE = "ge"  # >=
    LE = "le"  # <=
    EQ = "eq"
    IN = "in"
    CONTAINS = "contains"


class Region(str, Enum):
    """Market region."""

    INDIA = "india"
    US = "us"
    GLOBAL = "global"
    INTERNATIONAL = "international"


class TaxStatus(str, Enum):
    """Indian tax treatment of the security."""

    EEE = "eee"
    EET = "eet"
    EQUITY_LTCG = "equity_ltcg"
    DEBT_SLAB = "debt_slab"
    SGB_MATURITY = "sgb_maturity"
    REIT_INVIT = "reit_invit"
    NONE = "none"


class CreditRating(str, Enum):
    """Credit rating scale used for debt securities."""

    AAA = "AAA"
    AA = "AA"
    A = "A"
    BBB = "BBB"
    BB = "BB"
    B = "B"
    CCC = "CCC"
    UNRATED = "unrated"


class TimeFrame(str, Enum):
    """Time horizons used in return/risk computations."""

    _1M = "1m"
    _3M = "3m"
    _6M = "6m"
    _1Y = "1y"
    _3Y = "3y"
    _5Y = "5y"
    _10Y = "10y"
    INCEPTION = "inception"

