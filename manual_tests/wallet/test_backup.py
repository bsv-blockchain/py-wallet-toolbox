"""Manual tests for wallet backup functionality.

These tests verify that wallet data can be backed up to SQLite storage
and synchronized between different storage providers.

Implementation Intent:
- Test backup to SQLite from WalletClient
- Test backup with multiple identity keys
- Verify backup synchronization and data integrity

Why Manual Test:
1. Requires live wallet with real data
2. Uses actual file system for SQLite backup
3. Needs environment variables for identity keys
4. Tests real backup and restore operations

Background:
The backup functionality allows wallet data to be synchronized from
a primary storage (e.g., cloud storage) to a local SQLite backup.
This ensures data redundancy and offline access capability.

Reference: wallet-toolbox/test/examples/backup.man.test.ts
"""

import json
import logging
import os
from typing import Any

import pytest

logger = logging.getLogger(__name__)


async def backup_wallet_client(env: dict[str, Any], identity_key: str) -> None:
    """Backup a wallet client to SQLite storage.

    This function:
    1. Creates a WalletClient with the specified identity key
    2. Creates a SQLite backup storage
    3. Adds the backup storage provider
    4. Performs updateBackups to sync data
    5. Destroys the wallet

    Args:
        env: Environment configuration dict with:
            - devKeys: Dict mapping identity keys to root key hex
            - chain: 'main' or 'test'
        identity_key: Identity public key to use

    Reference: wallet-toolbox/test/examples/backup.man.test.ts
               backupWalletClient() function
    """
    try:
        from bsv_wallet_toolbox.key_derivation import PrivateKey
        from bsv_wallet_toolbox.storage import StorageClient, WalletStorageManager

        from bsv_wallet_toolbox.wallet import Wallet
    except ImportError:
        logger.warning("Required modules not yet implemented")
        raise NotImplementedError("Manual test requires Wallet, Storage, KeyDerivation implementations.")

    # Get root key from devKeys
    root_key_hex = env["devKeys"].get(identity_key)
    if not root_key_hex:
        raise ValueError(f"No root key found for identity key: {identity_key}")

    # Create WalletClient (simplified wallet)
    root_key = PrivateKey.from_hex(root_key_hex)
    storage_manager = WalletStorageManager()
    wallet = Wallet(chain=env["chain"], storage=storage_manager)

    # Create StorageClient (cloud storage)
    endpoint_url = (
        "https://storage.babbage.systems" if env["chain"] == "main" else "https://staging-storage.babbage.systems"
    )
    client = StorageClient(wallet, endpoint_url)
    await storage_manager.add_wallet_storage_provider(client)

    # Backup to SQLite
    await backup_to_sqlite(
        setup={
            "wallet": wallet,
            "storage": storage_manager,
            "identityKey": identity_key,
            "chain": env["chain"],
            "rootKey": root_key,
        }
    )

    # Cleanup
    await wallet.destroy()


async def backup_to_sqlite(
    setup: dict[str, Any], file_path: str | None = None, database_name: str | None = None
) -> None:
    """Backup wallet data to SQLite storage.

    This function creates a SQLite backup storage provider and syncs
    all wallet data from the active storage to the backup.

    Args:
        setup: Setup dict with:
            - wallet: Wallet instance
            - storage: WalletStorageManager
            - identityKey: Identity public key
            - chain: 'main' or 'test'
            - rootKey: Root private key
        file_path: Optional path to SQLite file (default: backup_{identityKey}.sqlite)
        database_name: Optional database name (default: {identityKey} backup)

    Reference: wallet-toolbox/test/examples/backup.man.test.ts
               backupToSQLite() function
    """
    try:
        from bsv_wallet_toolbox.storage import StorageSQLite
        from bsv_wallet_toolbox.utility import random_bytes_hex
    except ImportError:
        logger.warning("StorageSQLite not yet implemented")
        raise NotImplementedError("Manual test requires StorageSQLite implementation.")

    # Set defaults
    identity_key = setup["identityKey"]
    file_path = file_path or f"backup_{identity_key}.sqlite"
    database_name = database_name or f"{identity_key} backup"

    # Create SQLite backup storage
    backup_storage = StorageSQLite(
        chain=setup["chain"],
        file_path=file_path,
        database_name=database_name,
        commission_satoshis=0,
        commission_pub_key_hex=None,
        fee_model={"model": "sat/kb", "value": 1},
    )

    # Migrate and make available
    migration_key = random_bytes_hex(33)
    await backup_storage.migrate(database_name, migration_key)
    await backup_storage.make_available()

    # Add backup storage provider
    await setup["storage"].add_wallet_storage_provider(backup_storage)

    # Perform backup synchronization
    log = await setup["storage"].update_backups()
    logger.info(f"Backup completed: {log}")


class TestBackup:
    """Test suite for wallet backup manual tests.

    These tests verify wallet backup and synchronization functionality
    between different storage providers.

    Reference: wallet-toolbox/test/examples/backup.man.test.ts
               describe('backup example tests')
    """

    @pytest.mark.asyncio
    async def test_backup_my_test_identity(self) -> None:
        """Given: Test environment with MY_TEST_IDENTITY key
           When: Backup wallet client
           Then: Data is synced to SQLite backup

        Reference: wallet-toolbox/test/examples/backup.man.test.ts
                   test('1 backup MY_TEST_IDENTITY')
        """
        # Get environment
        identity_key = os.getenv("MY_TEST_IDENTITY")
        if not identity_key:
            pytest.skip("MY_TEST_IDENTITY environment variable not set")

        dev_keys_json = os.getenv("DEV_KEYS")
        if not dev_keys_json:
            pytest.skip("DEV_KEYS environment variable not set")

        dev_keys = json.loads(dev_keys_json)
        env = {"chain": "test", "devKeys": dev_keys}

        # Perform backup
        await backup_wallet_client(env, identity_key)

        logger.info(f"Successfully backed up wallet for identity: {identity_key}")

    @pytest.mark.asyncio
    async def test_backup_my_test_identity2(self) -> None:
        """Given: Test environment with MY_TEST_IDENTITY2 key
           When: Backup wallet client
           Then: Data is synced to SQLite backup

        Reference: wallet-toolbox/test/examples/backup.man.test.ts
                   test('2 backup MY_TEST_IDENTITY2')
        """
        # Get environment
        identity_key = os.getenv("MY_TEST_IDENTITY2")
        if not identity_key:
            pytest.skip("MY_TEST_IDENTITY2 environment variable not set")

        dev_keys_json = os.getenv("DEV_KEYS")
        if not dev_keys_json:
            pytest.skip("DEV_KEYS environment variable not set")

        dev_keys = json.loads(dev_keys_json)
        env = {"chain": "test", "devKeys": dev_keys}

        # Perform backup
        await backup_wallet_client(env, identity_key)

        logger.info(f"Successfully backed up wallet for identity: {identity_key}")
