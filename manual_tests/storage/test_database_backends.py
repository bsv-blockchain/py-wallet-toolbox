"""Manual tests for MySQL Dojo Reader storage sync.

These tests require:
- MySQL Dojo database access
- Connection credentials in environment variables
- Test identity key

Reference: toolbox/ts-wallet-toolbox/test/storage/StorageMySQLDojoReader.man.test.ts
"""

import os
import pytest
from typing import Optional
from bsv_wallet_toolbox.storage import StorageMySQLDojoReader, WalletStorageManager
from bsv_wallet_toolbox.sdk.types import Chain


def get_dojo_connection(chain: Chain) -> Optional[dict]:
    """Get Dojo MySQL connection configuration from environment.
    
    Args:
        chain: 'main' or 'test'
        
    Returns:
        Connection dict if configured, None otherwise
        
    Expected env format (JSON):
    {
        "host": "mysql.example.com",
        "port": 3306,
        "user": "username",
        "password": "password",
        "database": "dojo_db"
    }
    """
    env_var = "MAIN_DOJO_CONNECTION" if chain == "main" else "TEST_DOJO_CONNECTION"
    connection_str = os.getenv(env_var)
    
    if not connection_str:
        return None
    
    try:
        import json
        return json.loads(connection_str)
    except json.JSONDecodeError:
        return None


def get_test_identity_key() -> Optional[str]:
    """Get test identity key from environment.
    
    Returns:
        Identity key if set, None otherwise
    """
    return os.getenv("MY_TEST_IDENTITY")


class TestStorageMySQLDojoReader:
    """Test suite for StorageMySQLDojoReader sync operations.
    
    Reference: toolbox/ts-wallet-toolbox/test/storage/StorageMySQLDojoReader.man.test.ts
    """
    
    @pytest.mark.skip(reason="Requires MySQL Dojo database access - run manually")
    @pytest.mark.asyncio
    async def test_sync_from_dojo_testnet(self) -> None:
        """Given: MySQL Dojo Reader connected to testnet Dojo database
           When: Perform sync operations to local staging storage
           Then: Successfully syncs all data chunks from Dojo to local storage
           
        Note: Requires TEST_DOJO_CONNECTION environment variable with MySQL connection details.
              Requires MY_TEST_IDENTITY environment variable with test identity key.
              
        Reference: toolbox/ts-wallet-toolbox/test/storage/StorageMySQLDojoReader.man.test.ts
                   test('0')
        """
        # Given
        chain: Chain = "test"
        connection = get_dojo_connection(chain)
        identity_key = get_test_identity_key()
        
        if not connection:
            pytest.skip("TEST_DOJO_CONNECTION not configured")
        
        if not identity_key:
            pytest.skip("MY_TEST_IDENTITY not configured")
        
         Create MySQL Dojo Reader
        reader = StorageMySQLDojoReader(
             chain=chain,
             connection=connection
         )
        
         Create local staging storage (SQLite or MySQL)
        use_mysql = os.getenv("USE_MYSQL", "false").lower() == "true"
        if use_mysql:
             writer = create_local_mysql_storage("stagingdojotone", chain)
        else:
             writer = create_local_sqlite_storage("stagingdojotone", chain)
        
         Initialize writer
        await writer.drop_all_data()
        await writer.migrate("stagingdojotone", "1" * 64)
        
         Get settings
        reader_settings = await reader.get_settings()
        writer_settings = await writer.get_settings()
        
        # When - Perform sync
        sync_state = await EntitySyncState.from_storage(
             writer, identity_key, reader_settings
         )
        
         Sync loop
        while True:
             args = sync_state.make_request_sync_chunk_args(
                 identity_key, writer_settings.storage_identity_key
             )
             chunk = await reader.get_sync_chunk(args)
             result = await sync_state.process_request_sync_chunk_result(
                 writer, args, chunk
             )
             
             # Log progress
             print(f"Synced: max_updated_at={result.max_updated_at}, "
                   f"inserts={result.inserts}, updates={result.updates}")
             
             if result.done:
                 break
        
        # Then
        assert result.done is True
         
        # Cleanup
        await reader.destroy()
        await writer.destroy()
        
    
    @pytest.mark.skip(reason="Requires MySQL Dojo database access - run manually")
    @pytest.mark.asyncio
    async def test_sync_from_dojo_mainnet(self) -> None:
        """Given: MySQL Dojo Reader connected to mainnet Dojo database
           When: Perform sync operations to local staging storage
           Then: Successfully syncs all data chunks from Dojo to local storage
           
        Note: Requires MAIN_DOJO_CONNECTION environment variable with MySQL connection details.
              Requires MY_TEST_IDENTITY environment variable with identity key.
              USE WITH CAUTION: Syncs real mainnet data!
              
        Reference: toolbox/ts-wallet-toolbox/test/storage/StorageMySQLDojoReader.man.test.ts
        """
        # Given
        chain: Chain = "main"
        connection = get_dojo_connection(chain)
        identity_key = get_test_identity_key()
        
        if not connection:
            pytest.skip("MAIN_DOJO_CONNECTION not configured")
        
        if not identity_key:
            pytest.skip("MY_TEST_IDENTITY not configured")
        
         Same implementation as testnet


class TestStorageMultiDatabase:
    """Test suite for multi-database storage operations (SQLite, MySQL, PostgreSQL).
    
    Note: These tests verify that storage operations work consistently across different
          database backends: SQLite (development), MySQL (production), PostgreSQL (enterprise).
    """
    
    @pytest.mark.skip(reason="Requires database setup - run manually")
    @pytest.mark.asyncio
    async def test_sqlite_storage_operations(self) -> None:
        """Given: SQLite storage backend
           When: Perform CRUD operations (insert, find, update, count)
           Then: All operations succeed with correct results
           
        Note: SQLite is the default for development and testing.
        """
        # Given
        storage = create_sqlite_storage(":memory:")
        await storage.migrate("test_user", "test_identity_key")
        
        # When/Then - Insert
        user = User(identity_key="test_key", created_at=datetime.now())
        result = await storage.insert("users", user)
        assert result["userId"] is not None
        
        # When/Then - Find
        found = await storage.find("users", {"identityKey": "test_key"})
        assert len(found) == 1
        assert found[0]["identityKey"] == "test_key"
        
        # When/Then - Update
        update_result = await storage.update("users", {"userId": result["userId"]}, {"updated_at": datetime.now()})
        assert update_result["updated"] == 1
        
        # When/Then - Count
        count = await storage.count("users", {"identityKey": "test_key"})
        assert count == 1
        
        # Cleanup
        await storage.destroy()
        
    
    @pytest.mark.skip(reason="Requires MySQL database - run manually")
    @pytest.mark.asyncio
    async def test_mysql_storage_operations(self) -> None:
        """Given: MySQL storage backend
           When: Perform CRUD operations (insert, find, update, count)
           Then: All operations succeed with correct results
           
        Note: Requires MYSQL_CONNECTION environment variable:
              {"host": "localhost", "port": 3306, "user": "root", "password": "...", "database": "test_wallet"}
        """
        # Given
        connection = os.getenv("MYSQL_CONNECTION")
        if not connection:
            pytest.skip("MYSQL_CONNECTION not configured")
        
        import json
        conn_config = json.loads(connection)
        storage = create_mysql_storage(conn_config)
        await storage.migrate("test_user", "test_identity_key")
        
         Same operations as SQLite test
    
    @pytest.mark.skip(reason="Requires PostgreSQL database - run manually")
    @pytest.mark.asyncio
    async def test_postgresql_storage_operations(self) -> None:
        """Given: PostgreSQL storage backend
           When: Perform CRUD operations (insert, find, update, count)
           Then: All operations succeed with correct results
           
        Note: Requires POSTGRESQL_CONNECTION environment variable:
              {"host": "localhost", "port": 5432, "user": "postgres", "password": "...", "database": "test_wallet"}
        """
        # Given
        connection = os.getenv("POSTGRESQL_CONNECTION")
        if not connection:
            pytest.skip("POSTGRESQL_CONNECTION not configured")
        
        import json
        conn_config = json.loads(connection)
        storage = create_postgresql_storage(conn_config)
        await storage.migrate("test_user", "test_identity_key")
        
         Same operations as SQLite test
    
    @pytest.mark.skip(reason="Requires multiple databases - run manually")
    @pytest.mark.asyncio
    async def test_cross_database_sync(self) -> None:
        """Given: Data in SQLite storage
           When: Sync to MySQL storage
           Then: All data is correctly transferred and both storages are in sync
           
        Note: Tests that sync operations work correctly across different database backends.
        """
        # Given - Create and populate SQLite storage
        sqlite_storage = create_sqlite_storage(":memory:")
        await sqlite_storage.migrate("test_user", "test_identity_key")
         Insert test data...
        
         Create MySQL storage
        mysql_storage = create_mysql_storage(...)
        await mysql_storage.migrate("test_user", "test_identity_key")
        
        # When - Sync from SQLite to MySQL
        sync_result = await sync_storages(
             source=sqlite_storage,
             target=mysql_storage,
             identity_key="test_identity_key"
         )
        
        # Then
        assert sync_result["synced"] is True
        assert sync_result["records_transferred"] > 0
        
         Verify data matches
        sqlite_count = await sqlite_storage.count("users", {})
        mysql_count = await mysql_storage.count("users", {})
        assert sqlite_count == mysql_count
        

