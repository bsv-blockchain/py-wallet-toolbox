"""Unit tests for LocalKVStore.

This module tests local key-value storage functionality.

Reference: wallet-toolbox/test/bsv-ts-sdk/LocalKVStore.test.ts
"""

import asyncio

import pytest
from bsv.keys import PrivateKey
from bsv.wallet import KeyDeriver

try:
    from bsv_wallet_toolbox.local_kv_store import LocalKVStore
    from bsv_wallet_toolbox.wallet import Wallet

    IMPORTS_AVAILABLE = True
except ImportError:
    IMPORTS_AVAILABLE = False

root_key = PrivateKey(bytes.fromhex("6a2991c9de20e38b31d7ea147bf55f5039e4bbc073160f5e0d541d1f17e321b8"))
key_deriver = KeyDeriver(root_key)


class TestLocalKVStore:
    """Test suite for LocalKVStore.

    Reference: wallet-toolbox/test/bsv-ts-sdk/LocalKVStore.test.ts
                describe('LocalKVStore tests')
    """

    @pytest.mark.asyncio
    async def test_get_non_existent(self) -> None:
        """Given: LocalKVStore with empty storage
           When: Get a non-existent key
           Then: Returns None

        Reference: wallet-toolbox/test/bsv-ts-sdk/LocalKVStore.test.ts
                   test('0 get non-existent')
        """

        wallet = Wallet(chain="test", key_deriver=key_deriver)
        context = "test kv store"
        kv_store = LocalKVStore(wallet, context, False, None, True)

        # When
        value = await kv_store.get("key1")

        # Then
        assert value is None

    @pytest.mark.asyncio
    async def test_set_get(self) -> None:
        """Given: LocalKVStore instance
           When: Set a value and get it back
           Then: Returns the set value

        Reference: wallet-toolbox/test/bsv-ts-sdk/LocalKVStore.test.ts
                   test('1 set get')

        Note: TypeScript skips this test with includeTestChaintracks = false.
              Python implements it but skips until LocalKVStore is available.
        """
        # Given
        wallet = Wallet(chain="test", key_deriver=key_deriver)
        context = "test kv store"
        kv_store = LocalKVStore(wallet, context, False, None, True)

        # When
        await kv_store.set("key1", "value1")
        value = await kv_store.get("key1")

        # Then
        assert value == "value1"

    @pytest.mark.asyncio
    async def test_set_x_4_get(self) -> None:
        """Given: LocalKVStore instance
           When: Set the same key 4 times concurrently
           Then: Last value wins (value4)

        Reference: wallet-toolbox/test/bsv-ts-sdk/LocalKVStore.test.ts
                   test('3 set x 4 get')

        Note: TypeScript skips this test with includeTestChaintracks = false.
              Python implements it but skips until LocalKVStore is available.
        """
        # Given
        wallet = Wallet(chain="test", key_deriver=key_deriver)
        context = "test kv store"
        kv_store = LocalKVStore(wallet, context, False, None, True)

        # When
        await asyncio.gather(
            kv_store.set("key1", "value1"),
            kv_store.set("key1", "value2"),
            kv_store.set("key1", "value3"),
            kv_store.set("key1", "value4"),
        )
        value = await kv_store.get("key1")

        # Then
        assert value == "value4"

    # Note: TypeScript test('4 promise test') is skipped in Python.
    #       It tests Jest's fake timers, not LocalKVStore functionality.
    #       Reference: wallet-toolbox/test/bsv-ts-sdk/LocalKVStore.test.ts

    @pytest.mark.asyncio
    async def test_set_x_4_get_set_x_4_get(self) -> None:
        """Given: LocalKVStore instance
           When: Set key 4 times, capture value, set 4 more times, get final value
           Then: Captured value is value4, final value is value8

        Reference: wallet-toolbox/test/bsv-ts-sdk/LocalKVStore.test.ts
                   test('5 set x 4 get set x 4 get')

        Note: TypeScript skips this test with includeTestChaintracks = false.
              Python implements it but skips until LocalKVStore is available.
        """
        # Given
        wallet = Wallet(chain="test", key_deriver=key_deriver)
        context = "test kv store"
        kv_store = LocalKVStore(wallet, context, False, None, True)

        # When
        v4 = None

        async def capture_value() -> None:
            nonlocal v4
            v4 = await kv_store.get("key1")

        await asyncio.gather(
            kv_store.set("key1", "value1"),
            kv_store.set("key1", "value2"),
            kv_store.set("key1", "value3"),
            kv_store.set("key1", "value4"),
            capture_value(),
            kv_store.set("key1", "value5"),
            kv_store.set("key1", "value6"),
            kv_store.set("key1", "value7"),
            kv_store.set("key1", "value8"),
        )
        v8 = await kv_store.get("key1")

        # Then
        assert v4 == "value4"
        assert v8 == "value8"
