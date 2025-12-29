"""TTL-based cache manager for Services layer.

Implements generic caching with time-to-live (TTL) for service calls.
Reference: ts-wallet-toolbox/src/services/chaintracker/ChaintracksChainTracker.ts

Example:
    >>> cache = CacheManager[dict]()
    >>> cache.set("key1", {"data": "value"}, ttl_msecs=60000)  # 60 second TTL
    >>> result = cache.get("key1")
    >>> if result:
    ...     print(result)  # {"data": "value"}
"""

from datetime import UTC, datetime, timedelta
from typing import Generic, TypeVar

T = TypeVar("T")


class CacheEntry(Generic[T]):
    """Cache entry with TTL tracking."""

    def __init__(self, value: T, ttl_msecs: int) -> None:
        """Initialize cache entry.

        Args:
            value: The cached value
            ttl_msecs: Time-to-live in milliseconds
        """
        self.value = value
        self.created_at = datetime.now(UTC)
        self.ttl = timedelta(milliseconds=ttl_msecs)

    def is_expired(self) -> bool:
        """Check if entry has expired.

        Returns:
            True if the entry has exceeded its TTL, False otherwise
        """
        return datetime.now(UTC) > self.created_at + self.ttl


class CacheManager(Generic[T]):
    """Generic TTL-based cache manager.

    Manages cached entries with automatic expiration based on TTL.
    """

    def __init__(self) -> None:
        """Initialize cache manager."""
        self._cache: dict[str, CacheEntry[T]] = {}

    def set(self, key: str, value: T, ttl_msecs: int) -> None:
        """Set a cached value with TTL.

        Args:
            key: Cache key
            value: Value to cache
            ttl_msecs: Time-to-live in milliseconds
        """
        validated_key = self._validate_key(key)
        self._cache[validated_key] = CacheEntry(value, ttl_msecs)

    def get(self, key: str) -> T | None:
        """Get a cached value if it exists and hasn't expired.

        Args:
            key: Cache key

        Returns:
            The cached value if valid and not expired, None otherwise
        """
        validated_key = self._validate_key(key)
        entry = self._cache.get(validated_key)
        if entry is None:
            return None

        if entry.is_expired():
            del self._cache[validated_key]
            return None

        return entry.value

    def clear(self, key: str | None = None) -> None:
        """Clear cache entries.

        Args:
            key: Specific key to clear. If None, clears entire cache.
        """
        if key is None:
            self._cache.clear()
            return

        validated_key = self._validate_key(key)
        if validated_key in self._cache:
            del self._cache[validated_key]

    def has(self, key: str) -> bool:
        """Check if a valid (non-expired) entry exists.

        Args:
            key: Cache key

        Returns:
            True if key exists and hasn't expired, False otherwise
        """
        return self.get(key) is not None

    @staticmethod
    def _validate_key(key: str) -> str:
        """Enforce camelCase keys for cache entries."""
        if "_" in key:
            msg = f"CacheManager keys must be camelCase: {key}"
            raise ValueError(msg)
        return key
