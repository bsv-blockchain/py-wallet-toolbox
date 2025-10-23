# Manual Tests

These tests require manual execution and cannot be run in automated CI/CD pipelines.

## Why Manual Tests?

Manual tests are separated from automated tests because they:

- **Require network access**: API calls to external services (e.g., WhatsOnChain)
- **Are environment-dependent**: Timing-sensitive concurrent operations
- **Need specific setup**: Database configurations, API keys, etc.
- **Take significant time**: Long-running integration tests

## Requirements

### General Requirements
- Python 3.11+
- All dependencies installed (`pip install -e .`)
- Test dependencies installed (`pip install -e ".[test]"`)

### Service Tests
- **Network access** to blockchain APIs (WhatsOnChain)
- Optional: API keys for rate limit increases

### Integration Tests
- **SQLite database** support
- Sufficient system resources for concurrent operations

## Running Manual Tests

### Run All Manual Tests
```bash
pytest manual_tests/
```

### Run Specific Category
```bash
# Integration tests only
pytest manual_tests/integration/

# Services tests only
pytest manual_tests/services/
```

### Run with Verbose Output
```bash
pytest manual_tests/ -v
```

### Run Specific Test
```bash
# Run a specific test file
pytest manual_tests/services/test_get_beef_for_transaction.py

# Run a specific test case
pytest manual_tests/integration/test_wallet_storage_manager.py::TestWalletStorageManager::test_runasreader_runaswriter_runassync_interlock_correctly
```

## Test Categories

### Integration Tests (`integration/`)

#### `test_wallet_storage_manager.py`
Tests the reader/writer/sync concurrency control mechanisms in WalletStorageManager.

- **Test 1**: `test_runasreader_runaswriter_runassync_interlock_correctly`
  - Verifies that readers can run concurrently
  - Verifies that writers and sync operations are mutually exclusive
  - Uses realistic duration times (10-5000ms)

- **Test 2**: `test_runasreader_runaswriter_runassync_interlock_correctly_with_low_durations`
  - Stress test with minimal durations (0-5ms)
  - Tests race conditions and lock contention

**Requirements**: SQLite database, sufficient system resources

### Services Tests (`services/`)

#### `test_get_beef_for_transaction.py`
Tests BEEF (Background Evaluation Extended Format) retrieval from blockchain services.

- **Test**: `test_protostorage_getbeeffortxid`
  - Retrieves BEEF for real transaction IDs from WhatsOnChain
  - Verifies Merkle proof (bumps) structure
  - Uses mainnet transactions

**Requirements**: Network access, WhatsOnChain API access

**Transaction IDs used**:
- `794f836052ad73732a550c38bea3697a722c6a1e54bcbe63735ba79e0d23f623`
- `53023657e79f446ca457040a0ab3b903000d7281a091397c7853f021726a560e`

#### `test_arc.py`
Tests ARC (Atomic Router and Cache) service for transaction broadcast and validation.

- **Test 1**: `test_post_beef_testnet` - Post BEEF transactions to ARC testnet
- **Test 2**: `test_post_beef_mainnet` - Post BEEF transactions to ARC mainnet
- **Test 3**: `test_double_spend_detection` - Verify double spend detection
- **Test 4**: `test_post_raw_tx_testnet` - Post raw transactions to ARC testnet
- **Test 5**: `test_post_raw_tx_mainnet` - Post raw transactions to ARC mainnet

**Requirements**: Network access, TAAL API key (optional), funded test wallet

**Environment Variables**:
- `TAAL_API_KEY` - API key for TAAL ARC service
- `ARC_MAIN_URL` - Mainnet ARC endpoint (default: https://api.taal.com/arc)
- `ARC_TEST_URL` - Testnet ARC endpoint (default: https://api.taal.com/arc/testnet)

### Storage Tests (`storage/`)

#### `test_database_backends.py`
Tests storage operations across multiple database backends (SQLite, MySQL, PostgreSQL).

- **Test 1**: `test_sqlite_storage_operations` - CRUD operations on SQLite
- **Test 2**: `test_mysql_storage_operations` - CRUD operations on MySQL
- **Test 3**: `test_postgresql_storage_operations` - CRUD operations on PostgreSQL
- **Test 4**: `test_cross_database_sync` - Data synchronization between databases
- **Test 5**: `test_sync_from_dojo_testnet` - Sync from MySQL Dojo Reader (testnet)
- **Test 6**: `test_sync_from_dojo_mainnet` - Sync from MySQL Dojo Reader (mainnet)

**Requirements**: Database access (MySQL/PostgreSQL), Dojo connection credentials

**Environment Variables**:
- `MYSQL_CONNECTION` - MySQL connection details (JSON)
- `POSTGRESQL_CONNECTION` - PostgreSQL connection details (JSON)
- `TEST_DOJO_CONNECTION` - Testnet Dojo MySQL connection (JSON)
- `MAIN_DOJO_CONNECTION` - Mainnet Dojo MySQL connection (JSON)
- `MY_TEST_IDENTITY` - Test identity key for sync operations

**Connection Format (JSON)**:
```json
{
  "host": "localhost",
  "port": 3306,
  "user": "username",
  "password": "password",
  "database": "database_name"
}
```

### Wallet Tests (`wallet/`)

#### `test_local_wallet.py`
Tests local wallet operations with real blockchain interaction.

- **Test 1**: `test_monitor_run_once` - Monitor checks for new transactions
- **Test 2**: `test_monitor_run_once_with_call_history` - Monitor call history tracking
- **Test 3**: `test_create_one_sat_output_delayed_broadcast` - Delayed broadcast
- **Test 4**: `test_create_one_sat_output_immediate_broadcast` - Immediate broadcast
- **Test 5**: `test_create_nosend_and_send_with` - Batch broadcasting with sendWith
- **Test 6**: `test_balance_consistency_across_storage` - Balance across storage backends
- **Test 7**: `test_review_sync_chunk` - Sync chunk generation
- **Test 8**: `test_backup_update` - Automatic backup synchronization

**Requirements**: Funded test wallet, network access, blockchain services

**Environment Variables**:
- `MY_TEST_IDENTITY` - Test wallet identity key
- `TEST_STORAGE_CONNECTION` - Test storage connection (JSON)

**WARNING**: Tests create real blockchain transactions. Use testnet recommended!

#### `test_backup.py`
Tests wallet backup and restore operations.

- **Test 1**: `test_backup_to_local_file` - Backup wallet to local file
- **Test 2**: `test_restore_from_local_file` - Restore wallet from backup file
- **Test 3**: `test_backup_to_secondary_storage` - Multi-storage backup
- **Test 4**: `test_backup_to_cloud_storage` - Cloud backup (if configured)
- **Test 5**: `test_incremental_backup` - Incremental backup efficiency
- **Test 6**: `test_backup_encryption` - Encrypted backups with password

**Requirements**: Test wallet with data, storage backends

**Environment Variables**:
- `CLOUD_STORAGE_URL` - Cloud storage endpoint (optional)
- `CLOUD_STORAGE_API_KEY` - Cloud storage API key (optional)

## Notes

- These tests are **not run in CI/CD** by default
- Run them locally before major releases or when modifying related code
- Some tests may fail if external APIs are unavailable
- Timing-dependent tests may occasionally fail due to system load

## Troubleshooting

### Network Timeout
If services tests fail with timeout errors:
- Check your network connection
- Verify WhatsOnChain API is accessible
- Consider using an API key for higher rate limits

### Concurrent Test Failures
If WalletStorageManager tests report overlaps:
- System may be under heavy load
- Try running tests individually
- Check if database files have proper permissions

### Database Errors
If you see database lock errors:
- Ensure no other processes are using the test databases
- Clean up old test database files: `rm -rf /tmp/wallet_test_*.db`

## Reference

These tests are ported from TypeScript:
- `ts-wallet-toolbox/src/storage/__test/WalletStorageManager.test.ts`
- `ts-wallet-toolbox/src/storage/__test/getBeefForTransaction.test.ts`

