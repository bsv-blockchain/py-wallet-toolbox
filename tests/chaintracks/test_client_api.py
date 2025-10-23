"""Manual tests for ChaintracksClientApi.

This module tests the Chaintracks client API interface with JSON-RPC server.

Note: These tests require starting a local ChaintracksService JSON-RPC server
      and are therefore classified as manual tests.

Reference: wallet-toolbox/src/services/chaintracker/chaintracks/__tests/ChaintracksClientApi.test.ts
"""

from typing import TYPE_CHECKING, Any

import pytest

if TYPE_CHECKING:
    from bsv_wallet_toolbox.services.chaintracker.chaintracks.api import ChaintracksClientApi

try:
    from bsv_wallet_toolbox.services.chaintracker.chaintracks.util import (
        block_hash,
        deserialize_base_block_headers,
        genesis_buffer,
        serialize_base_block_header,
    )
    from bsv_wallet_toolbox.types import BaseBlockHeader, Chain

    from bsv_wallet_toolbox.services.chaintracker.chaintracks import Chaintracks, ChaintracksService
    from bsv_wallet_toolbox.services.chaintracker.chaintracks.api import ChaintracksClientApi

    IMPORTS_AVAILABLE = True
except ImportError:
    IMPORTS_AVAILABLE = False
    ChaintracksClientApi = None
    Chain = str
    BaseBlockHeader = dict


class TestChaintracksClientApi:
    """Test suite for ChaintracksClientApi.

    Reference: wallet-toolbox/src/services/chaintracker/chaintracks/__tests/ChaintracksClientApi.test.ts
               describe('ChaintracksClientApi tests')
    """

    @pytest.fixture(scope="class")
    async def setup_clients(self):
        """Setup test clients.

        Reference: wallet-toolbox/src/services/chaintracker/chaintracks/__tests/ChaintracksClientApi.test.ts
                   beforeAll()
        """
        chain: Chain = "main"
        clients = []

        # Create local Chaintracks instance
        local_service = ChaintracksService(ChaintracksService.create_chaintracks_service_options(chain))
        await local_service.start_json_rpc_server()

        clients.append({"client": local_service.chaintracks, "chain": chain})

        # Find first tip for reference
        first_tip = await local_service.chaintracks.find_chain_tip_header()

        yield {"clients": clients, "first_tip": first_tip, "local_service": local_service}

        # Cleanup
        await local_service.stop_json_rpc_server()

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Waiting for ChaintracksClientApi implementation")
    @pytest.mark.asyncio
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

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Waiting for ChaintracksClientApi implementation")
    @pytest.mark.asyncio
    async def test_getinfo(self, setup_clients) -> None:
        """Given: ChaintracksClientApi clients
           When: Call getInfo
           Then: Returns info with chain, heightBulk > 700000, and recent heightLive

        Reference: wallet-toolbox/src/services/chaintracker/chaintracks/__tests/ChaintracksClientApi.test.ts
                   test('1 getInfo')
        """
        # Given
        clients = setup_clients["clients"]
        first_tip = setup_clients["first_tip"]

        # When/Then
        for client_info in clients:
            client = client_info["client"]
            chain = client_info["chain"]
            got_info = await client.get_info()
            assert got_info.chain == chain
            assert got_info.height_bulk > 700000
            assert got_info.height_live >= first_tip.height - 2

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Waiting for ChaintracksClientApi implementation")
    @pytest.mark.asyncio
    async def test_getpresentheight(self, setup_clients) -> None:
        """Given: ChaintracksClientApi clients
           When: Call getPresentHeight
           Then: Returns height >= firstTip.height - 2

        Reference: wallet-toolbox/src/services/chaintracker/chaintracks/__tests/ChaintracksClientApi.test.ts
                   test('2 getPresentHeight')
        """
        # Given
        clients = setup_clients["clients"]
        first_tip = setup_clients["first_tip"]

        # When/Then
        for client_info in clients:
            client = client_info["client"]
            present_height = await client.get_present_height()
            assert present_height >= first_tip.height - 2

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Waiting for ChaintracksClientApi implementation")
    @pytest.mark.asyncio
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
            h0 = info.height_bulk + 1
            h1 = info.height_live or 10

            # Test bulk headers
            bulk_headers = await self._get_headers(client, h0 - 2, 2)
            assert len(bulk_headers) == 2
            assert bulk_headers[1].previous_hash == block_hash(bulk_headers[0])

            # Test both bulk and live headers
            both_headers = await self._get_headers(client, h0 - 1, 2)
            assert len(both_headers) == 2
            assert both_headers[1].previous_hash == block_hash(both_headers[0])

            # Test live headers
            live_headers = await self._get_headers(client, h0, 2)
            assert len(live_headers) == 2
            assert live_headers[1].previous_hash == block_hash(live_headers[0])

            # Test partial headers
            part_headers = await self._get_headers(client, h1, 2)
            assert len(part_headers) == 1

    async def _get_headers(self, client: Any, h: int, c: int) -> list[Any]:
        """Helper to get and deserialize headers."""
        data = bytes(await client.get_headers(h, c))
        headers = deserialize_base_block_headers(data)
        return headers

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Waiting for ChaintracksClientApi implementation")
    @pytest.mark.asyncio
    async def test_findchaintipheader(self, setup_clients) -> None:
        """Given: ChaintracksClientApi clients
           When: Call findChainTipHeader
           Then: Returns tip header with height >= firstTip.height

        Reference: wallet-toolbox/src/services/chaintracker/chaintracks/__tests/ChaintracksClientApi.test.ts
                   test('4 findChainTipHeader')
        """
        # Given
        clients = setup_clients["clients"]
        first_tip = setup_clients["first_tip"]

        # When/Then
        for client_info in clients:
            client = client_info["client"]
            tip_header = await client.find_chain_tip_header()
            assert tip_header.height >= first_tip.height

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Waiting for ChaintracksClientApi implementation")
    @pytest.mark.asyncio
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

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Waiting for ChaintracksClientApi implementation")
    @pytest.mark.asyncio
    async def test_findheaderforheight(self, setup_clients) -> None:
        """Given: ChaintracksClientApi clients
           When: Call findHeaderForHeight for genesis, tip, and missing height
           Then: Returns correct headers or None for missing

        Reference: wallet-toolbox/src/services/chaintracker/chaintracks/__tests/ChaintracksClientApi.test.ts
                   test('6 findHeaderForHeight')
        """
        # Given
        clients = setup_clients["clients"]
        first_tip = setup_clients["first_tip"]

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
            header = await client.find_header_for_height(first_tip.height)
            assert header is not None and header.height == first_tip.height

            # Test missing height
            missing = await client.find_header_for_height(99999999)
            assert missing is None

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Waiting for ChaintracksClientApi implementation")
    @pytest.mark.asyncio
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
                "version": t.version,
                "previousHash": t.previous_hash,
                "merkleRoot": t.merkle_root,
                "time": t.time,
                "bits": t.bits,
                "nonce": t.nonce,
            }
            await client.add_header(h)

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Waiting for ChaintracksClientApi implementation")
    @pytest.mark.asyncio
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

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Waiting for ChaintracksClientApi implementation")
    @pytest.mark.asyncio
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
                reorgs.append({"depth": depth, "old_tip": old_tip, "new_tip": new_tip})

            subscription_id = await client.subscribe_reorgs(reorg_listener)
            assert isinstance(subscription_id, str)
            assert await client.unsubscribe(subscription_id) is True
