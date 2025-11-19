"""WalletServicesOptions type definition.

This module defines the options for configuring WalletServices.

Reference: toolbox/ts-wallet-toolbox/src/sdk/WalletServices.interfaces.ts
"""

from typing import Any, TypedDict

from .wallet_services import Chain


class BsvExchangeRate(TypedDict, total=False):
    """BSV exchange rate information."""

    timestamp: str  # ISO format datetime
    base: str  # Currency base (e.g., 'USD')
    rate: float  # Exchange rate


class FiatExchangeRates(TypedDict, total=False):
    """Fiat currency exchange rates."""

    timestamp: str  # ISO format datetime
    base: str  # Currency base (e.g., 'USD')
    rates: dict[str, float]  # Mapping of currency codes to rates


class WalletServicesOptions(TypedDict, total=False):
    """Configuration options for WalletServices.

    This is the Python equivalent of TypeScript's WalletServicesOptions interface.

    Reference: toolbox/ts-wallet-toolbox/src/sdk/WalletServices.interfaces.ts
    Reference: toolbox/ts-wallet-toolbox/src/services/createDefaultWalletServicesOptions.ts
    """

    # Core chain configuration (required)
    chain: Chain

    # Provider API keys
    whatsOnChainApiKey: str | None
    bitailsApiKey: str | None
    taalApiKey: str | None  # Unused as of 2025-08-31

    # BSV/USD exchange rate
    bsvExchangeRate: BsvExchangeRate  # Default: 26.17 USD (as of 2025-08-31)
    bsvUpdateMsecs: int  # Default: 900000 (15 minutes)

    # Fiat exchange rates
    fiatExchangeRates: FiatExchangeRates  # Default: USD base with GBP, EUR
    fiatUpdateMsecs: int  # Default: 86400000 (24 hours)

    # Exchange rate API configuration
    disableMapiCallback: bool  # Default: True (MAPI callbacks deprecated)
    exchangeratesapiKey: str | None  # API key for exchangeratesapi.io
    chaintracksFiatExchangeRatesUrl: str | None  # URL for fiat rates (via Chaintracks)

    # ARC TAAL broadcaster options (TS parity)
    arcUrl: str | None
    arcApiKey: str | None
    arcHeaders: dict[str, str] | None

    # ARC GorillaPool broadcaster options (TS parity)
    arcGorillaPoolUrl: str | None
    arcGorillaPoolApiKey: str | None
    arcGorillaPoolHeaders: dict[str, str] | None

    # Advanced options (optional)
    chaintracks: Any | None  # ChaintracksClientApi instance
