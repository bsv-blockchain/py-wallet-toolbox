# Remaining 68 Tests - Fully Categorized

**Current Status:** 603/809 passing (75%), 68 failing, 196 skipped

---

## Summary by Category

| Category | Count | Type | Est. Effort |
|----------|-------|------|-------------|
| Universal Vectors | 22 | Deterministic setup | 40-60 calls |
| Certificates | 11 | Full subsystem | 50-80 calls |
| Permissions (remaining) | 10 | Proxy methods | 30-40 calls |
| Chaintracks (remaining) | 8 | Client implementation | 20-30 calls |
| Integration (remaining) | 7 | Utilities | 20-30 calls |
| Wallet test data | 7 | Test fixtures | 15-25 calls |
| Services | 2 | Quick fixes | 5-10 calls |
| Certificate lifecycle | 1 | Full flow | 10-15 calls |
| Monitor (remaining) | 1 | Live ingestor | 5-10 calls |

**Total:** 68 tests, 195-300 calls estimated

---

## Detailed Breakdown

### 1. Universal Vectors (22 tests) - DETERMINISTIC SETUP NEEDED

**Why Failing:** Need exact matching with TS/Go implementations
- Precise UTXO setup
- Deterministic key derivation
- Exact transaction building

**Tests:**
1. `test_createaction.py::test_createaction_1out_json_matches_universal_vectors`
2. `test_createaction.py::test_createaction_nosignandprocess_json_matches_universal_vectors`
3. `test_createhmac.py::test_createhmac_json_matches_universal_vectors`
4. `test_createsignature.py::test_createsignature_json_matches_universal_vectors`
5. `test_decrypt.py::test_decrypt_json_matches_universal_vectors`
6. `test_discoverbyattributes.py::test_discoverbyattributes_json_matches_universal_vectors`
7. `test_discoverbyidentitykey.py::test_discoverbyidentitykey_json_matches_universal_vectors`
8. `test_encrypt.py::test_encrypt_json_matches_universal_vectors`
9. `test_getpublickey.py::test_getpublickey_json_matches_universal_vectors`
10. `test_internalizeaction.py::test_internalizeaction_json_matches_universal_vectors`
11. `test_listactions.py::test_listactions_json_matches_universal_vectors`
12. `test_listcertificates.py::test_listcertificates_simple_json_matches_universal_vectors`
13. `test_listcertificates.py::test_listcertificates_full_json_matches_universal_vectors`
14. `test_listoutputs.py::test_listoutputs_json_matches_universal_vectors`
15. `test_provecertificate.py::test_provecertificate_json_matches_universal_vectors`
16. `test_relinquishcertificate.py::test_relinquishcertificate_json_matches_universal_vectors`
17. `test_relinquishoutput.py::test_relinquishoutput_json_matches_universal_vectors`
18. `test_revealcounterpartykeylinkage.py::test_revealcounterpartykeylinkage_json_matches_universal_vectors`
19. `test_revealspecifickeylinkage.py::test_revealspecifickeylinkage_json_matches_universal_vectors`
20. `test_signaction.py::test_signaction_json_matches_universal_vectors`
21. `test_verifyhmac.py::test_verifyhmac_json_matches_universal_vectors`
22. `test_verifysignature.py::test_verifysignature_json_matches_universal_vectors`

---

### 2. Certificates (11 tests) - CERTIFICATE SYSTEM NEEDED

**Why Failing:** Need full certificate subsystem implementation

**Tests:**
1. `test_certificates.py::TestWalletAcquireCertificate::test_acquirecertificate_listcertificate_provecertificate`
2. `test_certificates.py::TestWalletAcquireCertificate::test_privileged_acquirecertificate_listcertificate_provecertificate`
3. `test_certificates.py::TestWalletProveCertificate::test_prove_certificate`
4. `test_certificates.py::TestWalletDiscoverByIdentityKey::test_discover_by_identity_key`
5. `test_certificates.py::TestWalletDiscoverByAttributes::test_discover_by_attributes`
6. `test_list_certificates.py::TestWalletListCertificates::test_filter_by_certifier_lowercase`
7. `test_list_certificates.py::TestWalletListCertificates::test_filter_by_certifier_uppercase`
8. `test_list_certificates.py::TestWalletListCertificates::test_filter_by_multiple_certifiers`
9. `test_list_certificates.py::TestWalletListCertificates::test_filter_by_type`
10. `test_certificate_life_cycle.py::TestCertificateLifeCycle::test_complete_flow_mastercertificate_and_verifiablecertificate`

---

### 3. Permissions (10 remaining tests) - PROXY METHODS NEEDED

**Why Failing:** Need proxy method implementations

**Tests:**
1. `test_wallet_permissions_manager_encryption.py::TestWalletPermissionsManagerEncryptionIntegration::test_should_encrypt_metadata_fields_in_createaction_when_encryptwalletmetadata_true_then_decrypt_them_in_listactions`
2. `test_wallet_permissions_manager_encryption.py::TestWalletPermissionsManagerEncryptionIntegration::test_should_not_encrypt_metadata_if_encryptwalletmetadata_false_storing_and_retrieving_plaintext`
3. `test_wallet_permissions_manager_encryption.py::TestWalletPermissionsManagerListOutputsDecryption::test_should_decrypt_custominstructions_in_listoutputs_if_encryptwalletmetadata_true`
4. `test_wallet_permissions_manager_encryption.py::TestWalletPermissionsManagerListOutputsDecryption::test_should_fallback_to_the_original_ciphertext_if_decrypt_fails_in_listoutputs`
5. `test_wallet_permissions_manager_initialization.py::TestWalletPermissionsManagerInitialization::test_should_consider_calls_from_the_adminoriginator_as_admin_bypassing_checks`
6. `test_wallet_permissions_manager_initialization.py::TestWalletPermissionsManagerInitialization::test_should_skip_protocol_permission_checks_for_signing_if_seekprotocolpermissionsforsigning_false`
7. `test_wallet_permissions_manager_initialization.py::TestWalletPermissionsManagerInitialization::test_should_enforce_protocol_permission_checks_for_signing_if_seekprotocolpermissionsforsigning_true`
8. `test_wallet_permissions_manager_initialization.py::TestWalletPermissionsManagerInitialization::test_should_skip_basket_insertion_permission_checks_if_seekbasketinsertionpermissions_false`
9. `test_wallet_permissions_manager_initialization.py::TestWalletPermissionsManagerInitialization::test_should_skip_certificate_disclosure_permission_checks_if_seekcertificatedisclosurepermissions_false`
10. `test_wallet_permissions_manager_initialization.py::TestWalletPermissionsManagerInitialization::test_should_skip_metadata_encryption_if_encryptwalletmetadata_false`

---

### 4. Chaintracks (8 remaining tests) - CLIENT IMPL NEEDED

**Why Failing:** Need chaintracks service/client implementation

**Tests:**
1. `test_chaintracks.py::TestChaintracks::test_nodb_mainnet`
2. `test_chaintracks.py::TestChaintracks::test_nodb_testnet`
3. `test_fetch.py::TestChaintracksFetch::test_fetchjson`
4. `test_fetch.py::TestChaintracksFetch::test_download`
5. `test_fetch.py::TestChaintracksFetch::test_download_716`
6. `test_fetch.py::TestChaintracksFetch::test_download_717`
7. `test_service_client.py::TestChaintracksServiceClient::test_mainnet_findheaderforheight`
8. `test_service_client.py::TestChaintracksServiceClient::test_testnet_findheaderforheight`

---

### 5. Integration (7 remaining tests) - UTILITIES NEEDED

**Why Failing:** Need utility implementations

**Tests:**
1. `test_bulk_file_data_manager.py::TestBulkFileDataManager::test_default_options_cdn_files`
2. `test_bulk_file_data_manager.py::TestBulkFileDataManager::test_default_options_cdn_files_nodropall`
3. `test_local_kv_store.py::TestLocalKVStore::test_get_non_existent`
4. `test_local_kv_store.py::TestLocalKVStore::test_set_get`
5. `test_local_kv_store.py::TestLocalKVStore::test_set_x_4_get`
6. `test_local_kv_store.py::TestLocalKVStore::test_set_x_4_get_set_x_4_get`
7. `test_single_writer_multi_reader_lock.py::TestSingleWriterMultiReaderLock::test_concurrent_reads_and_writes_execute_in_correct_order`

---

### 6. Wallet Test Data (7 tests) - FIXTURES NEEDED

**Why Failing:** Need test data seeding

**Tests:**
1. `test_abort_action.py::TestWalletAbortAction::test_abort_specific_reference`
2. `test_internalize_action.py::TestWalletInternalizeAction::test_internalize_custom_output_basket_insertion`
3. `test_relinquish_output.py::TestWalletRelinquishOutput::test_relinquish_specific_output`
4. `test_sign_process_action.py::TestWalletSignAction::test_sign_action_with_valid_reference`
5. `test_sign_process_action.py::TestWalletSignAction::test_sign_action_with_spend_authorizations`
6. `test_sign_process_action.py::TestWalletProcessAction::test_process_action_invalid_params_missing_txid`
7. `test_sign_process_action.py::TestWalletProcessAction::test_process_action_new_transaction`
8. `test_sign_process_action.py::TestWalletProcessAction::test_process_action_with_send_with`

---

### 7. Services (2 tests) - QUICK FIXES

**Why Failing:** Simple implementation issues

**Tests:**
1. `test_get_raw_tx.py::TestGetRawTx::test_get_raw_tx` - Mock not returning data
2. `test_local_services_hash_and_locktime.py::TestNLockTimeIsFinal::test_height_based_locktime_strict_less_than` - Async/await issue

---

### 8. Monitor (1 remaining test) - LIVE INGESTOR NEEDED

**Why Failing:** Need live ingestor implementation

**Tests:**
1. `test_live_ingestor_whats_on_chain_poll.py::TestLiveIngestorWhatsOnChainPoll::test_listen_for_first_new_header`

---

## Next Steps for Each Category

### Universal Vectors
1. Create deterministic fixture system
2. Match TS/Go key derivation paths
3. Seed exact UTXO states
4. Verify transaction building produces exact txids

### Certificates
1. Implement certificate creation/storage
2. Implement certificate proving
3. Implement certificate discovery
4. Implement certificate listing/filtering

### Permissions (Remaining)
1. Implement proxy methods (create_action, create_signature, etc.)
2. Implement metadata encryption/decryption
3. Implement permission bypass for admin originator

### Chaintracks (Remaining)
1. Implement chaintracks service client
2. Implement header fetching
3. Implement JSON fetch utilities
4. Add nodb configuration support

### Integration (Remaining)
1. Implement LocalKVStore
2. Implement BulkFileDataManager
3. Implement SingleWriterMultiReaderLock

### Wallet Test Data
1. Create transaction seeding fixtures
2. Create output seeding fixtures
3. Create reference-based test data

### Services
1. Fix get_raw_tx mock return value
2. Fix async/await in locktime test

### Monitor (Remaining)
1. Implement live header ingestor

---

## Conclusion

All 68 remaining tests are:
- ✅ Fully categorized
- ✅ Root causes identified
- ✅ Effort estimated
- ✅ Next steps documented
- ✅ Ready for systematic implementation

**Status:** Categorization Complete - All Tests Accounted For

