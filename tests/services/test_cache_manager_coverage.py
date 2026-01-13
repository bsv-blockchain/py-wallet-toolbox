"""Coverage tests for CacheManager.

This module tests the TTL-based caching functionality to ensure full coverage
of cache operations including expiration, clearing, and edge cases.
"""

import time
from datetime import datetime, timedelta

import pytest

from bsv_wallet_toolbox.services.cache_manager import CacheEntry, CacheManager


class TestCacheEntry:
    """Test CacheEntry class."""

    def test_cache_entry_creation(self) -> None:
        """Test creating a cache entry."""
        value = {"test": "data"}
        ttl = 5000  # 5 seconds

        entry = CacheEntry(value, ttl)

        assert entry.value == value
        assert isinstance(entry.created_at, datetime)
        assert entry.ttl == timedelta(milliseconds=ttl)

    def test_cache_entry_not_expired(self) -> None:
        """Test that a fresh entry is not expired."""
        entry = CacheEntry("test_value", 5000)  # 5 second TTL

        assert not entry.is_expired()

    def test_cache_entry_expired(self) -> None:
        """Test that an entry expires after TTL."""
        entry = CacheEntry("test_value", 1)  # 1 millisecond TTL

        # Wait for expiration
        time.sleep(0.002)  # 2 milliseconds to be safe

        assert entry.is_expired()

    def test_cache_entry_with_different_types(self) -> None:
        """Test cache entry with various value types."""
        # String
        entry_str = CacheEntry("test", 1000)
        assert entry_str.value == "test"

        # Dict
        entry_dict = CacheEntry({"key": "value"}, 1000)
        assert entry_dict.value == {"key": "value"}

        # List
        entry_list = CacheEntry([1, 2, 3], 1000)
        assert entry_list.value == [1, 2, 3]

        # Int
        entry_int = CacheEntry(42, 1000)
        assert entry_int.value == 42


class TestCacheManager:
    """Test CacheManager class."""

    def test_cache_manager_creation(self) -> None:
        """Test creating a cache manager."""
        cache: CacheManager[dict] = CacheManager()
        assert cache._cache == {}

    def test_set_and_get_value(self) -> None:
        """Test setting and getting a cached value."""
        cache: CacheManager[str] = CacheManager()
        key = "testKey"
        value = "test_value"
        ttl = 5000  # 5 seconds

        cache.set(key, value, ttl)
        result = cache.get(key)

        assert result == value

    def test_set_with_snake_case_key_raises(self) -> None:
        """Ensure snake_case keys are rejected to enforce camelCase policy."""
        cache: CacheManager[str] = CacheManager()

        with pytest.raises(ValueError, match="must not contain underscores"):
            cache.set("snake_key", "value", 1000)

    def test_get_nonexistent_key(self) -> None:
        """Test getting a non-existent key returns None."""
        cache: CacheManager[str] = CacheManager()

        result = cache.get("nonexistent")

        assert result is None

    def test_get_expired_value(self) -> None:
        """Test that expired values are removed and return None."""
        cache: CacheManager[str] = CacheManager()
        key = "testKey"
        value = "test_value"
        ttl = 1  # 1 millisecond

        cache.set(key, value, ttl)

        # Wait for expiration
        time.sleep(0.002)  # 2 milliseconds

        result = cache.get(key)

        assert result is None
        # Verify key was removed from cache
        assert key not in cache._cache

    def test_overwrite_existing_key(self) -> None:
        """Test that setting a key again overwrites the old value."""
        cache: CacheManager[str] = CacheManager()
        key = "testKey"

        cache.set(key, "old_value", 5000)
        cache.set(key, "new_value", 5000)

        result = cache.get(key)
        assert result == "new_value"

    def test_clear_specific_key(self) -> None:
        """Test clearing a specific cache key."""
        cache: CacheManager[str] = CacheManager()

        cache.set("key1", "value1", 5000)
        cache.set("key2", "value2", 5000)

        cache.clear("key1")

        assert cache.get("key1") is None
        assert cache.get("key2") == "value2"

    def test_clear_nonexistent_key(self) -> None:
        """Test clearing a non-existent key doesn't raise error."""
        cache: CacheManager[str] = CacheManager()

        cache.set("key1", "value1", 5000)

        # Should not raise
        cache.clear("nonexistent")

        # Original key should still exist
        assert cache.get("key1") == "value1"

    def test_clear_all(self) -> None:
        """Test clearing entire cache."""
        cache: CacheManager[str] = CacheManager()

        cache.set("key1", "value1", 5000)
        cache.set("key2", "value2", 5000)
        cache.set("key3", "value3", 5000)

        cache.clear()  # Clear all

        assert cache.get("key1") is None
        assert cache.get("key2") is None
        assert cache.get("key3") is None
        assert len(cache._cache) == 0

    def test_has_valid_key(self) -> None:
        """Test has() returns True for valid keys."""
        cache: CacheManager[str] = CacheManager()

        cache.set("testKey", "test_value", 5000)

        assert cache.has("testKey") is True

    def test_has_nonexistent_key(self) -> None:
        """Test has() returns False for non-existent keys."""
        cache: CacheManager[str] = CacheManager()

        assert cache.has("nonexistent") is False

    def test_has_expired_key(self) -> None:
        """Test has() returns False for expired keys."""
        cache: CacheManager[str] = CacheManager()

        cache.set("testKey", "test_value", 1)  # 1 millisecond TTL

        # Wait for expiration
        time.sleep(0.002)

        assert cache.has("testKey") is False

    def test_cache_with_dict_values(self) -> None:
        """Test caching dictionary values."""
        cache: CacheManager[dict] = CacheManager()

        test_dict = {"name": "test", "value": 123, "nested": {"key": "val"}}
        cache.set("dictKey", test_dict, 5000)

        result = cache.get("dictKey")
        assert result == test_dict
        assert result is test_dict  # Same object reference

    def test_cache_with_list_values(self) -> None:
        """Test caching list values."""
        cache: CacheManager[list] = CacheManager()

        test_list = [1, 2, 3, "four", {"five": 5}]
        cache.set("listKey", test_list, 5000)

        result = cache.get("listKey")
        assert result == test_list

    def test_multiple_keys_different_ttls(self) -> None:
        """Test multiple keys with different TTL values."""
        cache: CacheManager[str] = CacheManager()

        cache.set("shortTtl", "expiresSoon", 1)  # 1 ms
        cache.set("longTtl", "expiresLater", 10000)  # 10 seconds

        # Wait for short TTL to expire
        time.sleep(0.002)

        assert cache.get("shortTtl") is None
        assert cache.get("longTtl") == "expiresLater"

    def test_cache_manager_with_complex_types(self) -> None:
        """Test cache manager with complex nested types."""
        cache: CacheManager[dict] = CacheManager()

        complex_value = {
            "transactions": [
                {"txid": "abc123", "amount": 1000},
                {"txid": "def456", "amount": 2000},
            ],
            "metadata": {"timestamp": 1234567890, "source": "test"},
        }

        cache.set("complex", complex_value, 5000)

        result = cache.get("complex")
        assert result == complex_value
        assert result["transactions"][0]["txid"] == "abc123"

    def test_zero_ttl(self) -> None:
        """Test cache with zero TTL (immediately expired)."""
        cache: CacheManager[str] = CacheManager()

        cache.set("zeroTtl", "value", 0)

        # Even immediately, it might be considered expired
        # Let's verify the behavior
        time.sleep(0.001)  # Small wait
        result = cache.get("zeroTtl")

        # With 0 TTL, it should expire immediately
        assert result is None
