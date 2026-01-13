"""Internal utilities for Chaintracks service.

This module contains internal utility classes and functions.

Reference: toolbox/go-wallet-toolbox/pkg/services/chaintracks/internal/
"""

import asyncio
import logging
from collections.abc import Callable
from typing import Generic, TypeVar

T = TypeVar("T")

logger = logging.getLogger(__name__)


class PubSubEvents(Generic[T]):
    """Generic pub/sub event system for broadcasting events to subscribers.

    This class provides a thread-safe way to subscribe to and publish events
    of any type. Subscribers receive events through channels.

    Reference: toolbox/go-wallet-toolbox/pkg/services/chaintracks/internal/pub_sub_events.go
    """

    def __init__(self, logger: logging.Logger | None = None):
        """Initialize pub/sub event system.

        Args:
            logger: Optional logger for debugging
        """
        self.logger = logger or logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.subscribers: dict[asyncio.Queue[T], Callable[[], None]] = {}
        self._lock = asyncio.Lock()

    async def subscribe(self) -> tuple[asyncio.Queue[T], Callable[[], None]]:
        """Subscribe to events.

        Returns:
            Tuple of (queue, unsubscribe_function)
        """
        async with self._lock:
            queue = asyncio.Queue(maxsize=10)  # Buffered queue

            def unsubscribe() -> None:
                """Unsubscribe from events."""
                asyncio.create_task(self._unsubscribe(queue))

            self.subscribers[queue] = unsubscribe
            return queue, unsubscribe

    async def _unsubscribe(self, queue: asyncio.Queue[T]) -> None:
        """Internal unsubscribe method."""
        async with self._lock:
            if queue in self.subscribers:
                del self.subscribers[queue]

    async def publish(self, event: T) -> None:
        """Publish an event to all subscribers.

        Args:
            event: Event to publish
        """
        async with self._lock:
            for queue in self.subscribers:
                try:
                    # Non-blocking put to prevent blocking if queue is full
                    await queue.put(event)
                except asyncio.QueueFull:
                    self.logger.warning("Subscriber queue full, dropping event")


class CacheableWithTTL(Generic[T]):
    """Generic cache with TTL (time-to-live) functionality.

    Reference: toolbox/go-wallet-toolbox/pkg/services/chaintracks/internal/cacheable_with_ttl.go
    """

    def __init__(self, ttl_seconds: float, fetcher: Callable[[], T]):
        """Initialize cache.

        Args:
            ttl_seconds: Time-to-live in seconds
            fetcher: Function to fetch new value when cache expires
        """
        self.ttl_seconds = ttl_seconds
        self.fetcher = fetcher
        self._value: T | None = None
        self._last_updated: float | None = None

    async def get(self) -> T:
        """Get cached value, fetching if expired.

        Returns:
            Cached or freshly fetched value
        """
        import time

        now = time.time()
        if self._value is None or self._last_updated is None or now - self._last_updated > self.ttl_seconds:

            self._value = self.fetcher()
            self._last_updated = now

        return self._value

    def invalidate(self) -> None:
        """Invalidate the cache, forcing next get() to fetch."""
        self._value = None
        self._last_updated = None
