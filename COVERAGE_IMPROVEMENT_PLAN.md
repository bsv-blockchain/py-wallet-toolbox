# Test Coverage Improvement Plan

## Phase 1: Run Full Test Suite with Coverage

Run pytest with coverage reporting and capture output:

```bash
cd /home/sneakyfox/TOOLBOX/py-wallet-toolbox
source venv/bin/activate
pytest tests/ --cov=src/bsv_wallet_toolbox --cov-report=html --cov-report=term-missing -v 2>&1 | tee coverage_results_$(date +%Y%m%d_%H%M%S).txt
```

This generates:
- Terminal output with missing line numbers
- HTML report in `htmlcov/`
- Timestamped results file

## Phase 2: High-Impact Coverage Targets

Based on analysis of existing `htmlcov/status.json`, these modules have the most missing statements (sorted by absolute impact):

| Module | Missing Lines | Total | Impact Priority |
|--------|--------------|-------|-----------------|
| [storage/provider.py](src/bsv_wallet_toolbox/storage/provider.py) | 610 | 1774 | Highest |
| [manager/wallet_permissions_manager.py](src/bsv_wallet_toolbox/manager/wallet_permissions_manager.py) | 452 | 1176 | High |
| [wallet.py](src/bsv_wallet_toolbox/wallet.py) | 253 | 901 | High |
| [storage/crud.py](src/bsv_wallet_toolbox/storage/crud.py) | 178 | 361 | High |
| [signer/methods.py](src/bsv_wallet_toolbox/signer/methods.py) | 176 | 396 | High |
| [storage/entities.py](src/bsv_wallet_toolbox/storage/entities.py) | 167 | 923 | Medium |
| [storage/methods.py](src/bsv_wallet_toolbox/storage/methods.py) | 163 | 539 | Medium |

## Phase 3: Systematic Test Development

For each target module, I will:

1. **Analyze uncovered code paths** using `--cov-report=term-missing` output
2. **Create focused test files** following existing naming convention (`test_*_coverage.py`)
3. **Write tests** that cover:
   - Uncovered branches and methods
   - Error handling paths
   - Edge cases
4. **Validate** by re-running coverage on the specific module

### Test File Locations

Tests will be added to existing test directories:
- [tests/storage/](tests/storage/) - for provider.py, crud.py, entities.py, methods.py
- [tests/permissions/](tests/permissions/) - for wallet_permissions_manager.py
- [tests/wallet/](tests/wallet/) - for wallet.py
- [tests/signer/](tests/signer/) - for signer/methods.py

## Execution Order

1. Run full test suite with coverage
2. Start with `storage/provider.py` (highest impact - 610 missing lines)
3. Move to `wallet_permissions_manager.py` (452 missing lines)
4. Continue through remaining high-impact modules
5. Re-run full coverage after each major module to track progress

---

## Progress Log

### Run 1: Initial Coverage Baseline
- **Date**: 2025-12-04
- **Results**: 3135 passed, 90 skipped, 5 xfailed, 1 xpassed in 71.39s
- **Overall Coverage**: 70.53% (15573 statements, 4589 missing)

### Work Completed: storage/provider.py
- **Date**: 2025-12-04
- **New Test File**: `tests/storage/test_provider_high_impact.py`
- **Tests Added**: 26 new tests covering:
  - Soft-deleted basket restoration (lines 203-205)
  - Sync state operations (insert, find)
  - list_outputs SpecOps (wallet balance, pagination)
  - Tag filtering (all, unspent, change)
  - Include options (labels, tags, custom instructions)
  - list_actions enhancements (status, txid filters)
  - InternalizeAction validation
  - Transaction operations (find, update status)
  - Certificate listing with filters
  - Output basket operations
  - BEEF building
  - create_action minimal test

### Work Completed: wallet_permissions_manager.py
- **Date**: 2025-12-04
- **New Test File**: `tests/permissions/test_permissions_protocols_coverage.py`
- **Tests Added**: 30 new tests covering:
  - DPACP methods (grant, verify, revoke, list)
  - DBAP methods (grant, verify, list)
  - DCAP methods (grant, verify, list)
  - DSAP methods (grant, verify, list)
  - Permission configuration (defaults, overrides)
  - Admin originator functionality
  - Callback management
  - Token expiry checks
  - Request ID generation

### Work Completed: wallet.py (partial)
- **Date**: 2025-12-04
- **New Test File**: `tests/wallet/test_wallet_high_impact_coverage.py`
- **Tests Added**: 20 new tests covering:
  - Wallet initialization exception handling (lines 274-276)
  - BEEF processing and delegation
  - Sign action BEEF merge functionality
  - Utility functions (_as_bytes, _to_byte_list)
  - Error conditions and edge cases

### Work Completed: storage/crud.py
- **Date**: 2025-12-04
- **New Test File**: `tests/storage/test_crud_conditions_coverage.py`
- **Tests Added**: 49 new tests covering:
  - StringCondition methods (equals, not_equals, in, not_in, like)
  - NumericCondition methods (equals, not_equals, in, not_in, like raises)
  - BoolCondition methods (equals, not_equals, in, not_in, like raises)
  - TimeCondition methods (equals, not_equals, in, not_in, like raises)
  - OutputReader fluent interface
  - TxNoteAccessor and TxNoteReader
  - KnownTxAccessor and KnownTxReader
  - CertifierAccessor and CertifierReader
  - OutputAccessor methods

---

## Final Coverage Report
- **Date**: 2025-12-04
- **Baseline**: 70.53% (15573 statements, 4589 missing)
- **Tests Added**: 125 new tests across 4 modules
- **Modules Improved**:
  - storage/provider.py: 26 tests (610 missing lines targeted)
  - wallet_permissions_manager.py: 30 tests (452 missing lines targeted)
  - wallet.py: 20 tests (253 missing lines partially addressed)
  - storage/crud.py: 49 tests (178 missing lines targeted)
- **Remaining High-Impact Targets**:
  - signer/methods.py (176 missing lines)
  - storage/methods.py (163 missing lines)
  - storage/entities.py (167 missing lines)

## Todo Checklist

- [x] Run full pytest suite with coverage and capture results to timestamped file
- [x] Analyze storage/provider.py uncovered lines and add tests (26 tests added)
- [x] Analyze wallet_permissions_manager.py uncovered lines and add tests (30 tests added)
- [x] Analyze wallet.py uncovered lines and add tests (20 tests added, 253 missing)
- [x] Analyze storage/crud.py uncovered lines and add tests (49 tests added, 178 missing)
- [x] Run final coverage report and document improvements
- [ ] Analyze signer/methods.py uncovered lines and add tests (176 missing)
- [ ] Analyze storage/methods.py uncovered lines and add tests (163 missing)
- [ ] Analyze storage/entities.py uncovered lines and add tests (167 missing)

