"""Manual tests for LocalKVStore functionality.

These tests verify that LocalKVStore correctly stores and retrieves
key-value pairs using wallet outputs (blockchain-based key-value storage).

Implementation Intent:
- Test LocalKVStore.set() - store key-value pairs as wallet outputs
- Test LocalKVStore.get() - retrieve values by key
- Test LocalKVStore.remove() - delete key-value pairs (spend outputs)
- Verify both encrypted and unencrypted storage modes
- Verify idempotency (same key-value returns same outpoint)

Why Manual Test:
1. Requires live wallet with real satoshis for creating outputs
2. Uses actual blockchain transactions for storage
3. Needs authentication and network connectivity
4. Tests both local (SQLite) and client (MySQL/StorageServer) backends

Background:
LocalKVStore uses wallet outputs to store key-value pairs:
- Each key-value pair is stored as a wallet output in a specific basket
- Keys are stored in output customInstructions
- Values can be encrypted or unencrypted
- Setting same key-value twice returns same outpoint (idempotent)
- Removing a key spends the output, making it unavailable

Test Variations:
1. Unencrypted storage (allOrNothing=False): Values stored as plaintext
2. Encrypted storage (allOrNothing=True): Values encrypted with wallet key
3. WalletClient vs Wallet: Tests both lightweight client and full wallet

Reference: wallet-toolbox/test/WalletClient/LocalKVStore.man.test.ts
"""

import logging

import pytest
from bsv_wallet_toolbox.local_kv_store import LocalKVStore
from bsv_wallet_toolbox.test_utils import create_setup
from bsv_wallet_toolbox.wallet_client import WalletClient

logger = logging.getLogger(__name__)


@pytest.mark.skip(reason="Waiting for LocalKVStore, createSetup implementation")
@pytest.mark.asyncio
async def test_unencrypted_wallet() -> None:
    """Given: Wallet with LocalKVStore (unencrypted, allOrNothing=False)
       When: Set, get, and remove key-value pairs
       Then: Operations work correctly and outputs are managed properly

    This test verifies:
    1. set() creates new output
    2. set() with same value returns same outpoint (idempotent)
    3. get() retrieves stored value
    4. get() with default value returns default for non-existent key
    5. remove() deletes output
    6. listOutputs shows 0 outputs after all removed

    Reference: wallet-toolbox/test/WalletClient/LocalKVStore.man.test.ts
               test('0 unencrypted Wallet')
    """

    chain = "main"
    options = {
        "setActiveClient": True,
        "useMySQLConnectionForClient": True,
        "useTestIdentityKey": False,
        "useIdentityKey2": False,
    }

    originator = "wallet-toolbox.tests"
    setup = await create_setup(chain, options)
    wallet = setup["wallet"]

    try:
        basket = "kvstoretest5"
        kv = LocalKVStore(wallet, basket, all_or_nothing=False, originator=originator)

        # Test set
        r1 = await kv.set("a", "apple")
        assert r1, "set should return outpoint"

        # Test idempotent set
        r1a = await kv.set("a", "apple")
        assert r1a == r1, "same value must return same outpoint"

        # Test get
        r2 = await kv.get("a")
        assert r2 == "apple", "get should return stored value"

        # Test get with default
        r3 = await kv.get("b", "banana")
        assert r3 == "banana", "get should return default for non-existent key"

        # Test remove non-existent
        r4 = await kv.remove("b")
        assert len(r4) == 0, "remove non-existent should return empty list"

        # Test remove existing
        r5 = await kv.remove("a")
        assert len(r5) == 1, "remove existing should return 1 outpoint"

        # Verify no outputs remain
        lor = await wallet.list_outputs({"basket": basket})
        assert lor["totalOutputs"] == 0, "basket should have 0 outputs after all removed"

        logger.info("test_unencrypted_wallet completed successfully")

    finally:
        await wallet.destroy()


@pytest.mark.skip(reason="Waiting for LocalKVStore, createSetup implementation")
@pytest.mark.asyncio
async def test_unencrypted_wallet_with_all_or_nothing() -> None:
    """Given: Wallet with LocalKVStore (unencrypted, allOrNothing=True)
       When: Set, get, and remove key-value pairs
       Then: Operations work correctly with allOrNothing mode

    This test is identical to test_unencrypted_wallet but uses
    allOrNothing=True mode, which affects transaction handling.

    Reference: wallet-toolbox/test/WalletClient/LocalKVStore.man.test.ts
               test('1 unencrypted Wallet')
    """

    chain = "main"
    options = {
        "setActiveClient": True,
        "useMySQLConnectionForClient": True,
        "useTestIdentityKey": False,
        "useIdentityKey2": False,
    }

    originator = "wallet-toolbox.tests"
    setup = await create_setup(chain, options)
    wallet = setup["wallet"]

    try:
        basket = "kvstoretest6"
        kv = LocalKVStore(wallet, basket, all_or_nothing=True, originator=originator)

        # Test set
        r1 = await kv.set("a", "apple")
        assert r1, "set should return outpoint"

        # Test idempotent set
        r1a = await kv.set("a", "apple")
        assert r1a == r1, "same value must return same outpoint"

        # Test get
        r2 = await kv.get("a")
        assert r2 == "apple", "get should return stored value"

        # Test get with default
        r3 = await kv.get("b", "banana")
        assert r3 == "banana", "get should return default for non-existent key"

        # Test remove non-existent
        r4 = await kv.remove("b")
        assert len(r4) == 0, "remove non-existent should return empty list"

        # Test remove existing
        r5 = await kv.remove("a")
        assert len(r5) == 1, "remove existing should return 1 outpoint"

        # Verify no outputs remain
        lor = await wallet.list_outputs({"basket": basket})
        assert lor["totalOutputs"] == 0, "basket should have 0 outputs after all removed"

        logger.info("test_unencrypted_wallet_with_all_or_nothing completed successfully")

    finally:
        await wallet.destroy()


@pytest.mark.skip(reason="Waiting for LocalKVStore, WalletClient implementation")
@pytest.mark.asyncio
async def test_unencrypted_walletclient() -> None:
    """Given: WalletClient with LocalKVStore (unencrypted, allOrNothing=False)
       When: Set, get, and remove key-value pairs
       Then: Operations work correctly with WalletClient

    This test verifies LocalKVStore works with WalletClient (browser mode)
    instead of full Wallet.

    Reference: wallet-toolbox/test/WalletClient/LocalKVStore.man.test.ts
               test('0a unencrypted WalletClient')
    """

    originator = "wallet-toolbox.tests"
    wallet = WalletClient(storage=None, originator=originator)

    basket = "kvstoretest7"
    kv = LocalKVStore(wallet, basket, all_or_nothing=False, originator=originator)

    # Test set
    r1 = await kv.set("a", "apple")
    assert r1, "set should return outpoint"

    # Test idempotent set
    r1a = await kv.set("a", "apple")
    assert r1a == r1, "same value must return same outpoint"

    # Test get
    r2 = await kv.get("a")
    assert r2 == "apple", "get should return stored value"

    # Test get with default
    r3 = await kv.get("b", "banana")
    assert r3 == "banana", "get should return default for non-existent key"

    # Test remove non-existent
    r4 = await kv.remove("b")
    assert len(r4) == 0, "remove non-existent should return empty list"

    # Test remove existing
    r5 = await kv.remove("a")
    assert len(r5) == 1, "remove existing should return 1 outpoint"

    # Verify no outputs remain
    lor = await wallet.list_outputs({"basket": basket})
    assert lor["totalOutputs"] == 0, "basket should have 0 outputs after all removed"

    logger.info("test_unencrypted_walletclient completed successfully")


@pytest.mark.skip(reason="Waiting for LocalKVStore, WalletClient implementation")
@pytest.mark.asyncio
async def test_unencrypted_walletclient_with_all_or_nothing() -> None:
    """Given: WalletClient with LocalKVStore (unencrypted, allOrNothing=True)
       When: Set, get, and remove key-value pairs
       Then: Operations work correctly with WalletClient in allOrNothing mode

    This test is identical to test_unencrypted_walletclient but uses
    allOrNothing=True mode.

    Reference: wallet-toolbox/test/WalletClient/LocalKVStore.man.test.ts
               test('1a unencrypted WalletClient')
    """

    originator = "wallet-toolbox.tests"
    wallet = WalletClient(storage=None, originator=originator)

    basket = "kvstoretest8"
    kv = LocalKVStore(wallet, basket, all_or_nothing=True, originator=originator)

    # Test set
    r1 = await kv.set("a", "apple")
    assert r1, "set should return outpoint"

    # Test idempotent set
    r1a = await kv.set("a", "apple")
    assert r1a == r1, "same value must return same outpoint"

    # Test get
    r2 = await kv.get("a")
    assert r2 == "apple", "get should return stored value"

    # Test get with default
    r3 = await kv.get("b", "banana")
    assert r3 == "banana", "get should return default for non-existent key"

    # Test remove non-existent
    r4 = await kv.remove("b")
    assert len(r4) == 0, "remove non-existent should return empty list"

    # Test remove existing
    r5 = await kv.remove("a")
    assert len(r5) == 1, "remove existing should return 1 outpoint"

    # Verify no outputs remain
    lor = await wallet.list_outputs({"basket": basket})
    assert lor["totalOutputs"] == 0, "basket should have 0 outputs after all removed"

    logger.info("test_unencrypted_walletclient_with_all_or_nothing completed successfully")
