# Skipped Tests Report

## Summary
**Total Skipped Tests**: 406 (46.83% of all tests)

**Note**: Currently, no tests are actively being skipped via pytest marks. The skip patterns in `conftest.py` are empty, allowing all tests to run. However, many tests are failing due to missing implementations rather than being explicitly skipped.

## Previously Skipped Tests (Now Enabled)

The following tests were previously skipped but are now running (and mostly failing):

### Storage Insert Tests (11 tests)
**Location**: `tests/storage/test_insert.py`
**Previous Skip Reason**: SQLAlchemy primary key naming mismatch
**Status**: Now running but failing due to data format issues

**Tests**:
- `test_insert_proventx`: TODO: merkle_path should be bytes, not list
- `test_insert_proventxreq`: TODO: Test data format issue
- `test_insert_monitorevent`: TODO: Test data format issue
- `test_insert_syncstate`: TODO: Test data format issue
- `test_insert_commission`: TODO: Transaction FK relationship setup
- `test_insert_output`: TODO: Transaction FK relationship setup
- `test_insert_outputtagmap`: TODO: OutputTag FK relationship setup
- `test_insert_certificate`: TODO: Test data missing required revocationOutpoint
- `test_insert_certificatefield`: TODO: Test data format or FK issue

### Storage Update Advanced Tests (4 tests)
**Location**: `tests/storage/test_update_advanced.py`
**Previous Skip Reason**: DB constraint validation
**Status**: Now running but failing due to missing constraint validation logic

**Tests**:
- `test_update_user_trigger_db_unique_constraint_errors`
- `test_update_user_trigger_db_foreign_key_constraint_errors`
- `test_update_certificate_trigger_db_unique_constraint_errors`
- `test_update_certificate_trigger_db_foreign_key_constraint_errors`

### User Merge Tests (2 tests)
**Location**: `tests/storage/test_users.py`
**Previous Skip Reason**: Missing storage mock for merge_existing
**Status**: Now running but failing due to missing merge_existing implementation

**Tests**:
- `test_mergeexisting_updates_user_when_ei_updated_at_is_newer`
- `test_mergeexisting_updates_user_with_trx`

## Recommended Skip Strategy

Given the current state of the codebase, consider implementing selective skipping for tests that:

1. **Require external services** (network calls, blockchain APIs)
2. **Need complex database setup** that isn't yet implemented
3. **Test unimplemented features** clearly marked as TODO
4. **Have known data format issues** that require schema changes

This would help focus development efforts on fixing core implementation issues rather than test setup problems.

## Skip Implementation

To re-enable selective skipping, update the `skip_patterns` dictionary in `tests/conftest.py`:

```python
skip_patterns = {
    # Network-dependent tests
    "test_whats_on_chain_*": "Requires network access",
    "test_arc_*": "Requires network access",

    # Database setup dependent
    "test_list_certificates_*": "Requires populated certificate database",
    "test_list_actions_*": "Requires populated actions database",

    # Unimplemented features
    "test_reveal_counterparty_key_linkage": "Method not implemented",
    "test_reveal_specific_key_linkage": "Method not implemented",
}
```
