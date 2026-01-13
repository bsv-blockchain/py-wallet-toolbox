"""WalletServices interface definition.

This module defines the WalletServices abstract interface for blockchain data access.
It's the Python equivalent of TypeScript's WalletServices interface.

Note: WalletServices does NOT exist in py-sdk. This is a toolbox-specific
      implementation ported from TypeScript to support wallet operations.
      py-sdk only provides ChainTracker (for merkle proof verification),
      but does not provide the broader services interface needed by wallets.

Reference: toolbox/ts-wallet-toolbox/src/sdk/WalletServices.interfaces.ts
"""

from abc import ABC, abstractmethod
from enum import Enum

from bsv.chaintracker import ChainTracker


class Chain(Enum):
    """Blockchain network enumeration."""

    MAIN = "main"
    TEST = "test"


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

    def __init__(self, chain: Chain | str = "main") -> None:
        """Initialize wallet services.

        Args:
            chain: Blockchain network ('main' or 'test') as Chain enum or string.
                  Accepts both Chain enum values and string values. String values
                  are automatically converted to Chain enum internally for consistency.
                  Defaults to 'main' as string to maintain backward compatibility.
        """
        # Convert string values to Chain enum for backward compatibility
        if isinstance(chain, str):
            chain = Chain(chain)
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
            Serialized block header bytes (80 bytes)

        Raises:
            ValueError: If height is negative
            Exception: If unable to retrieve header from services
        """
        ...
