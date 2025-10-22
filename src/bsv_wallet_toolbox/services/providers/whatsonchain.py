"""WhatsOnChain provider implementation.

This module provides WhatsOnChain-based implementations of chain tracking
and blockchain data access.

Reference: 
    - toolbox/ts-wallet-toolbox/src/services/providers/WhatsOnChain.ts
    - toolbox/ts-wallet-toolbox/src/services/providers/SdkWhatsOnChain.ts
"""

from typing import Optional

from bsv.chaintrackers.whatsonchain import WhatsOnChainTracker

from ..chaintracker.chaintracks.api import (
    BaseBlockHeader,
    BlockHeader,
    ChaintracksClientApi,
    ChaintracksInfo,
    HeaderListener,
    ReorgListener,
)
from ..wallet_services import Chain


class WhatsOnChain(WhatsOnChainTracker, ChaintracksClientApi):
    """WhatsOnChain implementation of ChaintracksClientApi.
    
    This is the Python equivalent of TypeScript's WhatsOnChain class.
    Extends py-sdk's WhatsOnChainTracker (equivalent to TS SdkWhatsOnChain) 
    to implement ChaintracksClientApi.
    
    TypeScript class hierarchy:
    - SdkWhatsOnChain implements ChainTracker
    - WhatsOnChainNoServices extends SdkWhatsOnChain
    - WhatsOnChain extends WhatsOnChainNoServices
    
    Python class hierarchy:
    - WhatsOnChainTracker (py-sdk) ≈ SdkWhatsOnChain (ts-sdk)
    - WhatsOnChain (toolbox) ≈ WhatsOnChain (ts-toolbox)
    
    Implemented methods:
    - is_valid_root_for_height() - SDK method (from WhatsOnChainTracker)
    - current_height() - SDK method (from WhatsOnChainTracker)
    - get_chain() - Returns the configured chain
    - find_header_for_height() - Returns block header as BlockHeader object
    
    Not implemented (WhatsOnChain API limitations):
    - get_info() - Chaintracks-specific
    - get_present_height() - Uses current_height() instead
    - get_headers() - Bulk header retrieval not supported
    - find_chain_tip_header() - Can be implemented
    - find_chain_tip_hash() - Can be implemented
    - find_header_for_block_hash() - Requires additional API calls
    - add_header() - Not supported by WhatsOnChain API
    - start_listening() - Event listening not supported
    - listening() - Event listening not supported
    - is_listening() - Event listening not supported
    - is_synchronized() - Event listening not supported
    - subscribe_headers() - Event listening not supported
    - subscribe_reorgs() - Event listening not supported
    - unsubscribe() - Event listening not supported
    
    Reference: 
        - toolbox/ts-wallet-toolbox/src/services/providers/WhatsOnChain.ts
        - toolbox/ts-wallet-toolbox/src/services/providers/SdkWhatsOnChain.ts
    """

    def __init__(self, network: str = "main", api_key: Optional[str] = None, http_client: Optional[any] = None):
        """Initialize WhatsOnChain chaintracks client.
        
        Args:
            network: Blockchain network ('main' or 'test')
            api_key: Optional WhatsOnChain API key
            http_client: Optional HTTP client (uses default if None)
        """
        super().__init__(network=network, api_key=api_key, http_client=http_client)

    async def get_chain(self) -> Chain:
        """Confirm the chain.
        
        Returns:
            Chain identifier ('main' or 'test')
        """
        return self.network  # type: ignore

    async def get_info(self) -> ChaintracksInfo:
        """Get summary of configuration and state.
        
        Not implemented for WhatsOnChain (Chaintracks-specific feature).
        
        Raises:
            NotImplementedError: Always (WhatsOnChain does not support this)
        """
        raise NotImplementedError("get_info() is not supported by WhatsOnChain provider")

    async def get_present_height(self) -> int:
        """Get the latest chain height.
        
        Uses current_height() as WhatsOnChain doesn't distinguish between
        bulk and live heights.
        
        Returns:
            Current blockchain height
        """
        return await self.current_height()

    async def get_headers(self, height: int, count: int) -> str:
        """Get headers in serialized format.
        
        Not implemented for WhatsOnChain (requires bulk header retrieval).
        
        Raises:
            NotImplementedError: Always (WhatsOnChain does not support bulk header retrieval)
        """
        raise NotImplementedError("get_headers() is not supported by WhatsOnChain provider")

    async def find_chain_tip_header(self) -> BlockHeader:
        """Get the active chain tip header.
        
        Not yet implemented but can be implemented using current_height() + find_header_for_height().
        
        Raises:
            NotImplementedError: Always (not yet implemented)
        """
        raise NotImplementedError("find_chain_tip_header() is not yet implemented for WhatsOnChain provider")

    async def find_chain_tip_hash(self) -> str:
        """Get the block hash of the active chain tip.
        
        Not yet implemented but can be implemented using find_chain_tip_header().
        
        Raises:
            NotImplementedError: Always (not yet implemented)
        """
        raise NotImplementedError("find_chain_tip_hash() is not yet implemented for WhatsOnChain provider")

    async def find_header_for_height(self, height: int) -> Optional[BlockHeader]:
        """Get block header for a given block height on active chain.
        
        Returns BlockHeader object (not bytes). For bytes representation,
        use the internal helper method.
        
        Args:
            height: Block height
            
        Returns:
            BlockHeader object or None if not found
        """
        if height < 0:
            raise ValueError(f"Height {height} must be a non-negative integer")

        request_options = {"method": "GET", "headers": self.get_headers()}

        response = await self.http_client.fetch(f"{self.URL}/block/{height}/header", request_options)
        if response.ok:
            data = response.json()["data"]
            if not data:
                return None
                
            # Parse WhatsOnChain header data into BlockHeader
            # Note: WhatsOnChain returns header fields, we need to construct BlockHeader
            return BlockHeader(
                version=data.get("version", 0),
                previousHash=data.get("previousblockhash", ""),
                merkleRoot=data.get("merkleroot", ""),
                time=data.get("time", 0),
                bits=data.get("bits", 0),
                nonce=data.get("nonce", 0),
                height=height,
                hash=data.get("hash", ""),
            )
        elif response.status_code == 404:
            return None
        else:
            raise RuntimeError(f"Failed to get header for height {height}: {response.json()}")

    async def find_header_for_block_hash(self, hash: str) -> Optional[BlockHeader]:
        """Get block header for a given block hash.
        
        Not yet implemented (requires additional API endpoint).
        
        Raises:
            NotImplementedError: Always (not yet implemented)
        """
        raise NotImplementedError("find_header_for_block_hash() is not yet implemented for WhatsOnChain provider")

    async def add_header(self, header: BaseBlockHeader) -> None:
        """Submit a possibly new header for adding.
        
        Not supported by WhatsOnChain API (read-only service).
        
        Raises:
            NotImplementedError: Always (WhatsOnChain is read-only)
        """
        raise NotImplementedError("add_header() is not supported by WhatsOnChain provider (read-only)")

    async def start_listening(self) -> None:
        """Start listening for new headers.
        
        Not supported by WhatsOnChain (no event stream).
        
        Raises:
            NotImplementedError: Always (WhatsOnChain does not support event streams)
        """
        raise NotImplementedError("start_listening() is not supported by WhatsOnChain provider")

    async def listening(self) -> None:
        """Wait for listening state.
        
        Not supported by WhatsOnChain (no event stream).
        
        Raises:
            NotImplementedError: Always (WhatsOnChain does not support event streams)
        """
        raise NotImplementedError("listening() is not supported by WhatsOnChain provider")

    async def is_listening(self) -> bool:
        """Check if actively listening.
        
        Not supported by WhatsOnChain (no event stream).
        
        Returns:
            Always False (WhatsOnChain does not support event streams)
        """
        return False

    async def is_synchronized(self) -> bool:
        """Check if synchronized.
        
        WhatsOnChain is always synchronized (no local state).
        
        Returns:
            Always True (WhatsOnChain queries live data)
        """
        return True

    async def subscribe_headers(self, listener: HeaderListener) -> str:
        """Subscribe to header events.
        
        Not supported by WhatsOnChain (no event stream).
        
        Raises:
            NotImplementedError: Always (WhatsOnChain does not support event streams)
        """
        raise NotImplementedError("subscribe_headers() is not supported by WhatsOnChain provider")

    async def subscribe_reorgs(self, listener: ReorgListener) -> str:
        """Subscribe to reorganization events.
        
        Not supported by WhatsOnChain (no event stream).
        
        Raises:
            NotImplementedError: Always (WhatsOnChain does not support event streams)
        """
        raise NotImplementedError("subscribe_reorgs() is not supported by WhatsOnChain provider")

    async def unsubscribe(self, subscription_id: str) -> bool:
        """Cancel subscriptions.
        
        Not supported by WhatsOnChain (no event stream).
        
        Raises:
            NotImplementedError: Always (WhatsOnChain does not support event streams)
        """
        raise NotImplementedError("unsubscribe() is not supported by WhatsOnChain provider")

    # Helper method for WalletServices compatibility (returns bytes, not BlockHeader)
    async def get_header_bytes_for_height(self, height: int) -> bytes:
        """Get block header bytes at specified height.
        
        This is a helper method for WalletServices.get_header_for_height()
        which expects bytes, not BlockHeader objects.
        
        Args:
            height: Block height
            
        Returns:
            80-byte serialized block header
        """
        if height < 0:
            raise ValueError(f"Height {height} must be a non-negative integer")

        request_options = {"method": "GET", "headers": self.get_headers()}

        response = await self.http_client.fetch(f"{self.URL}/block/{height}/header", request_options)
        if response.ok:
            header_hex = response.json()["data"].get("header")
            if not header_hex:
                raise RuntimeError(f"No header found for height {height}")
            return bytes.fromhex(header_hex)
        elif response.status_code == 404:
            raise RuntimeError(f"No header found for height {height}")
        else:
            raise RuntimeError(f"Failed to get header for height {height}: {response.json()}")
