"""WalletServices interface and implementations.

This module defines the WalletServices interface for blockchain data access.
It's the Python equivalent of TypeScript's WalletServices interface.

Note: WalletServices does NOT exist in py-sdk. This is a toolbox-specific
      implementation ported from TypeScript to support wallet operations.
      py-sdk only provides ChainTracker (for merkle proof verification),
      but does not provide the broader services interface needed by wallets.

Reference: toolbox/ts-wallet-toolbox/src/sdk/WalletServices.interfaces.ts
"""

from abc import ABC, abstractmethod
from typing import Literal

from bsv.chaintracker import ChainTracker

# Type alias for blockchain network
Chain = Literal["main", "test"]


class WalletServices(ABC):
    """Abstract interface for wallet services providing blockchain data access.

    This is the Python equivalent of TypeScript's WalletServices interface.
    Services provide access to blockchain height, headers, and ChainTracker.

    Important Notes:
    - This class does NOT exist in py-sdk. It is ported from TypeScript ts-wallet-toolbox.
    - TypeScript's WalletServices does NOT extend ChainTracker.
      Instead, it has a getChainTracker() method that returns a ChainTracker instance.
    - py-sdk provides ChainTracker (ABC) which we use, but not WalletServices itself.

    Reference: toolbox/ts-wallet-toolbox/src/sdk/WalletServices.interfaces.ts
    py-sdk Reference: ChainTracker exists in sdk/py-sdk/bsv/chaintracker.py

    Attributes:
        chain: The blockchain network ('main' or 'test')
    """

    def __init__(self, chain: Chain = "main") -> None:
        """Initialize wallet services.

        Args:
            chain: Blockchain network ('main' or 'test')
        """
        self.chain: Chain = chain

    @abstractmethod
    async def get_chain_tracker(self) -> ChainTracker:
        """Get a ChainTracker instance for merkle proof verification.

        Returns:
            ChainTracker instance

        Raises:
            Exception: If ChainTracker cannot be created
        """
        ...

    @abstractmethod
    async def get_height(self) -> int:
        """Get the current height of the blockchain.

        Returns:
            Current blockchain height as a positive integer

        Raises:
            Exception: If unable to retrieve height from services
        """
        ...

    @abstractmethod
    async def get_header_for_height(self, height: int) -> bytes:
        """Get the block header at a specified height.

        Args:
            height: Block height (must be non-negative)

        Returns:
            Serialized block header bytes

        Raises:
            ValueError: If height is negative
            Exception: If unable to retrieve header from services
        """
        ...


class MockWalletServices(WalletServices):
    """Mock implementation of WalletServices for testing.

    Returns fixed values for testing purposes. This implementation is used
    in unit tests and when no real services are configured.

    Note: This is a toolbox-specific implementation. py-sdk does not provide
          mock services; we implement them here for testing wallet operations.

    Example:
        >>> services = MockWalletServices(chain="main", height=850000)
        >>> height = await services.get_height()
        >>> print(height)
        850000
    """

    def __init__(
        self,
        chain: Chain = "main",
        height: int = 850000,
        header: bytes = b"",
        chain_tracker: ChainTracker | None = None,
    ) -> None:
        """Initialize mock services with fixed return values.

        Args:
            chain: Blockchain network ('main' or 'test')
            height: Fixed height to return (default: 850000, matching Universal Test Vectors)
            header: Fixed header bytes to return
            chain_tracker: Optional ChainTracker instance (creates mock if None)
        """
        super().__init__(chain)
        self._height = height
        self._header = header or b"\x00" * 80  # Default 80-byte empty header
        self._chain_tracker = chain_tracker

    async def get_chain_tracker(self) -> ChainTracker:
        """Return a mock ChainTracker.

        Returns:
            MockChainTracker instance that always validates
        """
        if self._chain_tracker is None:
            # Create inline mock ChainTracker
            class MockChainTracker(ChainTracker):
                async def is_valid_root_for_height(self, _root: str, _height: int) -> bool:
                    return True

            self._chain_tracker = MockChainTracker()

        return self._chain_tracker

    async def get_height(self) -> int:
        """Return the configured mock height.

        Returns:
            The fixed height value configured in __init__
        """
        return self._height

    async def get_header_for_height(self, height: int) -> bytes:
        """Return the configured mock header.

        Args:
            height: Block height (validated but not used in mock)

        Returns:
            The fixed header bytes configured in __init__

        Raises:
            ValueError: If height is negative
        """
        if height < 0:
            raise ValueError(f"Height {height} must be a non-negative integer")
        return self._header
