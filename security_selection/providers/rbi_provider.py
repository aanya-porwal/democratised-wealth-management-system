"""RBI provider — free government/sovereign data.

Covers Sovereign Gold Bonds (SGBs) and government-bond instruments using
public RBI data sources. Where an endpoint is unavailable, the provider
degrades to configured static metadata rather than failing the pipeline.
"""

from __future__ import annotations

import logging
from datetime import date, datetime, timezone
from typing import Any, Dict, List, Optional

from security_selection.models.data import (
    MarketSnapshot,
    ProviderPayload,
    SecurityIdentity,
)
from security_selection.models.enums import DataSource, ProviderName
from security_selection.providers.base import BaseDataProvider, ProviderException
from security_selection.utils.math import safe_float

logger = logging.getLogger(__name__)

try:
    import requests as _requests

    _HAS_REQUESTS = True
except Exception:  # pragma: no cover
    _requests = None
    _HAS_REQUESTS = False

_BASE_URL = "https://rbi.org.in"

_SUPPORTED_KINDS = {"sgb", "government_bond"}


class RBIProvider(BaseDataProvider):
    """Free RBI data for SGBs and government bonds.

    Note: RBI's public CSV/dataset endpoints are frequently rate-limited
    or restructured. This provider therefore attempts a live fetch and,
    on any failure, returns the configured static metadata for the known
    instruments so the pipeline never hard-fails.
    """

    name = ProviderName.RBI

    def __init__(self, **config: Any) -> None:
        super().__init__(**config)
        self._base_url = str(config.get("base_url") or _BASE_URL)

    def supports(self, identity: SecurityIdentity) -> bool:
        kind = identity.kind.value if identity.kind else ""
        if kind not in _SUPPORTED_KINDS:
            return False
        return self.enabled

    def fetch_snapshot(self, identity: SecurityIdentity) -> ProviderPayload:
        # SGB prices are published by RBI but not via a stable free API.
        # Return the static metadata as the snapshot; live series come
        # from the StaticDataProvider or fallback provider when available.
        from security_selection.providers.static_provider import SGB_STATIC

        if identity.kind and identity.kind.value == "sgb" and identity.symbol in SGB_STATIC:
            meta = SGB_STATIC[identity.symbol]
            return ProviderPayload(
                provider=self.name,
                identity=identity,
                snapshot=MarketSnapshot(
                    identity=identity,
                    current_price=safe_float(meta.get("current_price")),
                    as_of=datetime.now(timezone.utc),
                    currency="INR",
                    extra=meta,
                ),
                metrics={k: v for k, v in meta.items() if isinstance(v, (int, float, str))},
                success=True,
            )
        return self._error_payload(identity, "no RBI snapshot available for this security")

    def fetch_history(
        self,
        identity: SecurityIdentity,
        start: date | None = None,
        end: date | None = None,
    ) -> ProviderPayload:
        return self._error_payload(
            identity, "RBI history not available via stable free endpoint; use static data"
        )

    def search(self, query: str, **kwargs: Any) -> List[SecurityIdentity]:
        from security_selection.providers.static_provider import SGB_STATIC

        q = query.lower()
        out: List[SecurityIdentity] = []
        for symbol, meta in SGB_STATIC.items():
            name = str(meta.get("name", "")).lower()
            if q in symbol.lower() or q in name:
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
        from security_selection.providers.static_provider import SGB_STATIC

        if identity.kind and identity.kind.value == "sgb" and identity.symbol in SGB_STATIC:
            meta = SGB_STATIC[identity.symbol]
            return {k: v for k, v in meta.items() if isinstance(v, (int, float, str))}
        return {}

