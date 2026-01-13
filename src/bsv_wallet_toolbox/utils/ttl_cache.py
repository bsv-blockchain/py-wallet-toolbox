"""TTL-based cache with automatic expiration.

Provides thread-safe caching with time-to-live expiration,
following the Go pending sign actions cache pattern.

Reference: go-wallet-toolbox/pkg/wallet/pending/local_pending_sign_actions_repo.go
"""

import threading
import time
from dataclasses import dataclass
from typing import Any


@dataclass
class CacheItem:
    """Cache item with value and expiration time."""

    value: Any
    expires_at: float


class TTLCache:
    """Thread-safe TTL cache with automatic expiration.

    Provides caching with configurable time-to-live and automatic cleanup
    of expired items.

    Reference: go-wallet-toolbox/pkg/wallet/pending/local_pending_sign_actions_repo.go
    """

    def __init__(self, ttl_seconds: float = 300.0, cleanup_interval: float = 60.0):
        """Initialize TTL cache.

        Args:
            ttl_seconds: Default time-to-live in seconds
            cleanup_interval: How often to run cleanup in seconds
        """
        self.ttl_seconds = ttl_seconds
        self.cleanup_interval = cleanup_interval
        self.cache: dict[str, CacheItem] = {}
        self.lock = threading.RLock()
        self._cleanup_timer: threading.Timer | None = None
        self._schedule_cleanup()

    def get(self, key: str) -> Any:
        """Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found/expired
        """
        with self.lock:
            item = self.cache.get(key)
            if item is None:
                return None

            if time.time() > item.expires_at:
                # Item expired, remove it
                del self.cache[key]
                return None

            return item.value

    def set(self, key: str, value: Any, ttl_seconds: float | None = None) -> None:
        """Set value in cache with TTL.

        Args:
            key: Cache key
            value: Value to cache
            ttl_seconds: TTL override, uses default if None
        """
        ttl = ttl_seconds if ttl_seconds is not None else self.ttl_seconds
        expires_at = time.time() + ttl

        with self.lock:
            self.cache[key] = CacheItem(value=value, expires_at=expires_at)

    def delete(self, key: str) -> bool:
        """Delete item from cache.

        Args:
            key: Cache key

        Returns:
            True if item was deleted, False if not found
        """
        with self.lock:
            if key in self.cache:
                del self.cache[key]
                return True
            return False

    def clear(self) -> None:
        """Clear all items from cache."""
        with self.lock:
            self.cache.clear()

    def size(self) -> int:
        """Get number of items in cache (including expired)."""
        with self.lock:
            return len(self.cache)

    def cleanup(self) -> int:
        """Remove expired items from cache.

        Returns:
            Number of items removed
        """
        current_time = time.time()
        removed = 0

        with self.lock:
            expired_keys = [key for key, item in self.cache.items() if current_time > item.expires_at]

            for key in expired_keys:
                del self.cache[key]
                removed += 1

        if removed > 0:
            print(f"TTL cache cleanup: removed {removed} expired items")

        return removed

    def _schedule_cleanup(self) -> None:
        """Schedule next cleanup."""
        if self._cleanup_timer:
            self._cleanup_timer.cancel()

        self._cleanup_timer = threading.Timer(self.cleanup_interval, self._cleanup_task)
        self._cleanup_timer.daemon = True
        self._cleanup_timer.start()

    def _cleanup_task(self) -> None:
        """Periodic cleanup task."""
        try:
            self.cleanup()
        finally:
            # Schedule next cleanup
            self._schedule_cleanup()

    def stop(self) -> None:
        """Stop the cleanup timer."""
        if self._cleanup_timer:
            self._cleanup_timer.cancel()
            self._cleanup_timer = None

    def __len__(self) -> int:
        """Get number of non-expired items in cache."""
        with self.lock:
            current_time = time.time()
            return sum(1 for item in self.cache.values() if current_time <= item.expires_at)

    def __contains__(self, key: str) -> bool:
        """Check if key exists and is not expired."""
        return self.get(key) is not None

    def __getitem__(self, key: str) -> Any:
        """Get value from cache using dict-style access.

        Args:
            key: Cache key

        Returns:
            Cached value

        Raises:
            KeyError: If key not found or expired
        """
        value = self.get(key)
        if value is None:
            raise KeyError(key)
        return value

    def __setitem__(self, key: str, value: Any) -> None:
        """Set value in cache using dict-style assignment.

        Args:
            key: Cache key
            value: Value to cache
        """
        self.set(key, value)
