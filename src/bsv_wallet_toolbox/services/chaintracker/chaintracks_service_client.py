"""ChaintracksServiceClient - HTTP client for Chaintracks service.

Implements ChaintracksClientApi by connecting to a remote Chaintracks service
over HTTP REST API using requests library.

USAGE EXAMPLES:

    from bsv_wallet_toolbox.services.chaintracker import ChaintracksServiceClient

    # Connect to local Chaintracks server
    client = ChaintracksServiceClient(
        service_url="http://localhost:3011",
        chain="main"
    )

    # Connect to remote service
    client = ChaintracksServiceClient(
        service_url="https://chaintracks.example.com",
        chain="main"
    )

    # Get current height
    height = client.current_height()

    # Get header for height
    header = client.find_header_for_height(12345)

DESIGN NOTES:
- Uses requests.Session for connection pooling
- Synchronous (blocking) I/O by design
- No retry logic (user's responsibility)
- No WebSocket support (HTTP polling only)

Integration with Services layer:
    When deployed, ChaintracksServiceClient can proxy requests to:
    1. Local ChaintracksService instance
    2. Remote Chaintracks server
    3. WhatsOnChain API (fallback)
    4. ARC API (transaction broadcast)

Synchronous design (blocking I/O) for consistency with Manager layer.

Reference: toolbox/ts-wallet-toolbox/src/services/chaintracker/chaintracks/ChaintracksServiceClient.ts
"""

from __future__ import annotations

import asyncio
import json
import time
import uuid
from typing import Any, Generic, TypeVar, cast

import requests

from ..wallet_services import Chain
from .chaintracks.api import ChaintracksClientApi
from .chaintracks.models import FiatExchangeRates

T = TypeVar("T")


class FetchStatus(Generic[T]):
    """Response wrapper from Chaintracks service."""

    def __init__(self, data: dict[str, Any]) -> None:
        self.status: str = data.get("status", "error")
        self.code: str | None = data.get("code")
        self.description: str | None = data.get("description")
        self.value: T | None = data.get("value")


class ChaintracksServiceClientOptions:
    """Configuration options for ChaintracksServiceClient."""

    def __init__(self, use_authrite: bool = False) -> None:
        self.use_authrite: bool = use_authrite

    @staticmethod
    def create_default() -> ChaintracksServiceClientOptions:
        """Create default options."""
        return ChaintracksServiceClientOptions(use_authrite=False)


class ChaintracksServiceClient(ChaintracksClientApi):
    """HTTP client for Chaintracks service.

    Connects to a ChaintracksService to implement ChaintracksClientApi.

    Reference: toolbox/ts-wallet-toolbox/src/services/chaintracker/chaintracks/ChaintracksServiceClient.ts
    """

    def __init__(
        self,
        chain: Chain,
        service_url: str,
        options: ChaintracksServiceClientOptions | None = None,
    ) -> None:
        """Initialize ChaintracksServiceClient.

        Args:
            chain: Blockchain network ('main' or 'test')
            service_url: Base URL of Chaintracks service
            options: Client configuration options

        Reference: toolbox/ts-wallet-toolbox/src/services/chaintracker/chaintracks/ChaintracksServiceClient.ts
        """
        self.chain: Chain = chain
        self.service_url: str = service_url
        self.options: ChaintracksServiceClientOptions = options or ChaintracksServiceClientOptions.create_default()
        self.timeout: int = 30
        self.session: requests.Session = requests.Session()

        # WebSocket subscription tracking
        self._websocket_subscriptions: dict[str, dict[str, Any]] = {}
        self._websocket_url: str | None = None
        self._websocket_task: asyncio.Task | None = None

    def get_json_or_undefined(self, path: str) -> Any | None:
        """Fetch JSON from service with retry logic (blocking).

        Args:
            path: API endpoint path

        Returns:
            Parsed JSON value or None if not found

        Reference: toolbox/ts-wallet-toolbox/src/services/chaintracker/chaintracks/ChaintracksServiceClient.ts
        """
        # TODO: Phase 4 - Implement advanced retry strategies with exponential backoff
        # TODO: Phase 4 - Add circuit breaker pattern
        error: Exception | None = None

        for retry in range(3):
            try:
                url = f"{self.service_url}{path}"
                response = self.session.get(url, timeout=self.timeout)
                response.raise_for_status()

                data: dict[str, Any] = response.json()
                fetch_status = FetchStatus(data)

                if fetch_status.status == "success":
                    return fetch_status.value

                error = Exception(json.dumps(data))
            except (requests.ConnectionError, requests.Timeout) as e:
                error = e
                if retry < 2:
                    time.sleep(1)  # Retry on connection error
                continue
            except Exception as e:
                error = e
                break

        if error:
            raise error
        return None

    def get_json(self, path: str) -> Any:
        """Fetch JSON from service (raises if not found).

        Args:
            path: API endpoint path

        Returns:
            Parsed JSON value

        Raises:
            Exception: If value is undefined or request fails

        Reference: toolbox/ts-wallet-toolbox/src/services/chaintracker/chaintracks/ChaintracksServiceClient.ts
        """
        result = self.get_json_or_undefined(path)
        if result is None:
            raise Exception("Value was undefined. Requested object may not exist.")
        return result

    def post_json_void(self, path: str, params: Any) -> None:
        """POST JSON to service (blocking).

        Args:
            path: API endpoint path
            params: Request body parameters

        Raises:
            Exception: If request fails

        Reference: toolbox/ts-wallet-toolbox/src/services/chaintracker/chaintracks/ChaintracksServiceClient.ts
        """
        # TODO: Phase 4 - Implement POST retry logic
        try:
            url = f"{self.service_url}{path}"
            response = self.session.post(url, json=params, timeout=self.timeout)
            response.raise_for_status()

            data: dict[str, Any] = response.json()
            fetch_status = FetchStatus(data)

            if fetch_status.status != "success":
                raise Exception(json.dumps(data))

        except Exception as e:
            raise Exception(json.dumps({"error": str(e)}))

    async def current_height(self) -> int:
        """Get current blockchain height.

        Returns:
            Current block height

        Reference: toolbox/ts-wallet-toolbox/src/services/chaintracker/chaintracks/ChaintracksServiceClient.ts
        """
        return await self.get_present_height()

    async def is_valid_root_for_height(self, root: str, height: int) -> bool:
        """Verify if merkle root is valid for height.

        Args:
            root: Merkle root hex string
            height: Block height

        Returns:
            True if root matches header's merkleRoot

        Reference: toolbox/ts-wallet-toolbox/src/services/chaintracker/chaintracks/ChaintracksServiceClient.ts
        """
        header = await self.find_header_for_height(height)
        if header is None:
            return False
        # TODO: Phase 4 - Add proper root comparison with encoding
        return root == header.get("merkleRoot", "")

    async def find_header_for_height(self, height: int) -> dict[str, Any] | None:
        """Get block header at specified height.

        Args:
            height: Block height

        Returns:
            Block header or None if not found

        Reference: toolbox/ts-wallet-toolbox/src/services/chaintracker/chaintracks/ChaintracksServiceClient.ts
        """
        try:
            path = f"/header/height/{height}"
            return self.get_json(path)
        except Exception:
            return None

    async def get_present_height(self) -> int:
        """Get latest chain height.

        Returns:
            Latest block height

        Reference: toolbox/ts-wallet-toolbox/src/services/chaintracker/chaintracks/ChaintracksServiceClient.ts
        """
        # TODO: Phase 4 - Implement caching for height to reduce API calls
        result = self.get_json("/height")
        return cast(int, result.get("height", 0))

    def find_headers_for_heights(self, heights: list[int]) -> dict[int, dict[str, Any]]:
        """Get multiple block headers by height (blocking).

        Args:
            heights: List of block heights

        Returns:
            Mapping of heights to headers

        Reference: toolbox/ts-wallet-toolbox/src/services/chaintracker/chaintracks/ChaintracksServiceClient.ts
        """
        results: dict[int, dict[str, Any]] = {}
        for height in heights:
            try:
                header = self.find_header_for_height(height)
                if header:
                    results[height] = header
            except Exception:
                pass
        return results

    async def subscribe_headers(self, listener: Any) -> str:
        """Subscribe to header updates (WebSocket - Phase 4).

        Args:
            listener: Callback for header updates

        Returns:
            Subscription ID

        Reference: toolbox/ts-wallet-toolbox/src/services/chaintracker/chaintracks/ChaintracksServiceClient.ts
        """
        # WebSocket implementation requires running ChainTracks service with WebSocket support
        # This is a Phase 4 feature that needs:
        # 1. WebSocket server endpoint in ChainTracks service
        # 2. Client-side WebSocket connection management
        # 3. Real-time event forwarding

        subscription_id = f"headers_{uuid.uuid4().hex[:8]}"
        self._websocket_subscriptions[subscription_id] = {
            "type": "headers",
            "listener": listener,
            "active": False,  # Would be True if WebSocket connected
        }

        # TODO: Establish WebSocket connection and register subscription
        # For now, mark as not implemented but provide structure
        raise NotImplementedError("WebSocket subscriptions require Phase 4 ChainTracks server implementation")

    async def subscribe_reorgs(self, listener: Any) -> str:
        """Subscribe to reorg updates (WebSocket - Phase 4).

        Args:
            listener: Callback for reorg updates

        Returns:
            Subscription ID

        Reference: toolbox/ts-wallet-toolbox/src/services/chaintracker/chaintracks/ChaintracksServiceClient.ts
        """
        # WebSocket implementation requires running ChainTracks service with WebSocket support

        subscription_id = f"reorgs_{uuid.uuid4().hex[:8]}"
        self._websocket_subscriptions[subscription_id] = {
            "type": "reorgs",
            "listener": listener,
            "active": False,  # Would be True if WebSocket connected
        }

        # TODO: Establish WebSocket connection and register subscription
        raise NotImplementedError("WebSocket subscriptions require Phase 4 ChainTracks server implementation")

    async def unsubscribe(self, subscription_id: str) -> bool:
        """Cancel a WebSocket subscription (Phase 4).

        Args:
            subscription_id: ID returned from subscribe

        Returns:
            True if unsubscribed

        Reference: toolbox/ts-wallet-toolbox/src/services/chaintracker/chaintracks/ChaintracksServiceClient.ts
        """
        # Remove subscription from tracking
        if subscription_id in self._websocket_subscriptions:
            del self._websocket_subscriptions[subscription_id]

            # TODO: Send unsubscription message over WebSocket if connected
            # For now, just return success
            return True

        return False

    async def get_fiat_exchange_rates(self) -> FiatExchangeRates:
        """Get latest fiat currency exchange rates from the Chaintracks service.

        Returns:
            FiatExchangeRates with timestamp, rates, and base currency

        Reference: toolbox/ts-wallet-toolbox/src/services/chaintracker/chaintracks/ChaintracksServiceClient.ts
        """
        path = "/getFiatExchangeRates"
        return self.get_json(path)

    async def get_headers(self, height: int, count: int) -> str:
        """Get headers in serialized format starting at height.

        Args:
            height: Starting block height
            count: Number of headers to retrieve

        Returns:
            Hex-encoded concatenated block headers

        Reference: toolbox/ts-wallet-toolbox/src/services/chaintracker/chaintracks/ChaintracksServiceClient.ts
        """
        path = f"/getHeaders?height={height}&count={count}"
        return self.get_json(path)

    async def add_header(self, header: dict[str, Any]) -> None:
        """Add a block header to the chaintracks service.

        Args:
            header: BaseBlockHeader to add

        Returns:
            None (void)

        Reference: toolbox/ts-wallet-toolbox/src/services/chaintracker/chaintracks/ChaintracksServiceClient.ts
        """
        self.post_json("/addHeaderHex", header)

    async def find_chain_tip_header(self) -> dict[str, Any]:
        """Get the active chain tip header.

        Returns:
            BlockHeader object of the current chain tip

        Reference: toolbox/ts-wallet-toolbox/src/services/chaintracker/chaintracks/ChaintracksServiceClient.ts
        """
        return self.get_json("/findChainTipHeaderHex")

    async def find_chain_tip_hash(self) -> str:
        """Get the block hash of the active chain tip.

        Returns:
            Block hash (hex string) of the chain tip

        Reference: toolbox/ts-wallet-toolbox/src/services/chaintracker/chaintracks/ChaintracksServiceClient.ts
        """
        return self.get_json("/findChainTipHashHex")

    def destroy(self) -> None:
        """Close all resources.

        Reference: toolbox/ts-wallet-toolbox/src/services/chaintracker/chaintracks/ChaintracksServiceClient.ts
        """
        # Clean up WebSocket subscriptions
        self._websocket_subscriptions.clear()

        # Cancel WebSocket task if running
        if self._websocket_task and not self._websocket_task.done():
            self._websocket_task.cancel()

        # Close HTTP session
        if self.session:
            self.session.close()
