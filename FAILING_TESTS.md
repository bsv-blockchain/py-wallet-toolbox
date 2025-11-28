# Failing Tests Report

## Summary
**Total Tests Run**: 867
- ✅ **Passed**: 388 (44.75%)
- ❌ **Failed**: 65 (7.50%)
- ⏭️ **Skipped**: 406 (46.83%)
- ⚠️ **XFailed**: 8 (0.92%)
- 🔧 **Errors**: 11 (1.27%)

**Overall Coverage**: 47.97%

## Failing Test Categories

### 1. Protocol Name Validation (16 tests)
**Issue**: Protocol names ending with " protocol" are rejected by the underlying BSV SDK key deriver.

**Affected Tests**:
- `tests/wallet/test_hmac_signature.py::TestWalletCreateHmac::test_create_hmac`
- `tests/wallet/test_hmac_signature.py::TestWalletVerifyHmac::test_verify_hmac_valid`
- `tests/wallet/test_hmac_signature.py::TestWalletVerifyHmac::test_verify_hmac_invalid`
- `tests/wallet/test_hmac_signature.py::TestWalletCreateSignature::test_create_signature`
- `tests/wallet/test_hmac_signature.py::TestWalletVerifySignature::test_verify_signature_valid`
- `tests/wallet/test_hmac_signature.py::TestWalletVerifySignature::test_verify_signature_invalid`
- `tests/wallet/test_crypto_methods.py::TestWalletGetPublicKey::test_get_public_key_with_protocol_id`
- `tests/wallet/test_crypto_methods.py::TestWalletCreateHmac::test_create_hmac`
- `tests/wallet/test_crypto_methods.py::TestWalletVerifyHmac::test_verify_hmac_valid`
- `tests/wallet/test_crypto_methods.py::TestWalletVerifyHmac::test_verify_hmac_invalid`
- `tests/wallet/test_crypto_methods.py::TestWalletCreateSignature::test_create_signature`
- `tests/wallet/test_crypto_methods.py::TestWalletVerifySignature::test_verify_signature_valid`
- `tests/wallet/test_crypto_methods.py::TestWalletVerifySignature::test_verify_signature_invalid`

**Error**: `ValueError: no need to end your protocol name with " protocol"`

**Solution**: Change test protocol names from `"test protocol"` to `"test"` or similar.

### 2. Storage/Database Issues (13 tests)
**Issue**: Tests require populated databases and proper storage setup that isn't available.

**Affected Tests**:
- `tests/wallet/test_internalize_action.py::TestWalletInternalizeAction::test_internalize_custom_output_basket_insertion`
- `tests/wallet/test_list_actions.py::TestWalletListActions::test_specific_label_filter`
- `tests/wallet/test_list_certificates.py::*` (6 tests)
- `tests/wallet/test_list_outputs.py::*` (5 tests)

**Common Errors**:
- `InvalidParameterError: Invalid parameter 'tx': valid AtomicBEEF with minimum 4 bytes`
- `AssertionError: assert 0 == expected_count`
- `KeyError: 'userId'`

**Solution**: Implement proper database fixtures and test data setup.

### 3. Services Not Configured (4 tests)
**Issue**: Tests require blockchain services (WhatsOnChain, ARC, etc.) that aren't properly mocked.

**Affected Tests**:
- `tests/wallet/test_certificates.py::TestWalletAcquireCertificate::*`
- `tests/wallet/test_certificates.py::TestWalletProveCertificate::test_prove_certificate`
- `tests/wallet/test_certificates.py::TestWalletDiscoverByIdentityKey::test_discover_by_identity_key`
- `tests/wallet/test_certificates.py::TestWalletDiscoverByAttributes::test_discover_by_attributes`

**Error**: `RuntimeError: services are not configured`

**Solution**: Add proper service mocking in test fixtures.

### 4. Async/Coroutine Issues (3 tests)
**Issue**: Tests expecting synchronous results but getting coroutines.

**Affected Tests**:
- `tests/services/test_local_services_hash_and_locktime.py::*`
- `tests/services/test_whats_on_chain.py::*` (2 tests)

**Error**: `TypeError: int() argument must be a string, a bytes-like object or a real number, not 'coroutine'`

**Solution**: Fix async/await handling in service methods.

### 5. Attribute Naming Mismatches (10 tests)
**Issue**: Database model attributes use snake_case but tests expect camelCase.

**Affected Tests**:
- `tests/storage/test_update.py::*` (9 tests)
- `tests/wallet/test_wallet_create_action.py::TestWalletCreateAction::test_repeatable_txid`

**Error**: `AttributeError: type object 'ModelName' has no attribute 'camelCaseAttribute'`

**Solution**: Update tests to use correct snake_case attribute names.

### 6. Missing Implementations (6 tests)
**Issue**: Core functionality not yet implemented.

**Affected Tests**:
- `tests/chaintracks/test_service_client.py::*` (2 tests)
- `tests/services/test_get_merkle_path.py::*`
- `tests/services/test_get_raw_tx.py::*`
- `tests/wallet/test_crypto_methods.py::*` (2 tests)

**Errors**:
- `AttributeError: 'KeyDeriver' object has no attribute 'reveal_counterparty_key_linkage'`
- `AttributeError: 'Services' object has no attribute 'get_merkle_path'`
- `assert None is not None`

**Solution**: Implement missing methods in respective classes.

### 7. Validation and Parameter Issues (6 tests)
**Issue**: Tests expecting specific validation behavior that isn't implemented.

**Affected Tests**:
- `tests/wallet/test_abort_action.py::*`
- `tests/wallet/test_sign_process_action.py::*` (4 tests)
- `tests/utils/validation/test_validate_internalize_action_args.py::*` (2 tests)

**Errors**:
- `InvalidParameterError: Invalid parameter 'reference': transaction not found`
- `AssertionError: assert 'label' in error_message`

**Solution**: Implement proper validation logic and error handling.

### 8. Miscellaneous Issues (7 tests)
**Affected Tests**:
- `tests/storage/test_create_action.py::*`
- `tests/wallet/test_relinquish_output.py::*`
- `tests/wallet/test_wallet_create_action.py::*`

**Errors**:
- Various assertion failures and missing parameters

**Solution**: Fix individual test issues as identified.
