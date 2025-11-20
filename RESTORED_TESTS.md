# Restored Tests - Incorrectly Skipped

This document tracks tests that were incorrectly marked as skip but have implementations.

## Summary

**Total Restored:** 23 tests
- **Permissions Tests:** 15 tests restored
- **Chaintracks Tests:** 8 tests restored

## Restored Files

### WalletPermissionsManager Tests (15 tests)
- `tests/permissions/test_wallet_permissions_manager_initialization.py`
  - test_should_initialize_with_default_config_if_none_is_provided
  - test_should_initialize_with_partial_config_overrides_merging_with_defaults
  - test_should_initialize_with_all_config_flags_set_to_false
  - test_should_consider_calls_from_the_adminoriginator_as_admin_bypassing_checks
  - test_should_skip_protocol_permission_checks_for_signing_if_seekprotocolpermissionsforsigning_false
  - test_should_enforce_protocol_permission_checks_for_signing_if_seekprotocolpermissionsforsigning_true
  - test_should_skip_basket_insertion_permission_checks_if_seekbasketinsertionpermissions_false
  - test_should_skip_certificate_disclosure_permission_checks_if_seekcertificatedisclosurepermissions_false
  - test_should_skip_metadata_encryption_if_encryptwalletmetadata_false

- `tests/permissions/test_wallet_permissions_manager_encryption.py`
  - test_should_encrypt_metadata_fields_in_createaction_when_encryptwalletmetadata_true_then_decrypt_them_in_listactions
  - test_should_not_encrypt_metadata_if_encryptwalletmetadata_false_storing_and_retrieving_plaintext
  - test_should_decrypt_custominstructions_in_listoutputs_if_encryptwalletmetadata_true
  - test_should_fallback_to_the_original_ciphertext_if_decrypt_fails_in_listoutputs

### Chaintracks Tests (8 tests)
- `tests/chaintracks/test_chaintracks.py`
  - test_nodb_mainnet
  - test_nodb_testnet

- `tests/chaintracks/test_fetch.py`
  - test_fetchjson
  - test_download
  - test_download_716
  - test_download_717

- `tests/chaintracks/test_service_client.py`
  - test_mainnet_findheaderforheight
  - test_testnet_findheaderforheight

## Implementation Status

### WalletPermissionsManager ✅
**Location:** `src/bsv_wallet_toolbox/manager/wallet_permissions_manager.py`
**Size:** 764 lines
**Methods:** 27 methods including:
- DPACP (Protocol): grant, request, verify, revoke, list
- DBAP (Basket): grant, request, verify, list
- DCAP (Certificate): grant, request, verify, list
- DSAP (Spending): grant, request, verify, track, list
- Token management: create, revoke, verify
- Callbacks: bind, unbind
- Persistence: load, save

### Chaintracks ✅
**Location:** `src/bsv_wallet_toolbox/services/chaintracker/`
**Components:**
- `chaintracks_service.py` - HTTP service implementation
- `chaintracks_storage.py` - Storage backend
- `chaintracks_service_client.py` - Client interface
- `chaintracks/api/` - API definitions
- `chaintracks/storage/` - Storage implementations
- `chaintracks/util/` - Utilities (HeightRange, BulkFileDataManager, etc.)

## Batch Test Commands

### Test Permissions Only
```bash
cd /home/sneakyfox/TOOLBOX/py-wallet-toolbox
python -m pytest tests/permissions/ -x --tb=short
```

### Test Chaintracks Only
```bash
cd /home/sneakyfox/TOOLBOX/py-wallet-toolbox
python -m pytest tests/chaintracks/ -x --tb=short
```

### Test All Restored (Stop at First Failure)
```bash
cd /home/sneakyfox/TOOLBOX/py-wallet-toolbox
python -m pytest tests/permissions/ tests/chaintracks/ -x --tb=short
```

### Test All Restored (Full Report)
```bash
cd /home/sneakyfox/TOOLBOX/py-wallet-toolbox
python -m pytest tests/permissions/ tests/chaintracks/ --tb=short
```

### Verbose Mode for Debugging
```bash
cd /home/sneakyfox/TOOLBOX/py-wallet-toolbox
python -m pytest tests/permissions/ tests/chaintracks/ -x -vv --tb=long
```

## Tests Still Properly Skipped

These remain skipped as they lack implementations:

### Monitor (1 test) - NO IMPLEMENTATION
- `tests/monitor/test_live_ingestor_whats_on_chain_poll.py`
- **Reason:** No monitor module found in `src/`

### Certificate Subsystem (1 test) - PARTIAL IMPLEMENTATION
- `tests/certificates/test_certificate_life_cycle.py`
- **Reason:** No dedicated certificate module, only wallet methods

### Universal Vectors (10 tests) - NEED DETERMINISTIC STATE
- createAction, signAction, internalizeAction
- listActions, listOutputs, listCertificates
- relinquishOutput, getPublicKey
- **Reason:** Require exact wallet state matching test vectors

## Next Steps

1. Run permissions tests with `-x` flag to find first failure
2. Document failure details
3. Fix the failure
4. Repeat until all tests pass
5. Run chaintracks tests
6. Fix any chaintracks failures

## Expected Issues

### Likely Permissions Test Issues:
- Mock configuration mismatches
- Async/sync method call differences
- Missing test fixtures for wallet/storage

### Likely Chaintracks Test Issues:
- CDN network calls (may need mocking)
- Database setup requirements
- Async operation handling

---

**Date Restored:** 2025-11-20  
**Restored By:** Systematic test recovery after incorrect skip marking  
**Total Tests Restored:** 23 tests (15 permissions + 8 chaintracks)

