"""BRC-100 compliant Bitcoin SV wallet implementation.

Reference: ts-wallet-toolbox/src/Wallet.ts
"""

from typing import Literal

from bsv.wallet.wallet_interface import (
    AuthenticatedResult,
    GetHeaderResult,
    GetHeightResult,
    GetNetworkResult,
    GetVersionResult,
)

from .errors import InvalidParameterError
from .services import WalletServices

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
        Python implementation uses "0.4.0" during development, will become "1.0.0"
        when all 28 methods are implemented.

    Example:
        >>> wallet = Wallet()
        >>> result = await wallet.get_version({})
        >>> print(result["version"])
        0.4.0
    """

    # Version constant (matches TypeScript's hardcoded return value)
    VERSION = "0.6.0"  # Will become "1.0.0" when all 28 methods are complete (6/28 done)

    def __init__(self, chain: Chain = "main", services: WalletServices | None = None) -> None:
        """Initialize wallet.

        Args:
            chain: Bitcoin network chain ('main' or 'test'). Defaults to 'main'.
            services: Optional WalletServices instance for blockchain data access.
                     If None, some methods requiring services will not work.

        Note:
            Version is not configurable, it's a class constant.
        """
        self.chain: Chain = chain
        self.services: WalletServices | None = services

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

    async def wait_for_authentication(
        self,
        _args: dict,
        originator: str | None = None,  # Empty dict for waitForAuthentication (unused but required by interface)
    ) -> AuthenticatedResult:
        """Wait for user authentication.

        BRC-100 WalletInterface method implementation.
        In the base Wallet implementation, returns immediately with authenticated=true
        since the wallet is always authenticated (initialized with keys).

        Note:
            In wallet manager implementations (SimpleWalletManager, CWIStyleWalletManager),
            this method waits in a loop until authentication occurs. However, in the base
            Wallet class, authentication is immediate.

        Reference:
            - ts-wallet-toolbox/src/Wallet.ts

        Args:
            args: Empty dict (waitForAuthentication takes no parameters)
            originator: Optional originator domain name (must be string under 250 bytes)

        Returns:
            Dictionary with 'authenticated' key set to True

        Raises:
            InvalidParameterError: If originator is invalid

        Example:
            >>> wallet = Wallet()
            >>> result = await wallet.wait_for_authentication({})
            >>> assert result == {"authenticated": True}
        """
        self._validate_originator(originator)
        return {"authenticated": True}

    async def get_height(
        self, _args: dict, originator: str | None = None  # Empty dict for getHeight (unused but required by interface)
    ) -> GetHeightResult:
        """Get current blockchain height.

        BRC-100 WalletInterface method implementation.
        Returns the current height of the blockchain by querying configured services.

        Reference:
            - ts-wallet-toolbox/src/Wallet.ts
            - ts-wallet-toolbox/test/Wallet/get/getHeight.test.ts

        Args:
            args: Empty dict (getHeight takes no parameters)
            originator: Optional originator domain name (must be string under 250 bytes)

        Returns:
            Dictionary with 'height' key containing current blockchain height

        Raises:
            InvalidParameterError: If originator parameter is invalid
            RuntimeError: If services are not configured

        Example:
            >>> from bsv_wallet_toolbox.services import MockWalletServices
            >>> services = MockWalletServices(height=850000)
            >>> wallet = Wallet(services=services)
            >>> result = await wallet.get_height({})
            >>> print(result["height"])
            850000

        Note:
            Requires services to be configured. If services is None, raises RuntimeError.
        """
        self._validate_originator(originator)

        if self.services is None:
            raise RuntimeError("Services must be configured to use getHeight")

        height = await self.services.get_height()
        return {"height": height}

    async def get_header_for_height(self, args: dict, originator: str | None = None) -> GetHeaderResult:
        """Get block header at specified height.

        BRC-100 WalletInterface method implementation.
        Returns the block header at the specified height as a hex string.

        Reference:
            - ts-wallet-toolbox/src/Wallet.ts
            - ts-wallet-toolbox/test/Wallet/get/getHeaderForHeight.test.ts

        Args:
            args: Dictionary with 'height' key (non-negative integer)
            originator: Optional originator domain name (must be string under 250 bytes)

        Returns:
            Dictionary with 'header' key containing block header as hex string

        Raises:
            InvalidParameterError: If originator parameter is invalid or height is invalid
            RuntimeError: If services are not configured
            Exception: If unable to retrieve header from services

        Example:
            >>> from bsv_wallet_toolbox.services import MockWalletServices
            >>> services = MockWalletServices(height=850000)
            >>> wallet = Wallet(services=services)
            >>> result = await wallet.get_header_for_height({"height": 850000})
            >>> print(result["header"][:16])  # First 16 chars of hex
            0100000000000000

        Note:
            Requires services to be configured. If services is None, raises RuntimeError.
            Height must be a non-negative integer.
        """
        self._validate_originator(originator)

        if self.services is None:
            raise RuntimeError("Services must be configured to use getHeaderForHeight")

        # Validate height parameter
        if "height" not in args:
            raise InvalidParameterError("height", "required")

        height = args["height"]

        if not isinstance(height, int):
            raise InvalidParameterError("height", "an integer")

        if height < 0:
            raise InvalidParameterError("height", f"a non-negative integer (got {height})")

        # Get header from services (returns bytes)
        header_bytes = await self.services.get_header_for_height(height)

        # Convert bytes to hex string (matching TypeScript behavior)
        return {"header": header_bytes.hex()}
