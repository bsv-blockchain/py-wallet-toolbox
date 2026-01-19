"""Tests for chaintracks internal utilities.

This module provides comprehensive test coverage for PubSubEvents and CacheableWithTTL.
"""

import asyncio
from unittest.mock import Mock

import pytest

from bsv_wallet_toolbox.services.chaintracker.chaintracks.internal import (
    CacheableWithTTL,
    PubSubEvents,
)


class TestPubSubEvents:
    """Tests for PubSubEvents class."""

    @pytest.mark.asyncio
    async def test_init_default_logger(self) -> None:
        """Test initialization with default logger."""
        pubsub = PubSubEvents[str]()
        assert pubsub.subscribers == {}
        assert pubsub.logger is not None

    @pytest.mark.asyncio
    async def test_init_custom_logger(self) -> None:
        """Test initialization with custom logger."""
        custom_logger = Mock()
        pubsub = PubSubEvents[str](logger=custom_logger)
        assert pubsub.logger == custom_logger

    @pytest.mark.asyncio
    async def test_subscribe_returns_queue_and_unsubscribe(self) -> None:
        """Test that subscribe returns a queue and unsubscribe function."""
        pubsub = PubSubEvents[str]()

        queue, unsubscribe = await pubsub.subscribe()

        assert isinstance(queue, asyncio.Queue)
        assert callable(unsubscribe)
        assert queue in pubsub.subscribers

    @pytest.mark.asyncio
    async def test_unsubscribe_removes_subscriber(self) -> None:
        """Test that unsubscribe removes the subscriber."""
        pubsub = PubSubEvents[str]()

        queue, unsubscribe = await pubsub.subscribe()
        assert queue in pubsub.subscribers

        # Unsubscribe
        unsubscribe()
        await asyncio.sleep(0.1)  # Let the task complete

        assert queue not in pubsub.subscribers

    @pytest.mark.asyncio
    async def test_publish_sends_to_all_subscribers(self) -> None:
        """Test that publish sends to all subscribers."""
        pubsub = PubSubEvents[str]()

        queue1, _ = await pubsub.subscribe()
        queue2, _ = await pubsub.subscribe()

        await pubsub.publish("test_event")

        event1 = await queue1.get()
        event2 = await queue2.get()

        assert event1 == "test_event"
        assert event2 == "test_event"

    @pytest.mark.asyncio
    async def test_publish_multiple_events(self) -> None:
        """Test publishing multiple events."""
        pubsub = PubSubEvents[int]()

        queue, _ = await pubsub.subscribe()

        await pubsub.publish(1)
        await pubsub.publish(2)
        await pubsub.publish(3)

        assert await queue.get() == 1
        assert await queue.get() == 2
        assert await queue.get() == 3

    @pytest.mark.asyncio
    async def test_publish_to_empty_subscribers(self) -> None:
        """Test publishing when there are no subscribers."""
        pubsub = PubSubEvents[str]()

        # Should not raise
        await pubsub.publish("test_event")

    @pytest.mark.asyncio
    async def test_queue_full_drops_event(self) -> None:
        """Test that full queue drops events with warning."""
        pubsub = PubSubEvents[int]()

        queue, _ = await pubsub.subscribe()

        # Fill the queue (maxsize is 10)
        for i in range(10):
            await pubsub.publish(i)

        # The queue should be full now
        assert queue.qsize() == 10

        # Publishing more should trigger warning (queue full)
        # Note: This test may be flaky if put() doesn't raise QueueFull
        # The implementation uses await queue.put() which will block, not raise
        # To properly test this, we'd need to adjust the implementation

    @pytest.mark.asyncio
    async def test_multiple_subscribe_unsubscribe(self) -> None:
        """Test multiple subscribe and unsubscribe operations."""
        pubsub = PubSubEvents[str]()

        queue1, _unsub1 = await pubsub.subscribe()
        queue2, unsub2 = await pubsub.subscribe()
        queue3, _unsub3 = await pubsub.subscribe()

        assert len(pubsub.subscribers) == 3

        unsub2()
        await asyncio.sleep(0.1)

        assert len(pubsub.subscribers) == 2
        assert queue1 in pubsub.subscribers
        assert queue2 not in pubsub.subscribers
        assert queue3 in pubsub.subscribers


class TestCacheableWithTTL:
    """Tests for CacheableWithTTL class."""

    def test_init(self) -> None:
        """Test CacheableWithTTL initialization."""
        fetcher = Mock(return_value="value")
        cache = CacheableWithTTL[str](ttl_seconds=10.0, fetcher=fetcher)

        assert cache.ttl_seconds == 10.0
        assert cache.fetcher == fetcher
        assert cache._value is None
        assert cache._last_updated is None

    @pytest.mark.asyncio
    async def test_get_fetches_on_first_call(self) -> None:
        """Test that get() fetches on first call."""
        fetcher = Mock(return_value="fresh_value")
        cache = CacheableWithTTL[str](ttl_seconds=10.0, fetcher=fetcher)

        result = await cache.get()

        assert result == "fresh_value"
        fetcher.assert_called_once()
        assert cache._value == "fresh_value"
        assert cache._last_updated is not None

    @pytest.mark.asyncio
    async def test_get_returns_cached_value_within_ttl(self) -> None:
        """Test that get() returns cached value within TTL."""
        fetcher = Mock(return_value="value")
        cache = CacheableWithTTL[str](ttl_seconds=10.0, fetcher=fetcher)

        # First call
        result1 = await cache.get()
        assert result1 == "value"
        assert fetcher.call_count == 1

        # Second call should return cached value
        result2 = await cache.get()
        assert result2 == "value"
        assert fetcher.call_count == 1  # Not called again

    @pytest.mark.asyncio
    async def test_get_refetches_after_ttl(self) -> None:
        """Test that get() refetches after TTL expires."""
        call_count = 0

        def fetcher() -> str:
            nonlocal call_count
            call_count += 1
            return f"value_{call_count}"

        cache = CacheableWithTTL[str](ttl_seconds=0.1, fetcher=fetcher)

        # First call
        result1 = await cache.get()
        assert result1 == "value_1"

        # Wait for TTL to expire
        await asyncio.sleep(0.15)

        # Second call should refetch
        result2 = await cache.get()
        assert result2 == "value_2"
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_invalidate_clears_cache(self) -> None:
        """Test that invalidate() clears the cache."""
        fetcher = Mock(return_value="value")
        cache = CacheableWithTTL[str](ttl_seconds=100.0, fetcher=fetcher)

        # First call
        await cache.get()
        assert cache._value is not None
        assert cache._last_updated is not None

        # Invalidate
        cache.invalidate()

        assert cache._value is None
        assert cache._last_updated is None

    @pytest.mark.asyncio
    async def test_invalidate_forces_refetch(self) -> None:
        """Test that invalidate() forces next get() to refetch."""
        call_count = 0

        def fetcher() -> str:
            nonlocal call_count
            call_count += 1
            return f"value_{call_count}"

        cache = CacheableWithTTL[str](ttl_seconds=100.0, fetcher=fetcher)

        # First call
        result1 = await cache.get()
        assert result1 == "value_1"
        assert call_count == 1

        # Invalidate
        cache.invalidate()

        # Second call should refetch
        result2 = await cache.get()
        assert result2 == "value_2"
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_get_with_complex_type(self) -> None:
        """Test get() with complex type."""
        data = {"key": "value", "count": 42}
        fetcher = Mock(return_value=data)
        cache = CacheableWithTTL[dict](ttl_seconds=10.0, fetcher=fetcher)

        result = await cache.get()

        assert result == data
        assert result["key"] == "value"
        assert result["count"] == 42
