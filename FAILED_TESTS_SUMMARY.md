# Failed Tests Summary

**Total Test Results:**
- **247 FAILED**
- 562 passed
- 58 skipped
- 8 xfailed
- 3 errors
- Total: 878 tests collected

---

## Failed Tests by File

### 1. tests/certificates/test_certificate_life_cycle.py (1 failure)
- `test_complete_flow_mastercertificate_and_verifiablecertificate`

### 2. tests/chaintracks/test_chaintracks.py (2 failures)
- `test_nodb_mainnet`
- `test_nodb_testnet`

### 3. tests/chaintracks/test_client_api.py (10 failures)
- `test_getchain`
- `test_getinfo`
- `test_getpresentheight`
- `test_getheaders`
- `test_findchaintipheader`
- `test_findchaintiphash`
- `test_findheaderforheight`
- `test_addheader`
- `test_subscribeheaders`
- `test_subscribereorgs`

### 4. tests/chaintracks/test_fetch.py (4 failures)
- `test_fetchjson`
- `test_download`
- `test_download_716`
- `test_download_717`

### 5. tests/chaintracks/test_service_client.py (2 failures)
- `test_mainnet_findheaderforheight`
- `test_testnet_findheaderforheight`

### 6. tests/integration/test_bulk_file_data_manager.py (2 failures)
- `test_default_options_cdn_files`
- `test_default_options_cdn_files_nodropall`

### 7. tests/integration/test_cwi_style_wallet_manager.py (25 failures)
- TestCWIStyleWalletManagerNewUser:
  - `test_successfully_creates_a_new_token_and_calls_buildandsend`
  - `test_throws_if_user_tries_to_provide_recovery_key_during_new_user_flow`
- TestCWIStyleWalletManagerExistingUser:
  - `test_decryption_of_primary_key_and_building_the_wallet`
  - `test_successfully_decrypts_with_presentation_plus_recovery`
  - `test_throws_if_presentation_key_not_provided_first`
  - `test_works_with_correct_keys_sets_mode_as_existing_user`
  - `test_throws_if_no_token_found_by_recovery_key_hash`
- TestCWIStyleWalletManagerSnapshot:
  - `test_saves_a_snapshot_and_can_load_it_into_a_fresh_manager_instance`
  - `test_throws_error_if_saving_snapshot_while_no_primary_key_or_token_set`
  - `test_throws_if_snapshot_is_corrupt_or_cannot_be_decrypted`
- TestCWIStyleWalletManagerChangePassword:
  - `test_requires_authentication_and_updates_the_ump_token_on_chain`
  - `test_throws_if_not_authenticated`
- TestCWIStyleWalletManagerChangeRecoveryKey:
  - `test_prompts_to_save_the_new_key_updates_the_token`
  - `test_throws_if_not_authenticated_527`
- TestCWIStyleWalletManagerChangePresentationKey:
  - `test_requires_authentication_re_publishes_the_token_old_token_consumed`
- TestCWIStyleWalletManagerDestroy:
  - `test_destroy_callback_clears_sensitive_data`
- TestCWIStyleWalletManagerProxyMethods:
  - `test_throws_if_user_is_not_authenticated`
  - `test_throws_if_originator_is_adminoriginator`
  - `test_passes_if_user_is_authenticated_and_originator_is_not_admin`
  - `test_all_proxied_methods_call_underlying_with_correct_arguments`
  - `test_isauthenticated_rejects_if_originator_is_admin_resolves_otherwise`
  - `test_waitforauthentication_eventually_resolves`
- TestCWIStyleWalletManagerAdditionalTests:
  - `test_serializeumptoken_and_deserializeumptoken_correctly_round_trip_a_ump_token`
  - `test_password_retriever_callback_the_test_function_is_passed_and_returns_a_boolean`
  - `test_privileged_key_expiry_each_call_to_decrypt_via_the_privileged_manager_invokes_passwordretriever`

### 8. tests/integration/test_local_kv_store.py (4 failures)
- `test_get_non_existent`
- `test_set_get`
- `test_set_x_4_get`
- `test_set_x_4_get_set_x_4_get`

### 9. tests/integration/test_single_writer_multi_reader_lock.py (1 failure)
- `test_concurrent_reads_and_writes_execute_in_correct_order`

### 10. tests/monitor/test_live_ingestor_whats_on_chain_poll.py (1 failure)
- `test_listen_for_first_new_header`

### 11. tests/monitor/test_monitor.py (8 failures)
- `test_taskclock`
- `test_tasknewheader`
- `test_tasksendwaiting_success`
- `test_taskcheckforproofs_success`
- `test_taskcheckforproofs_fail`
- `test_taskreviewstatus`
- `test_processproventransaction`
- `test_processbroadcastedtransactions`

### 12. tests/permissions/test_wallet_permissions_manager_callbacks.py (9 failures)
- `test_bindcallback_should_register_multiple_callbacks_for_the_same_event_which_are_called_in_sequence`
- `test_unbindcallback_by_numeric_id_should_prevent_the_callback_from_being_called_again`
- `test_unbindcallback_by_function_reference_should_remove_the_callback`
- `test_a_failing_callback_throwing_an_error_does_not_block_subsequent_callbacks`
- `test_should_trigger_onprotocolpermissionrequested_with_correct_params_when_a_non_admin_domain_requests_a_protocol_operation`
- `test_should_resolve_the_original_caller_promise_when_requests_are_granted`
- `test_should_reject_the_original_caller_promise_when_permission_is_denied`
- `test_multiple_pending_requests_for_the_same_resource_should_trigger_only_one_onxxxrequested_callback`
- `test_multiple_pending_requests_for_different_resources_should_trigger_separate_onxxxrequested_callbacks`

### 13. tests/permissions/test_wallet_permissions_manager_checks.py (25 failures)
- `test_should_skip_permission_prompt_if_seclevel_0_open_usage`
- `test_should_prompt_for_protocol_usage_if_securitylevel_1_and_no_existing_token`
- `test_should_deny_protocol_usage_if_user_denies_permission`
- `test_should_enforce_privileged_token_if_differentiateprivilegedoperations_true`
- `test_should_ignore_privileged_true_if_differentiateprivilegedoperations_false`
- `test_should_fail_if_protocol_name_is_admin_reserved_and_caller_is_not_admin`
- `test_should_prompt_for_renewal_if_token_is_found_but_expired`
- `test_should_fail_immediately_if_using_an_admin_only_basket_as_non_admin`
- `test_should_fail_immediately_if_using_the_reserved_basket_default_as_non_admin`
- `test_should_prompt_for_insertion_permission_if_seekbasketinsertionpermissions_true`
- `test_should_skip_insertion_permission_if_seekbasketinsertionpermissions_false`
- `test_should_require_listing_permission_if_seekbasketlistingpermissions_true_and_no_token`
- `test_should_prompt_for_removal_permission_if_seekbasketremovalpermissions_true`
- `test_should_skip_certificate_disclosure_permission_if_config_seekcertificatedisclosurepermissions_false`
- `test_should_require_permission_if_seekcertificatedisclosurepermissions_true_no_valid_token`
- `test_should_check_that_requested_fields_are_a_subset_of_the_tokens_fields`
- `test_should_prompt_for_renewal_if_token_is_expired_cert`
- `test_should_skip_if_seekspendingpermissions_false`
- `test_should_require_spending_token_if_netspent_gt_0_and_seekspendingpermissions_true`
- `test_should_check_monthly_limit_usage_and_prompt_renewal_if_insufficient`
- `test_should_pass_if_usage_plus_new_spend_is_within_the_monthly_limit`
- `test_should_fail_if_label_starts_with_admin`
- `test_should_skip_label_permission_if_seekpermissionwhenapplyingactionlabels_false`
- `test_should_prompt_for_label_usage_if_seekpermissionwhenapplyingactionlabels_true`
- `test_should_also_prompt_for_listing_actions_by_label_if_seekpermissionwhenlistingactionsbylabel_true`

### 14. tests/permissions/test_wallet_permissions_manager_encryption.py (8 failures)
- TestWalletPermissionsManagerEncryptionHelpers:
  - `test_should_call_underlying_encrypt_with_correct_protocol_and_key_when_encryptwalletmetadata_true`
  - `test_should_not_call_underlying_encrypt_if_encryptwalletmetadata_false`
  - `test_should_call_underlying_decrypt_with_correct_protocol_and_key_returning_plaintext_on_success`
  - `test_should_fallback_to_original_string_if_underlying_decrypt_fails`
- TestWalletPermissionsManagerEncryptionIntegration:
  - `test_should_encrypt_metadata_fields_in_createaction_when_encryptwalletmetadata_true_then_decrypt_them_in_listactions`
  - `test_should_not_encrypt_metadata_if_encryptwalletmetadata_false_storing_and_retrieving_plaintext`
- TestWalletPermissionsManagerListOutputsDecryption:
  - `test_should_decrypt_custominstructions_in_listoutputs_if_encryptwalletmetadata_true`
  - `test_should_fallback_to_the_original_ciphertext_if_decrypt_fails_in_listoutputs`

### 15. tests/permissions/test_wallet_permissions_manager_flows.py (7 failures)
- `test_should_coalesce_parallel_requests_for_the_same_resource_into_a_single_user_prompt`
- `test_should_generate_two_distinct_user_prompts_for_two_different_permission_requests`
- `test_should_resolve_all_parallel_requests_when_permission_is_granted_referencing_the_same_requestid`
- `test_should_reject_only_the_matching_request_queue_on_deny_if_requestid_is_specified`
- `test_should_not_create_a_token_if_ephemeral_true_so_subsequent_calls_re_trigger_the_request`
- `test_should_create_a_token_if_ephemeral_false_so_subsequent_calls_do_not_re_trigger_if_unexpired`
- `test_should_handle_renewal_if_the_found_token_is_expired_passing_previoustoken_in_the_request`

### 16. tests/permissions/test_wallet_permissions_manager_initialization.py (9 failures)
- `test_should_initialize_with_default_config_if_none_is_provided`
- `test_should_initialize_with_partial_config_overrides_merging_with_defaults`
- `test_should_initialize_with_all_config_flags_set_to_false`
- `test_should_consider_calls_from_the_adminoriginator_as_admin_bypassing_checks`
- `test_should_skip_protocol_permission_checks_for_signing_if_seekprotocolpermissionsforsigning_false`
- `test_should_enforce_protocol_permission_checks_for_signing_if_seekprotocolpermissionsforsigning_true`
- `test_should_skip_basket_insertion_permission_checks_if_seekbasketinsertionpermissions_false`
- `test_should_skip_certificate_disclosure_permission_checks_if_seekcertificatedisclosurepermissions_false`
- `test_should_skip_metadata_encryption_if_encryptwalletmetadata_false`

### 17. tests/permissions/test_wallet_permissions_manager_proxying.py (30 failures)
- `test_should_pass_createaction_calls_through_label_them_handle_metadata_encryption_and_check_spending_authorization`
- `test_should_abort_the_action_if_spending_permission_is_denied`
- `test_should_throw_an_error_if_a_non_admin_tries_signandprocess_true`
- `test_should_proxy_signaction_calls_directly_if_invoked_by_the_user`
- `test_should_proxy_abortaction_calls_directly`
- `test_should_call_listactions_on_the_underlying_wallet_and_decrypt_metadata_fields_if_encryptwalletmetadata_true`
- `test_should_pass_internalizeaction_calls_to_underlying_after_ensuring_basket_permissions_and_encrypting_custominstructions_if_config_on`
- `test_should_ensure_basket_listing_permission_then_call_listoutputs_decrypting_custominstructions`
- `test_should_ensure_basket_removal_permission_then_call_relinquishoutput`
- `test_should_call_getpublickey_on_underlying_after_ensuring_protocol_permission`
- `test_should_call_revealcounterpartykeylinkage_with_permission_check_pass_result`
- `test_should_call_revealspecifickeylinkage_with_permission_check_pass_result`
- `test_should_proxy_encrypt_calls_after_checking_protocol_permission`
- `test_should_proxy_decrypt_calls_after_checking_protocol_permission`
- `test_should_proxy_createhmac_calls`
- `test_should_proxy_verifyhmac_calls`
- `test_should_proxy_createsignature_calls_already_tested_the_netspent_logic_in_createaction_but_lets_double_check`
- `test_should_proxy_verifysignature_calls`
- `test_should_call_acquirecertificate_verifying_permission_if_config_seekcertificateacquisitionpermissions_true`
- `test_should_call_listcertificates_verifying_permission_if_config_seekcertificatelistingpermissions_true`
- `test_should_call_provecertificate_after_ensuring_certificate_permission`
- `test_should_call_relinquishcertificate_if_config_seekcertificaterelinquishmentpermissions_true`
- `test_should_call_discoverbyidentitykey_after_ensuring_identity_resolution_permission`
- `test_should_call_discoverbyattributes_after_ensuring_identity_resolution_permission`
- `test_should_proxy_isauthenticated_without_any_special_permission_checks`
- `test_should_proxy_waitforauthentication_without_any_special_permission_checks`
- `test_should_proxy_getheight`
- `test_should_proxy_getheaderforheight`
- `test_should_proxy_getnetwork`
- `test_should_proxy_getversion`
- `test_should_propagate_errors_from_the_underlying_wallet_calls`

### 18. tests/permissions/test_wallet_permissions_manager_tokens.py (12 failures)
- `test_should_build_correct_fields_for_a_protocol_token_dpacp`
- `test_should_build_correct_fields_for_a_basket_token_dbap`
- `test_should_build_correct_fields_for_a_certificate_token_dcap`
- `test_should_build_correct_fields_for_a_spending_token_dsap`
- `test_should_create_a_new_protocol_token_with_the_correct_basket_script_and_tags`
- `test_should_create_a_new_basket_token_dbap`
- `test_should_create_a_new_certificate_token_dcap`
- `test_should_create_a_new_spending_authorization_token_dsap`
- `test_should_spend_the_old_token_input_and_create_a_new_protocol_token_output_with_updated_expiry`
- `test_should_allow_updating_the_authorizedamount_in_dsap_renewal`
- `test_should_create_a_transaction_that_consumes_spends_the_old_token_with_no_new_outputs`
- `test_should_remove_the_old_token_from_listing_after_revocation`

### 19. tests/services/test_exchange_rates.py (1 failure)
- `test_update_exchange_rates_for_multiple_currencies`

### 20. tests/services/test_get_merkle_path.py (1 failure)
- `test_get_merkle_path`

### 21. tests/services/test_get_raw_tx.py (1 failure)
- `test_get_raw_tx`

### 22. tests/services/test_local_services_hash_and_locktime.py (1 failure)
- `test_height_based_locktime_strict_less_than`

### 23. tests/services/test_post_beef.py (2 failures)
- `test_postbeef_mainnet`
- `test_postbeef_testnet`

### 24. tests/services/test_verify_beef.py (2 failures)
- `test_verify_beef_from_hex`
- `test_verify_beef_from_storage`

### 25. tests/unit/test_utility_helpers.py (14 failures)
- TestToWalletNetwork:
  - `test_converts_main_to_mainnet`
  - `test_converts_test_to_testnet`
- TestVerifyTruthy:
  - `test_returns_truthy_value`
- TestVerifyHexString:
  - `test_trims_and_lowercases_hex_string`
- TestVerifyNumber:
  - `test_returns_valid_number`
- TestVerifyInteger:
  - `test_returns_valid_integer`
- TestVerifyId:
  - `test_returns_valid_id`
  - `test_raises_error_for_negative`
  - `test_raises_error_for_float`
- TestVerifyOneOrNone:
  - `test_returns_first_element_for_single_item`
  - `test_returns_none_for_empty_list`
  - `test_raises_error_for_multiple_items`
- TestVerifyOne:
  - `test_returns_element_for_single_item`
  - `test_raises_error_for_empty_list`
  - `test_raises_error_for_multiple_items`

### 26. tests/unit/test_wallet_constructor.py (1 failure)
- `test_constructor_creates_wallet_with_default_labels_and_baskets`

### 27. tests/unit/test_wallet_getknowntxids.py (3 failures)
- `test_adds_new_known_txids`
- `test_avoids_duplicating_txids`
- `test_returns_sorted_txids`

### 28. tests/universal/test_createaction.py (2 failures)
- `test_createaction_1out_json_matches_universal_vectors`
- `test_createaction_nosignandprocess_json_matches_universal_vectors`

### 29. tests/universal/test_createhmac.py (1 failure)
- `test_createhmac_json_matches_universal_vectors`

### 30. tests/universal/test_createsignature.py (1 failure)
- `test_createsignature_json_matches_universal_vectors`

### 31. tests/universal/test_decrypt.py (1 failure)
- `test_decrypt_json_matches_universal_vectors`

### 32. tests/universal/test_discoverbyattributes.py (1 failure)
- `test_discoverbyattributes_json_matches_universal_vectors`

### 33. tests/universal/test_discoverbyidentitykey.py (1 failure)
- `test_discoverbyidentitykey_json_matches_universal_vectors`

### 34. tests/universal/test_encrypt.py (1 failure)
- `test_encrypt_json_matches_universal_vectors`

### 35. tests/universal/test_getpublickey.py (1 failure)
- `test_getpublickey_json_matches_universal_vectors`

### 36. tests/universal/test_internalizeaction.py (1 failure)
- `test_internalizeaction_json_matches_universal_vectors`

### 37. tests/universal/test_listactions.py (1 failure)
- `test_listactions_json_matches_universal_vectors`

### 38. tests/universal/test_listcertificates.py (2 failures)
- `test_listcertificates_simple_json_matches_universal_vectors`
- `test_listcertificates_full_json_matches_universal_vectors`

### 39. tests/universal/test_listoutputs.py (1 failure)
- `test_listoutputs_json_matches_universal_vectors`

### 40. tests/universal/test_provecertificate.py (1 failure)
- `test_provecertificate_json_matches_universal_vectors`

### 41. tests/universal/test_relinquishcertificate.py (1 failure)
- `test_relinquishcertificate_json_matches_universal_vectors`

### 42. tests/universal/test_relinquishoutput.py (1 failure)
- `test_relinquishoutput_json_matches_universal_vectors`

### 43. tests/universal/test_revealcounterpartykeylinkage.py (1 failure)
- `test_revealcounterpartykeylinkage_json_matches_universal_vectors`

### 44. tests/universal/test_revealspecifickeylinkage.py (1 failure)
- `test_revealspecifickeylinkage_json_matches_universal_vectors`

### 45. tests/universal/test_signaction.py (1 failure)
- `test_signaction_json_matches_universal_vectors`

### 46. tests/universal/test_verifyhmac.py (1 failure)
- `test_verifyhmac_json_matches_universal_vectors`

### 47. tests/universal/test_verifysignature.py (1 failure)
- `test_verifysignature_json_matches_universal_vectors`

### 48. tests/utils/test_bitrails.py (2 failures)
- `test_verify_merkle_proof_to_merkle_path`
- `test_bitails_get_merkle_path`

### 49. tests/utils/test_height_range.py (5 failures)
- `test_length`
- `test_copy`
- `test_intersect`
- `test_union`
- `test_subtract`

### 50. tests/utils/test_pushdrop.py (1 failure)
- `test_pushdrop_transfer_example`

### 51. tests/utils/test_utility_helpers_no_buffer.py (4 failures)
- `test_convert_from_uint8array`
- `test_convert_from_number_array`
- `test_convert_from_hex_string`
- `test_convert_from_utf8_string`

### 52. tests/wallet/test_abort_action.py (1 failure)
- `test_abort_specific_reference`

### 53. tests/wallet/test_certificates.py (5 failures)
- TestWalletAcquireCertificate:
  - `test_acquirecertificate_listcertificate_provecertificate`
  - `test_privileged_acquirecertificate_listcertificate_provecertificate`
- TestWalletProveCertificate:
  - `test_prove_certificate`
- TestWalletDiscoverByIdentityKey:
  - `test_discover_by_identity_key`
- TestWalletDiscoverByAttributes:
  - `test_discover_by_attributes`

### 54. tests/wallet/test_internalize_action.py (1 failure)
- `test_internalize_custom_output_basket_insertion`

### 55. tests/wallet/test_list_actions.py (1 failure)
- `test_specific_label_filter`

### 56. tests/wallet/test_list_certificates.py (5 failures)
- `test_invalid_params_invalid_certifier`
- `test_filter_by_certifier_lowercase`
- `test_filter_by_certifier_uppercase`
- `test_filter_by_multiple_certifiers`
- `test_filter_by_type`

### 57. tests/wallet/test_list_outputs.py (6 failures)
- `test_invalid_params_empty_basket`
- `test_invalid_params_empty_tag`
- `test_invalid_params_limit_zero`
- `test_invalid_params_limit_exceeds_max`
- `test_invalid_params_negative_offset`
- `test_valid_params_with_originator`

### 58. tests/wallet/test_relinquish_output.py (1 failure)
- `test_relinquish_specific_output`

### 59. tests/wallet/test_sign_process_action.py (4 failures)
- TestWalletSignAction:
  - `test_sign_action_with_valid_reference`
  - `test_sign_action_with_spend_authorizations`
- TestWalletProcessAction:
  - `test_process_action_new_transaction`
  - `test_process_action_with_send_with`

### 60. tests/wallet/test_wallet_create_action.py (1 failure)
- `test_repeatable_txid`

### 61. tests/wallet/test_sync.py (3 errors)
- `test_sync_initial_then_no_changes_then_one_change` (ERROR)
- `test_set_active_to_backup_and_back_without_backup_first` (ERROR)
- `test_set_active_to_backup_and_back_with_backup_first` (ERROR)

---

## Summary by Category

### Most Affected Areas:
1. **Permissions Manager** (100 failures)
   - callbacks: 9
   - checks: 25
   - encryption: 8
   - flows: 7
   - initialization: 9
   - proxying: 30
   - tokens: 12

2. **Universal Vectors Tests** (22 failures)
   - Various protocol operations failing to match universal test vectors

3. **Chaintracks** (18 failures)
   - API, client, fetch, and service tests

4. **Integration Tests** (32 failures)
   - CWI Style Wallet Manager: 25
   - Bulk File Data Manager: 2
   - Local KV Store: 4
   - Single Writer Multi Reader Lock: 1

5. **Wallet Tests** (18 failures)
   - Actions, certificates, lists, signatures

6. **Services** (8 failures)
   - Exchange rates, merkle paths, raw transactions, beef handling

7. **Unit Tests** (18 failures)
   - Utility helpers and wallet basic operations

8. **Utils Tests** (12 failures)
   - Height range, pushdrop, bitrails, buffer utilities

9. **Monitor Tests** (9 failures)
   - Task processing and transaction handling

10. **Certificate Tests** (1 failure)
    - Life cycle test

---

## Next Steps Recommendations:

1. **Priority 1 - Core Permissions System**: Fix the permissions manager (100 failures)
2. **Priority 2 - Universal Vectors Compliance**: Address protocol compatibility (22 failures)
3. **Priority 3 - Integration Tests**: Fix wallet manager and storage (32 failures)
4. **Priority 4 - Chaintracks**: Resolve chain tracking functionality (18 failures)
5. **Priority 5 - Wallet Operations**: Fix wallet core operations (18 failures)
6. **Priority 6 - Utilities & Services**: Address utility and service failures (20 failures)

