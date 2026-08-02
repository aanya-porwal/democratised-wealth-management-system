"""Provider bundle — the dependencies injected into every evaluator.

The evaluator depends only on this bundle (an abstraction), never on a
concrete provider. Tests substitute a fake bundle easily.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from security_selection.cache.engine import CacheLayer
from security_selection.config import SecuritySelectionConfig, get_config
from security_selection.providers.base import BaseDataProvider
from security_selection.providers.fallback_provider import FallbackProvider


@dataclass
class BaseProviderSet:
    """Everything a evaluator may need from the outside world.

    Attributes
    ----------
    data:
        The data provider (typically a :class:`FallbackProvider` chain).
    cache:
        The provider-independent cache layer.
    config:
        The typed platform configuration.
    """

    data: BaseDataProvider
    cache: CacheLayer = field(default_factory=CacheLayer)
    config: SecuritySelectionConfig = field(default_factory=get_config)

    def with_data(self, provider: BaseDataProvider) -> "BaseProviderSet":
        """Return a copy with a different data provider (test helper)."""
        return BaseProviderSet(data=provider, cache=self.cache, config=self.config)

