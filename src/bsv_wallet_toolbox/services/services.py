"""Services implementation.

Main implementation of WalletServices interface with provider support.

Reference: toolbox/ts-wallet-toolbox/src/services/Services.ts
"""


from bsv.chaintracker import ChainTracker

from .providers.whatsonchain import WhatsOnChain
from .wallet_services import Chain, WalletServices
from .wallet_services_options import WalletServicesOptions


def create_default_options(chain: Chain) -> WalletServicesOptions:
    """Create default WalletServicesOptions for a given chain.

    Equivalent to TypeScript's Services.createDefaultOptions()

    Args:
        chain: Blockchain network ('main' or 'test')

    Returns:
        WalletServicesOptions with default values

    Reference: toolbox/ts-wallet-toolbox/src/services/createDefaultWalletServicesOptions.ts
    """
    return WalletServicesOptions(chain=chain)


class Services(WalletServices):
    """Production-ready WalletServices implementation.

    This is the Python equivalent of TypeScript's Services class.
    Supports multiple providers (WhatsOnChain, ARC, Bitails, etc.).

    Current implementation status:
    - ✅ WhatsOnChain: Fully implemented
    - ❌ ARC (TAAL): Not yet implemented
    - ❌ ARC (GorillaPool): Not yet implemented
    - ❌ Bitails: Not yet implemented

    Reference: toolbox/ts-wallet-toolbox/src/services/Services.ts

    Example:
        >>> # Simple usage with chain
        >>> services = Services("main")
        >>>
        >>> # Advanced usage with options
        >>> options = WalletServicesOptions(
        ...     chain="main",
        ...     whatsOnChainApiKey="your-api-key"
        ... )
        >>> services = Services(options)
        >>>
        >>> # Get blockchain height
        >>> height = await services.get_height()
        >>> print(height)
        850123
    """

    # Provider instances (TypeScript structure)
    options: WalletServicesOptions
    whatsonchain: WhatsOnChain
    # Future providers (not yet implemented):
    # arc_taal: ARC
    # arc_gorillapool: Optional[ARC]
    # bitails: Bitails

    def __init__(self, options_or_chain: Chain | WalletServicesOptions) -> None:
        """Initialize wallet services.

        Equivalent to TypeScript's Services constructor which accepts either
        a Chain string or WalletServicesOptions object.

        Args:
            options_or_chain: Either a Chain ('main'/'test') or full WalletServicesOptions

        Example:
            >>> # Simple: Just pass chain
            >>> services = Services("main")
            >>>
            >>> # Advanced: Pass full options
            >>> options = WalletServicesOptions(
            ...     chain="main",
            ...     whatsOnChainApiKey="your-api-key"
            ... )
            >>> services = Services(options)

        Reference: toolbox/ts-wallet-toolbox/src/services/Services.ts constructor
        """
        # Determine chain and options (matching TypeScript logic)
        if isinstance(options_or_chain, str):
            # Simple case: chain string provided
            chain: Chain = options_or_chain
            self.options = create_default_options(chain)
        else:
            # Advanced case: full options provided
            chain = options_or_chain["chain"]
            self.options = options_or_chain

        # Call parent constructor
        super().__init__(chain)

        # Initialize WhatsOnChain provider (currently only implemented provider)
        api_key = self.options.get("whatsOnChainApiKey")
        self.whatsonchain = WhatsOnChain(network=chain, api_key=api_key, http_client=None)

        # Future providers (not yet implemented):
        # self.arc_taal = ARC(self.options["arcUrl"], self.options["arcConfig"], "arcTaal")
        # if self.options.get("arcGorillaPoolUrl"):
        #     self.arc_gorillapool = ARC(
        #         self.options["arcGorillaPoolUrl"],
        #         self.options.get("arcGorillaPoolConfig"),
        #         "arcGorillaPool"
        #     )
        # self.bitails = Bitails(chain, {"apiKey": self.options.get("bitailsApiKey")})

    async def get_chain_tracker(self) -> ChainTracker:
        """Get ChainTracker instance for Merkle proof verification.

        Returns the WhatsOnChain ChainTracker implementation.

        Returns:
            WhatsOnChain instance (implements ChaintracksClientApi)
        """
        return self.whatsonchain

    async def get_height(self) -> int:
        """Get current blockchain height from WhatsOnChain.

        Equivalent to TypeScript's Services.getHeight()
        Uses py-sdk's WhatsOnChainTracker.current_height() (SDK method)

        Returns:
            Current blockchain height

        Raises:
            RuntimeError: If unable to retrieve height
        """
        return await self.whatsonchain.current_height()

    async def get_header_for_height(self, height: int) -> bytes:
        """Get block header at specified height from WhatsOnChain.

        Equivalent to TypeScript's Services.getHeaderForHeight()
        Uses WhatsOnChain.get_header_bytes_for_height() helper method

        Args:
            height: Block height (must be non-negative)

        Returns:
            80-byte serialized block header

        Raises:
            ValueError: If height is negative
            RuntimeError: If unable to retrieve header
        """
        return await self.whatsonchain.get_header_bytes_for_height(height)
