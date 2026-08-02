"""Data providers for the Security Selection platform.

Providers are injected into evaluators so the core engine never depends
on a specific vendor. The default set uses only free public sources:

* ``yfinance`` — stocks, ETFs, gold ETFs, REITs, InvITs, international
* ``mfapi`` — Indian mutual fund schemes + NAV (api.mfapi.in)
* ``rbi`` — SGB / government-bond datasets
* ``static`` — FD / PPF / NPS / SGB static rate tables
* ``fallback`` — ordered chain with cache fallback
* ``factory`` — build providers from configuration
"""

from security_selection.providers.base import BaseDataProvider, ProviderException
from security_selection.providers.yfinance_provider import YFinanceProvider
from security_selection.providers.mfapi_provider import MFAPIProvider
from security_selection.providers.rbi_provider import RBIProvider
from security_selection.providers.static_provider import StaticDataProvider
from security_selection.providers.fallback_provider import FallbackProvider
from security_selection.providers.factory import build_provider, build_fallback_provider

__all__ = [
    "BaseDataProvider",
    "ProviderException",
    "YFinanceProvider",
    "MFAPIProvider",
    "RBIProvider",
    "StaticDataProvider",
    "FallbackProvider",
    "build_provider",
    "build_fallback_provider",
]

