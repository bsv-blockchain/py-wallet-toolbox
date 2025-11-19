"""Manual tests for StorageClient.

This module tests StorageClient functionality for backing up wallet storage to cloud.

Reference: wallet-toolbox/test/Wallet/StorageClient/storageClient.man.test.ts

WARNING: This test hangs the commit to master automated test run cycle if included in regular tests.
"""

import os

import pytest

try:
    from bsv_wallet_toolbox.storage import StorageClient

    from bsv_wallet_toolbox.utils import TestUtils

    IMPORTS_AVAILABLE = True
except ImportError:
    IMPORTS_AVAILABLE = False


class TestStorageClientManual:
    """Manual test suite for StorageClient.

    Reference: wallet-toolbox/test/Wallet/StorageClient/storageClient.man.test.ts
               describe('walletStorageClient test')
    """

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Waiting for StorageClient implementation")
    @pytest.mark.asyncio
    async def test_backup_to_client(self) -> None:
        """Given: Legacy wallet with SQLite copy
           When: Add StorageClient provider and update backups
           Then: Backup succeeds to staging storage server

        Reference: wallet-toolbox/test/Wallet/StorageClient/storageClient.man.test.ts
                   test('1 backup to client')
        """
        # Given
        ctx = await TestUtils.create_legacy_wallet_sqlite_copy("walletStorageClient1")
        wallet = ctx["wallet"]
        storage = ctx["storage"]

        try:
            # When
            client = StorageClient(wallet, "https://staging-storage.babbage.systems")
            await storage.add_wallet_storage_provider(client)
            await storage.update_backups()

            # Then - backup completes without error
        finally:
            # Cleanup
            await storage.destroy()

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Waiting for StorageClient implementation")
    @pytest.mark.asyncio
    async def test_create_storage_client_backup_for_test_wallet(self) -> None:
        """Given: Test wallet with storage client
           When: Get auth from storage
           Then: Returns truthy userId

        Reference: wallet-toolbox/test/Wallet/StorageClient/storageClient.man.test.ts
                   test('2 create storage client backup for test wallet')
        """
        # Given
        ctx = await TestUtils.create_test_wallet_with_storage_client(
            {"rootKeyHex": "1" * 64, "endpointUrl": "https://staging-storage.babbage.systems"}
        )
        ctx["wallet"]
        storage = ctx["storage"]

        try:
            # When
            auth = await storage.get_auth()

            # Then
            assert auth["userId"] is not None
        finally:
            # Cleanup
            await storage.destroy()

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Waiting for StorageClient implementation")
    @pytest.mark.asyncio
    async def test_create_storage_client_backup_for_main_wallet(self) -> None:
        """Given: Main wallet with file path from environment
           When: Add StorageClient provider and update backups
           Then: Backup succeeds to production storage server

        Reference: wallet-toolbox/test/Wallet/StorageClient/storageClient.man.test.ts
                   test('3 create storage client backup for main wallet')
        """
        # Given
        file_path = os.getenv("MY_MAIN_FILEPATH")
        identity_key = os.getenv("MY_MAIN_IDENTITY", "")

        env = TestUtils.get_env("test")
        root_key_hex = env.dev_keys.get(identity_key, "")

        if not (file_path and identity_key and root_key_hex):
            pytest.skip("MY_MAIN_FILEPATH, MY_MAIN_IDENTITY, and corresponding dev key required")

        chain = "main"

        main = await TestUtils.create_sqlite_test_wallet(
            {"filePath": file_path, "databaseName": "tone42", "chain": chain, "rootKeyHex": root_key_hex}
        )

        try:
            # When
            client = StorageClient(main.wallet, "https://storage.babbage.systems")
            await main.storage.add_wallet_storage_provider(client)
            await main.storage.update_backups()

            # Then - backup completes without error
        finally:
            # Cleanup
            await main.storage.destroy()
