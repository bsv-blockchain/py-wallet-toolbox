"""Manual tests for local wallet operations.

These tests verify local wallet functionality including monitor operations,
transaction creation, storage switching, and backup synchronization.

Implementation Intent:
- Test monitor.runOnce() operations
- Test transaction creation (delayed/immediate/nosend)
- Test switching between local and cloud storage
- Test sync chunk operations
- Test backup operations

Why Manual Test:
1. Requires live wallet with real balance
2. Uses actual monitor daemon
3. Needs MySQL cloud storage connection
4. Tests real blockchain operations

Reference: wallet-toolbox/test/Wallet/local/localWallet.man.test.ts
"""

import logging

import pytest
from bsv_wallet_toolbox.storage.models import EntitySyncState
from bsv_wallet_toolbox.test_utils import create_one_sat_test_output, create_setup

logger = logging.getLogger(__name__)


@pytest.mark.skip(reason="Waiting for createSetup, Monitor, Services implementation")
@pytest.mark.asyncio
async def test_monitor_run_once() -> None:
    """Given: Wallet setup with monitor
       When: Call monitor.runOnce()
       Then: Monitor tasks execute successfully and identity key matches

    Reference: wallet-toolbox/test/Wallet/local/localWallet.man.test.ts
               test('0 monitor runOnce')
    """

    chain = "test"
    options = {
        "setActiveClient": False,
        "useMySQLConnectionForClient": True,
        "useTestIdentityKey": True,
        "useIdentityKey2": False,
    }

    setup = await create_setup(chain, options)

    # Verify identity key matches
    key_result = await setup["wallet"].get_public_key({"identityKey": True})
    assert key_result["publicKey"] == setup["identityKey"]

    # Run monitor once
    await setup["monitor"].run_once()

    await setup["wallet"].destroy()


@pytest.mark.skip(reason="Waiting for createSetup, Monitor, Services implementation")
@pytest.mark.asyncio
async def test_monitor_run_once_call_history() -> None:
    """Given: Wallet setup with monitor and services
       When: Call services.getRawTx() and monitor.runOnce()
       Then: Monitor call history is tracked correctly

    Reference: wallet-toolbox/test/Wallet/local/localWallet.man.test.ts
               test('0a monitor runOnce call history')
    """

    chain = "test"
    options = {
        "setActiveClient": False,
        "useMySQLConnectionForClient": True,
        "useTestIdentityKey": True,
        "useIdentityKey2": False,
    }

    setup = await create_setup(chain, options)

    # Verify identity key
    key_result = await setup["wallet"].get_public_key({"identityKey": True})
    assert key_result["publicKey"] == setup["identityKey"]

    # Call services to populate call history
    await setup["services"].get_raw_tx("6dd8e416dfaf14c04899ccad2bf76a67c1d5598fece25cf4dcb7a076012b7d8d")
    await setup["services"].get_raw_tx("ac9cced61e2491be55061ce6577e0c59b909922ba92d5cc1cd754b10d721ab0e")

    # Run monitor
    await setup["monitor"].run_once()

    # Call more services (will fail - invalid txids)
    await setup["services"].get_raw_tx("0000e416dfaf14c04899ccad2bf76a67c1d5598fece25cf4dcb7a076012b7d8d")
    await setup["services"].get_raw_tx("0000ced61e2491be55061ce6577e0c59b909922ba92d5cc1cd754b10d721ab0e")

    # Check monitor call history
    history = await setup["monitor"].run_task("MonitorCallHistory")
    logger.info(f"Monitor call history: {history}")

    await setup["wallet"].destroy()


@pytest.mark.skip(reason="Waiting for createSetup, createOneSatTestOutput implementation")
@pytest.mark.asyncio
async def test_create_1_sat_delayed() -> None:
    """Given: Wallet setup
       When: Create 1 sat output with delayed broadcast (default)
       Then: Transaction is created and broadcasted with delay

    Reference: wallet-toolbox/test/Wallet/local/localWallet.man.test.ts
               test('2 create 1 sat delayed')
    """

    chain = "test"
    options = {
        "setActiveClient": False,
        "useMySQLConnectionForClient": True,
        "useTestIdentityKey": True,
        "useIdentityKey2": False,
    }

    setup = await create_setup(chain, options)

    # Create 1 sat output with default options (delayed broadcast)
    await create_one_sat_test_output(setup, {}, 1)

    # Note: TypeScript has trackReqByTxid commented out
    # await track_req_by_txid(setup, car["txid"])

    await setup["wallet"].destroy()


@pytest.mark.skip(reason="Waiting for createSetup, createOneSatTestOutput implementation")
@pytest.mark.asyncio
async def test_create_1_sat_immediate() -> None:
    """Given: Wallet setup
       When: Create 1 sat output with immediate broadcast
       Then: Transaction is created and broadcasted immediately

    Reference: wallet-toolbox/test/Wallet/local/localWallet.man.test.ts
               test('2a create 1 sat immediate')
    """

    chain = "test"
    options = {
        "setActiveClient": False,
        "useMySQLConnectionForClient": True,
        "useTestIdentityKey": True,
        "useIdentityKey2": False,
    }

    setup = await create_setup(chain, options)

    # Create 1 sat output with acceptDelayedBroadcast=False (immediate)
    await create_one_sat_test_output(setup, {"acceptDelayedBroadcast": False}, 1)

    # Note: TypeScript has trackReqByTxid commented out
    # await track_req_by_txid(setup, car["txid"])

    await setup["wallet"].destroy()


@pytest.mark.skip(reason="Waiting for createSetup, createOneSatTestOutput implementation")
@pytest.mark.asyncio
async def test_create_2_nosend_and_send_with() -> None:
    """Given: Wallet setup
       When: Create 2 outputs with noSend option
       Then: Transactions are created but not sent

    Reference: wallet-toolbox/test/Wallet/local/localWallet.man.test.ts
               test('2b create 2 nosend and sendWith')
    """

    chain = "test"
    options = {
        "setActiveClient": False,
        "useMySQLConnectionForClient": True,
        "useTestIdentityKey": True,
        "useIdentityKey2": False,
    }

    setup = await create_setup(chain, options)

    # Create 2 outputs with noSend=True
    await create_one_sat_test_output(setup, {"noSend": True}, 2)

    # Note: TypeScript has trackReqByTxid commented out
    # await track_req_by_txid(setup, car["txid"])

    await setup["wallet"].destroy()


@pytest.mark.skip(reason="Waiting for createSetup, WalletStorageManager.setActive implementation")
@pytest.mark.asyncio
async def test_return_active_to_cloud_client() -> None:
    """Given: Wallet with local and cloud storage
       When: Switch active storage from local to cloud
       Then: Balance remains the same across storages

    Reference: wallet-toolbox/test/Wallet/local/localWallet.man.test.ts
               test('3 return active to cloud client')
    """

    chain = "test"
    options = {
        "setActiveClient": False,
        "useMySQLConnectionForClient": True,
        "useTestIdentityKey": True,
        "useIdentityKey2": False,
    }

    setup = await create_setup(chain, options)

    # Get balance with local storage active
    local_balance = await setup["wallet"].balance()

    # Switch to cloud client storage
    log = await setup["storage"].set_active(setup["clientStorageIdentityKey"])
    logger.info(log)
    logger.info(f"ACTIVE STORAGE: {setup['storage'].get_active_store_name()}")

    # Get balance with cloud storage active
    client_balance = await setup["wallet"].balance()

    # Balances should match
    assert local_balance == client_balance

    await setup["wallet"].destroy()


@pytest.mark.skip(reason="Waiting for createSetup, EntitySyncState implementation")
@pytest.mark.asyncio
async def test_review_synchunk() -> None:
    """Given: Wallet with backup storage
       When: Request sync chunk from reader storage
       Then: Sync chunk is retrieved successfully

    Reference: wallet-toolbox/test/Wallet/local/localWallet.man.test.ts
               test('5 review synchunk')
    """

    chain = "test"
    options = {
        "setActiveClient": False,
        "useMySQLConnectionForClient": True,
        "useTestIdentityKey": True,
        "useIdentityKey2": False,
    }

    setup = await create_setup(chain, options)

    identity_key = setup["identityKey"]
    reader = setup["activeStorage"]
    reader_settings = reader.get_settings()

    # Get writer (first backup storage)
    writer = setup["storage"]._backups[0].storage
    writer_settings = writer.get_settings()

    # Create sync state and request chunk
    ss = await EntitySyncState.from_storage(writer, identity_key, reader_settings)
    args = ss.make_request_sync_chunk_args(identity_key, writer_settings["storageIdentityKey"])
    chunk = await reader.get_sync_chunk(args)

    logger.info(f"Retrieved sync chunk: {len(chunk)} items")

    await setup["wallet"].destroy()


@pytest.mark.skip(reason="Waiting for createSetup, WalletStorageManager.updateBackups implementation")
@pytest.mark.asyncio
async def test_backup() -> None:
    """Given: Wallet with backup configured
       When: Call storage.updateBackups()
       Then: Backup synchronization completes successfully

    Reference: wallet-toolbox/test/Wallet/local/localWallet.man.test.ts
               test('6 backup')
    """

    chain = "test"
    options = {
        "setActiveClient": False,
        "useMySQLConnectionForClient": True,
        "useTestIdentityKey": True,
        "useIdentityKey2": False,
    }

    setup = await create_setup(chain, options)

    # Perform backup
    log = await setup["storage"].update_backups()
    logger.info(f"Backup result: {log}")

    await setup["wallet"].destroy()
