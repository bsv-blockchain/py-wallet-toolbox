"""Manual tests for local wallet operations with live blockchain.

These tests require:
- Network access to blockchain services (WhatsOnChain, ARC)
- Test wallet with funded outputs
- API keys (TAAL_API_KEY, etc.)
- Real blockchain interaction (testnet recommended)

Reference: toolbox/ts-wallet-toolbox/test/Wallet/local/localWallet.man.test.ts
"""

import os
import pytest
from typing import Optional
from bsv_wallet_toolbox import Wallet
from bsv_wallet_toolbox.storage import WalletStorageManager
from bsv_wallet_toolbox.services import WalletServices
from bsv_wallet_toolbox.monitor import WalletMonitor
from bsv_wallet_toolbox.sdk.types import Chain


# Helper function stubs - to be implemented
def create_test_storage(chain: Chain):
    """Create test storage for wallet.
    
    Raises:
        NotImplementedError: This helper is not yet implemented
    """
    raise NotImplementedError(
        "create_test_storage helper not implemented yet. "
        "This requires porting test utilities from TypeScript."
    )


def create_test_services(chain: Chain):
    """Create test services for wallet.
    
    Raises:
        NotImplementedError: This helper is not yet implemented
    """
    raise NotImplementedError(
        "create_test_services helper not implemented yet. "
        "This requires porting test utilities from TypeScript."
    )


async def create_local_wallet_setup(chain: Chain, identity_key: str, **options):
    """Create local wallet setup with storage and services.
    
    Raises:
        NotImplementedError: This helper is not yet implemented
    """
    raise NotImplementedError(
        "create_local_wallet_setup helper not implemented yet. "
        "This requires porting test utilities from TypeScript."
    )


async def create_one_sat_test_output(setup, options: dict, count: int):
    """Create test output with 1 satoshi.
    
    Raises:
        NotImplementedError: This helper is not yet implemented
    """
    raise NotImplementedError(
        "create_one_sat_test_output helper not implemented yet. "
        "This requires porting test utilities from TypeScript."
    )


def get_test_identity_key() -> Optional[str]:
    """Get test identity key from environment.
    
    Returns:
        Identity key if set, None otherwise
    """
    return os.getenv("MY_TEST_IDENTITY")


def get_test_storage_connection() -> Optional[dict]:
    """Get test storage connection configuration.
    
    Returns:
        Connection dict if configured, None otherwise
    """
    conn_str = os.getenv("TEST_STORAGE_CONNECTION")
    if not conn_str:
        return None
    
    try:
        import json
        return json.loads(conn_str)
    except json.JSONDecodeError:
        return None


class TestLocalWalletMonitor:
    """Test suite for local wallet with monitor operations.
    
    Reference: toolbox/ts-wallet-toolbox/test/Wallet/local/localWallet.man.test.ts
    """
    
    @pytest.mark.skip(reason="Requires test wallet and network access - run manually")
    @pytest.mark.asyncio
    async def test_monitor_run_once(self) -> None:
        """Given: Local wallet with test identity key and monitor
           When: Call monitor.runOnce to check for new transactions
           Then: Monitor completes successfully without errors
           
        Note: Requires MY_TEST_IDENTITY environment variable.
              Requires funded test wallet with existing outputs.
              Connects to real testnet blockchain services.
              
        Reference: toolbox/ts-wallet-toolbox/test/Wallet/local/localWallet.man.test.ts
                   test('0 monitor runOnce')
        """
        # Given
        chain: Chain = "test"
        identity_key = get_test_identity_key()
        
        if not identity_key:
            pytest.skip("MY_TEST_IDENTITY not configured")
        
         Create wallet with test identity
        storage = create_test_storage(chain)
        services = create_test_services(chain)
        wallet = Wallet(chain=chain, storage=storage, services=services, identity_key=identity_key)
        
         Create monitor
        monitor = WalletMonitor(wallet=wallet, services=services)
        
         Verify identity key
        key_result = await wallet.get_public_key({"identityKey": True})
        assert key_result["publicKey"] == identity_key
        
        # When
        await monitor.run_once()
        
        # Then
         No errors should occur
        
        # Cleanup
        await wallet.destroy()
    
    @pytest.mark.skip(reason="Requires test wallet and network access - run manually")
    @pytest.mark.asyncio
    async def test_monitor_run_once_with_call_history(self) -> None:
        """Given: Local wallet with monitor and service call history tracking
           When: Make service calls and run monitor, then check call history
           Then: Call history contains all service API calls
           
        Note: Tests that monitor's call history tracking works correctly.
              Requires MY_TEST_IDENTITY environment variable.
              
        Reference: toolbox/ts-wallet-toolbox/test/Wallet/local/localWallet.man.test.ts
                   test('0a monitor runOnce call history')
        """
        # Given
        chain: Chain = "test"
        identity_key = get_test_identity_key()
        
        if not identity_key:
            pytest.skip("MY_TEST_IDENTITY not configured")
        
         Create wallet and monitor with call history enabled
        setup = await create_local_wallet_setup(chain, identity_key, track_calls=True)
        
         Make some service calls
        await setup.services.get_raw_tx("6dd8e416dfaf14c04899ccad2bf76a67c1d5598fece25cf4dcb7a076012b7d8d")
        await setup.services.get_raw_tx("ac9cced61e2491be55061ce6577e0c59b909922ba92d5cc1cd754b10d721ab0e")
        
        # When
        await setup.monitor.run_once()
        
         Make more calls after monitor
        await setup.services.get_raw_tx("0000e416dfaf14c04899ccad2bf76a67c1d5598fece25cf4dcb7a076012b7d8d")
        await setup.services.get_raw_tx("0000ced61e2491be55061ce6577e0c59b909922ba92d5cc1cd754b10d721ab0e")
        
        # Then - Check call history
        history = await setup.monitor.run_task("MonitorCallHistory")
        assert len(history) > 0
        assert any("get_raw_tx" in call["method"] for call in history)
        
        # Cleanup
        await setup.wallet.destroy()


class TestLocalWalletActions:
    """Test suite for local wallet createAction with real blockchain.
    
    Reference: toolbox/ts-wallet-toolbox/test/Wallet/local/localWallet.man.test.ts
    """
    
    @pytest.mark.skip(reason="Requires funded test wallet - run manually")
    @pytest.mark.asyncio
    async def test_create_one_sat_output_delayed_broadcast(self) -> None:
        """Given: Funded test wallet
           When: Create action with 1 sat output and delayed broadcast
           Then: Action is created, queued, and eventually broadcast
           
        Note: Tests delayed broadcast mechanism with real blockchain.
              Requires funded test wallet outputs.
              Transaction will be broadcast to testnet!
              
        Reference: toolbox/ts-wallet-toolbox/test/Wallet/local/localWallet.man.test.ts
                   test('2 create 1 sat delayed')
        """
        # Given
        chain: Chain = "test"
        identity_key = get_test_identity_key()
        
        if not identity_key:
            pytest.skip("MY_TEST_IDENTITY not configured")
        
        setup = await create_local_wallet_setup(chain, identity_key)
        
        # When - Create action with delayed broadcast
        result = await setup.wallet.create_action({
            "description": "Test 1 sat output",
            "outputs": [{
                "satoshis": 1,
                "lockingScript": "...",  # P2PKH to test address
                "description": "Test output"
            }],
            "acceptDelayedBroadcast": True
        })
        
        # Then
        assert result["txid"] is not None
        assert result["status"] in ["queued", "sending"]
        
        # Note: TypeScript has trackReqByTxid commented out
        # await track_req_by_txid(setup, result["txid"])
        
        # Cleanup
        await setup.wallet.destroy()
        
    
    @pytest.mark.skip(reason="Requires funded test wallet - run manually")
    @pytest.mark.asyncio
    async def test_create_one_sat_output_immediate_broadcast(self) -> None:
        """Given: Funded test wallet
           When: Create action with 1 sat output and immediate broadcast
           Then: Action is created and immediately broadcast
           
        Note: Tests immediate broadcast with acceptDelayedBroadcast=False.
              Requires funded test wallet outputs.
              Transaction will be broadcast to testnet!
              
        Reference: toolbox/ts-wallet-toolbox/test/Wallet/local/localWallet.man.test.ts
                   test('2a create 1 sat immediate')
        """
        # Given
        chain: Chain = "test"
        identity_key = get_test_identity_key()
        
        if not identity_key:
            pytest.skip("MY_TEST_IDENTITY not configured")
        
        setup = await create_local_wallet_setup(chain, identity_key)
        
        # When - Create action with immediate broadcast
        result = await setup.wallet.create_action({
             "description": "Test 1 sat immediate",
             "outputs": [{
                 "satoshis": 1,
                 "lockingScript": "...",
                 "description": "Test immediate output"
             }],
             "acceptDelayedBroadcast": False
        })
        
        # Then
        assert result["txid"] is not None
        assert result["status"] == "success"
        
        # Note: TypeScript has trackReqByTxid commented out
        # await track_req_by_txid(setup, result["txid"])
        
        # Cleanup
        await setup.wallet.destroy()
        
    
    @pytest.mark.skip(reason="Requires funded test wallet - run manually")
    @pytest.mark.asyncio
    async def test_create_nosend_and_send_with(self) -> None:
        """Given: Funded test wallet
           When: Create 2 actions with noSend=True, then sendWith to broadcast together
           Then: Both actions are created but not sent, then sent together
           
        Note: Tests noSend and sendWith functionality for batch broadcasting.
              Requires funded test wallet outputs.
              Transactions will be broadcast to testnet!
              
        Reference: toolbox/ts-wallet-toolbox/test/Wallet/local/localWallet.man.test.ts
                   test('2b create 2 nosend and sendWith')
        """
        # Given
        chain: Chain = "test"
        identity_key = get_test_identity_key()
        
        if not identity_key:
            pytest.skip("MY_TEST_IDENTITY not configured")
        
        setup = await create_local_wallet_setup(chain, identity_key)
        
        # When - Create first action with noSend
        result1 = await setup.wallet.create_action({
             "description": "Test nosend 1",
             "outputs": [{"satoshis": 1, "lockingScript": "..."}],
             "options": {"noSend": True}
        })
        
        # Then
        assert result1["txid"] is not None
        assert result1["status"] == "nosend"
        
        # When - Create second action with noSend
        result2 = await setup.wallet.create_action({
             "description": "Test nosend 2",
             "outputs": [{"satoshis": 1, "lockingScript": "..."}],
             "options": {"noSend": True}
        })
        
        # Then
        assert result2["txid"] is not None
        assert result2["status"] == "nosend"
        
        # When - Send both together with sendWith
        send_result = await setup.wallet.send_with({
             "txids": [result1["txid"], result2["txid"]]
        })
        
        # Then
        assert send_result["status"] == "success"
        assert len(send_result["txids"]) == 2
        
        # Note: TypeScript has trackReqByTxid commented out
        # await track_req_by_txid(setup, result1["txid"])
        
        # Cleanup
        await setup.wallet.destroy()
        


class TestLocalWalletBalance:
    """Test suite for wallet balance operations with real blockchain.
    
    Reference: toolbox/ts-wallet-toolbox/test/Wallet/local/localWallet.man.test.ts
    """
    
    @pytest.mark.skip(reason="Requires test wallet - run manually")
    @pytest.mark.asyncio
    async def test_balance_consistency_across_storage(self) -> None:
        """Given: Wallet with local and cloud storage
           When: Check balance, switch to cloud storage, check balance again
           Then: Balance is consistent across both storage backends
           
        Note: Tests that balance calculations are consistent when switching storage.
              Requires wallet with both local and cloud storage configured.
              
        Reference: toolbox/ts-wallet-toolbox/test/Wallet/local/localWallet.man.test.ts
                   test('3 return active to cloud client')
        """
        # Given
        chain: Chain = "test"
        identity_key = get_test_identity_key()
        
        if not identity_key:
            pytest.skip("MY_TEST_IDENTITY not configured")
        
        setup = await create_local_wallet_setup(chain, identity_key, with_cloud_client=True)
        
        # When - Get balance with local storage
        local_balance = await setup.wallet.balance()
        
         Switch to cloud client storage
        log = await setup.storage.set_active(setup.client_storage_identity_key)
        print(f"Set active storage log: {log}")
        print(f"Active storage: {setup.storage.get_active_storage_name()}")
        
         Get balance with cloud storage
        client_balance = await setup.wallet.balance()
        
        # Then
        assert local_balance == client_balance
        
        # Cleanup
        await setup.wallet.destroy()
        


class TestLocalWalletSync:
    """Test suite for wallet sync operations.
    
    Reference: toolbox/ts-wallet-toolbox/test/Wallet/local/localWallet.man.test.ts
    """
    
    @pytest.mark.skip(reason="Requires test wallet - run manually")
    @pytest.mark.asyncio
    async def test_review_sync_chunk(self) -> None:
        """Given: Wallet with active storage and backup storage
           When: Request sync chunk from active storage
           Then: Returns sync chunk with entity data
           
        Note: Tests sync chunk generation for backup/replication.
              
        Reference: toolbox/ts-wallet-toolbox/test/Wallet/local/localWallet.man.test.ts
                   test('5 review synchunk')
        """
        # Given
        chain: Chain = "test"
        identity_key = get_test_identity_key()
        
        if not identity_key:
            pytest.skip("MY_TEST_IDENTITY not configured")
        
        setup = await create_local_wallet_setup(chain, identity_key, with_backup=True)
        
        reader = setup.active_storage
        reader_settings = reader.get_settings()
        writer = setup.storage._backups[0].storage
        writer_settings = writer.get_settings()
        
        # When - Create sync state and request chunk
        sync_state = await EntitySyncState.from_storage(writer, identity_key, reader_settings)
        args = sync_state.make_request_sync_chunk_args(identity_key, writer_settings.storage_identity_key)
        chunk = await reader.get_sync_chunk(args)
        
        # Then
        assert chunk is not None
         Review chunk contents...
        
        # Cleanup
        await setup.wallet.destroy()
        
    
    @pytest.mark.skip(reason="Requires test wallet - run manually")
    @pytest.mark.asyncio
    async def test_backup_update(self) -> None:
        """Given: Wallet with configured backup storage
           When: Call updateBackups to sync data to backup
           Then: Backup is updated with latest data
           
        Note: Tests automatic backup synchronization.
              
        Reference: toolbox/ts-wallet-toolbox/test/Wallet/local/localWallet.man.test.ts
                   test('6 backup')
        """
        # Given
        chain: Chain = "test"
        identity_key = get_test_identity_key()
        
        if not identity_key:
            pytest.skip("MY_TEST_IDENTITY not configured")
        
        setup = await create_local_wallet_setup(chain, identity_key, with_backup=True)
        
        # When
        log = await setup.storage.update_backups()
        print(f"Backup log: {log}")
        
        # Then
        assert log["updated"] is True
        assert log["records_synced"] >= 0
        
        # Cleanup
        await setup.wallet.destroy()
        

