"""Unit tests for BulkIngestorCDNBabbage.

This module tests BulkIngestorCDNBabbage functionality for mainnet and testnet.

Reference: wallet-toolbox/src/services/chaintracker/chaintracks/Ingest/__tests/BulkIngestorCDNBabbage.test.ts
"""

import pytest

pytestmark = pytest.mark.skip(reason="Module not yet implemented")

try:
    from bsv_wallet_toolbox.services.chaintracker.chaintracks.ingest import BulkIngestorCDNBabbage
    from bsv_wallet_toolbox.services.chaintracker.chaintracks.storage import ChaintracksStorageKnex
    from bsv_wallet_toolbox.services.chaintracker.chaintracks.util import (
        BulkFilesReaderStorage,
        ChaintracksFetch,
        ChaintracksFs,
        HeightRange,
    )

    IMPORTS_AVAILABLE = True
except ImportError:
    IMPORTS_AVAILABLE = False


ROOT_FOLDER = "./tests/integration/data"


class TestBulkIngestorCDNBabbage:
    """Test suite for BulkIngestorCDNBabbage.

    Reference: wallet-toolbox/src/services/chaintracker/chaintracks/Ingest/__tests/BulkIngestorCDNBabbage.test.ts
               describe('BulkIngestorCDNBabbage tests')
    """

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Waiting for BulkIngestorCDNBabbage implementation")
    @pytest.mark.asyncio
    async def test_mainnet(self) -> None:
        """Given: BulkIngestorCDNBabbage for mainnet with local SQLite storage
           When: Update local cache with bulk files from CDN
           Then: CDN has >8 bulk files, 0 live headers, height range 0 to >800000

        Reference: wallet-toolbox/src/services/chaintracker/chaintracks/Ingest/__tests/BulkIngestorCDNBabbage.test.ts
                   test('0 mainNet')
        """
        # Given/When
        result = await self._test_update_local_cache("main", "0")
        cdn = result["cdn"]
        r = result["r"]

        # Then
        assert cdn.available_bulk_files is not None
        assert len(cdn.available_bulk_files.files) > 8
        assert len(r["live_headers"]) == 0
        assert r["reader"].range.min_height == 0
        assert r["reader"].range.max_height > 800000

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Waiting for BulkIngestorCDNBabbage implementation")
    @pytest.mark.asyncio
    async def test_testnet(self) -> None:
        """Given: BulkIngestorCDNBabbage for testnet with local SQLite storage
           When: Update local cache with bulk files from CDN
           Then: CDN has >15 bulk files, 0 live headers, height range 0 to >1500000

        Reference: wallet-toolbox/src/services/chaintracker/chaintracks/Ingest/__tests/BulkIngestorCDNBabbage.test.ts
                   test('1 testNet')
        """
        # Given/When
        result = await self._test_update_local_cache("test", "1")
        cdn = result["cdn"]
        r = result["r"]

        # Then
        assert cdn.available_bulk_files is not None
        assert len(cdn.available_bulk_files.files) > 15
        assert len(r["live_headers"]) == 0
        assert r["reader"].range.min_height == 0
        assert r["reader"].range.max_height > 1500000

    async def _test_update_local_cache(self, chain: str, test: str) -> dict:
        """Test updating local cache with bulk files from CDN.

        Reference: wallet-toolbox/src/services/chaintracker/chaintracks/Ingest/__tests/BulkIngestorCDNBabbage.test.ts
                   async function testUpdateLocalCache(chain: Chain, test: string)
        """
        # Given
        fetch = ChaintracksFetch()
        bulk_cdn_options = BulkIngestorCDNBabbage.create_bulk_ingestor_cdn_babbage_options(chain, fetch)
        cdn = BulkIngestorCDNBabbage(bulk_cdn_options)

        # Create local SQLite storage
        fs = ChaintracksFs

        local_sqlite = {
            "client": "sqlite3",
            "connection": {"filename": fs.path_join(ROOT_FOLDER, f"BulkIngestorCDNBabbage.test_{test}.sqlite")},
            "use_null_as_default": True,
        }
        knex_instance = knex.make_knex(local_sqlite)
        knex_options = ChaintracksStorageKnex.create_storage_knex_options(chain, knex_instance)
        storage = ChaintracksStorageKnex(knex_options)

        # When
        before = await storage.get_available_height_ranges()
        await cdn.set_storage(storage, print)

        range_obj = HeightRange(0, 9900000)
        live_headers = await cdn.fetch_headers(before, range_obj, range_obj, [])
        reader = await BulkFilesReaderStorage.from_storage(storage, fetch, range_obj)

        await storage.knex.destroy()

        # Then
        return {"cdn": cdn, "r": {"reader": reader, "live_headers": live_headers}}
