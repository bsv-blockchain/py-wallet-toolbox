"""Manual tests for wallet backup and restore operations.

These tests require:
- Test wallet with data
- Multiple storage backends (SQLite, MySQL, etc.)
- Network access for cloud backups (optional)

Reference: toolbox/ts-wallet-toolbox/test/examples/backup.man.test.ts
"""

import os
import pytest
from typing import Optional
from bsv_wallet_toolbox import Wallet
from bsv_wallet_toolbox.storage import WalletStorageManager
from bsv_wallet_toolbox.sdk.types import Chain


class TestWalletBackupRestore:
    """Test suite for wallet backup and restore operations.
    
    Reference: toolbox/ts-wallet-toolbox/test/examples/backup.man.test.ts
    """
    
    @pytest.mark.skip(reason="Requires test wallet with data - run manually")
    @pytest.mark.asyncio
    async def test_backup_to_local_file(self) -> None:
        """Given: Wallet with transactions and outputs
           When: Create backup to local file
           Then: Backup file is created with all wallet data
           
        Note: Tests local file backup functionality.
        """
        # Given
        chain: Chain = "test"
        wallet = await create_test_wallet_with_data(chain)
        
        # When
        backup_path = "/tmp/wallet_backup.json"
        await wallet.backup_to_file(backup_path)
        
        # Then
        assert os.path.exists(backup_path)
        backup_data = read_backup_file(backup_path)
        assert len(backup_data["transactions"]) > 0
        assert len(backup_data["outputs"]) > 0
        
        # Cleanup
        os.remove(backup_path)
        await wallet.destroy()
        
    
    @pytest.mark.skip(reason="Requires test wallet with data - run manually")
    @pytest.mark.asyncio
    async def test_restore_from_local_file(self) -> None:
        """Given: Backup file from previous wallet
           When: Restore wallet from backup file
           Then: New wallet has all data from backup
           
        Note: Tests local file restore functionality.
        """
        # Given
        chain: Chain = "test"
         Create and backup original wallet
        original_wallet = await create_test_wallet_with_data(chain)
        backup_path = "/tmp/wallet_backup.json"
        await original_wallet.backup_to_file(backup_path)
        original_balance = await original_wallet.balance()
        await original_wallet.destroy()
        
        # When - Restore to new wallet
        restored_wallet = Wallet(chain=chain)
        await restored_wallet.restore_from_file(backup_path)
        
        # Then
        restored_balance = await restored_wallet.balance()
        assert restored_balance == original_balance
        
         Verify transactions
        txs = await restored_wallet.list_actions({})
        assert len(txs) > 0
        
        # Cleanup
        os.remove(backup_path)
        await restored_wallet.destroy()
        
    
    @pytest.mark.skip(reason="Requires multiple storage backends - run manually")
    @pytest.mark.asyncio
    async def test_backup_to_secondary_storage(self) -> None:
        """Given: Wallet with primary SQLite storage
           When: Setup secondary MySQL storage and backup
           Then: Data is synchronized to MySQL storage
           
        Note: Tests multi-storage backup synchronization.
              Requires MYSQL_CONNECTION environment variable.
        """
        # Given
        chain: Chain = "test"
        primary_wallet = await create_test_wallet_with_data(chain, storage_type="sqlite")
        
         Setup secondary storage
        mysql_connection = os.getenv("MYSQL_CONNECTION")
        if not mysql_connection:
             pytest.skip("MYSQL_CONNECTION not configured")
        
        secondary_storage = create_mysql_storage(mysql_connection)
        await primary_wallet.add_backup_storage(secondary_storage)
        
        # When
        await primary_wallet.update_backups()
        
        # Then
         Verify data in secondary storage
        secondary_wallet = Wallet(chain=chain, storage=secondary_storage)
        secondary_balance = await secondary_wallet.balance()
        primary_balance = await primary_wallet.balance()
        assert secondary_balance == primary_balance
        
        # Cleanup
        await primary_wallet.destroy()
        await secondary_wallet.destroy()
        
    
    @pytest.mark.skip(reason="Requires cloud storage access - run manually")
    @pytest.mark.asyncio
    async def test_backup_to_cloud_storage(self) -> None:
        """Given: Wallet with local storage
           When: Configure cloud storage and backup
           Then: Data is backed up to cloud storage
           
        Note: Tests cloud backup functionality.
              Requires CLOUD_STORAGE_URL and credentials.
        """
        # Given
        chain: Chain = "test"
        cloud_url = os.getenv("CLOUD_STORAGE_URL")
        cloud_api_key = os.getenv("CLOUD_STORAGE_API_KEY")
        
        if not cloud_url or not cloud_api_key:
            pytest.skip("Cloud storage credentials not configured")
        
        wallet = await create_test_wallet_with_data(chain)
        
        # When
        await wallet.backup_to_cloud(cloud_url, api_key=cloud_api_key)
        
        # Then
         Verify backup was created
        backup_info = await wallet.get_cloud_backup_info()
        assert backup_info["last_backup"] is not None
        assert backup_info["status"] == "success"
        
        # Cleanup
        await wallet.destroy()
        
    
    @pytest.mark.skip(reason="Requires test wallet - run manually")
    @pytest.mark.asyncio
    async def test_incremental_backup(self) -> None:
        """Given: Wallet with existing backup
           When: Make new transactions and backup again
           Then: Only new data is synchronized (incremental backup)
           
        Note: Tests incremental backup efficiency.
        """
        # Given
        chain: Chain = "test"
        wallet = await create_test_wallet_with_data(chain, with_backup=True)
        
         Initial backup
        backup_result1 = await wallet.update_backups()
        initial_records = backup_result1["records_synced"]
        
         Make new transactions
        await wallet.create_action({
             "description": "Test transaction",
             "outputs": [{"satoshis": 1, "lockingScript": "..."}]
        })
        
        # When - Incremental backup
        backup_result2 = await wallet.update_backups()
        
        # Then
        assert backup_result2["records_synced"] < initial_records  # Only new records
        assert backup_result2["status"] == "success"
        
        # Cleanup
        await wallet.destroy()
        
    
    @pytest.mark.skip(reason="Requires test wallet - run manually")
    @pytest.mark.asyncio
    async def test_backup_encryption(self) -> None:
        """Given: Wallet with sensitive data
           When: Create encrypted backup with password
           Then: Backup is encrypted and can only be restored with password
           
        Note: Tests backup encryption for security.
        """
        # Given
        chain: Chain = "test"
        password = "test_password_123"
        wallet = await create_test_wallet_with_data(chain)
        
        # When - Create encrypted backup
        backup_path = "/tmp/wallet_backup_encrypted.json"
        await wallet.backup_to_file(backup_path, password=password)
        
        # Then - Try to restore without password (should fail)
        new_wallet = Wallet(chain=chain)
        with pytest.raises(Exception):  # Should raise decryption error
             await new_wallet.restore_from_file(backup_path)
        
         Restore with correct password (should succeed)
        await new_wallet.restore_from_file(backup_path, password=password)
        balance = await new_wallet.balance()
        assert balance > 0
        
        # Cleanup
        os.remove(backup_path)
        await wallet.destroy()
        await new_wallet.destroy()
        

