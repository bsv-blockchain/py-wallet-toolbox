"""WalletServicesOptions type definition.

This module defines the options for configuring WalletServices.

Reference: toolbox/ts-wallet-toolbox/src/sdk/WalletServices.interfaces.ts
"""

from typing import TypedDict

from .wallet_services import Chain


class WalletServicesOptions(TypedDict, total=False):
    """Configuration options for WalletServices.

    This is the Python equivalent of TypeScript's WalletServicesOptions interface.

    Reference: toolbox/ts-wallet-toolbox/src/sdk/WalletServices.interfaces.ts

    Note: Currently only implementing the minimum required options for WhatsOnChain.
          Additional options from TypeScript (for future implementation):
          - taalApiKey: TAAL API key (unused as of 2025-08-31)
          - bitailsApiKey: Bitails API key
          - arcUrl: ARC service URL
          - arcConfig: ARC configuration
          - arcGorillaPoolUrl: GorillaPool ARC URL
          - arcGorillaPoolConfig: GorillaPool ARC config
          - chaintracks: Chaintracks client API instance
          - bsvExchangeRate: BSV/USD exchange rate
          - bsvUpdateMsecs: Exchange rate update interval
          - fiatExchangeRates: Fiat currency exchange rates
          - fiatUpdateMsecs: Fiat rate update interval
    """

    chain: Chain  # Required field
    whatsOnChainApiKey: str | None
    # Future fields (not yet implemented):
    # taalApiKey: Optional[str]
    # bitailsApiKey: Optional[str]
    # arcUrl: Optional[str]
    # arcConfig: Optional[Any]
    # arcGorillaPoolUrl: Optional[str]
    # arcGorillaPoolConfig: Optional[Any]
    # chaintracks: Optional[Any]
    # bsvExchangeRate: Optional[Any]
    # bsvUpdateMsecs: Optional[int]
    # fiatExchangeRates: Optional[Any]
    # fiatUpdateMsecs: Optional[int]
