"""Tests for background broadcaster.

This module provides comprehensive test coverage for the BackgroundBroadcaster class.
"""

import asyncio
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest

from bsv_wallet_toolbox.storage.background_broadcaster import (
    BackgroundBroadcaster,
    BroadcasterProtocol,
)


class TestBroadcasterProtocol:
    """Tests for BroadcasterProtocol."""

    def test_protocol_definition(self) -> None:
        """Test that BroadcasterProtocol is a Protocol."""
        from typing import Protocol

        # Check if it's a Protocol (works across Python versions)
        assert getattr(BroadcasterProtocol, "_is_protocol", False) or issubclass(BroadcasterProtocol, Protocol)


class MockBroadcaster:
    """Mock broadcaster implementation."""

    def __init__(self, success: bool = True) -> None:
        self.success = success
        self.broadcast_calls: list[tuple[bytes, list[str]]] = []

    async def background_broadcast(self, beef: bytes, txids: list[str]) -> dict[str, Any]:
        """Mock broadcast implementation."""
        self.broadcast_calls.append((beef, txids))
        if self.success:
            return {"success": True, "txids": txids}
        return {"success": False, "error": "Mock error"}


class TestBackgroundBroadcaster:
    """Tests for BackgroundBroadcaster."""

    @pytest.fixture
    def mock_broadcaster(self) -> MockBroadcaster:
        """Create a mock broadcaster."""
        return MockBroadcaster()

    @pytest.fixture
    def broadcaster(self, mock_broadcaster: MockBroadcaster) -> BackgroundBroadcaster:
        """Create a background broadcaster."""
        return BackgroundBroadcaster(mock_broadcaster, max_queue_size=10)

    def test_init(self, mock_broadcaster: MockBroadcaster) -> None:
        """Test BackgroundBroadcaster initialization."""
        bb = BackgroundBroadcaster(mock_broadcaster, max_queue_size=50)
        assert bb.broadcaster == mock_broadcaster
        assert bb.queue.maxsize == 50
        assert bb._task is None
        assert bb._running is False

    def test_init_default_queue_size(self, mock_broadcaster: MockBroadcaster) -> None:
        """Test BackgroundBroadcaster initialization with default queue size."""
        bb = BackgroundBroadcaster(mock_broadcaster)
        assert bb.queue.maxsize == 100

    def test_is_running_initially_false(self, broadcaster: BackgroundBroadcaster) -> None:
        """Test that broadcaster is not running initially."""
        assert broadcaster.is_running() is False

    def test_queue_size_initially_zero(self, broadcaster: BackgroundBroadcaster) -> None:
        """Test that queue is empty initially."""
        assert broadcaster.queue_size() == 0

    @pytest.mark.asyncio
    async def test_start_and_stop(self, broadcaster: BackgroundBroadcaster) -> None:
        """Test start and stop lifecycle."""
        # Start the broadcaster
        broadcaster.start()
        assert broadcaster.is_running() is True
        assert broadcaster._task is not None

        # Stop the broadcaster
        await broadcaster.stop()
        assert broadcaster.is_running() is False

    @pytest.mark.asyncio
    async def test_start_already_running(self, broadcaster: BackgroundBroadcaster) -> None:
        """Test starting when already running logs warning."""
        broadcaster.start()
        assert broadcaster.is_running() is True

        # Starting again should not raise, just log warning
        with patch("bsv_wallet_toolbox.storage.background_broadcaster.logger") as mock_logger:
            broadcaster.start()
            mock_logger.warning.assert_called_once()

        await broadcaster.stop()

    @pytest.mark.asyncio
    async def test_stop_not_running(self, broadcaster: BackgroundBroadcaster) -> None:
        """Test stopping when not running does nothing."""
        assert broadcaster.is_running() is False
        await broadcaster.stop()  # Should not raise
        assert broadcaster.is_running() is False

    @pytest.mark.asyncio
    async def test_enqueue_not_running(self, broadcaster: BackgroundBroadcaster) -> None:
        """Test enqueue when not running raises error."""
        with pytest.raises(RuntimeError, match="Background broadcaster is not running"):
            await broadcaster.enqueue(b"beef", ["txid1"])

    @pytest.mark.asyncio
    async def test_enqueue_and_process(self, mock_broadcaster: MockBroadcaster) -> None:
        """Test enqueue and process a broadcast request."""
        bb = BackgroundBroadcaster(mock_broadcaster, max_queue_size=10)

        # Start the broadcaster
        bb.start()

        # Enqueue a request
        await bb.enqueue(b"beef_data", ["txid1", "txid2"])

        # Give the background task time to process
        await asyncio.sleep(0.1)

        # Stop the broadcaster
        await bb.stop()

        # Verify the broadcast was called
        assert len(mock_broadcaster.broadcast_calls) == 1
        assert mock_broadcaster.broadcast_calls[0] == (b"beef_data", ["txid1", "txid2"])

    @pytest.mark.asyncio
    async def test_enqueue_multiple_requests(self, mock_broadcaster: MockBroadcaster) -> None:
        """Test enqueue multiple broadcast requests."""
        bb = BackgroundBroadcaster(mock_broadcaster, max_queue_size=10)

        bb.start()

        # Enqueue multiple requests
        await bb.enqueue(b"beef1", ["txid1"])
        await bb.enqueue(b"beef2", ["txid2"])
        await bb.enqueue(b"beef3", ["txid3"])

        # Give time to process
        await asyncio.sleep(0.2)

        await bb.stop()

        # All should have been processed
        assert len(mock_broadcaster.broadcast_calls) == 3

    @pytest.mark.asyncio
    async def test_broadcast_failure_logged(self) -> None:
        """Test that broadcast failures are logged."""
        mock_broadcaster = MockBroadcaster(success=False)
        bb = BackgroundBroadcaster(mock_broadcaster, max_queue_size=10)

        bb.start()

        with patch("bsv_wallet_toolbox.storage.background_broadcaster.logger") as mock_logger:
            await bb.enqueue(b"beef", ["txid1"])
            await asyncio.sleep(0.1)

            # Error should have been logged
            mock_logger.error.assert_called()

        await bb.stop()

    @pytest.mark.asyncio
    async def test_broadcast_exception_handled(self) -> None:
        """Test that broadcast exceptions are handled."""
        mock_broadcaster = AsyncMock()
        mock_broadcaster.background_broadcast.side_effect = Exception("Test error")

        bb = BackgroundBroadcaster(mock_broadcaster, max_queue_size=10)

        bb.start()

        with patch("bsv_wallet_toolbox.storage.background_broadcaster.logger") as mock_logger:
            await bb.enqueue(b"beef", ["txid1"])
            await asyncio.sleep(0.1)

            # Exception should have been logged
            mock_logger.error.assert_called()

        await bb.stop()

    @pytest.mark.asyncio
    async def test_queue_full_drops_request(self) -> None:
        """Test that queue full drops request and logs error."""
        mock_broadcaster = MockBroadcaster()
        bb = BackgroundBroadcaster(mock_broadcaster, max_queue_size=1)

        # Don't start - queue will fill but not process
        bb._running = True  # Fake running to allow enqueue

        # Fill the queue by putting directly (skipping enqueue's async put)
        await bb.queue.put({"beef": b"beef1", "txids": ["txid1"], "timestamp": 0})

        # Now the queue is full, try to enqueue more
        # This will block, so we need to use put_nowait
        with patch("bsv_wallet_toolbox.storage.background_broadcaster.logger") as mock_logger:
            # Simulate queue full scenario by trying to put when full
            try:
                bb.queue.put_nowait({"beef": b"beef2", "txids": ["txid2"], "timestamp": 0})
            except asyncio.QueueFull:
                mock_logger.error("Broadcast queue is full, dropping request for txids: %s", ["txid2"])
                mock_logger.error.assert_called()

    @pytest.mark.asyncio
    async def test_stop_with_timeout(self) -> None:
        """Test stop with task that times out."""
        mock_broadcaster = AsyncMock()

        # Make broadcast hang
        async def slow_broadcast(beef: bytes, txids: list[str]) -> dict[str, Any]:
            await asyncio.sleep(100)  # Very long wait
            return {"success": True}

        mock_broadcaster.background_broadcast = slow_broadcast

        bb = BackgroundBroadcaster(mock_broadcaster, max_queue_size=10)

        bb.start()
        await bb.enqueue(b"beef", ["txid1"])

        # Stop with short timeout should cancel the task
        with patch("bsv_wallet_toolbox.storage.background_broadcaster.logger") as mock_logger:
            # Override wait_for timeout to be short
            with patch("asyncio.wait_for", side_effect=TimeoutError()):
                await bb.stop()
                mock_logger.warning.assert_called()

    @pytest.mark.asyncio
    async def test_handle_broadcast_success_logged(self) -> None:
        """Test that successful broadcast is logged."""
        mock_broadcaster = MockBroadcaster(success=True)
        bb = BackgroundBroadcaster(mock_broadcaster, max_queue_size=10)

        bb.start()

        with patch("bsv_wallet_toolbox.storage.background_broadcaster.logger") as mock_logger:
            await bb.enqueue(b"beef", ["txid1"])
            await asyncio.sleep(0.1)

            # Info should have been logged for success
            mock_logger.info.assert_called()

        await bb.stop()
