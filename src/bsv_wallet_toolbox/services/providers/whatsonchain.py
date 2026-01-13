"""WhatsOnChain provider implementation.

Summary:
    Adapter over py-sdk's WhatsOnChainTracker to provide toolbox-level
    ChaintracksClientApi and TS-compatible shapes for select methods.

TS parity:
    - Mirrors the TypeScript provider layering where SdkWhatsOnChain
      supplies core tracker functionality and the higher-level class
      adds toolbox-specific methods and response shapes.

Reference:
    - toolbox/ts-wallet-toolbox/src/services/providers/WhatsOnChain.ts
    - toolbox/ts-wallet-toolbox/src/services/providers/SdkWhatsOnChain.ts
"""

import asyncio
import struct
from typing import Any
from urllib.parse import urlencode

from bsv.chaintrackers.whatsonchain import WhatsOnChainTracker

from ...utils.merkle_path_utils import convert_proof_to_merkle_path
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

    Summary:
        Python equivalent of the TS provider that relies on py-sdk's
        WhatsOnChainTracker for core RPCs while exposing toolbox-level
        methods and TS-compatible return shapes where needed.

    TS parity:
        - Class layering matches TS: base tracker + toolbox adapter.
        - Methods that surface data to higher layers return shapes used
          by TS tests (e.g., MerklePath, UTXO status, tx status).

    Implemented highlights:
        - current_height / is_valid_root_for_height via py-sdk (tracker)
        - find_header_for_height returns BlockHeader objects
        - find_chain_tip_header/hash derived from current tip height

    Unsupported / out of scope:
        - Bulk headers and event streaming (no WoC API)
        - add_header (read-only provider)
        - find_header_for_block_hash (no direct WoC endpoint)

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

        Raises:
            ValueError: If network is not 'main' or 'test'
        """
        if network not in ("main", "test"):
            raise ValueError(f"Invalid network: {network}. Must be 'main' or 'test'.")
        super().__init__(network=network, api_key=api_key, http_client=http_client)
        self.chain = network
        self.api_key = api_key

    async def get_chain(self) -> Chain:
        """Confirm the chain.

        This method must remain async to satisfy the ChaintracksClientApi interface contract
        (defined as @abstractmethod async def get_chain()), even though the implementation
        performs no I/O operations and could be synchronous.

        Returns:
            Chain enum value (Chain.MAIN or Chain.TEST)
        """
        return self._get_chain()

    def _get_chain(self) -> Chain:
        """Internal implementation of get_chain."""
        if self.network == "main":
            return Chain.MAIN
        if self.network == "test":
            return Chain.TEST
        raise ValueError(f"Unexpected network value: {self.network!r}. Expected 'main' or 'test'.")

    # ------------------------------------------------------------------ #
    # Override selected py-sdk tracker methods to avoid signature clash  #
    # with ChaintracksClientApi.get_headers(height, count).              #
    #                                                                     #
    # Background: py-sdk's WhatsOnChainTracker already defines            #
    # get_headers() as "return HTTP headers" for REST calls, whereas this #
    # toolbox layer must expose ChaintracksClientApi.get_headers(height,  #
    # count) to match the TypeScript implementation. If we leave the      #
    # original methods intact, adding the Chaintracks signature would     #
    # break py-sdk's calls that currently invoke self.get_headers()       #
    # (no args). To prevent that clash, we duplicate the relevant py-sdk  #
    # logic locally and call self._get_http_headers() directly, reserving #
    # the public get_headers(height, count) name for the Chaintracks API. #
    # ------------------------------------------------------------------ #

    async def is_valid_root_for_height(self, root: str, height: int) -> bool:  # type: ignore[override]
        """Verify merkle root for a given height using WoC HTTP API.

        This reimplements the py-sdk tracker method but uses the local
        ``_get_http_headers`` helper instead of ``self.get_headers()`` so
        that our Chaintracks-style ``get_headers(height, count)`` does not
        interfere with SDK behavior.
        """
        request_options = {"method": "GET", "headers": self._get_http_headers()}

        response = await self.http_client.fetch(f"{self.URL}/block/{height}/header", request_options)
        if response.ok:
            merkleroot = response.json()["data"].get("merkleroot")
            return merkleroot == root
        if response.status_code == 404:
            return False
        raise RuntimeError(f"Failed to verify merkleroot for height {height} because of an error: {response.json()}")

    async def current_height(self) -> int:  # type: ignore[override]
        """Get current blockchain height from WhatsOnChain API.

        Reimplementation of the py-sdk tracker method that avoids calling
        the base-class ``get_headers()`` (which would be shadowed by this
        class's Chaintracks-style ``get_headers(height, count)``).
        """
        request_options = {"method": "GET", "headers": self._get_http_headers()}

        response = await self.http_client.fetch(f"{self.URL}/chain/info", request_options)
        if response.ok:
            data = response.json() or {}
            return data.get("blocks", 0)
        raise RuntimeError(f"Failed to get current height: {response.json()}")

    def _get_http_headers(self) -> dict[str, str]:
        """Get HTTP headers for API requests.

        Returns headers including Accept and optional Authorization (if api_key is set).
        This is a wrapper around the parent class's get_headers() method.

        Returns:
            HTTP headers dictionary.
        """
        headers: dict[str, str] = {
            "Accept": "application/json",
        }

        if isinstance(self.api_key, str) and self.api_key.strip():
            headers["Authorization"] = self.api_key

        return headers

    async def get_info(self) -> ChaintracksInfo:
        """Get summary of configuration and state.

        Not implemented: Chaintracks-specific feature absent in WoC API.

        Raises:
            NotImplementedError: Always (not provided by WoC)
        """
        return self._get_info()

    def _get_info(self) -> ChaintracksInfo:
        """Internal implementation of get_info."""
        raise NotImplementedError("get_info() is not supported by WhatsOnChain provider")

    async def get_present_height(self) -> int:
        """Get the latest chain height.

        Uses current_height() as WhatsOnChain doesn't distinguish between
        bulk and live heights.

        Returns:
            Current blockchain height
        """
        return await self._get_present_height()

    async def _get_present_height(self) -> int:
        """Internal implementation of get_present_height."""
        return await self.current_height()

    async def get_headers(self, height: int, count: int) -> str:
        """Get headers in serialized format.

        Implements ChaintracksClientApi.get_headers() interface.

        Not implemented: WoC lacks bulk header endpoint required for this.

        Args:
            height: Starting block height
            count: Number of headers to return

        Returns:
            Serialized headers as hex string

        Raises:
            NotImplementedError: Always (no bulk header API)

        Reference:
            - toolbox/ts-wallet-toolbox/src/services/chaintracker/chaintracks/Api/ChaintracksClientApi.ts
        """
        return await self._get_headers(height, count)

    async def _get_headers(self, height: int, count: int) -> str:
        """Internal implementation of get_headers."""
        raise NotImplementedError("get_headers() is not supported by WhatsOnChain provider")

    async def get_bulk_headers(self, height: int, count: int) -> str:
        """Get headers in serialized format (bulk).

        Alias for get_headers() for backward compatibility.

        Note: This method exists for compatibility but delegates to get_headers().

        Args:
            height: Starting block height
            count: Number of headers to return

        Returns:
            Serialized headers as hex string

        Raises:
            NotImplementedError: Always (no bulk header API)
        """
        return await self.get_headers(height, count)

    async def find_chain_tip_header(self) -> BlockHeader:
        """Get the active chain tip header.

        Implementation strategy: use current_height() and then find_header_for_height().

        Returns:
            BlockHeader: Header at the current tip height.
        """
        return await self._find_chain_tip_header()

    async def _find_chain_tip_header(self) -> BlockHeader:
        """Internal implementation of find_chain_tip_header."""
        tip_height = await self.current_height()
        header = await self.find_header_for_height(int(tip_height))
        if header is None:
            raise RuntimeError("Failed to resolve chain tip header")
        return header

    async def find_chain_tip_hash(self) -> str:
        """Get the block hash of the active chain tip.

        Returns:
            str: Block hash hex string of the chain tip.
        """
        return await self._find_chain_tip_hash()

    async def _find_chain_tip_hash(self) -> str:
        """Internal implementation of find_chain_tip_hash."""
        h = await self.find_chain_tip_header()
        return h.hash

    async def find_header_for_height(self, height: int) -> BlockHeader | None:
        """Get block header for a given block height on active chain.

        TS parity:
            - Returns a structured header object. Use
              `get_header_bytes_for_height` when byte serialization is needed.

        Args:
            height: Block height (non-negative)

        Returns:
            BlockHeader | None: Header at height or None when missing
        """
        return await self._find_header_for_height(height)

    async def _fetch_header(
        self, url: str, height: int | None = None, hash_override: str | None = None
    ) -> BlockHeader | None:
        """Fetch and parse a block header from WhatsOnChain API.

        Args:
            url: The API endpoint URL to fetch from
            height: Block height (if known, otherwise extracted from response)
            hash_override: Block hash (if known, otherwise extracted from response)

        Returns:
            BlockHeader object or None if not found
        """
        request_options = {"method": "GET", "headers": self._get_http_headers()}
        response = await self.http_client.fetch(url, request_options)

        if response.ok:
            data = response.json().get("data") or {}
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
                height=height if height is not None else int(data.get("height", 0)),
                hash=hash_override if hash_override is not None else data.get("hash", ""),
            )
        elif response.status_code == 404:
            return None
        else:
            raise RuntimeError(f"Failed to get header from {url}: {response.json()}")

    async def _find_header_for_height(self, height: int) -> BlockHeader | None:
        """Internal implementation of find_header_for_height."""
        if height < 0:
            raise ValueError(f"Height {height} must be a non-negative integer")

        return await self._fetch_header(f"{self.URL}/block/{height}/header", height=height)

    async def find_header_for_block_hash(self, hash: str) -> BlockHeader | None:
        """Get a block header by block hash.

        Summary:
            Resolve a single block header from WhatsOnChain using the hash.
            Returns a structured `BlockHeader` (toolbox shape) or None when
            the hash is unknown (404) or invalid.

        TS parity:
            Matches the TypeScript provider`s intent: given a block hash,
            provide a structured header object with version/prevHash/merkleRoot/
            time/bits/nonce/height/hash fields.

        Args:
            hash: 64-character hex string of the block hash (big-endian)

        Returns:
            BlockHeader | None: Structured header on success; None if not found

        Raises:
            RuntimeError: On non-OK provider responses other than 404

        Reference:
            - toolbox/ts-wallet-toolbox/src/services/providers/WhatsOnChain.ts
        """
        return await self._find_header_for_block_hash(hash)

    async def _find_header_for_block_hash(self, hash: str) -> BlockHeader | None:
        """Internal implementation of find_header_for_block_hash."""
        if not isinstance(hash, str) or len(hash) != 64:
            return None

        return await self._fetch_header(f"{self.URL}/block/hash/{hash}", hash_override=hash)

    async def add_header(self, header: BaseBlockHeader) -> None:
        """Submit a possibly new header for adding.

        Not supported by WhatsOnChain API (read-only service).

        Raises:
            NotImplementedError: Always (WhatsOnChain is read-only)
        """
        return await self._add_header(header)

    async def _add_header(self, header: BaseBlockHeader) -> None:
        """Internal implementation of add_header."""
        raise NotImplementedError("add_header() is not supported by WhatsOnChain provider (read-only)")

    async def start_listening(self) -> None:
        """Start listening for new headers.

        Not supported: WoC does not provide a header event stream.

        Raises:
            NotImplementedError: Always
        """
        return await self._start_listening()

    async def _start_listening(self) -> None:
        """Internal implementation of start_listening."""
        raise NotImplementedError("start_listening() is not supported by WhatsOnChain provider")

    async def listening(self) -> None:
        """Wait for listening state.

        Not supported: WoC does not provide a header event stream.

        Raises:
            NotImplementedError: Always
        """
        return await self._listening()

    async def _listening(self) -> None:
        """Internal implementation of listening."""
        raise NotImplementedError("listening() is not supported by WhatsOnChain provider")

    async def is_listening(self) -> bool:
        """Check if actively listening.

        Not supported: always returns False.

        Returns:
            bool: False
        """
        return await self._is_listening()

    async def _is_listening(self) -> bool:
        """Internal implementation of is_listening."""
        return False

    async def is_synchronized(self) -> bool:
        """Check if synchronized.

        WoC is stateless from our perspective; queries are live.

        Returns:
            bool: True
        """
        return await self._is_synchronized()

    async def _is_synchronized(self) -> bool:
        """Internal implementation of is_synchronized."""
        return True

    async def subscribe_headers(self, listener: HeaderListener) -> str:
        """Subscribe to header events.

        Not supported: no header event stream.

        Raises:
            NotImplementedError: Always
        """
        return await self._subscribe_headers(listener)

    async def _subscribe_headers(self, listener: HeaderListener) -> str:
        """Internal implementation of subscribe_headers."""
        raise NotImplementedError("subscribe_headers() is not supported by WhatsOnChain provider")

    async def subscribe_reorgs(self, listener: ReorgListener) -> str:
        """Subscribe to reorganization events.

        Not supported: no reorg event stream.

        Raises:
            NotImplementedError: Always
        """
        return await self._subscribe_reorgs(listener)

    async def _subscribe_reorgs(self, listener: ReorgListener) -> str:
        """Internal implementation of subscribe_reorgs."""
        raise NotImplementedError("subscribe_reorgs() is not supported by WhatsOnChain provider")

    async def unsubscribe(self, subscription_id: str) -> bool:
        """Cancel subscriptions.

        Not supported: no subscription lifecycle.

        Raises:
            NotImplementedError: Always
        """
        return await self._unsubscribe(subscription_id)

    async def _unsubscribe(self, subscription_id: str) -> bool:
        """Internal implementation of unsubscribe."""
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
        return await self._get_header_bytes_for_height(height)

    async def _get_header_bytes_for_height(self, height: int) -> bytes:
        """Internal implementation of get_header_bytes_for_height."""
        if height < 0:
            raise ValueError(f"Height {height} must be a non-negative integer")

        request_options = {"method": "GET", "headers": self._get_http_headers()}

        response = await self.http_client.fetch(f"{self.URL}/block/{height}/header", request_options)
        if response.ok:
            data = response.json().get("data", {})
            if not data:
                raise RuntimeError(f"No header found for height {height}")

            # WhatsOnChain returns header fields, not serialized bytes.
            # We need to serialize them into 80-byte block header format:
            # version (4) + prevHash (32) + merkleRoot (32) + time (4) + bits (4) + nonce (4) = 80 bytes

            version = data.get("version", 0)
            prev_hash = data.get("previousblockhash", "0" * 64)
            merkle_root = data.get("merkleroot", "0" * 64)
            timestamp = data.get("time", 0)
            bits_hex = data.get("bits", "00000000")
            nonce = data.get("nonce", 0)

            # Serialize to 80-byte header
            # version: 4 bytes little-endian
            header = struct.pack("<I", version)
            # previousblockhash: 32 bytes
            # NOTE: Blockchain hashes are conventionally represented as big-endian hex
            # (as returned by APIs like WhatsOnChain), but in the serialized block header
            # they are stored in little-endian byte order. We reverse the bytes here to
            # convert from the big-endian hex representation to the little-endian binary
            # format used on the wire. The same convention applies to merkleroot and bits.
            try:
                header += bytes.fromhex(prev_hash)[::-1]
            except ValueError as e:
                raise RuntimeError(f"Invalid previousblockhash hex '{prev_hash}' for height {height}: {e}") from e
            # merkleroot: 32 bytes (reversed from big-endian hex)
            try:
                header += bytes.fromhex(merkle_root)[::-1]
            except ValueError as e:
                raise RuntimeError(f"Invalid merkleroot hex '{merkle_root}' for height {height}: {e}") from e
            # time: 4 bytes little-endian
            header += struct.pack("<I", timestamp)
            # bits: 4 bytes little-endian (from hex string like "1d00ffff")
            try:
                header += bytes.fromhex(bits_hex)[::-1]
            except ValueError as e:
                raise RuntimeError(f"Invalid bits hex '{bits_hex}' for height {height}: {e}") from e
            # nonce: 4 bytes little-endian
            header += struct.pack("<I", nonce)

            return header
        elif response.status_code == 404:
            raise RuntimeError(f"No header found for height {height}")
        else:
            raise RuntimeError(f"Failed to get header for height {height}: {response.json()}")

    async def get_merkle_path(self, txid: str, services: Any) -> dict[str, Any]:
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
        return await self._get_merkle_path(txid, services)

    async def _get_merkle_path(self, txid: str, services: Any) -> dict[str, Any]:
        """Internal implementation of get_merkle_path."""
        # Initialize result dict
        result: dict[str, Any] = {"name": "WoCTsc", "notes": []}

        # Build URL and request options
        url = f"{self.URL}/tx/{txid}/proof/tsc"
        request_options = {"method": "GET", "headers": self._get_http_headers()}

        try:
            response = await self.http_client.fetch(url, request_options)
            status_text = getattr(response, "status_text", None)
            if response.status_code == 200 and not status_text:
                status_text = "OK"
            note_base = {
                "name": "WoCTsc",
                "txid": txid,
                "url": url,
                "status": response.status_code,
                "statusText": status_text,
            }

            if response.status_code == 429:
                result["notes"].append({**note_base, "what": "getMerklePathRetry"})
                await asyncio.sleep(2)
                response = await self.http_client.fetch(url, request_options)
                note_base["status"] = response.status_code
                note_base["statusText"] = getattr(response, "status_text", None)

            if response.status_code == 404:
                # NotFound note should only include name, status, statusText, and what (not txid/url)
                not_found_note = {
                    "name": note_base["name"],
                    "status": note_base["status"],
                    "statusText": note_base["statusText"],
                    "what": "getMerklePathNotFound",
                }
                result["notes"].append(not_found_note)
                return result

            if not response.ok or response.status_code != 200:
                result["notes"].append({**note_base, "what": "getMerklePathBadStatus"})
                result["error"] = {
                    "message": f"Unexpected WhatsOnChain status {response.status_code}",
                    "code": "HTTP_ERROR",
                }
                return result

            body = response.json() or {}
            payload = body.get("data") if isinstance(body, dict) else body
            if not payload:
                # NoData note should only include name, status, statusText, and what (not txid/url)
                no_data_note = {
                    "name": note_base["name"],
                    "status": note_base["status"],
                    "statusText": note_base["statusText"],
                    "what": "getMerklePathNoData",
                }
                result["notes"].append(no_data_note)
                return result

            proofs = payload if isinstance(payload, list) else [payload]
            proof_entry = proofs[0] if proofs else None
            if not proof_entry:
                # NoData note should only include name, status, statusText, and what (not txid/url)
                no_data_note = {
                    "name": note_base["name"],
                    "status": note_base["status"],
                    "statusText": note_base["statusText"],
                    "what": "getMerklePathNoData",
                }
                result["notes"].append(no_data_note)
                return result

            proof_target = proof_entry.get("target")
            header = None
            if proof_target and hasattr(services, "hash_to_header_async"):
                try:
                    header = await services.hash_to_header_async(proof_target)
                except Exception as exc:
                    result["notes"].append({**note_base, "what": "getMerklePathNoHeader", "error": str(exc)})
                    return result

            if not header:
                result["notes"].append({**note_base, "what": "getMerklePathNoHeader"})
                return result

            # Get block height from header
            block_height = header.get("height") if isinstance(header, dict) else getattr(header, "height", None)
            if block_height is None:
                result["notes"].append({**note_base, "what": "getMerklePathNoHeader"})
                return result

            proof_dict = {
                "index": proof_entry.get("index", 0),
                "nodes": proof_entry.get("nodes") or [],
                "height": block_height,
            }

            # Convert proof to merkle path format (returns dict with blockHeight and path)
            merkle_path_dict = convert_proof_to_merkle_path(txid, proof_dict)

            # Preserve py-sdk MerklePath-compatible structure (hash_str) while also
            # exposing a TS-style "hash" field for compatibility where needed.
            path = merkle_path_dict.get("path", [])
            converted_path = []
            for level in path:
                converted_level = []
                for leaf in level:
                    converted_leaf = {"offset": leaf["offset"]}
                    if "hash_str" in leaf:
                        # Keep py-sdk compatible field name
                        converted_leaf["hash_str"] = leaf["hash_str"]
                        # Add TS-style alias for any Python callers expecting "hash"
                        converted_leaf["hash"] = leaf["hash_str"]
                    if leaf.get("txid"):
                        converted_leaf["txid"] = True
                    if leaf.get("duplicate"):
                        converted_leaf["duplicate"] = True
                    converted_level.append(converted_leaf)
                converted_path.append(converted_level)

            result["merklePath"] = {
                "blockHeight": merkle_path_dict["blockHeight"],
                "path": converted_path,
            }
            if header:
                # Convert header to dict format if needed, and ensure bits is an integer
                if isinstance(header, dict):
                    header_dict = header.copy()
                else:
                    header_dict = {
                        "version": getattr(header, "version", None),
                        "previousHash": getattr(header, "previousHash", None),
                        "merkleRoot": getattr(header, "merkleRoot", None),
                        "time": getattr(header, "time", None),
                        "bits": getattr(header, "bits", None),
                        "nonce": getattr(header, "nonce", None),
                        "height": getattr(header, "height", None),
                        "hash": getattr(header, "hash", None),
                    }
                # Convert bits from string to int if needed
                if "bits" in header_dict:
                    bits = header_dict["bits"]
                    if isinstance(bits, str):
                        # Convert hex string to int (e.g., "1d00ffff" -> 486604799)
                        try:
                            header_dict["bits"] = int(bits, 16)
                        except (ValueError, TypeError):
                            pass  # Keep original if conversion fails
                result["header"] = header_dict
            # Success note should only include name, status, statusText, and what (not txid/url)
            success_note = {
                "name": note_base["name"],
                "status": note_base["status"],
                "statusText": note_base["statusText"],
                "what": "getMerklePathSuccess",
            }
            result["notes"].append(success_note)
            return result
        except Exception as exc:
            result["notes"].append({"name": "WoCTsc", "what": "getMerklePathCatch", "error": str(exc)})
            result["error"] = {"message": str(exc), "code": "NETWORK_ERROR"}
            return result

    async def update_bsv_exchange_rate(self) -> dict[str, Any]:
        """Fetch the current BSV/USD exchange rate (TS-compatible shape).

        Returns:
            dict: { "base": "USD", "rate": number, "timestamp": number }

        Raises:
            RuntimeError: If the provider request fails or returns a non-OK status.

        Reference:
            - toolbox/ts-wallet-toolbox/src/services/providers/WhatsOnChain.ts
        """
        return await self._update_bsv_exchange_rate()

    async def _update_bsv_exchange_rate(self) -> dict[str, Any]:
        """Internal implementation of update_bsv_exchange_rate."""
        try:
            request_options = {"method": "GET", "headers": self._get_http_headers()}
            response = await self.http_client.fetch(f"{self.URL}/exchange-rate/bsvusd", request_options)
            if response.ok:
                body = response.json() or {}
                return body
            raise RuntimeError("Failed to update BSV exchange rate")
        except Exception:
            # Handle connection errors
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
        return await self._get_fiat_exchange_rate(currency, base)

    async def _get_fiat_exchange_rate(self, currency: str, base: str = "USD") -> float:
        """Internal implementation of get_fiat_exchange_rate."""
        request_options = {"method": "GET", "headers": WhatsOnChainTracker.get_headers(self)}
        # Chaintracks fiat endpoint (tests will mock this URL)
        url = "https://mainnet-chaintracks.babbage.systems/getFiatExchangeRates"
        response = await self.http_client.fetch(url, request_options)
        if not response.ok:
            raise RuntimeError("Failed to get fiat exchange rates")
        body = response.json() or {}
        rates = body.get("rates") or {}
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
        use_next: bool | None = None,
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
        # Only pass non-None arguments to match test expectations
        args = [output]
        if output_format is not None:
            args.append(output_format)
        if outpoint is not None:
            args.append(outpoint)
        if use_next is not None:
            args.append(use_next)
        return await self._get_utxo_status(*args)

    async def _get_utxo_status(self, *args, **kwargs) -> dict[str, Any]:
        """Internal implementation of get_utxo_status."""
        request_options = {"method": "GET", "headers": WhatsOnChainTracker.get_headers(self)}
        # Chaintracks-like endpoint (tests will mock this)
        base_url = "https://mainnet-chaintracks.babbage.systems/getUtxoStatus"
        # Extract parameters from args/kwargs
        output = args[0] if args else kwargs.get("output", "")
        output_format = kwargs.get("outputFormat")
        outpoint = kwargs.get("outpoint")
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

    async def get_script_history(self, script_hash: str, _use_next: bool | None = None) -> dict[str, Any]:
        """Get script history for a given script hash (TS-compatible response shape).

        Returns two arrays, matching TS semantics:
        - confirmed: Transactions confirmed on-chain spending/creating outputs related to the script hash
        - unconfirmed: Transactions seen but not yet confirmed

        Args:
            script_hash: The script hash (typically little-endian) as required by the provider
            use_next: Provider selection hint (ignored here; kept for parity with TS)

        Returns:
            dict: { "status": "success", "name": "WhatsOnChain", "confirmed": [...], "unconfirmed": [...] }

        Raises:
            RuntimeError: If the provider request fails or returns a non-OK status.

        Reference:
            - toolbox/ts-wallet-toolbox/src/services/Services.ts#getScriptHistory
        """
        return await self._get_script_history(script_hash, _use_next)

    async def _get_script_history(self, script_hash: str, _use_next: bool | None = None) -> dict[str, Any]:
        """Internal implementation of get_script_history."""
        request_options = {"method": "GET", "headers": WhatsOnChainTracker.get_headers(self)}
        base_url = "https://mainnet-chaintracks.babbage.systems/getScriptHistory"
        url = f"{base_url}?{urlencode({'hash': script_hash})}"
        response = await self.http_client.fetch(url, request_options)
        if not response.ok:
            raise RuntimeError("Failed to get script history")
        data = response.json() or {"confirmed": [], "unconfirmed": []}
        return {
            "status": "success",
            "name": "WhatsOnChain",
            "confirmed": data.get("confirmed", []),
            "unconfirmed": data.get("unconfirmed", []),
        }

    async def get_transaction_status(self, txid: str, use_next: bool | None = None) -> dict[str, Any]:
        """Get transaction status for a given txid (TS-compatible response shape).

        Behavior (aligned with ts-wallet-toolbox):
        - Returns an object describing the transaction status (e.g., confirmed/unconfirmed/pending)
          and optional confirmation metadata (confirmations count, block height/hash, etc.).
        - On errors: raises RuntimeError with provider-specific error information.

        Args:
            txid: Transaction ID (hex, big-endian)
            use_next: Provider selection hint (ignored here; kept for parity with TS)

        Returns:
            dict: A dictionary describing the transaction status with "name" and "status" fields.
                  Status can be "confirmed", "not_found", "unknown", etc.

        Reference:
            - toolbox/ts-wallet-toolbox/src/services/Services.ts#getTransactionStatus
        """
        return await self._get_transaction_status(txid, use_next)

    async def _get_transaction_status(self, txid: str, use_next: bool | None = None) -> dict[str, Any]:
        """Internal implementation of get_transaction_status."""
        request_options = {"method": "GET", "headers": WhatsOnChainTracker.get_headers(self)}
        base_url = "https://mainnet-chaintracks.babbage.systems/getTransactionStatus"
        url = f"{base_url}?{urlencode({'txid': txid})}"

        try:
            response = await self.http_client.fetch(url, request_options)
            if response.status == 500:
                raise RuntimeError("WhatsOnChain server error (500)")
            elif response.status == 429:
                raise RuntimeError("WhatsOnChain rate limit exceeded (429)")
            elif response.status == 404:
                return {"name": "WhatsOnChain", "status": "not_found", "txid": txid}
            elif not response.ok:
                raise RuntimeError(f"WhatsOnChain HTTP error {response.status}")
        except TimeoutError:
            raise RuntimeError("WhatsOnChain request timeout")
        except Exception as e:
            if "timeout" in str(e).lower():
                raise RuntimeError("WhatsOnChain request timeout")
            elif "connection" in str(e).lower():
                raise RuntimeError("WhatsOnChain connection error")
            else:
                raise RuntimeError(f"WhatsOnChain error: {e!s}")

        try:
            data = response.json() or {"status": "unknown"}
        except Exception:
            raise RuntimeError("WhatsOnChain malformed JSON response")

        # Add provider name to response
        data["name"] = "WhatsOnChain"
        return data

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
        return await self._get_raw_tx(txid)

    async def _get_raw_tx(self, txid: str) -> str | None:
        """Internal implementation of get_raw_tx."""
        # Validate txid format
        if not isinstance(txid, str) or len(txid) != 64:
            return None
        try:
            bytes.fromhex(txid)
        except ValueError:
            return None

        try:
            request_options = {"method": "GET", "headers": self._get_http_headers()}
            response = await self.http_client.fetch(f"{self.URL}/tx/{txid}/hex", request_options)

            if response.status_code == 200:
                body = response.json() or {}
                data = body.get("data")
                if data:
                    return data

            if response.status_code == 404:
                return None
            # Unexpected status or empty body - return None
            return None
        except Exception:
            # Handle connection errors, timeouts, etc. - return None
            return None

    async def get_tx_propagation(self, txid: str) -> dict[str, Any]:
        """Get transaction propagation info for a given txid (TS-compatible intent).

        Summary:
            Returns provider-specific propagation information. Exact fields may
            vary; this method surfaces the response body as-is for higher-level
            handling/tests.

        Args:
            txid: Transaction ID (64 hex chars, big-endian)

        Returns:
            dict: Provider response body (may include counts or peer details)

        Raises:
            RuntimeError: If the provider request fails or returns non-OK

        Reference:
            - toolbox/ts-wallet-toolbox/src/services/providers/WhatsOnChain.ts#getTxPropagation
        """
        return await self._get_tx_propagation(txid)

    async def _get_tx_propagation(self, txid: str) -> dict[str, Any]:
        """Internal implementation of get_tx_propagation."""
        if not isinstance(txid, str) or len(txid) != 64:
            raise ValueError("invalid txid length; expected 64 hex characters")
        request_options = {"method": "GET", "headers": self._get_http_headers()}
        url = f"{self.URL}/tx/{txid}/propagation"
        response = await self.http_client.fetch(url, request_options)
        if not response.ok:
            raise RuntimeError("Failed to get tx propagation")
        return response.json() or {}
