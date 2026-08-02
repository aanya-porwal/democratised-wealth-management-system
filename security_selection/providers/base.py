"""Base data provider interface.

Every data source — free or premium — implements this interface.
Evaluators depend only on this abstraction, so premium providers
(Refinitiv, Bloomberg, Morningstar, etc.) can be added later without
touching the evaluators or the core engine.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from datetime import date, timedelta
from typing import Any, Dict, List, Optional

from security_selection.models.data import ProviderPayload, SecurityIdentity
from security_selection.models.enums import ProviderName

logger = logging.getLogger(__name__)


class ProviderException(Exception):
    """Raised when a provider cannot fulfil a request."""


class BaseDataProvider(ABC):
    """Abstract interface all data providers implement.

    Implementations are stateless beyond configuration; caching happens
    in the :class:`CacheLayer`, never inside a provider.
    """

    name: ProviderName = ProviderName.STATIC

    def __init__(self, **config: Any) -> None:
        self._config = config
        self._enabled = bool(config.get("enabled", True))

    @property
    def enabled(self) -> bool:
        return self._enabled

    # ── required hooks ──────────────────────────────────────────────

    @abstractmethod
    def supports(self, identity: SecurityIdentity) -> bool:
        """Whether this provider can serve the given security."""

    @abstractmethod
    def fetch_snapshot(self, identity: SecurityIdentity) -> ProviderPayload:
        """Fetch the latest price/NAV snapshot for a security."""

    @abstractmethod
    def fetch_history(
        self,
        identity: SecurityIdentity,
        start: date | None = None,
        end: date | None = None,
    ) -> ProviderPayload:
        """Fetch historical price/NAV series (inclusive)."""

    @abstractmethod
    def search(self, query: str, **kwargs: Any) -> List[SecurityIdentity]:
        """Search for securities by name/symbol query."""

    # ── optional hooks (override in subclasses) ─────────────────────

    def fetch_metrics(self, identity: SecurityIdentity) -> Dict[str, Any]:
        """Fetch structured metrics (expense ratio, AUM, yield, ...)."""
        return {}

    def fetch_holdings(self, identity: SecurityIdentity) -> List[Dict[str, Any]]:
        """Fetch fund/ETF top holdings."""
        return []

    def fetch_sector_allocations(self, identity: SecurityIdentity) -> Dict[str, float]:
        """Fetch sector breakdown."""
        return {}

    def fetch_country_allocations(self, identity: SecurityIdentity) -> Dict[str, float]:
        """Fetch country breakdown (for international funds)."""
        return {}

    # ── helpers ─────────────────────────────────────────────────────

    @staticmethod
    def default_start() -> date:
        """Default history start: 10 years ago."""
        return date.today() - timedelta(days=365 * 10)

    def _error_payload(
        self, identity: SecurityIdentity, error: str
    ) -> ProviderPayload:
        return ProviderPayload(
            provider=self.name,
            identity=identity,
            success=False,
            error=error,
        )

