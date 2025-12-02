# Missing Sync Test Fixtures Documentation

## Overview

Three sync tests require fixtures that are currently missing or incomplete. These fixtures are needed for functional tests that verify actual sync behavior, not just parameter validation.

## Missing Fixtures

### 1. `_wallet` Fixture

**Status:** ❌ Missing (not defined)

**Required For:**
- `test_sync_initial_then_no_changes_then_one_change`
- `test_set_active_to_backup_and_back_without_backup_first`
- `test_set_active_to_backup_and_back_with_backup_first`

**Expected Type:** `Wallet`

**Requirements:**
- Wallet instance with populated data (users, transactions, outputs, certificates, etc.)
- Should have substantial data (>1000 items) for sync testing
- Must be configured with:
  - KeyDeriver (for cryptographic operations)
  - StorageProvider (with seeded data)
  - Services (for blockchain data access)

**Reference Implementation:**
- TypeScript: `wallet-toolbox/test/utils/TestUtilsWalletStorage.ts` - `createSQLiteTestSetup1Wallet()`
- Go: `go-wallet-toolbox/pkg/storage/internal/testabilities/fixture_sync.go` - `GivenSyncFixture()`

**Suggested Implementation:**
```python
@pytest.fixture
def _wallet(test_key_deriver: KeyDeriver) -> Wallet:
    """Create a wallet with seeded data for sync testing.
    
    Seeds the wallet with:
    - User data
    - Multiple transactions (>1000)
    - Output baskets
    - Proven transaction requests
    - Certificates (if applicable)
    
    Returns:
        Wallet instance with populated data
    """
    # Create in-memory SQLite database
    engine = create_engine_from_url("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    
    # Create storage provider
    storage = StorageProvider(engine=engine, chain="main", storage_identity_key="test_wallet_sync")
    storage.make_available()
    
    # Seed with substantial data
    # - Insert user
    # - Insert 1000+ transactions
    # - Insert output baskets
    # - Insert proven tx reqs
    # - etc.
    
    # Create wallet with seeded storage
    wallet = Wallet(chain="main", key_deriver=test_key_deriver, storage_provider=storage)
    
    return wallet
```

### 2. `destination_storage` Fixture

**Status:** ⚠️ Placeholder exists (returns `None`)

**Required For:**
- `test_sync_initial_then_no_changes_then_one_change`

**Expected Type:** Storage identity key string (based on test usage: `_wallet.set_active(backup_storage)`)

**Note:** Tests call `set_active()` with the storage fixture directly, suggesting they expect a string (storage identity key) rather than a StorageProvider object.

**Requirements:**
- Empty storage provider (initially)
- Should be a separate storage instance from the source wallet
- Must be writable (for sync operations)
- Should be in-memory for test isolation

**Current Implementation:**
```python
@pytest.fixture
def destination_storage() -> None:
    # TODO: Implement actual storage fixture
    return None
```

**Suggested Implementation:**
```python
@pytest.fixture
def destination_storage() -> str:
    """Create an empty destination storage for sync testing.
    
    This storage is used as the target for sync_to_writer operations.
    It starts empty and receives data from the source wallet.
    
    Returns:
        Storage identity key string for the destination storage
    """
    # Create separate in-memory SQLite database
    engine = create_engine_from_url("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    
    # Create storage provider with different identity key
    storage = StorageProvider(
        engine=engine, 
        chain="main", 
        storage_identity_key="test_destination_storage"
    )
    storage.make_available()
    
    # Return storage identity key (string) as expected by sync_to_writer
    return "test_destination_storage"
```

### 3. `backup_storage` Fixture

**Status:** ⚠️ Placeholder exists (returns `None`)

**Required For:**
- `test_set_active_to_backup_and_back_without_backup_first`
- `test_set_active_to_backup_and_back_with_backup_first`

**Expected Type:** Storage identity key string (based on test usage: `_wallet.set_active(backup_storage)`)

**Note:** Tests call `set_active()` with the storage fixture directly, suggesting they expect a string (storage identity key) rather than a StorageProvider object.

**Requirements:**
- Empty storage provider (initially)
- Should be a separate storage instance from the original wallet
- Must be writable (for sync operations)
- Should be in-memory for test isolation
- Used as backup storage for `set_active` operations

**Current Implementation:**
```python
@pytest.fixture
def backup_storage() -> None:
    """Fixture for backup storage (placeholder)."""
    # TODO: Implement actual storage fixture
    return None
```

**Suggested Implementation:**
```python
@pytest.fixture
def backup_storage() -> str:
    """Create an empty backup storage for set_active testing.
    
    This storage is used as a backup target for set_active operations.
    It starts empty and receives data when switching active storage.
    
    Returns:
        Storage identity key string for the backup storage
    """
    # Create separate in-memory SQLite database
    engine = create_engine_from_url("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    
    # Create storage provider with different identity key
    storage = StorageProvider(
        engine=engine, 
        chain="main", 
        storage_identity_key="test_backup_storage"
    )
    storage.make_available()
    
    # Return storage identity key (string) as expected by set_active
    return "test_backup_storage"
```

### 4. `original_storage` Fixture

**Status:** ⚠️ Placeholder exists (returns `None`)

**Required For:**
- `test_set_active_to_backup_and_back_without_backup_first`
- `test_set_active_to_backup_and_back_with_backup_first`

**Expected Type:** Storage identity key string (based on test usage: `_wallet.set_active(backup_storage)`)

**Note:** Tests call `set_active()` with the storage fixture directly, suggesting they expect a string (storage identity key) rather than a StorageProvider object.

**Requirements:**
- Storage provider with the original wallet's data
- Should be the same storage instance used by `_wallet` fixture
- Must be readable/writable
- Used as the "original" storage when switching back from backup

**Current Implementation:**
```python
@pytest.fixture
def original_storage() -> None:
    """Fixture for original storage (placeholder)."""
    # TODO: Implement actual storage fixture
    return None
```

**Suggested Implementation:**
```python
@pytest.fixture
def original_storage(_wallet: Wallet) -> str:
    """Get the original storage identity key from the wallet fixture.
    
    This fixture provides the storage identity key of the wallet's current storage.
    It's used when switching back from backup storage.
    
    Args:
        _wallet: Wallet fixture with seeded data
        
    Returns:
        Storage identity key string from the wallet's storage provider
    """
    if _wallet.storage_provider is None:
        raise ValueError("Wallet must have storage_provider configured")
    return _wallet.storage_provider.storage_identity_key
```

## Test Requirements Summary

### Test: `test_sync_initial_then_no_changes_then_one_change`
- **Needs:** `_wallet` (with >1000 items), `destination_storage` (empty)
- **Purpose:** Verify sync inserts all data, then no changes, then only new changes
- **Expected Behavior:**
  - First sync: `inserts > 1000`, `updates == 2`
  - Second sync: `inserts == 0`, `updates == 0`
  - Third sync: `inserts == 1`, `updates == 0` (after adding one item)

### Test: `test_set_active_to_backup_and_back_without_backup_first`
- **Needs:** `_wallet` (with data), `backup_storage` (empty), `original_storage` (with data)
- **Purpose:** Verify bidirectional sync when switching active storage
- **Expected Behavior:**
  - Switch to backup: backup receives all data from original
  - Switch back to original: original unchanged (no new data in backup)
  - Repeat process: should complete successfully

### Test: `test_set_active_to_backup_and_back_with_backup_first`
- **Needs:** `_wallet` (with data), `backup_storage` (empty), `original_storage` (with data)
- **Purpose:** Verify sync with `backup_first=True` semantics
- **Expected Behavior:**
  - Similar to above but with backup-first semantics maintained

## Implementation Notes

1. **Storage Identity Keys:** Each storage fixture should use a unique `storage_identity_key` to avoid conflicts
2. **Data Seeding:** The `_wallet` fixture needs substantial data seeding (1000+ items) to properly test sync
3. **Isolation:** All fixtures should use in-memory databases for test isolation
4. **Chain Consistency:** All storage fixtures must use the same chain ("main" or "test")
5. **User Setup:** Storage providers need users created before they can be used

## Related Files

- **Test File:** `tests/wallet/test_sync.py`
- **Conftest:** `tests/conftest.py` (contains other wallet fixtures)
- **Reference:** `wallet-toolbox/test/utils/TestUtilsWalletStorage.ts` (TypeScript implementation)
- **Reference:** `go-wallet-toolbox/pkg/storage/internal/testabilities/fixture_sync.go` (Go implementation)

## Method Signature Mismatch

**Important Issue:** There's a mismatch between how tests call methods and how the stub implementations expect parameters:

**Test Usage:**
```python
_wallet.sync_to_writer(destination_storage)  # Passes storage directly
_wallet.set_active(backup_storage)           # Passes storage directly
```

**Current Stub Implementation:**
```python
def sync_to_writer(self, args: dict[str, Any]) -> dict[str, Any]:
    # Expects: {"writer": storage_key, "options": {...}}
    
def set_active(self, args: dict[str, Any] | str) -> None:
    # Accepts both: string OR {"storage": storage_key, "backup_first": False}
```

**Resolution Options:**
1. **Update tests** to pass dicts: `_wallet.sync_to_writer({"writer": destination_storage, "options": {}})`
2. **Update method signatures** to accept storage directly and wrap internally
3. **Make `sync_to_writer` accept both forms** (like `set_active` already does)

**Recommendation:** Option 3 - Update `sync_to_writer` to accept both string and dict forms for consistency.

## Next Steps

1. ✅ Document fixtures (this document)
2. Resolve method signature mismatch (update `sync_to_writer` OR tests)
3. Implement `_wallet` fixture with data seeding (>1000 items)
4. Implement `destination_storage` fixture (returns storage identity key string)
5. Implement `backup_storage` fixture (returns storage identity key string)
6. Implement `original_storage` fixture (returns storage identity key string from wallet)
7. Run functional tests to verify sync behavior

