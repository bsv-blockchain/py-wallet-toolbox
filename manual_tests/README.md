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

