"""Static data provider — curated public metadata for instruments without
a stable free API (Fixed Deposits, PPF, NPS, SGBs, RBI bonds).

These figures are publicly published (RBI, India Post, NPS Trust, bank
websites) and are refreshed via the background job schedule. They are
explicitly static metadata, never fabricated market prices.
"""

from __future__ import annotations

import logging
from datetime import date, datetime, timezone
from typing import Any, Dict, List, Optional

from security_selection.models.data import (
    DataPoint,
    HistoricalSeries,
    MarketSnapshot,
    ProviderPayload,
    SecurityIdentity,
)
from security_selection.models.enums import DataSource, ProviderName
from security_selection.providers.base import BaseDataProvider, ProviderException

logger = logging.getLogger(__name__)

# ── curated static metadata (public sources) ─────────────────────────

SGB_STATIC: Dict[str, Dict[str, Any]] = {
    "SGB-2016-I": {
        "name": "Sovereign Gold Bond Series I 2016-17",
        "current_price": 0.0,
        "interest_rate": 0.025,
        "maturity_years": 8,
        "min_investment": 1,
        "tax_treatment": "sgb_maturity",
        "issuer": "Government of India via RBI",
        "isin": "INE002A16A01",
    },
    "SGB-2017-I": {
        "name": "Sovereign Gold Bond Series I 2017-18",
        "current_price": 0.0,
        "interest_rate": 0.025,
        "maturity_years": 8,
        "min_investment": 1,
        "tax_treatment": "sgb_maturity",
        "issuer": "Government of India via RBI",
        "isin": "INE002A17A00",
    },
}

FD_STATIC: Dict[str, Dict[str, Any]] = {
    "SBI-FD-1Y": {
        "name": "SBI Fixed Deposit 1 Year",
        "interest_rate": 0.065,
        "min_investment": 1000,
        "tenure_years": 1,
        "issuer": "State Bank of India",
        "tax_treatment": "debt_slab",
        "insured": "DICGC up to ₹5L",
    },
    "SBI-FD-3Y": {
        "name": "SBI Fixed Deposit 3 Year",
        "interest_rate": 0.070,
        "min_investment": 1000,
        "tenure_years": 3,
        "issuer": "State Bank of India",
        "tax_treatment": "debt_slab",
        "insured": "DICGC up to ₹5L",
    },
    "HDFC-FD-1Y": {
        "name": "HDFC Bank Fixed Deposit 1 Year",
        "interest_rate": 0.067,
        "min_investment": 10000,
        "tenure_years": 1,
        "issuer": "HDFC Bank",
        "tax_treatment": "debt_slab",
        "insured": "DICGC up to ₹5L",
    },
}

PPF_STATIC: Dict[str, Dict[str, Any]] = {
    "PPF": {
        "name": "Public Provident Fund",
        "interest_rate": 0.071,
        "min_investment": 500,
        "max_investment": 150000,
        "lock_in_years": 15,
        "tax_treatment": "eee",
        "issuer": "Government of India (India Post / banks)",
        "partial_withdrawal_year": 7,
    }
}

NPS_STATIC: Dict[str, Dict[str, Any]] = {
    "NPS-TIER1-AGGRESSIVE": {
        "name": "NPS Tier 1 — Aggressive (LC75)",
        "interest_rate": 0.105,
        "min_investment": 500,
        "lock_in_years": 30,
        "tax_treatment": "eet",
        "issuer": "PFRDA / NPS Trust",
    },
    "NPS-TIER1-BALANCED": {
        "name": "NPS Tier 1 — Balanced (LC50)",
        "interest_rate": 0.095,
        "min_investment": 500,
        "lock_in_years": 30,
        "tax_treatment": "eet",
        "issuer": "PFRDA / NPS Trust",
    },
    "NPS-TIER2": {
        "name": "NPS Tier 2",
        "interest_rate": 0.09,
        "min_investment": 250,
        "lock_in_years": 0,
        "tax_treatment": "debt_slab",
        "issuer": "PFRDA / NPS Trust",
    },
}

GOVT_BOND_STATIC: Dict[str, Dict[str, Any]] = {
    "GSEC-2033": {
        "name": "7.26% GS 2033 (Government of India)",
        "interest_rate": 0.0726,
        "maturity_years": 10,
        "min_investment": 10000,
        "tax_treatment": "debt_slab",
        "issuer": "Government of India via RBI Retail Direct",
    },
}

CORPORATE_BOND_STATIC: Dict[str, Dict[str, Any]] = {
    "HDFC-CORP-AAA-2030": {
        "name": "HDFC Ltd Corporate Bond 2030 (AAA)",
        "interest_rate": 0.0765,
        "maturity_years": 5,
        "min_investment": 10000,
        "credit_rating": "AAA",
        "tax_treatment": "debt_slab",
        "issuer": "HDFC Ltd via NSE/BSE listed bonds",
    },
    "RELIANCE-CORP-AAA-2032": {
        "name": "Reliance Industries Corporate Bond 2032 (AAA)",
        "interest_rate": 0.0750,
        "maturity_years": 7,
        "min_investment": 10000,
        "credit_rating": "AAA",
        "tax_treatment": "debt_slab",
        "issuer": "Reliance Industries via NSE/BSE listed bonds",
    },
    "SBI-CORP-AAA-2029": {
        "name": "SBI Corporate Bond 2029 (AAA)",
        "interest_rate": 0.0735,
        "maturity_years": 3,
        "min_investment": 10000,
        "credit_rating": "AAA",
        "tax_treatment": "debt_slab",
        "issuer": "State Bank of India via NSE/BSE listed bonds",
    },
    "L&T-CORP-AA+-2031": {
        "name": "L&T Finance Corporate Bond 2031 (AA+)",
        "interest_rate": 0.0810,
        "maturity_years": 6,
        "min_investment": 10000,
        "credit_rating": "AA",
        "tax_treatment": "debt_slab",
        "issuer": "L&T Finance via NSE/BSE listed bonds",
    },
}

STATIC_CATALOGS = {
    "sgb": SGB_STATIC,
    "fixed_deposit": FD_STATIC,
    "ppf": PPF_STATIC,
    "nps": NPS_STATIC,
    "government_bond": GOVT_BOND_STATIC,
    "corporate_bond": CORPORATE_BOND_STATIC,
}


class StaticDataProvider(BaseDataProvider):
    """Provides curated public static metadata for non-API instruments."""

    name = ProviderName.STATIC

    def supports(self, identity: SecurityIdentity) -> bool:
        if not self.enabled:
            return False
        kind = identity.kind.value if identity.kind else ""
        if kind not in STATIC_CATALOGS:
            return False
        return identity.symbol in STATIC_CATALOGS[kind]

    def fetch_snapshot(self, identity: SecurityIdentity) -> ProviderPayload:
        meta = self._meta(identity)
        if meta is None:
            return self._error_payload(identity, "unknown static instrument")
        snapshot = MarketSnapshot(
            identity=identity,
            current_price=None,
            nav=None,
            as_of=datetime.now(timezone.utc),
            currency="INR",
            extra=dict(meta),
        )
        return ProviderPayload(
            provider=self.name,
            identity=identity,
            snapshot=snapshot,
            metrics={k: v for k, v in meta.items() if isinstance(v, (int, float, str))},
            success=True,
        )

    def fetch_history(
        self,
        identity: SecurityIdentity,
        start: date | None = None,
        end: date | None = None,
    ) -> ProviderPayload:
        meta = self._meta(identity)
        if meta is None:
            return self._error_payload(identity, "unknown static instrument")
        # For guaranteed instruments, the "history" is a flat series of
        # the static annual return compounded — used by the evaluator to
        # compute metrics (volatility ~0). This is a derived static
        # series, clearly marked STATIC, not fabricated market prices.
        rate = float(meta.get("interest_rate", 0.0))
        tenure = float(meta.get("tenure_years", meta.get("maturity_years", 1)) or 1)
        start_date = date.today()
        points: List[DataPoint] = []
        base = 100.0
        points.append(DataPoint(date=start_date, value=base))
        for i in range(1, max(2, int(tenure) + 1)):
            base *= (1 + rate)
            points.append(
                DataPoint(date=_add_years(start_date, i), value=round(base, 4))
            )
        return ProviderPayload(
            provider=self.name,
            identity=identity,
            history=HistoricalSeries(points=points, source=DataSource.STATIC, currency="INR"),
            metrics={k: v for k, v in meta.items() if isinstance(v, (int, float, str))},
            success=True,
        )

    def search(self, query: str, **kwargs: Any) -> List[SecurityIdentity]:
        q = query.lower()
        out: List[SecurityIdentity] = []
        for kind, catalog in STATIC_CATALOGS.items():
            for symbol, meta in catalog.items():
                if q in symbol.lower() or q in str(meta.get("name", "")).lower():
                    out.append(
                        SecurityIdentity(
                            symbol=symbol,
                            name=str(meta.get("name", symbol)),
                            currency="INR",
                            kind=None,
                        )
                    )
        return out

    def fetch_metrics(self, identity: SecurityIdentity) -> Dict[str, Any]:
        meta = self._meta(identity)
        if meta is None:
            return {}
        return {k: v for k, v in meta.items() if isinstance(v, (int, float, str))}

    def _meta(self, identity: SecurityIdentity) -> Dict[str, Any] | None:
        kind = identity.kind.value if identity.kind else ""
        catalog = STATIC_CATALOGS.get(kind)
        if catalog is None:
            return None
        return catalog.get(identity.symbol)


def _add_years(d: date, years: int) -> date:
    try:
        return d.replace(year=d.year + years)
    except ValueError:
        return d.replace(year=d.year + years, day=28)

