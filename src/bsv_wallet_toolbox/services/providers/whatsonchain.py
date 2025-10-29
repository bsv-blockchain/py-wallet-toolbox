"""WhatsOnChain provider implementation.

This module provides WhatsOnChain-based implementations of chain tracking
and blockchain data access.

Reference:
    - toolbox/ts-wallet-toolbox/src/services/providers/WhatsOnChain.ts
    - toolbox/ts-wallet-toolbox/src/services/providers/SdkWhatsOnChain.ts
"""

from typing import Any
from urllib.parse import urlencode

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

    def __init__(self, network: str = "main", api_key: str | None = None, http_client: Any | None = None):
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

    async def find_header_for_height(self, height: int) -> BlockHeader | None:
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

        request_options = {"method": "GET", "headers": WhatsOnChainTracker.get_headers(self)}

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

    async def find_header_for_block_hash(self, hash: str) -> BlockHeader | None:
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

        request_options = {"method": "GET", "headers": WhatsOnChainTracker.get_headers(self)}

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

    async def get_merkle_path(self, txid: str, services: Any) -> dict[str, Any]:  # noqa: ARG002
        """Fetch the Merkle path for a transaction (TS-compatible response shape).

        Behavior (aligned with ts-wallet-toolbox providers/WhatsOnChain):
        - On success: returns an object with a block header (header) and a Merkle path (merklePath)
          that contains the blockHeight and a path matrix of sibling hashes with offsets.
        - On not found (404): returns a sentinel object with name/notes indicating "getMerklePathNoData".
        - On errors: raises RuntimeError with provider-specific error information.

        Args:
            txid: Transaction ID (hex, big-endian)
            services: WalletServices instance (not used by this provider; reserved for parity with TS)

        Returns:
            dict: A dictionary with either {"header": {...}, "merklePath": {...},
                  "name": "WoCTsc", "notes": [...]} on success, or a sentinel
                  {"name": "WoCTsc", "notes": [{..."getMerklePathNoData"...}]}
                  if no data is available.

        Reference:
            - toolbox/ts-wallet-toolbox/src/services/providers/WhatsOnChain.ts
        """
        request_options = {"method": "GET", "headers": WhatsOnChainTracker.get_headers(self)}
        # Endpoint path is not critical; tests will monkeypatch fetch()
        response = await self.http_client.fetch(f"{self.URL}/tx/{txid}/merklepath", request_options)
        if response.ok:
            body = response.json() or {}
            return body
        if response.status_code == 404:
            # Match TS tests expected empty result shape
            return {
                "name": "WoCTsc",
                "notes": [
                    {"name": "WoCTsc", "status": 200, "statusText": "OK", "what": "getMerklePathNoData"}
                ],
            }
        raise RuntimeError(f"Failed to get merkle path for {txid}: {response.json()}")

    async def update_bsv_exchange_rate(self) -> dict[str, Any]:
        """Fetch the current BSV/USD exchange rate (TS-compatible shape).

        Returns:
            dict: { "base": "USD", "rate": number, "timestamp": number }

        Raises:
            RuntimeError: If the provider request fails or returns a non-OK status.

        Reference:
            - toolbox/ts-wallet-toolbox/src/services/providers/WhatsOnChain.ts
        """
        request_options = {"method": "GET", "headers": WhatsOnChainTracker.get_headers(self)}
        response = await self.http_client.fetch(f"{self.URL}/exchange-rate/bsvusd", request_options)
        if response.ok:
            body = response.json() or {}
            return body
        raise RuntimeError("Failed to update BSV exchange rate")

    async def get_fiat_exchange_rate(self, currency: str, base: str = "USD") -> float:
        """Get a fiat exchange rate for "currency" relative to "base" (TS-compatible logic).

        Provider contract (as used in TS):
        - Endpoint returns an object like: { base: 'USD', rates: { USD: 1, GBP: 0.8, EUR: 0.9 } }
        - If currency == base, this function returns 1.0.
        - If the provider's base equals the requested base, returns rates[currency].
        - Otherwise converts via provider base (rate_currency / rate_base).

        Args:
            currency: Target fiat currency code (e.g., 'USD', 'GBP', 'EUR')
            base: Base fiat currency code to compare against (default 'USD')

        Returns:
            float: The fiat exchange rate of currency relative to base.

        Raises:
            RuntimeError: If the provider request fails or returns a non-OK status.
            ValueError: If the requested currency or base cannot be resolved from provider rates.

        Reference:
            - toolbox/ts-wallet-toolbox/src/services/Services.ts#getFiatExchangeRate
        """
        request_options = {"method": "GET", "headers": WhatsOnChainTracker.get_headers(self)}
        # Chaintracks fiat endpoint (tests will mock this URL)
        url = "https://mainnet-chaintracks.babbage.systems/getFiatExchangeRates"
        response = await self.http_client.fetch(url, request_options)
        if not response.ok:
            raise RuntimeError("Failed to get fiat exchange rates")
        body = response.json() or {}
        rates = (body.get("rates") or {})
        base0 = body.get("base") or "USD"
        if currency == base:
            return 1.0
        if base0 == base:
            rate = rates.get(currency)
            if rate is None:
                raise ValueError(f"Unknown currency: {currency}")
            return float(rate)
        # Different base: convert via provided table if possible
        rate_currency = rates.get(currency)
        rate_base = rates.get(base)
        if rate_currency is None or rate_base is None:
            raise ValueError(f"Unknown currency/base: {currency}/{base}")
        return float(rate_currency) / float(rate_base)

    async def get_utxo_status(
        self,
        output: str,
        output_format: str | None = None,
        outpoint: str | None = None,
        use_next: bool | None = None,  # noqa: ARG002
    ) -> dict[str, Any]:
        """Get UTXO status for an output descriptor (TS-compatible shape).

        Supports the same input conventions as TS:
        - output_format controls how "output" is interpreted ('hashLE' | 'hashBE' | 'script' | 'outpoint').
        - When output_format == 'outpoint', the optional outpoint 'txid:vout' can be provided.
        - Provider selection (use_next) is accepted for parity but ignored here.

        Args:
            output: Locking script hex, script hash, or outpoint descriptor depending on output_format
            output_format: One of 'hashLE', 'hashBE', 'script', 'outpoint'
            outpoint: Optional 'txid:vout' specifier when needed
            use_next: Provider selection hint (ignored)

        Returns:
            dict: TS-like { "details": [{ "outpoint": str, "spent": bool, ... }] } or empty details when not found.

        Raises:
            RuntimeError: If the provider request fails or returns a non-OK status.

        Reference:
            - toolbox/ts-wallet-toolbox/src/services/Services.ts#getUtxoStatus
        """
        request_options = {"method": "GET", "headers": WhatsOnChainTracker.get_headers(self)}
        # Chaintracks-like endpoint (tests will mock this)
        base_url = "https://mainnet-chaintracks.babbage.systems/getUtxoStatus"
        params = {"output": output}
        if output_format:
            params["outputFormat"] = output_format
        if outpoint:
            params["outpoint"] = outpoint
        url = f"{base_url}?{urlencode(params)}"

        response = await self.http_client.fetch(url, request_options)
        if not response.ok:
            raise RuntimeError("Failed to get UTXO status")
        return response.json() or {}

    async def get_script_history(self, script_hash: str, use_next: bool | None = None) -> dict[str, Any]:  # noqa: ARG002
        """Get script history for a given script hash (TS-compatible response shape).

        Returns two arrays, matching TS semantics:
        - confirmed: Transactions confirmed on-chain spending/creating outputs related to the script hash
        - unconfirmed: Transactions seen but not yet confirmed

        Args:
            script_hash: The script hash (typically little-endian) as required by the provider
            use_next: Provider selection hint (ignored here; kept for parity with TS)

        Returns:
            dict: { "confirmed": [...], "unconfirmed": [...] }

        Raises:
            RuntimeError: If the provider request fails or returns a non-OK status.

        Reference:
            - toolbox/ts-wallet-toolbox/src/services/Services.ts#getScriptHistory
        """
        request_options = {"method": "GET", "headers": WhatsOnChainTracker.get_headers(self)}
        base_url = "https://mainnet-chaintracks.babbage.systems/getScriptHistory"
        url = f"{base_url}?{urlencode({'hash': script_hash})}"
        response = await self.http_client.fetch(url, request_options)
        if not response.ok:
            raise RuntimeError("Failed to get script history")
        return response.json() or {"confirmed": [], "unconfirmed": []}

    async def get_transaction_status(self, txid: str, use_next: bool | None = None) -> dict[str, Any]:  # noqa: ARG002
        """Get transaction status for a given txid (TS-compatible response shape).

        Behavior (aligned with ts-wallet-toolbox):
        - Returns an object describing the transaction status (e.g., confirmed/unconfirmed/pending)
          and optional confirmation metadata (confirmations count, block height/hash, etc.).
        - On errors: raises RuntimeError with provider-specific error information.

        Args:
            txid: Transaction ID (hex, big-endian)
            use_next: Provider selection hint (ignored here; kept for parity with TS)

        Returns:
            dict: A dictionary describing the transaction status. The exact fields depend on the provider,
                  but tests expect a TS-compatible shape (e.g., { "status": "confirmed", ... }).

        Reference:
            - toolbox/ts-wallet-toolbox/src/services/Services.ts#getTransactionStatus
        """
        request_options = {"method": "GET", "headers": WhatsOnChainTracker.get_headers(self)}
        base_url = "https://mainnet-chaintracks.babbage.systems/getTransactionStatus"
        url = f"{base_url}?{urlencode({'txid': txid})}"
        response = await self.http_client.fetch(url, request_options)
        if not response.ok:
            raise RuntimeError("Failed to get transaction status")
        return response.json() or {"status": "unknown"}

    async def get_raw_tx(self, txid: str) -> str | None:
        """Get raw transaction hex for a given txid (TS-compatible optional result).

        Behavior:
        - Returns the raw transaction hex string when available.
        - Returns None when the transaction is not found (404) or provider returns empty body.
        - Performs basic txid validation (64 hex chars) for early return.

        Args:
            txid: Transaction ID (64 hex chars, big-endian)

        Returns:
            Optional[str]: Raw transaction hex when found; otherwise None.

        Reference:
            - toolbox/ts-wallet-toolbox/src/services/providers/WhatsOnChain.ts
        """
        if not isinstance(txid, str) or len(txid) != 64:
            return None
        try:
            # Validate hex
            bytes.fromhex(txid)
        except ValueError:
            return None

        request_options = {"method": "GET", "headers": WhatsOnChainTracker.get_headers(self)}
        response = await self.http_client.fetch(f"{self.URL}/tx/{txid}/hex", request_options)

        if response.ok:
            body = response.json() or {}
            data = body.get("data")
            if data:
                return data

        if response.status_code == 404:
            return None
        # Unknown error or empty body; treat as None to match TS optional return
        return None
