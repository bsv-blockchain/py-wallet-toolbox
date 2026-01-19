"""Manual tests for ChaintracksClientApi.

This module tests the Chaintracks client API interface with JSON-RPC server.

Note: These tests require starting a local ChaintracksService JSON-RPC server
      and are therefore classified as manual tests.

Reference: wallet-toolbox/src/services/chaintracker/chaintracks/__tests/ChaintracksClientApi.test.ts
"""

from typing import TYPE_CHECKING, Any

import pytest

# Tests for ChaintracksClientApi implementation

if TYPE_CHECKING:
    from bsv_wallet_toolbox.services.chaintracker.chaintracks.api import ChaintracksClientApi

try:
    from bsv_wallet_toolbox.services.chaintracker import ChaintracksService
    from bsv_wallet_toolbox.services.chaintracker.chaintracks import Chaintracks
    from bsv_wallet_toolbox.services.chaintracker.chaintracks.api import BaseBlockHeader, ChaintracksClientApi
    from bsv_wallet_toolbox.services.chaintracker.chaintracks.options import create_default_no_db_chaintracks_options
    from bsv_wallet_toolbox.services.chaintracker.chaintracks.util import (
        block_hash,
        deserialize_base_block_headers,
        genesis_buffer,
        serialize_base_block_header,
    )
    from bsv_wallet_toolbox.services.wallet_services import Chain

    IMPORTS_AVAILABLE = True
except ImportError:
    IMPORTS_AVAILABLE = False
    Chaintracks = None
    create_default_no_db_chaintracks_options = None
    ChaintracksService = None
    ChaintracksClientApi = None
    BaseBlockHeader = None
    Chain = str


class TestChaintracksClientApi:
    """Test suite for ChaintracksClientApi.

    Reference: wallet-toolbox/src/services/chaintracker/chaintracks/__tests/ChaintracksClientApi.test.ts
               describe('ChaintracksClientApi tests')
    """

    @pytest.fixture(scope="function")
    async def setup_clients(self):
        """Setup test clients.

        Reference: wallet-toolbox/src/services/chaintracker/chaintracks/__tests/ChaintracksClientApi.test.ts
                   beforeAll()
        """
        chain: Chain = "main"
        clients = []

        # Create local Chaintracks instance
        chaintracks_options = create_default_no_db_chaintracks_options(chain)
        chaintracks = Chaintracks(chaintracks_options)
        chaintracks.make_available()

        clients.append({"client": chaintracks, "chain": chain})

        # Find first tip for reference
        first_tip = await chaintracks.find_chain_tip_header()

        yield {"clients": clients, "firstTip": first_tip, "chaintracks": chaintracks}

        # No cleanup needed for in-memory instance

    async def test_getchain(self, setup_clients) -> None:
        """Given: ChaintracksClientApi clients
           When: Call getChain
           Then: Returns expected chain

        Reference: wallet-toolbox/src/services/chaintracker/chaintracks/__tests/ChaintracksClientApi.test.ts
                   test('0 getChain')
        """
        # Given
        clients = setup_clients["clients"]

        # When/Then
        for client_info in clients:
            client = client_info["client"]
            chain = client_info["chain"]
            got_chain = await client.get_chain()
            assert got_chain == chain

    async def test_getinfo(self, setup_clients) -> None:
        """Given: ChaintracksClientApi clients
           When: Call getInfo
           Then: Returns info with chain, heightBulk > 700000, and recent heightLive

        Reference: wallet-toolbox/src/services/chaintracker/chaintracks/__tests/ChaintracksClientApi.test.ts
                   test('1 getInfo')
        """
        # Given
        clients = setup_clients["clients"]
        first_tip = setup_clients["firstTip"]

        # When/Then
        for client_info in clients:
            client = client_info["client"]
            chain = client_info["chain"]
            got_info = await client.get_info()
            assert got_info["chain"] == chain
            assert got_info["heightBulk"] > 700000
            assert got_info["heightLive"] >= first_tip["height"] - 2

    async def test_getpresentheight(self, setup_clients) -> None:
        """Given: ChaintracksClientApi clients
           When: Call getPresentHeight
           Then: Returns height >= firstTip.height - 2

        Reference: wallet-toolbox/src/services/chaintracker/chaintracks/__tests/ChaintracksClientApi.test.ts
                   test('2 getPresentHeight')
        """
        # Given
        clients = setup_clients["clients"]
        first_tip = setup_clients["firstTip"]

        # When/Then
        for client_info in clients:
            client = client_info["client"]
            present_height = await client.get_present_height()
            assert present_height >= first_tip["height"] - 2

    async def test_getheaders(self, setup_clients) -> None:
        """Given: ChaintracksClientApi clients
           When: Call getHeaders for various height ranges
           Then: Returns correct number of headers with proper chaining

        Reference: wallet-toolbox/src/services/chaintracker/chaintracks/__tests/ChaintracksClientApi.test.ts
                   test('3 getHeaders')
        """
        # Given
        clients = setup_clients["clients"]

        # When/Then
        for client_info in clients:
            client = client_info["client"]
            info = await client.get_info()
            h0 = info["heightBulk"] + 1
            h1 = info["heightLive"] or 10

            # Test bulk headers
            bulk_headers = await self._get_headers(client, h0 - 2, 2)
            assert len(bulk_headers) == 2
            assert bulk_headers[1]["previousHash"] == block_hash(serialize_base_block_header(bulk_headers[0]))

            # Test both bulk and live headers
            both_headers = await self._get_headers(client, h0 - 1, 2)
            assert len(both_headers) >= 1  # At least 1 header
            if len(both_headers) > 1:
                assert both_headers[1]["previousHash"] == block_hash(serialize_base_block_header(both_headers[0]))

            # Test live headers
            live_headers = await self._get_headers(client, h0, 2)
            assert len(live_headers) >= 1  # At least 1 header
            if len(live_headers) > 1:
                assert live_headers[1]["previousHash"] == block_hash(serialize_base_block_header(live_headers[0]))

            # Test partial headers
            part_headers = await self._get_headers(client, h1, 2)
            assert len(part_headers) >= 1  # At least 1 header

    async def _get_headers(self, client: Any, h: int, c: int) -> list[Any]:
        """Helper to get and deserialize headers."""
        data = await client.get_headers(h, c)
        headers = deserialize_base_block_headers(bytes.fromhex(data))
        return headers

    async def test_findchaintipheader(self, setup_clients) -> None:
        """Given: ChaintracksClientApi clients
           When: Call findChainTipHeader
           Then: Returns tip header with height >= firstTip.height

        Reference: wallet-toolbox/src/services/chaintracker/chaintracks/__tests/ChaintracksClientApi.test.ts
                   test('4 findChainTipHeader')
        """
        # Given
        clients = setup_clients["clients"]
        first_tip = setup_clients["firstTip"]

        # When/Then
        for client_info in clients:
            client = client_info["client"]
            tip_header = await client.find_chain_tip_header()
            assert tip_header["height"] >= first_tip["height"]

    async def test_findchaintiphash(self, setup_clients) -> None:
        """Given: ChaintracksClientApi clients
           When: Call findChainTipHash
           Then: Returns 64-character hash string

        Reference: wallet-toolbox/src/services/chaintracker/chaintracks/__tests/ChaintracksClientApi.test.ts
                   test('5 findChainTipHash')
        """
        # Given
        clients = setup_clients["clients"]

        # When/Then
        for client_info in clients:
            client = client_info["client"]
            hash_str = await client.find_chain_tip_hash()
            assert len(hash_str) == 64

    async def test_findheaderforheight(self, setup_clients) -> None:
        """Given: ChaintracksClientApi clients
           When: Call findHeaderForHeight for genesis, tip, and missing height
           Then: Returns correct headers or None for missing

        Reference: wallet-toolbox/src/services/chaintracker/chaintracks/__tests/ChaintracksClientApi.test.ts
                   test('6 findHeaderForHeight')
        """
        # Given
        clients = setup_clients["clients"]
        first_tip = setup_clients["firstTip"]

        # When/Then
        for client_info in clients:
            client = client_info["client"]
            chain = client_info["chain"]

            # Test genesis block
            header0 = await client.find_header_for_height(0)
            assert header0 is not None
            if header0:
                assert genesis_buffer(chain) == serialize_base_block_header(header0)

            # Test tip height
            header = await client.find_header_for_height(first_tip["height"])
            assert header is not None and header["height"] == first_tip["height"]

            # Test missing height
            missing = await client.find_header_for_height(99999999)
            assert missing is None

    async def test_addheader(self, setup_clients) -> None:
        """Given: ChaintracksClientApi clients
           When: Call addHeader with chain tip header data
           Then: Successfully adds header

        Reference: wallet-toolbox/src/services/chaintracker/chaintracks/__tests/ChaintracksClientApi.test.ts
                   test('7 addHeader')
        """
        # Given
        clients = setup_clients["clients"]

        # When/Then
        for client_info in clients:
            client = client_info["client"]
            t = await client.find_chain_tip_header()
            h: BaseBlockHeader = {
                "version": t["version"],
                "previousHash": t["previousHash"],
                "merkleRoot": t["merkleRoot"],
                "time": t["time"],
                "bits": t["bits"],
                "nonce": t["nonce"],
            }
            await client.add_header(h)

    async def test_subscribeheaders(self, setup_clients) -> None:
        """Given: ChaintracksClientApi clients
           When: Call subscribeHeaders with header listener
           Then: Returns subscription ID string and can unsubscribe

        Reference: wallet-toolbox/src/services/chaintracker/chaintracks/__tests/ChaintracksClientApi.test.ts
                   test('subscribeHeaders') (commented out in TS)

        Note: TypeScript has this test commented out, but we implement it for completeness.
        """
        # Given
        clients = setup_clients["clients"]

        # When/Then
        for client_info in clients:
            client = client_info["client"]
            headers = []

            def header_listener(header) -> None:
                headers.append(header)

            subscription_id = await client.subscribe_headers(header_listener)
            assert isinstance(subscription_id, str)
            assert await client.unsubscribe(subscription_id) is True

    async def test_subscribereorgs(self, setup_clients) -> None:
        """Given: ChaintracksClientApi clients
           When: Call subscribeReorgs with reorg listener
           Then: Returns subscription ID string and can unsubscribe

        Reference: wallet-toolbox/src/services/chaintracker/chaintracks/__tests/ChaintracksClientApi.test.ts
                   test('subscribeReorgs') (commented out in TS)

        Note: TypeScript has this test commented out, but we implement it for completeness.
        """
        # Given
        clients = setup_clients["clients"]

        # When/Then
        for client_info in clients:
            client = client_info["client"]
            reorgs = []

            def reorg_listener(depth, old_tip, new_tip) -> None:
                reorgs.append({"depth": depth, "oldTip": old_tip, "newTip": new_tip})

            subscription_id = await client.subscribe_reorgs(reorg_listener)
            assert isinstance(subscription_id, str)
            assert await client.unsubscribe(subscription_id) is True
