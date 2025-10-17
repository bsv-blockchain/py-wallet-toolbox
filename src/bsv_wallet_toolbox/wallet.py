"""BRC-100 compliant Bitcoin SV wallet implementation.

Reference: ts-wallet-toolbox/src/Wallet.ts
"""

from typing import Literal

from bsv.wallet.wallet_interface import AuthenticatedResult, GetNetworkResult, GetVersionResult

from .errors import InvalidParameterError

# Type alias for chain (matches TypeScript: 'main' | 'test')
Chain = Literal["main", "test"]

# Type alias for wallet network (matches TypeScript: 'mainnet' | 'testnet')
WalletNetwork = Literal["mainnet", "testnet"]

# Constants
MAX_ORIGINATOR_LENGTH_BYTES = 250  # BRC-100 standard: originator must be under 250 bytes


class Wallet:
    """BRC-100 compliant wallet implementation.

    Implements the WalletInterface defined in bsv-sdk.

    Reference: ts-wallet-toolbox/src/Wallet.ts

    Note:
        Version is hardcoded as a class constant, matching TypeScript implementation.
        Python implementation uses "0.3.0" during development, will become "1.0.0"
        when all 28 methods are implemented.

    Example:
        >>> wallet = Wallet()
        >>> result = await wallet.get_version({})
        >>> print(result["version"])
        0.3.0
    """

    # Version constant (matches TypeScript's hardcoded return value)
    VERSION = "0.3.0"  # Will become "1.0.0" when all 28 methods are complete (3/28 done)

    def __init__(self, chain: Chain = "main") -> None:
        """Initialize wallet.

        Args:
            chain: Bitcoin network chain ('main' or 'test'). Defaults to 'main'.

        Note:
            Version is not configurable, it's a class constant.
        """
        self.chain: Chain = chain

    def _validate_originator(self, originator: str | None) -> None:
        """Validate originator parameter.

        BRC-100 requires originator to be a string under 250 bytes.

        Args:
            originator: Originator domain name (optional)

        Raises:
            InvalidParameterError: If originator is invalid
        """
        if originator is not None:
            if not isinstance(originator, str):
                raise InvalidParameterError("originator", "must be a string")
            if len(originator.encode("utf-8")) > MAX_ORIGINATOR_LENGTH_BYTES:
                raise InvalidParameterError("originator", "must be under 250 bytes")

    def _to_wallet_network(self, chain: Chain) -> WalletNetwork:
        """Convert chain to wallet network name.

        Reference: ts-wallet-toolbox/src/utility/utilityHelpers.ts (toWalletNetwork)

        Args:
            chain: Chain identifier ('main' or 'test')

        Returns:
            Wallet network name ('mainnet' or 'testnet')
        """
        return "mainnet" if chain == "main" else "testnet"

    async def get_network(
        self, _args: dict, originator: str | None = None  # Empty dict for getNetwork (unused but required by interface)
    ) -> GetNetworkResult:
        """Get Bitcoin network.

        BRC-100 WalletInterface method implementation.
        Returns the Bitcoin network (mainnet or testnet) that this wallet is using.

        Reference:
            - ts-wallet-toolbox/src/Wallet.ts
            - ts-wallet-toolbox/test/Wallet/get/getNetwork.test.ts

        Args:
            args: Empty dict (getNetwork takes no parameters)
            originator: Optional originator domain name (must be string under 250 bytes)

        Returns:
            Dictionary with 'network' key containing 'mainnet' or 'testnet'

        Raises:
            InvalidParameterError: If originator is invalid

        Example:
            >>> wallet = Wallet(chain="main")
            >>> result = await wallet.get_network({})
            >>> assert result == {"network": "mainnet"}
        """
        self._validate_originator(originator)
        return {"network": self._to_wallet_network(self.chain)}

    async def get_version(
        self, _args: dict, originator: str | None = None  # Empty dict for getVersion (unused but required by interface)
    ) -> GetVersionResult:
        """Get wallet version.

        BRC-100 WalletInterface method implementation.

        Reference:
            - ts-wallet-toolbox/src/Wallet.ts
            - ts-wallet-toolbox/test/Wallet/get/getVersion.test.ts

        Args:
            args: Empty dict (getVersion takes no parameters)
            originator: Optional originator domain name (must be string under 250 bytes)

        Returns:
            Dictionary with 'version' key containing the version string

        Raises:
            InvalidParameterError: If originator is invalid

        Example:
            >>> wallet = Wallet()
            >>> result = await wallet.get_version({})
            >>> assert result == {"version": Wallet.VERSION}
        """
        self._validate_originator(originator)
        return {"version": self.VERSION}

    async def is_authenticated(
        self,
        _args: dict,
        originator: str | None = None,  # Empty dict for isAuthenticated (unused but required by interface)
    ) -> AuthenticatedResult:
        """Check if user is authenticated.

        BRC-100 WalletInterface method implementation.
        In the base Wallet implementation, authentication is always true since
        the wallet is initialized with keys.

        Reference:
            - ts-wallet-toolbox/src/Wallet.ts

        Args:
            args: Empty dict (isAuthenticated takes no parameters)
            originator: Optional originator domain name (must be string under 250 bytes)

        Returns:
            Dictionary with 'authenticated' key set to True

        Raises:
            InvalidParameterError: If originator is invalid

        Example:
            >>> wallet = Wallet()
            >>> result = await wallet.is_authenticated({})
            >>> assert result == {"authenticated": True}
        """
        self._validate_originator(originator)
        return {"authenticated": True}
