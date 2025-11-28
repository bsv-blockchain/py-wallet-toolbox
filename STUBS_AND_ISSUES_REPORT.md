# Stubs and Issues Report - py-wallet-toolbox

This report documents all stubbed functionality, incomplete implementations, and issues found in the recent test additions and functionality.

**Generated:** 2025-11-20

---

## 🔴 Critical Issues

### 1. SQLAlchemy Session Management Conflicts
**Affected:** 6 wallet integration tests  
**Status:** Known issue, tests skipped  

**Problem:** Cross-session object conflicts when fixtures seed data and tests query it.

```python
sqlalchemy.exc.InvalidRequestError: Object '<Transaction at 0x...>' is already attached to session 'X' (this is 'Y')
```

**Affected Tests:**
- `tests/wallet/test_abort_action.py::test_abort_specific_reference`
- `tests/wallet/test_relinquish_output.py::test_relinquish_specific_output`
- `tests/wallet/test_sign_process_action.py` (multiple tests: 5 tests)
- `tests/wallet/test_internalize_action.py::test_internalize_custom_output_basket_insertion`

**Solution:** Implement `scoped_session` or add `session.expunge()` in `StorageProvider._insert_generic()`

**Reference:** `tests/fixtures/SESSION_MANAGEMENT_ISSUE.md`

---

### 2. Async/Sync Mismatch in Services Layer
**Affected:** `tests/services/test_get_raw_tx.py`  
**Status:** Test skipped

**Problem:** Provider methods are async but Services calls them synchronously.

```python
@pytest.mark.skip(reason="Async/sync mismatch - provider methods are async but Services calls them synchronously")
```

**Solution:** Either make Services async-aware or create sync wrappers for provider methods.

---

## 🟠 Missing Core Subsystems

### 3. Certificate Subsystem (Not Implemented)
**Affected:** 11+ tests across multiple files  
**Impact:** High - BRC-100 certificate functionality incomplete

**Missing Helper Functions (in `tests/wallet/test_certificates.py`):**
```python
def _make_sample_cert(subject: str) -> tuple:
    raise NotImplementedError("Certificate helper not implemented yet")

def _create_proto_wallet(certifier: str) -> Never:
    raise NotImplementedError("ProtoWallet not implemented yet")

def _create_certificate(cert_data: dict) -> dict:
    raise NotImplementedError("Certificate creation not implemented yet")

def _create_certificate_fields(wallet, subject: str, fields: dict) -> dict:
    raise NotImplementedError("MasterCertificate.createCertificateFields not implemented yet")

def _create_signed_certificate(cert_data: dict, signed_fields: dict) -> dict:
    raise NotImplementedError("Signed certificate creation not implemented yet")

def _sign_certificate(cert: dict, wallet) -> None:
    raise NotImplementedError("Certificate signing not implemented yet")

def _create_verifiable_certificate(cert: dict, keyring: dict) -> Never:
    raise NotImplementedError("VerifiableCertificate not implemented yet")

def _decrypt_fields(cert, wallet, privileged: bool = False, privileged_reason: str = None) -> dict:
    raise NotImplementedError("Field decryption not implemented yet")
```

**Affected Test Files:**
- `tests/certificates/test_certificate_life_cycle.py` (1 test)
- `tests/wallet/test_certificates.py` (5 tests)
- `tests/universal/test_acquirecertificate.py` (2 tests marked xfail - incomplete test vectors)
- `tests/universal/test_provecertificate.py` (1 test)
- `tests/universal/test_relinquishcertificate.py` (1 test)
- `tests/universal/test_discoverbyidentitykey.py` (1 test)
- `tests/universal/test_discoverbyattributes.py` (1 test)

**Total:** 12 tests skipped due to missing certificate subsystem

---

### 4. Crypto Subsystem Methods (Not Implemented)
**Affected:** 8 universal test files  
**Impact:** Medium - BRC-100 crypto operations incomplete

**Missing Methods:**
- `wallet.encrypt()` - Not implemented
- `wallet.decrypt()` - Not implemented
- `wallet.create_hmac()` - Not implemented
- `wallet.verify_hmac()` - Not implemented
- `wallet.create_signature()` - Not implemented
- `wallet.verify_signature()` - Not implemented
- `wallet.reveal_counterparty_key_linkage()` - Not implemented
- `wallet.reveal_specific_key_linkage()` - Not implemented

**Affected Test Files:**
- `tests/universal/test_encrypt.py`
- `tests/universal/test_decrypt.py`
- `tests/universal/test_createhmac.py`
- `tests/universal/test_verifyhmac.py`
- `tests/universal/test_createsignature.py`
- `tests/universal/test_verifysignature.py`
- `tests/universal/test_revealcounterpartykeylinkage.py`
- `tests/universal/test_revealspecifickeylinkage.py`

**Total:** 8 tests skipped due to missing crypto subsystem

**Note:** These are also marked in `conftest.py` skip patterns:
```python
"test_reveal_counterparty_key_linkage": "TODO: Implement reveal_counterparty_key_linkage method",
"test_reveal_specific_key_linkage": "TODO: Implement reveal_specific_key_linkage method",
```

---

### 5. Wallet Sync Subsystem (Not Implemented)
**Affected:** 3 tests in `tests/wallet/test_sync.py`  
**Impact:** Medium - Multi-storage sync functionality missing

**Missing Fixtures:**
```python
@pytest.fixture
def destination_storage() -> None:
    """Fixture for destination storage (placeholder)."""
    # TODO: Implement actual storage fixture
    return None

@pytest.fixture
def backup_storage() -> None:
    """Fixture for backup storage (placeholder)."""
    # TODO: Implement actual storage fixture
    return None

@pytest.fixture
def original_storage() -> None:
    """Fixture for original storage (placeholder)."""
    # TODO: Implement actual storage fixture
    return None
```

**Affected Tests:**
- `test_sync_initial_then_no_changes_then_one_change` - Sync infrastructure missing
- `test_set_active_to_backup_and_back_without_backup_first` - Sync infrastructure missing
- `test_set_active_to_backup_and_back_with_backup_first` - Sync infrastructure missing

**Total:** 3 tests skipped

---

## 🟡 Incomplete Implementations

### 6. WalletPermissionsManager Permission Checks
**Location:** `src/bsv_wallet_toolbox/manager/wallet_permissions_manager.py`  
**Status:** Methods implemented but permission checks stubbed with TODOs  
**Impact:** Medium - Permission system lacks enforcement

**Methods with TODO permission checks (18 instances):**

```python
# Line 709-712: Persistent storage
# TODO: Phase 4 - Implement persistent storage (SQLite/PostgreSQL)
# TODO: Phase 4 - Serialize permission tokens to database
# TODO: Phase 4 - Handle concurrent access with transactions
# TODO: Phase 4 - Add backup/recovery mechanism

# Line 790-792: Authorization
# TODO: Phase 4 - Implement caller authorization checks
# TODO: Phase 4 - Verify originator against admin list
# TODO: Phase 4 - Check permission tokens from storage

# Line 915: create_signature
# TODO: Implement permission check

# Line 937: sign_action
# TODO: Add permission checks

# Line 958: abort_action
# TODO: Add permission checks

# Line 978: internalize_action
# TODO: Add permission checks for basket insertion

# Line 997: relinquish_output
# TODO: Add basket removal permission checks

# Line 1016: get_public_key
# TODO: Add protocol permission checks

# Line 1035: reveal_counterparty_key_linkage
# TODO: Add key linkage revelation permission checks

# Line 1054: reveal_specific_key_linkage
# TODO: Add key linkage revelation permission checks

# Line 1073: encrypt
# TODO: Add protocol permission checks for encrypting

# Line 1092: decrypt
# TODO: Add protocol permission checks for decrypting

# Line 1111: create_hmac
# TODO: Add protocol permission checks for HMAC

# Line 1130: verify_hmac
# TODO: Add protocol permission checks

# Line 1149: verify_signature
# TODO: Add protocol permission checks

# Line 1168: acquire_certificate
# TODO: Add certificate acquisition permission checks

# Line 1187: list_certificates
# TODO: Add certificate listing permission checks

# Line 1206: prove_certificate
# TODO: Add certificate proving permission checks

# Line 1225: relinquish_certificate
# TODO: Add certificate relinquishment permission checks

# Line 1246: disclose_certificate
# TODO: Implement permission check

# Line 1267: discover_by_identity_key
# TODO: Add identity resolution permission checks

# Line 1286: discover_by_attributes
# TODO: Add identity resolution permission checks
```

**Affected Tests:**
- `tests/permissions/test_wallet_permissions_manager_flows.py` (entire class skipped)
- `tests/permissions/test_wallet_permissions_manager_checks.py` (entire class skipped)
- `tests/permissions/test_wallet_permissions_manager_tokens.py` (entire class skipped - 15 tests)
- `tests/permissions/test_wallet_permissions_manager_callbacks.py` (entire class skipped)

**Total:** ~20+ tests skipped awaiting permission subsystem completion

---

### 7. Storage Layer - createAction Parity Issues
**Location:** `tests/storage/test_create_action.py`  
**Status:** Tests marked xfail with strict=True  
**Impact:** Low - Tests document missing parity with TS/Go implementations

**Missing Features (5 xfail tests):**

```python
@pytest.mark.xfail(reason="TODO: parity with TS/Go noSendChange duplicate check", strict=True)
def test_create_action_nosendchange_duplicate(...): ...

@pytest.mark.xfail(reason="TODO: parity with TS/Go output tag propagation", strict=True)
def test_create_action_output_tags_persisted(...): ...

@pytest.mark.xfail(reason="TODO: parity with TS/Go signAndProcess happy path", strict=True)
def test_create_action_sign_and_process_happy_path(...): ...

@pytest.mark.xfail(reason="TODO: parity with TS/Go noSendChange sequencing", strict=True)
def test_create_action_nosendchange_output_sequence(...): ...

@pytest.mark.xfail(reason="TODO: parity with TS randomizeOutputs", strict=True)
def test_create_action_randomizes_outputs(...): ...
```

**Total:** 5 xfail tests documenting missing parity

---

### 8. Storage Layer - Database Constraint Validation
**Location:** Dynamically skipped in `tests/conftest.py`  
**Status:** Constraint validation not implemented  
**Impact:** Low - Test infrastructure issue

**Tests Skipped via conftest.py (lines 581-606):**

```python
skip_patterns = {
    # Test data format issues (4 tests)
    "test_insert_proventx": "TODO: merkle_path should be bytes, not list",
    "test_insert_proventxreq": "TODO: Test data format issue",
    "test_insert_monitorevent": "TODO: Test data format issue",
    "test_insert_syncstate": "TODO: Test data format issue",
    
    # DB constraint validation (4 tests)
    "test_update_user_trigger_db_unique_constraint_errors": "TODO: Implement DB unique constraint validation",
    "test_update_user_trigger_db_foreign_key_constraint_errors": "TODO: Implement DB foreign key constraint validation",
    "test_update_certificate_trigger_db_unique_constraint_errors": "TODO: Implement DB unique constraint validation",
    "test_update_certificate_trigger_db_foreign_key_constraint_errors": "TODO: Implement DB foreign key constraint validation",
    
    # Merge existing storage integration (2 tests)
    "test_mergeexisting_updates_user_when_ei_updated_at_is_newer": "TODO: Add storage mock for merge_existing",
    "test_mergeexisting_updates_user_with_trx": "TODO: Add storage mock for merge_existing",
    
    # FK relationship setup (3 tests)
    "test_insert_commission": "TODO: Transaction FK relationship setup",
    "test_insert_output": "TODO: Transaction FK relationship setup",
    "test_insert_outputtagmap": "TODO: OutputTag FK relationship setup",
    
    # Test data issues (2 tests)
    "test_insert_certificate": "TODO: Test data missing required revocationOutpoint",
    "test_insert_certificatefield": "TODO: Test data format or FK issue",
}
```

**Total:** 15 tests skipped via conftest

---

### 9. Missing Test Fixtures
**Affected:** 2 tests in `tests/wallet/test_wallet_create_action.py`  
**Impact:** Low

**Missing Fixture:**
```python
@pytest.mark.skip(reason="Fixture wallet_with_mocked_create_action not yet implemented")
def test_create_action_defaults_options_and_returns_signable(...): ...

@pytest.mark.skip(reason="Fixture wallet_with_mocked_create_action not yet implemented")
def test_create_action_sign_and_process_flow(...): ...
```

**Total:** 2 tests skipped

---

### 10. Universal Test Vector Issues
**Location:** `tests/universal/` directory  
**Status:** Test vectors incomplete or missing data  
**Impact:** Low - Test infrastructure issue

**Tests Marked xfail:**

```python
# tests/universal/test_abortaction.py
@pytest.mark.xfail(reason="Test vector incomplete: transaction with reference 'dGVzdA==' must be pre-created in database")
def test_abortaction_json_matches_universal_vectors(...): ...

# tests/universal/test_acquirecertificate.py
@pytest.mark.xfail(reason="Test vector incomplete: missing required 'subject' field in simple variant")
def test_acquirecertificate_simple_json_matches_universal_vectors(...): ...

@pytest.mark.xfail(reason="Test vector incomplete: missing required 'serialNumber' field in issuance variant")
def test_acquirecertificate_issuance_json_matches_universal_vectors(...): ...
```

**Total:** 3 xfail tests due to incomplete test vectors

---

### 11. Tests Requiring Deterministic Wallet State
**Affected:** Multiple universal tests  
**Status:** Tests skipped - need seeded wallet fixtures  
**Impact:** Low - Test infrastructure issue

**Tests Requiring Wallet Seeding (11 tests):**

- `tests/universal/test_listoutputs.py::test_listoutputs_json_matches_universal_vectors`
  - "Requires deterministic wallet state with seeded outputs"

- `tests/universal/test_getpublickey.py::test_getpublickey_json_matches_universal_vectors`
  - "Requires deterministic key derivation setup"

- `tests/universal/test_listcertificates.py` (2 tests)
  - "Requires deterministic wallet state with seeded certificates"

- `tests/universal/test_listactions.py::test_listactions_json_matches_universal_vectors`
  - "Requires deterministic wallet state with seeded transactions"

- `tests/universal/test_relinquishoutput.py::test_relinquishoutput_json_matches_universal_vectors`
  - "Requires deterministic wallet state with seeded outputs"

- `tests/universal/test_internalizeaction.py::test_internalizeaction_json_matches_universal_vectors`
  - "Requires deterministic wallet state"

- `tests/universal/test_signaction.py::test_signaction_json_matches_universal_vectors`
  - "Requires deterministic pending action state"

- `tests/universal/test_createaction.py` (2 tests)
  - "Requires deterministic wallet state with exact UTXO and key configuration"

- `tests/wallet/test_sign_process_action.py` (5 tests)
  - "Requires proper pending sign action setup with inputBeef"
  - "Requires proper transaction state setup"

- `tests/wallet/test_list_certificates.py` (4 tests)
  - "Requires populated test database with specific certificate test data from TypeScript"

**Total:** 20+ tests skipped requiring deterministic state

---

### 12. Network/Integration Tests
**Affected:** Various test files  
**Status:** Tests skipped - require external services  
**Impact:** Low - Integration tests, not unit tests

**Tests Requiring External Services:**

- `tests/chaintracks/test_service_client.py` (2 tests)
  - "Requires running Chaintracks service"

- `tests/chaintracks/test_fetch.py` (4 tests)
  - "Requires network access to CDN"

- `tests/services/test_get_merkle_path.py::test_get_merkle_path_placeholder`
  - "Integration test requiring async service calls and network access"

- `tests/utils/test_pushdrop.py::test_pushdrop_decode_integration`
  - "Integration test requiring live network and wallet setup"

- `tests/services/test_exchange_rates.py::test_update_exchange_rates`
  - "update_exchangeratesapi not yet implemented"

**Total:** ~10 tests skipped (integration/network tests)

---

### 13. Monitor System Not Implemented
**Affected:** 1 test  
**Impact:** Low

```python
# tests/monitor/test_live_ingestor_whats_on_chain_poll.py
@pytest.mark.skip(reason="Requires full Monitor system implementation")
def test_monitor_ingestor_whatsonchain_live_poll(...): ...
```

---

### 14. BEEF Parsing Not Integrated
**Affected:** 1 test in `tests/services/test_verify_beef.py`  
**Impact:** Low

```python
@pytest.mark.skip(reason="Beef.from_string not available, needs parse_beef integration")
def test_verify_beef(...): ...
```

---

### 15. Complex Permission Queueing Not Implemented
**Affected:** 1 test  
**Impact:** Low

```python
# tests/permissions/test_wallet_permissions_manager_initialization.py
@pytest.mark.skip(reason="Complex async permission queueing not yet implemented")
def test_should_allow_queueing_multiple_permission_requests(...): ...
```

---

### 16. Unclear Test Expectation
**Affected:** 1 test  
**Impact:** Low

```python
# tests/permissions/test_wallet_permissions_manager_encryption.py
@pytest.mark.skip(reason="Test expectation unclear - expects decrypt calls when encryption=False")
def test_should_not_attempt_decryption_when_encryption_is_off(...): ...
```

---

## 🟢 NotImplementedError in Service Providers (Expected Behavior)

### 17. WhatsOnChain Provider - Expected Limitations
**Location:** `src/bsv_wallet_toolbox/services/providers/whatsonchain.py`  
**Status:** Intentional - Not supported by WhatsOnChain API  
**Impact:** None - These are correct for this provider

**Methods that raise NotImplementedError (by design):**
- `get_info()` - Line 87: "Not supported by WhatsOnChain provider"
- `get_headers()` - Line 108: "No bulk header API"
- `add_header()` - Line 231: "WhatsOnChain is read-only"
- `start_listening()` - Line 241: "Not supported"
- `listening()` - Line 251: "Not supported"
- `subscribe_headers()` - Line 281: "Not supported"
- `subscribe_reorgs()` - Line 291: "Not supported"
- `unsubscribe()` - Line 301: "Not supported"

**Note:** These are correct - WhatsOnChain doesn't support these features. Other providers (ChainTracks) should implement them.

---

### 18. ChainTracks WebSocket - Phase 4 TODO
**Location:** `src/bsv_wallet_toolbox/services/chaintracker/chaintracks_service_client.py`  
**Status:** Planned for Phase 4  
**Impact:** Low - WebSocket features deferred

**Methods that raise NotImplementedError:**
- `subscribe_headers()` - Line 287: "WebSocket subscriptions require Phase 4 implementation"
- `subscribe_reorgs()` - Line 301: "WebSocket subscriptions require Phase 4 implementation"
- `unsubscribe()` - Line 315: "WebSocket unsubscription requires Phase 4 implementation"

---

### 19. ChainTracks Storage Integration TODOs
**Location:** `src/bsv_wallet_toolbox/services/chaintracker/chaintracks/chaintracks.py`  
**Status:** Basic functionality works, advanced features deferred  
**Impact:** Low

```python
# Line 70
# TODO: Load headers from storage or remote source
# For now, just mark as available with a reasonable height

# Line 109
# TODO: Close storage connections if using database
```

---

## 📊 Summary Statistics

### Tests by Status

| Status | Count | Category |
|--------|-------|----------|
| ❌ Skipped - Certificate subsystem | 12 | Missing core feature |
| ❌ Skipped - Crypto subsystem | 8 | Missing core feature |
| ❌ Skipped - Sync subsystem | 3 | Missing core feature |
| ❌ Skipped - Permissions Manager | 20+ | Incomplete implementation |
| ❌ Skipped - Deterministic state needed | 20+ | Test infrastructure |
| ❌ Skipped - Session conflicts | 6 | Critical bug |
| ❌ Skipped - Integration/network | 10 | External dependencies |
| ❌ Skipped - Storage via conftest | 15 | Test data issues |
| ⚠️ xfail - Storage parity | 5 | Missing features |
| ⚠️ xfail - Test vector issues | 3 | Test infrastructure |
| ❌ Skipped - Missing fixtures | 5 | Test infrastructure |
| ❌ Skipped - Other issues | 7 | Various |

**Total Skipped/xfail Tests:** ~115+ tests

**Total TODO Comments in Source:** 30+ (mostly in WalletPermissionsManager)

**Total NotImplementedError (by design):** 11 (in service providers, expected)

---

## 🎯 Priority Recommendations

### High Priority (Should Fix Soon)

1. **SQLAlchemy Session Management** (6 tests)
   - Quick fix: Add `scoped_session` or `session.expunge()`
   - High impact on integration tests

2. **Services async/sync mismatch** (1 test)
   - Affects service layer testing
   - May indicate architectural issue

3. **Storage conftest skips** (15 tests)
   - Fix test data format issues
   - Add constraint validation
   - Most are test infrastructure issues

### Medium Priority (Can Wait)

4. **Deterministic wallet state fixtures** (20+ tests)
   - Create proper seeding fixtures
   - Enables universal test vector validation

5. **WalletPermissionsManager permission checks** (20+ tests)
   - Currently methods exist but don't enforce permissions
   - Mark as Phase 4 if intended

6. **Storage createAction parity** (5 xfail tests)
   - Document known differences from TS/Go
   - Decide if Python needs same behavior

### Low Priority (Future Work)

7. **Certificate subsystem** (12 tests)
   - Large feature area
   - Requires significant development

8. **Crypto subsystem methods** (8 tests)
   - Core BRC-100 functionality
   - Should be implemented eventually

9. **Sync subsystem** (3 tests)
   - Multi-storage sync feature
   - Can be deferred

10. **Integration/network tests** (10 tests)
   - Require external services
   - Good to have but not critical

---

## ✅ What's Working Well

### Completed Features
- ✅ Wallet core functionality (create_action, list_outputs, etc.)
- ✅ Storage layer (basic CRUD operations)
- ✅ SimpleWalletManager (100% complete)
- ✅ CWIStyleWalletManager (100% complete)
- ✅ WalletSettingsManager (100% complete)
- ✅ Services layer (basic operations)
- ✅ ChainTracks integration (Phase 1-3)
- ✅ Utility helpers and validation
- ✅ Basic test infrastructure (fixtures, conftest)

### Test Coverage
- Passing tests: 200+ tests passing
- Well-documented: Most skipped tests have clear skip reasons
- Good test structure: Following TS/Go test patterns

---

## 📝 Notes

1. **Skip Reasons Are Well-Documented**: Most skipped tests have clear, actionable skip reasons.

2. **xfail vs skip**: 
   - `xfail` is used for known issues that should be fixed (storage parity)
   - `skip` is used for missing subsystems or external dependencies

3. **Phase 4 TODOs**: Many TODOs are explicitly marked "Phase 4" indicating planned future work.

4. **Test Vector Issues**: Some universal test vectors are incomplete - may need upstream fixes.

5. **By Design**: WhatsOnChain NotImplementedError instances are correct and expected.

---

**Report End**

