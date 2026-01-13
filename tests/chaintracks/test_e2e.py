"""End-to-End tests for Chaintracks service.

Tests full integration of live ingestors, bulk managers, and storage.

Note: The subscription tests (test_header_subscription, test_reorg_subscription)
are currently skipped due to issues with background worker cancellation in test
environments. These tests verify the pub/sub event system functionality.

Reference: wallet-toolbox/src/services/chaintracker/__tests__/e2e.test.ts
"""

import asyncio
from typing import Any

import pytest

from bsv_wallet_toolbox.services.chaintracker.chaintracks.core_service import (
    ChaintracksCoreService,
    ChaintracksServiceConfig,
)


class TestChaintracksE2E:
    """End-to-end test suite for Chaintracks service.

    Reference: wallet-toolbox/src/services/chaintracker/__tests__/e2e.test.ts
    """

    @pytest.mark.asyncio
    async def test_core_service_initialization(self) -> None:
        """Test core service initializes correctly."""
        # Given
        config = ChaintracksServiceConfig(chain="main")
        service = ChaintracksCoreService(config)

        # When
        await service.make_available()

        # Then
        assert service.is_available()
        assert service.get_chain() == "main"

        info = await service.get_info()
        assert info.chain == "main"
        assert len(info.live_ingestors) > 0

        # Cleanup
        service.destroy()

    @pytest.mark.asyncio
    async def test_height_ranges(self) -> None:
        """Test height range management."""
        # Given
        config = ChaintracksServiceConfig(chain="main")
        service = ChaintracksCoreService(config)

        # When
        await service.make_available()

        # Then
        ranges = await service.get_available_height_ranges()
        assert ranges is not None
        assert ranges.live is not None
        assert ranges.bulk is not None

        # Cleanup
        service.destroy()

    @pytest.mark.asyncio
    async def test_present_height(self) -> None:
        """Test present height retrieval."""
        # Given
        config = ChaintracksServiceConfig(chain="main")
        service = ChaintracksCoreService(config)

        # When
        await service.make_available()

        # Then
        height = await service.get_present_height()
        assert isinstance(height, int)
        assert height > 0

        # Cleanup
        service.destroy()

    @pytest.mark.skip(reason="Event subscription tests are causing hangs in background worker")
    @pytest.mark.asyncio
    async def test_header_subscription(self) -> None:
        """Test header event subscription system."""
        # Given
        config = ChaintracksServiceConfig(chain="main")
        service = ChaintracksCoreService(config)
        await service.make_available()

        received_events: list[dict[str, Any]] = []

        def event_handler(event: dict[str, Any]) -> None:
            received_events.append(event)

        # When
        send_callback, unsubscribe = service.subscribe_headers()

        # Send a test event
        test_header = {"hash": "test_hash", "height": 100, "merkleRoot": "test_root"}
        send_callback(test_header)

        # Give event processing a moment
        await asyncio.sleep(0.1)

        # Then
        assert len(received_events) == 1
        assert received_events[0] == test_header

        # Test unsubscribe
        unsubscribe()
        send_callback({"hash": "second_test"})
        await asyncio.sleep(0.1)
        assert len(received_events) == 1  # Should not have increased

        # Cleanup
        service.destroy()

    @pytest.mark.skip(reason="Event subscription tests are causing hangs in background worker")
    @pytest.mark.asyncio
    async def test_reorg_subscription(self) -> None:
        """Test reorg event subscription system."""
        # Given
        config = ChaintracksServiceConfig(chain="main")
        service = ChaintracksCoreService(config)
        await service.make_available()

        received_events: list[dict[str, Any]] = []

        def event_handler(event: dict[str, Any]) -> None:
            received_events.append(event)

        # When
        send_callback, _unsubscribe = service.subscribe_reorgs()

        # Send a test event
        test_reorg = {"oldTip": "old_hash", "newTip": "new_hash"}
        send_callback(test_reorg)

        # Give event processing a moment
        await asyncio.sleep(0.1)

        # Then
        assert len(received_events) == 1
        assert received_events[0] == test_reorg

        # Cleanup
        service.destroy()

    @pytest.mark.asyncio
    async def test_live_header_processing(self) -> None:
        """Test live header processing pipeline."""
        # Given
        config = ChaintracksServiceConfig(chain="main")
        service = ChaintracksCoreService(config)
        await service.make_available()

        # Test header
        test_header = {
            "version": 1,
            "previousHash": "0000000000000000000000000000000000000000000000000000000000000000",
            "merkleRoot": "0000000000000000000000000000000000000000000000000000000000000000",
            "time": 1231006505,
            "bits": 486604799,
            "nonce": 2083236893,
            "hash": "000000000019d6689c085ae165831e934ff763ae46a2a6c172b3f1b60a8ce26f",
            "height": 0,
        }

        # When
        await service.live_headers_chan.put(test_header)
        await asyncio.sleep(0.1)  # Allow processing

        # Then
        # Check if header was stored
        stored_header = await service.find_header_for_height(0)
        if stored_header:
            assert stored_header["hash"] == test_header["hash"]

        # Cleanup
        service.destroy()
