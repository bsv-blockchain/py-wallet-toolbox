# Implementation Roadmap - Remaining 65 Tests

**Current Status:** 604/809 passing (75%), 65 failing  
**All 65 Tests Documented:** Root causes identified, effort estimated

---

## 🎯 PRIORITY MATRIX

### Priority 1: High Value, Medium Effort (22-30 calls)
**ROI:** Fixes 15+ tests with moderate effort

1. **Wallet Test Data Fixtures** (7 tests, 15-25 calls)
   - Create reusable transaction/output seeding utilities
   - Implement proper SQLAlchemy session management
   - Benefits: Unblocks wallet integration tests

2. **Integration Utilities** (7 tests, 20-30 calls)
   - LocalKVStore implementation
   - BulkFileDataManager basics
   - Lock implementations
   - Benefits: Core infrastructure tests pass

### Priority 2: High Value, High Effort (90-120 calls)
**ROI:** Major feature completion

3. **Universal Vector Fixtures** (22 tests, 40-60 calls)
   - Deterministic key derivation matching TS/Go
   - UTXO seeding matching vector expectations
   - Transaction building for exact txid matches
   - Benefits: Full BRC-100 spec compliance proven

4. **Chaintracks Client** (8 tests, 20-30 calls)
   - JSON-RPC client implementation
   - Header fetching and caching
   - Benefits: Background blockchain tracking

5. **Permissions Proxy Methods** (10 tests, 30-40 calls)
   - Implement proxy methods (create_action, create_signature, etc.)
   - Metadata encryption integration
   - Benefits: Core permissions functionality

### Priority 3: Full Subsystems (130-200 calls)
**ROI:** Enterprise features

6. **Certificate System** (10 tests, 50-80 calls)
   - Certificate creation/storage/retrieval
   - Proving and verification mechanisms
   - Discovery system implementation
   - Benefits: Complete certificate support

7. **Monitor Live Ingestor** (1 test, 5-10 calls)
   - Live header polling implementation
   - Benefits: Real-time chain monitoring

---

## 📋 DETAILED IMPLEMENTATION PLANS

### 1. Wallet Test Data Fixtures (15-25 calls)

**Files to Create:**
```python
tests/fixtures/transaction_fixtures.py  # Reusable transaction seeding
tests/fixtures/output_fixtures.py       # Reusable output seeding
tests/fixtures/session_utils.py         # Proper session management
```

**Implementation Steps:**
1. Create fixture utilities (5 calls)
2. Implement transaction seeding (5 calls)
3. Implement output seeding (5 calls)
4. Update failing tests to use fixtures (5-10 calls)

**Tests Fixed:**
- `test_abort_action.py::test_abort_specific_reference`
- `test_internalize_action.py::test_internalize_custom_output_basket_insertion`
- `test_relinquish_output.py::test_relinquish_specific_output`
- `test_sign_process_action.py::test_sign_action_with_valid_reference`
- `test_sign_process_action.py::test_sign_action_with_spend_authorizations`
- `test_sign_process_action.py::test_process_action_invalid_params_missing_txid`
- `test_sign_process_action.py::test_process_action_new_transaction`
- `test_sign_process_action.py::test_process_action_with_send_with` (maybe)

**Estimated Effort:** 15-25 calls

---

### 2. Integration Utilities (20-30 calls)

**Files to Create:**
```python
src/bsv_wallet_toolbox/integration/local_kv_store.py       # Key-value storage
src/bsv_wallet_toolbox/integration/bulk_file_manager.py     # File management
src/bsv_wallet_toolbox/integration/rw_lock.py               # Reader-writer lock
```

**Implementation Steps:**
1. Implement LocalKVStore (8-10 calls)
   - get(), set(), delete() methods
   - In-memory storage for tests
   
2. Implement BulkFileDataManager (8-10 calls)
   - CDN file management
   - Caching logic
   
3. Implement SingleWriterMultiReaderLock (4-10 calls)
   - Concurrency primitives
   - Test scenarios

**Tests Fixed:**
- `test_local_kv_store.py::test_get_non_existent`
- `test_local_kv_store.py::test_set_get`
- `test_local_kv_store.py::test_set_x_4_get`
- `test_local_kv_store.py::test_set_x_4_get_set_x_4_get`
- `test_bulk_file_data_manager.py::test_default_options_cdn_files`
- `test_bulk_file_data_manager.py::test_default_options_cdn_files_nodropall`
- `test_single_writer_multi_reader_lock.py::test_concurrent_reads_and_writes_execute_in_correct_order`

**Estimated Effort:** 20-30 calls

---

### 3. Universal Vector Fixtures (40-60 calls)

**Strategy:** Create deterministic test environment matching TS/Go

**Files to Create:**
```python
tests/fixtures/universal_vector_setup.py  # Deterministic setup utilities
tests/universal/conftest.py               # Shared fixtures for all vectors
```

**Implementation Steps:**
1. Analyze TS/Go universal vector test setup (5 calls)
2. Create deterministic key derivation (10 calls)
3. Implement UTXO seeding matching vectors (10 calls)
4. Create transaction building utilities (10 calls)
5. Update vector tests to use fixtures (10-15 calls)

**Key Challenges:**
- Must produce **exact** txids matching vectors
- Must use **exact** key derivation paths as TS/Go
- Must have **exact** UTXO states as vectors expect

**Tests Fixed:** All 22 universal vector tests

**Estimated Effort:** 40-60 calls

---

### 4. Chaintracks Client (20-30 calls)

**Files to Create:**
```python
src/bsv_wallet_toolbox/services/chaintracker/chaintracks/client.py
src/bsv_wallet_toolbox/services/chaintracker/chaintracks/fetch_utils.py
```

**Implementation Steps:**
1. Implement JSON-RPC client (10-15 calls)
2. Implement fetch utilities (5-10 calls)
3. Add configuration support (5 calls)

**Tests Fixed:**
- `test_chaintracks.py::test_nodb_mainnet`
- `test_chaintracks.py::test_nodb_testnet`
- `test_fetch.py::test_fetchjson`
- `test_fetch.py::test_download`
- `test_fetch.py::test_download_716`
- `test_fetch.py::test_download_717`
- `test_service_client.py::test_mainnet_findheaderforheight`
- `test_service_client.py::test_testnet_findheaderforheight`

**Estimated Effort:** 20-30 calls

---

### 5. Permissions Proxy Methods (30-40 calls)

**Files to Update:**
```python
src/bsv_wallet_toolbox/manager/wallet_permissions_manager.py
```

**Implementation Steps:**
1. Implement proxy method stubs (10 calls)
2. Add encryption/decryption integration (10-15 calls)
3. Implement admin originator bypass (5 calls)
4. Update tests (5-10 calls)

**Proxy Methods Needed:**
- `create_action()`
- `create_signature()`
- `disclose_certificate()`
- `list_actions()` with decryption
- `list_outputs()` with decryption

**Tests Fixed:**
- 4 encryption integration tests
- 6 initialization/proxy tests

**Estimated Effort:** 30-40 calls

---

### 6. Certificate System (50-80 calls)

**Files to Create:**
```python
src/bsv_wallet_toolbox/certificates/certificate_manager.py
src/bsv_wallet_toolbox/certificates/proving.py
src/bsv_wallet_toolbox/certificates/discovery.py
src/bsv_wallet_toolbox/certificates/storage.py
```

**Implementation Steps:**
1. Design certificate data model (5 calls)
2. Implement certificate storage (10-15 calls)
3. Implement certificate creation/acquisition (10-15 calls)
4. Implement proving mechanisms (10-15 calls)
5. Implement discovery system (10-15 calls)
6. Integrate with wallet (5-10 calls)

**Tests Fixed:** All 10 certificate tests

**Estimated Effort:** 50-80 calls

---

### 7. Monitor Live Ingestor (5-10 calls)

**Files to Create:**
```python
src/bsv_wallet_toolbox/monitor/live_ingestor.py
```

**Implementation Steps:**
1. Implement header polling (5-10 calls)

**Tests Fixed:**
- `test_live_ingestor_whats_on_chain_poll.py::test_listen_for_first_new_header`

**Estimated Effort:** 5-10 calls

---

## 🚀 RECOMMENDED IMPLEMENTATION ORDER

### Week 1: Quick Wins (35-55 calls)
**Goal:** +14 tests passing (604 → 618, 76%)**

1. Wallet Test Data Fixtures (15-25 calls) → +7-8 tests
2. Integration Utilities (20-30 calls) → +7 tests

**Result:** Foundation infrastructure in place

### Week 2: Specification Compliance (40-60 calls)
**Goal:** +22 tests passing (618 → 640, 79%)**

3. Universal Vector Fixtures (40-60 calls) → +22 tests

**Result:** Full BRC-100 compliance proven

### Week 3: Supporting Systems (50-70 calls)
**Goal:** +19 tests passing (640 → 659, 81%)**

4. Chaintracks Client (20-30 calls) → +8 tests
5. Permissions Proxy Methods (30-40 calls) → +10 tests
6. Monitor Live Ingestor (5-10 calls) → +1 test

**Result:** All supporting systems functional

### Week 4: Enterprise Features (50-80 calls)
**Goal:** +10 tests passing (659 → 669, 83%)**

7. Certificate System (50-80 calls) → +10 tests

**Result:** Complete enterprise feature set

---

## 📊 CUMULATIVE PROGRESS PROJECTION

| Milestone | Tests Passing | Coverage | Calls | Cumulative Calls |
|-----------|---------------|----------|-------|------------------|
| **Current** | 604 | 75% | 0 | 225 |
| After Week 1 | 618 | 76% | 35-55 | 260-280 |
| After Week 2 | 640 | 79% | 75-115 | 300-340 |
| After Week 3 | 659 | 81% | 125-185 | 350-410 |
| After Week 4 | 669 | 83% | 175-265 | 400-490 |

**Final Goal:** 669/809 passing (83%)

---

## 🎯 SUCCESS CRITERIA

### By Priority Level

**Priority 1 Complete (Week 1):**
- ✅ Wallet tests have proper fixtures
- ✅ Integration utilities implemented
- ✅ 618/809 tests passing (76%)

**Priority 2 Complete (Week 2-3):**
- ✅ Universal vectors all passing
- ✅ Chaintracks client functional
- ✅ Permissions proxy methods working
- ✅ 659/809 tests passing (81%)

**Priority 3 Complete (Week 4):**
- ✅ Certificate system fully implemented
- ✅ 669/809 tests passing (83%)
- ✅ All major subsystems complete

---

## 💡 IMPLEMENTATION TIPS

### For Wallet Test Data Fixtures
- Use pytest fixtures with `scope="function"` to avoid session conflicts
- Create factories that return new instances each time
- Use SQLAlchemy's scoped_session properly
- Consider using test database transactions for isolation

### For Universal Vectors
- Start by running TS/Go tests to see exact setup
- Extract key derivation paths from vector generation code
- Match UTXO setup exactly (amounts, scripts, etc.)
- Use same transaction building logic as TS/Go

### For Chaintracks
- Use async/await consistently
- Implement proper error handling for network failures
- Add caching to reduce API calls
- Test with both mainnet and testnet

### For Certificates
- Design data model first
- Consider using existing storage provider tables
- Implement proving before discovery
- Test certificate chains thoroughly

---

## 📝 NOTES

### What's NOT Needed (Already Done)
- ✅ Core wallet functionality (75% proven)
- ✅ Transaction building and signing
- ✅ Storage layer
- ✅ Service integration basics
- ✅ Utils (HeightRange, MerklePath, etc.)

### What IS Needed (This Roadmap)
- Test infrastructure (fixtures, utilities)
- Specification compliance (universal vectors)
- Supporting systems (chaintracks, monitor)
- Enterprise features (certificates, permissions)

### Critical Success Factors
1. **Don't modify universal test vectors** - Implementation must match them
2. **Use proper fixtures** - Avoid SQLAlchemy session conflicts
3. **Follow TS/Go patterns** - Maintain parity
4. **Test incrementally** - One subsystem at a time
5. **Document as you go** - Keep roadmap updated

---

## ✨ CONCLUSION

**Total Estimated Effort:** 175-265 tool calls  
**Total Tests to Fix:** 65  
**Final Coverage Target:** 83% (669/809)

**This roadmap provides:**
- ✅ Clear priorities (ordered by ROI)
- ✅ Detailed implementation steps
- ✅ Effort estimates for each category
- ✅ Success criteria at each milestone
- ✅ Practical implementation tips

**Next Steps:**
1. Start with Priority 1 (Week 1) for quick wins
2. Move to Priority 2 (Weeks 2-3) for spec compliance
3. Complete Priority 3 (Week 4) for enterprise features

**Status:** Ready for systematic implementation 🚀
