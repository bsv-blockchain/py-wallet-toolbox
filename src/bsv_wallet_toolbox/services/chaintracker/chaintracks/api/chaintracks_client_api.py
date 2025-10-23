"""Chaintracks client API interface.

This module defines the ChaintracksClientApi interface which extends ChainTracker
with additional methods needed by wallet operations.

Reference: toolbox/ts-wallet-toolbox/src/services/chaintracker/chaintracks/Api/ChaintracksClientApi.ts
"""

from abc import abstractmethod
from collections.abc import Callable

from bsv.chaintracker import ChainTracker

from .....services.wallet_services import Chain
from .block_header_api import BaseBlockHeader, BlockHeader, ChaintracksInfo

# Type aliases for listeners (equivalent to TypeScript function types)
HeaderListener = Callable[[BlockHeader], None]
ReorgListener = Callable[[int, BlockHeader, BlockHeader, list[BlockHeader] | None], None]


class ChaintracksClientApi(ChainTracker):
    """Chaintracks client API interface with extended methods.

    This is the Python equivalent of TypeScript's ChaintracksClientApi.
    Extends the base ChainTracker with additional methods needed by wallet operations.

    Note: This does NOT exist in py-sdk. It is a toolbox-specific extension,
          mirroring TypeScript's ChaintracksClientApi extends ChainTracker pattern.

    Reference: toolbox/ts-wallet-toolbox/src/services/chaintracker/chaintracks/Api/ChaintracksClientApi.ts

    The interface includes all methods from TypeScript's ChaintracksClientApi:

    From ChainTracker (SDK):
    - is_valid_root_for_height() - Verify Merkle root
    - current_height() - Get current blockchain height

    Chaintracks extensions:
    - get_chain() - Confirm the chain
    - get_info() - Get summary of configuration and state
    - get_present_height() - Get latest chain height from bulk ingestors
    - get_headers() - Get headers in serialized format
    - find_chain_tip_header() - Get active chain tip header
    - find_chain_tip_hash() - Get block hash of active chain tip
    - find_header_for_height() - Get block header at specified height
    - find_header_for_block_hash() - Get header for given block hash
    - add_header() - Submit a possibly new header
    - start_listening() - Start listening for new headers
    - listening() - Wait for listening state
    - is_listening() - Check if actively listening
    - is_synchronized() - Check if synchronized
    - subscribe_headers() - Subscribe to header events
    - subscribe_reorgs() - Subscribe to reorganization events
    - unsubscribe() - Cancel subscriptions
    """

    @abstractmethod
    async def get_chain(self) -> Chain:
        """Confirm the chain.

        Returns:
            Chain identifier ('main' or 'test')
        """
        ...

    @abstractmethod
    async def get_info(self) -> ChaintracksInfo:
        """Get summary of configuration and state.

        Returns:
            ChaintracksInfo with configuration and state details
        """
        ...

    @abstractmethod
    async def get_present_height(self) -> int:
        """Get the latest chain height from configured bulk ingestors.

        Returns:
            Latest blockchain height from bulk ingestors
        """
        ...

    @abstractmethod
    async def get_headers(self, height: int, count: int) -> str:
        """Get headers in 80 byte serialized format.

        Adds headers in 80 byte serialized format to an array.
        Only adds active headers.
        Array length divided by 80 is the actual number returned.

        Args:
            height: Height of first header
            count: Maximum number of headers to return

        Returns:
            Array of headers as serialized hex string
        """
        ...

    @abstractmethod
    async def find_chain_tip_header(self) -> BlockHeader:
        """Get the active chain tip header.

        Returns:
            BlockHeader of the current chain tip
        """
        ...

    @abstractmethod
    async def find_chain_tip_hash(self) -> str:
        """Get the block hash of the active chain tip.

        Returns:
            Block hash (hex string) of the chain tip
        """
        ...

    @abstractmethod
    async def find_header_for_height(self, height: int) -> BlockHeader | None:
        """Get block header for a given block height on active chain.

        Note: Returns BlockHeader object (not bytes). This differs from the
        find_header_for_height() helper in WhatsOnChainChaintracksClient which
        returns bytes for compatibility with WalletServices.

        Args:
            height: Block height

        Returns:
            BlockHeader object or None if not found
        """
        ...

    @abstractmethod
    async def find_header_for_block_hash(self, hash: str) -> BlockHeader | None:
        """Get block header for a given recent block hash.

        Args:
            hash: Block hash (hex string)

        Returns:
            BlockHeader object or None if not found
        """
        ...

    @abstractmethod
    async def add_header(self, header: BaseBlockHeader) -> None:
        """Submit a possibly new header for adding.

        If the header is invalid or a duplicate it will not be added.

        This header will be ignored if the previous header has not already been
        inserted when this header is considered for insertion.

        Args:
            header: Block header to add

        Returns:
            Returns immediately (void)
        """
        ...

    @abstractmethod
    async def start_listening(self) -> None:
        """Start or resume listening for new headers.

        Calls `synchronize` to catch up on headers that were found while not listening.

        Begins listening to any number of configured new header notification services.

        Begins sending notifications to subscribed listeners only after processing any
        previously found headers.

        May be called if already listening or synchronizing to listen.

        The `listening()` method can be awaited to wait for listening state.
        """
        ...

    @abstractmethod
    async def listening(self) -> None:
        """Wait for listening state.

        Returns a Promise that will resolve when the previous call to start_listening()
        enters the listening-for-new-headers state.
        """
        ...

    @abstractmethod
    async def is_listening(self) -> bool:
        """Check if actively listening for new headers.

        Returns:
            True if actively listening for new headers and client api is enabled
        """
        ...

    @abstractmethod
    async def is_synchronized(self) -> bool:
        """Check if synchronized.

        Returns:
            True if `synchronize` has completed at least once
        """
        ...

    @abstractmethod
    async def subscribe_headers(self, listener: HeaderListener) -> str:
        """Subscribe to "header" events.

        Args:
            listener: Callback function for header events

        Returns:
            Subscription identifier

        Raises:
            NotImplementedError: If callback events are not supported
        """
        ...

    @abstractmethod
    async def subscribe_reorgs(self, listener: ReorgListener) -> str:
        """Subscribe to "reorganization" events.

        Args:
            listener: Callback function for reorganization events

        Returns:
            Subscription identifier

        Raises:
            NotImplementedError: If callback events are not supported
        """
        ...

    @abstractmethod
    async def unsubscribe(self, subscription_id: str) -> bool:
        """Cancel all subscriptions with the given subscription ID.

        Args:
            subscription_id: Value previously returned by subscribe_headers or subscribe_reorgs

        Returns:
            True if a subscription was canceled

        Raises:
            NotImplementedError: If callback events are not supported
        """
        ...
