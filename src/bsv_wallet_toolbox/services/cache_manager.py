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
    def to_camel_case(key: str) -> str:
        """Convert an underscore-delimited key to camelCase.

        This helper is intended for API consumers who need to migrate from
        snake_case (or other underscore-delimited formats) to the camelCase
        style enforced by :meth:`_validate_key`.

        Examples:
            >>> CacheManager.to_camel_case("my_cache_key")
            'myCacheKey'
            >>> CacheManager.to_camel_case("alreadyCamel")
            'alreadyCamel'

        Args:
            key: Original cache key that may contain underscores.

        Returns:
            A camelCase version of the key with underscores removed.
        """
        if "_" not in key:
            return key
        parts = [part for part in key.split("_") if part]
        if not parts:
            return ""
        head, *tail = parts
        return head + "".join(part[:1].upper() + part[1:] for part in tail)

    @staticmethod
    def _validate_key(key: str) -> str:
        """Validate cache keys by enforcing a camelCase naming convention.

        Cache keys must not contain underscores and should follow camelCase
        (for example: ``myCacheKey`` or ``anotherKey123``). For callers that
        currently use snake_case keys, use :meth:`to_camel_case` to obtain a
        compliant key before interacting with the cache.

        Args:
            key: Cache key to validate.

        Returns:
            The validated key (unchanged if valid).

        Raises:
            ValueError: If key contains underscores.
        """
        if "_" in key:
            msg = (
                f"CacheManager keys must not contain underscores: {key}. "
                "Use CacheManager.to_camel_case(key) to convert underscore-delimited "
                "keys to camelCase before calling CacheManager methods."
            )
            raise ValueError(msg)
        return key
