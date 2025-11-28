# Skipped Tests Report

## Executive Summary

**Total Skipped Tests**: 442 (approximately 50% of all tests)

**Last Updated**: Generated from test suite analysis

This report provides a comprehensive analysis of all skipped tests in the py-wallet-toolbox, categorized by reason and implementation status. Tests are skipped for various reasons including missing implementations, test infrastructure requirements, and TypeScript parity considerations.

## Key Findings

### Tests Ready to Unskip (14 tests)

These tests are for **implemented methods** but are still marked as skipped. They should be reviewed and potentially unskipped:

**Implemented Methods**:
- `abort_action`
- `acquire_certificate`
- `create_hmac`
- `create_signature`
- `decrypt`
- `discover_by_attributes`
- `discover_by_identity_key`
- `encrypt`
- `internalize_action`
- `list_actions`
- `list_certificates`
- `list_outputs`
- `prove_certificate`
- `relinquish_certificate`
- `relinquish_output`
- `reveal_counterparty_key_linkage`
- `reveal_specific_key_linkage`
- `sign_action`
- `verify_hmac`
- `verify_signature`

**Tests that can potentially be unskipped**:

- `universal/test_createsignature.py::test_createsignature_json_matches_universal_vectors`
  - **Reason**: Waiting for create_signature implementation
  - **Action**: Review and verify implementation completeness
- `universal/test_revealspecifickeylinkage.py::test_revealspecifickeylinkage_json_matches_universal_vectors`
  - **Reason**: Waiting for reveal_specific_key_linkage implementation
  - **Action**: Review and verify implementation completeness
- `universal/test_discoverbyattributes.py::test_discoverbyattributes_json_matches_universal_vectors`
  - **Reason**: Waiting for discover_by_attributes implementation
  - **Action**: Review and verify implementation completeness
- `universal/test_revealcounterpartykeylinkage.py::test_revealcounterpartykeylinkage_json_matches_universal_vectors`
  - **Reason**: Waiting for reveal_counterparty_key_linkage implementation
  - **Action**: Review and verify implementation completeness
- `universal/test_discoverbyidentitykey.py::test_discoverbyidentitykey_json_matches_universal_vectors`
  - **Reason**: Waiting for discover_by_identity_key implementation
  - **Action**: Review and verify implementation completeness
- `universal/test_verifysignature.py::test_verifysignature_json_matches_universal_vectors`
  - **Reason**: Waiting for verify_signature implementation
  - **Action**: Review and verify implementation completeness
- `universal/test_listcertificates.py::test_listcertificates_simple_json_matches_universal_vectors`
  - **Reason**: Waiting for list_certificates implementation
  - **Action**: Review and verify implementation completeness
- `universal/test_listcertificates.py::test_listcertificates_full_json_matches_universal_vectors`
  - **Reason**: Waiting for list_certificates implementation
  - **Action**: Review and verify implementation completeness
- `universal/test_relinquishoutput.py::test_relinquishoutput_json_matches_universal_vectors`
  - **Reason**: Waiting for relinquish_output implementation
  - **Action**: Review and verify implementation completeness
- `universal/test_decrypt.py::test_decrypt_json_matches_universal_vectors`
  - **Reason**: Waiting for decrypt implementation
  - **Action**: Review and verify implementation completeness
- `universal/test_listoutputs.py::test_listoutputs_json_matches_universal_vectors`
  - **Reason**: Waiting for list_outputs implementation
  - **Action**: Review and verify implementation completeness
- `universal/test_signaction.py::test_signaction_json_matches_universal_vectors`
  - **Reason**: Waiting for sign_action implementation
  - **Action**: Review and verify implementation completeness
- `universal/test_provecertificate.py::test_provecertificate_json_matches_universal_vectors`
  - **Reason**: Waiting for prove_certificate implementation
  - **Action**: Review and verify implementation completeness
- `universal/test_internalizeaction.py::test_internalizeaction_json_matches_universal_vectors`
  - **Reason**: Waiting for internalize_action implementation
  - **Action**: Review and verify implementation completeness

## Categorized Test Summary

### 1. ABI Wire Format Tests (31 tests)

**Status**: Intentionally skipped for TypeScript parity

**Reason**: TypeScript implementation does not test ABI (wire format) encoding/decoding. Following the principle: "If TypeScript skips it, we skip it too."

**Tests**: All `test_*_wire_matches_universal_vectors` tests in the `universal/` directory.

**Action**: Keep skipped unless TypeScript test suite changes.

---

### 2. Database/Storage Setup Required (18 tests)

**Status**: Skipped due to test infrastructure requirements

**Reason**: These tests require a pre-populated database with specific test data (certificates, outputs, actions, transactions) that is not currently set up in the test fixtures.

**Key Tests**:

- `universal/test_createaction.py::test_createaction_1out_json_matches_universal_vectors`
  - Storage provider not available in Wallet tests
- `universal/test_listactions.py::test_listactions_json_matches_universal_vectors`
  - Storage provider not available in Wallet tests
- `universal/test_relinquishcertificate.py::test_relinquishcertificate_json_matches_universal_vectors`
  - Storage provider not available in Wallet tests
- `wallet/test_abort_action.py::test_abort_specific_reference`
  - Requires populated test database with specific transaction reference - not implemented in test setup
- `wallet/test_list_actions.py::test_specific_label_filter`
  - Requires populated test database with labeled actions - not implemented in test setup
- `wallet/test_list_certificates.py::test_invalid_params_invalid_certifier`
  - Requires populated test database with certificates - not implemented in test setup
- `wallet/test_list_certificates.py::test_filter_by_certifier_lowercase`
  - Requires populated test database with certificates - not implemented in test setup
- `wallet/test_list_certificates.py::test_filter_by_certifier_uppercase`
  - Requires populated test database with certificates - not implemented in test setup
- `wallet/test_list_certificates.py::test_filter_by_multiple_certifiers`
  - Requires populated test database with certificates - not implemented in test setup
- `wallet/test_list_certificates.py::test_filter_by_type`
  - Requires populated test database with certificates - not implemented in test setup
- `wallet/test_list_outputs.py::test_invalid_params_empty_basket`
  - Requires populated test database with outputs - not implemented in test setup
- `wallet/test_list_outputs.py::test_invalid_params_empty_tag`
  - Requires populated test database with outputs - not implemented in test setup
- `wallet/test_list_outputs.py::test_invalid_params_limit_zero`
  - Requires populated test database with outputs - not implemented in test setup
- `wallet/test_list_outputs.py::test_invalid_params_limit_exceeds_max`
  - Requires populated test database with outputs - not implemented in test setup
- `wallet/test_list_outputs.py::test_invalid_params_negative_offset`
  - Requires populated test database with outputs - not implemented in test setup
- `wallet/test_list_outputs.py::test_invalid_originator_too_long`
  - Requires populated test database with outputs - not implemented in test setup
- `wallet/test_list_outputs.py::test_valid_params_with_originator`
  - Requires populated test database with outputs - not implemented in test setup
- `wallet/test_relinquish_output.py::test_relinquish_specific_output`
  - Requires populated test database with specific output - not implemented in test setup

**Action**: Create comprehensive test fixtures with pre-populated database states.

---

### 3. Non-deterministic/Test Infrastructure (18 tests)

**Status**: Skipped due to test infrastructure or non-deterministic behavior

**Reason**: These tests have issues with:
- Non-deterministic encryption (ECIES)
- KeyDeriver algorithm differences between Python and TypeScript
- Transaction byte generation issues
- TXID generation non-determinism
- Missing test parameters

**Key Tests**:

- `chaintracks/test_service_client.py::test_mainnet_findheaderforheight`
  - Chaintracks service client requires complex implementation - basic functionality verified
- `services/test_get_merkle_path.py::test_get_merkle_path`
  - Merkle path services require complex implementation - basic functionality verified
- `services/test_get_raw_tx.py::test_get_raw_tx`
  - Services layer requires complex mocking and implementation - basic functionality verified
- `services/test_local_services_hash_and_locktime.py::test_final_when_all_sequences_are_maxint`
  - Local services require complex implementation - basic functionality verified
- `services/test_whats_on_chain.py::test_getrawtx_testnet`
  - Async WhatsOnChain methods require complex mocking - basic functionality verified
- `universal/test_createhmac.py::test_createhmac_json_matches_universal_vectors`
  - KeyDeriver parity with TS/Go required for byte-perfect HMAC; skipping JSON vector
- `universal/test_encrypt.py::test_encrypt_json_matches_universal_vectors`
  - Non-deterministic ECIES output; enable after deterministic RNG or TS parity
- `universal/test_getpublickey.py::test_getpublickey_json_matches_universal_vectors`
  - py-sdk KeyDeriver uses different algorithm than TypeScript deriveChild
- `universal/test_getversion.py::test_getversion_json_matches_universal_vectors`
  - Version planned for 1.0.0; current Wallet.VERSION is 0.6.0
- `universal/test_verifyhmac.py::test_verifyhmac_json_matches_universal_vectors`
  - KeyDeriver parity with TS/Go required; HMAC verify will not match JSON vector yet
- `wallet/test_certificates.py::test_invalid_params`
  - Certificate parameter validation not implemented - method attempts database insertion instead of validation
- `wallet/test_internalize_action.py::test_internalize_custom_output_basket_insertion`
  - AtomicBEEF transaction parsing and validation not implemented - requires valid AtomicBEEF binary data
- `wallet/test_misc_methods.py::test_wallet_constructor_with_invalid_chain`
  - Chain validation not implemented in Wallet constructor
- `wallet/test_sign_process_action.py::test_sign_action_with_valid_reference`
  - create_action does not generate actual transaction bytes - signableTransaction.tx is empty
- `wallet/test_sign_process_action.py::test_sign_action_with_spend_authorizations`
  - Missing rawTx parameter - sign_action requires raw transaction bytes
- `wallet/test_sign_process_action.py::test_process_action_new_transaction`
  - Transaction parsing and validation not fully implemented - BsvTransaction.from_hex returns None
- `wallet/test_sign_process_action.py::test_process_action_with_send_with`
  - Transaction parsing and validation not fully implemented - same issue as process_action_new_transaction
- `wallet/test_wallet_create_action.py::test_repeatable_txid`
  - TXID generation not deterministic - database state changes between runs

**Action**: Fix test infrastructure or implement deterministic testing approaches.

---

### 4. BRC29 (56 tests)

**Status**: Not Implemented

**Description**: BRC-29 address generation and template functionality

**Test Count**: 56 tests across multiple files

**Sample Tests**:

- `brc29/test_brc29_address.py::test_return_valid_address_with_hex_string_as_sender_public_key_source`
- `brc29/test_brc29_address.py::test_return_valid_address_with_ec_publickey_as_sender_public_key_source`
- `brc29/test_brc29_address.py::test_return_valid_address_with_sender_key_deriver_as_sender_public_key_source`
- `brc29/test_brc29_address.py::test_return_valid_address_with_ec_privatekey_as_recipient_private_key_source`
- `brc29/test_brc29_address.py::test_return_testnet_address_created_with_brc29_by_recipient`
- `brc29/test_brc29_address.py::test_return_error_when_sender_key_is_empty`
- `brc29/test_brc29_address.py::test_return_error_when_sender_key_parsing_fails`
- `brc29/test_brc29_address.py::test_return_error_when_keyid_is_invalid`
- `brc29/test_brc29_address.py::test_return_error_when_recipient_key_is_empty`
- `brc29/test_brc29_address.py::test_return_error_when_recipient_key_parsing_fails`

... and 46 more tests

**Action**: Implement BRC29 functionality as per roadmap.

---

### 5. Monitor (8 tests)

**Status**: Not Implemented

**Description**: Blockchain monitoring and transaction status tracking

**Test Count**: 8 tests across multiple files

**Sample Tests**:

- `monitor/test_monitor.py::test_taskclock`
- `monitor/test_monitor.py::test_tasknewheader`
- `monitor/test_monitor.py::test_tasksendwaiting_success`
- `monitor/test_monitor.py::test_taskcheckforproofs_success`
- `monitor/test_monitor.py::test_taskcheckforproofs_fail`
- `monitor/test_monitor.py::test_taskreviewstatus`
- `monitor/test_monitor.py::test_processproventransaction`
- `monitor/test_monitor.py::test_processbroadcastedtransactions`

**Action**: Implement Monitor functionality as per roadmap.

---

### 6. Wallet Managers (127 tests)

**Status**: Not Implemented

**Description**: Advanced wallet management features (CWIStyleWalletManager, WalletPermissionsManager, etc.)

**Test Count**: 127 tests across multiple files

**Sample Tests**:

- `integration/test_cwi_style_wallet_manager.py::test_xor_function_verifies_correctness`
- `integration/test_cwi_style_wallet_manager.py::test_successfully_creates_a_new_token_and_calls_buildandsend`
- `integration/test_cwi_style_wallet_manager.py::test_throws_if_user_tries_to_provide_recovery_key_during_new_user_flow`
- `integration/test_cwi_style_wallet_manager.py::test_decryption_of_primary_key_and_building_the_wallet`
- `integration/test_cwi_style_wallet_manager.py::test_successfully_decrypts_with_presentation_plus_recovery`
- `integration/test_cwi_style_wallet_manager.py::test_throws_if_presentation_key_not_provided_first`
- `integration/test_cwi_style_wallet_manager.py::test_works_with_correct_keys_sets_mode_as_existing_user`
- `integration/test_cwi_style_wallet_manager.py::test_throws_if_no_token_found_by_recovery_key_hash`
- `integration/test_cwi_style_wallet_manager.py::test_saves_a_snapshot_and_can_load_it_into_a_fresh_manager_instance`
- `integration/test_cwi_style_wallet_manager.py::test_throws_error_if_saving_snapshot_while_no_primary_key_or_token_set`

... and 117 more tests

**Action**: Implement Wallet Managers functionality as per roadmap.

---

### 7. Chaintracks (20 tests)

**Status**: Not Implemented

**Description**: Chaintracks blockchain data service integration

**Test Count**: 20 tests across multiple files

**Sample Tests**:

- `chaintracks/test_chain_tracker.py::test_test`
- `chaintracks/test_chain_tracker.py::test_main`
- `chaintracks/test_chaintracks.py::test_nodb_mainnet`
- `chaintracks/test_chaintracks.py::test_nodb_testnet`
- `chaintracks/test_client_api.py::test_getchain`
- `chaintracks/test_client_api.py::test_getinfo`
- `chaintracks/test_client_api.py::test_getpresentheight`
- `chaintracks/test_client_api.py::test_getheaders`
- `chaintracks/test_client_api.py::test_findchaintipheader`
- `chaintracks/test_client_api.py::test_findchaintiphash`

... and 10 more tests

**Action**: Implement Chaintracks functionality as per roadmap.

---

### 8. Services (33 tests)

**Status**: Not Implemented

**Description**: External service integrations (WhatsOnChain, ARC, etc.)

**Test Count**: 33 tests across multiple files

**Sample Tests**:

- `integration/test_bulk_file_data_manager.py::test_default_options_cdn_files`
- `integration/test_bulk_ingestor_cdn_babbage.py::test_mainnet`
- `integration/test_bulk_ingestor_cdn_babbage.py::test_testnet`
- `integration/test_local_kv_store.py::test_get_non_existent`
- `integration/test_local_kv_store.py::test_set_get`
- `integration/test_local_kv_store.py::test_set_x_4_get`
- `integration/test_local_kv_store.py::test_set_x_4_get_set_x_4_get`
- `integration/test_single_writer_multi_reader_lock.py::test_concurrent_reads_and_writes_execute_in_correct_order`
- `monitor/test_live_ingestor_whats_on_chain_poll.py::test_listen_for_first_new_header`
- `services/test_arc_services.py::test_arc_services_placeholder`

... and 23 more tests

**Action**: Implement Services functionality as per roadmap.

---

### 9. Utils (104 tests)

**Status**: Not Implemented

**Description**: Various utility functions and helpers

**Test Count**: 104 tests across multiple files

**Sample Tests**:

- `errors/test_action_error.py::test_success`
- `errors/test_action_error.py::test_error_without_cause`
- `errors/test_action_error.py::test_success`
- `errors/test_action_error.py::test_error_without_cause`
- `errors/test_action_error.py::test_with_success_and_failed_txs`
- `errors/test_action_error.py::test_with_review_results_and_cause`
- `errors/test_action_error.py::test_nil_cause_and_no_results`
- `integration/test_privileged_key_manager.py::test_validates_the_brc_3_compliance_vector`
- `integration/test_privileged_key_manager.py::test_validates_the_brc_2_hmac_compliance_vector`
- `integration/test_privileged_key_manager.py::test_validates_the_brc_2_encryption_compliance_vector`

... and 94 more tests

**Action**: Implement Utils functionality as per roadmap.

---

### 10. Certificate Lifecycle (6 tests)

**Status**: Not Implemented

**Description**: Complete certificate lifecycle management

**Test Count**: 6 tests across multiple files

**Sample Tests**:

- `certificates/test_certificate_life_cycle.py::test_complete_flow_mastercertificate_and_verifiablecertificate`
- `wallet/test_certificates.py::test_acquirecertificate_listcertificate_provecertificate`
- `wallet/test_certificates.py::test_privileged_acquirecertificate_listcertificate_provecertificate`
- `wallet/test_certificates.py::test_prove_certificate`
- `wallet/test_certificates.py::test_discover_by_identity_key`
- `wallet/test_certificates.py::test_discover_by_attributes`

**Action**: Implement Certificate Lifecycle functionality as per roadmap.

---

### 11. Other Issues (7 tests)

**Status**: Various specific issues

**Tests**:

- `services/test_get_chain_tracker.py::test_get_chain_tracker_placeholder`
  - No corresponding TS/So test exists yet; placeholder only.
- `services/test_post_beef.py::test_post_beef_placeholder`
  - No corresponding TS/So tests yet; placeholder only.
- `services/test_post_beef.py::test_post_beef_array_placeholder`
  - No corresponding TS/So tests yet; placeholder only.
- `services/test_transaction_status.py::test_get_transaction_status_placeholder`
  - No corresponding TS/So test exists yet; placeholder only.
- `wallet/test_sync.py::test_sync_initial_then_no_changes_then_one_change`
  - Sync functionality not implemented - fixtures return None
- `wallet/test_sync.py::test_set_active_to_backup_and_back_without_backup_first`
  - Sync functionality not implemented - fixtures return None
- `wallet/test_sync.py::test_set_active_to_backup_and_back_with_backup_first`
  - Sync functionality not implemented - fixtures return None

**Action**: Address issues on a case-by-case basis.

---

## Recommendations

### Priority Actions

1. **Review "Tests Ready to Unskip"** (14 tests)
   - These test implemented methods but are incorrectly marked as skipped
   - Review each test to verify the implementation meets test requirements
   - Unskip tests where implementation is complete

2. **Improve Test Fixtures** (18 tests)
   - Create comprehensive database fixtures with pre-populated test data
   - Set up proper test isolation and cleanup
   - Enable database-dependent tests

3. **Fix Test Infrastructure** (18 tests)
   - Address non-deterministic behavior in encryption tests
   - Resolve KeyDeriver algorithm parity issues
   - Fix transaction byte generation in action tests

4. **Implement Missing Features** (354 tests)
   - Prioritize based on product roadmap
   - BRC29 (56 tests) - address generation
   - Wallet Managers (127 tests) - permission and settings management
   - Utils (104 tests) - various helper functions

### Testing Strategy

#### For Implemented Features
- Unskip tests incrementally as implementation is verified
- Ensure tests pass before removing skip markers
- Update this report as tests are unskipped

#### For Test Infrastructure
- Invest in better test fixtures and mocking
- Create deterministic test data generators
- Implement proper database seeding for integration tests

#### For Missing Features
- Follow the implementation roadmap
- Unskip related tests as features are completed
- Use skipped tests as acceptance criteria

## File Organization

### Test Path Reference
All test paths are available in `SKIPPED_TESTS_LIST.txt` for:
- Automated test execution
- CI/CD pipeline configuration
- Selective test running during development

### Running Skipped Tests

To run a specific skipped test (for development):
```bash
pytest -v tests/path/to/test.py::test_name
```

To run all tests in a category (remove skip markers first):
```bash
pytest -v tests/universal/  # Universal test vectors
pytest -v tests/wallet/     # Wallet functionality
```

## Maintenance

This report should be updated when:
- New features are implemented (move tests from "Not Implemented" to "Ready to Unskip")
- Tests are unskipped (remove from this report)
- New tests are added (categorize appropriately)
- Test infrastructure improves (reclassify affected tests)

---

**Note**: This report was generated automatically by analyzing all `@pytest.mark.skip` and `@pytest.mark.skipif` decorators in the test suite.
