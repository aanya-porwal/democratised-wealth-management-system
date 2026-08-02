"""Provider factory — builds providers from configuration.

Keeps provider instantiation in one place so evaluators and services
receive an already-wired provider chain. Tests can replace the chain with
mocks by passing providers explicitly.
"""

from __future__ import annotations

from typing import Any, List, Optional

from security_selection.cache.engine import CacheLayer
from security_selection.config import ProviderConfig, get_config
from security_selection.providers.base import BaseDataProvider
from security_selection.providers.fallback_provider import FallbackProvider
from security_selection.providers.mfapi_provider import MFAPIProvider
from security_selection.providers.rbi_provider import RBIProvider
from security_selection.providers.static_provider import StaticDataProvider
from security_selection.providers.yfinance_provider import YFinanceProvider


def _provider_classes() -> dict[str, type[BaseDataProvider]]:
    return {
        "yfinance": YFinanceProvider,
        "mfapi": MFAPIProvider,
        "rbi": RBIProvider,
        "static": StaticDataProvider,
    }


def build_provider(name: str, config: Optional[ProviderConfig] = None) -> BaseDataProvider:
    """Build one provider by name using the process config."""
    cfg = config or get_config().providers
    classes = _provider_classes()
    if name not in classes:
        raise ValueError(f"unknown provider: {name}")
    provider_cfg = getattr(cfg, name, None)
    settings: dict[str, Any] = {}
    if provider_cfg is not None:
        settings = {
            "enabled": provider_cfg.enabled,
            "timeout_seconds": provider_cfg.timeout_seconds or cfg.timeout_seconds,
            "retries": provider_cfg.retries or cfg.retries,
            "base_url": provider_cfg.base_url,
            "max_history_years": provider_cfg.max_history_years,
        }
    return classes[name](**settings)


def build_fallback_provider(
    config: Optional[ProviderConfig] = None,
    cache: Optional[CacheLayer] = None,
    providers: Optional[List[BaseDataProvider]] = None,
) -> FallbackProvider:
    """Build the default fallback provider chain from configuration.

    ``providers`` may be supplied to override the chain (used by tests).
    """
    cfg = config or get_config().providers
    if providers is None:
        providers = [build_provider(name, cfg) for name in cfg.order]
    return FallbackProvider(providers=providers, cache=cache, config=cfg)

