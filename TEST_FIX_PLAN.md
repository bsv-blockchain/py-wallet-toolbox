# Systematic Test Fix Plan - 219 Failing Tests

**Goal:** Fix all failing tests systematically, prioritizing core functionality
**Current:** 590 passing, 219 failing (3 errors)
**Target:** 809 passing, 0 failing

---

## 📋 PHASE 1: CORE FUNCTIONALITY (HIGH PRIORITY)

### Estimated Effort: 60-80 tool calls
### Impact: Core wallet fully tested and production-ready

---

### **Step 1.1: Fix Wallet Constructor** (5-10 calls)

**File:** `tests/unit/test_wallet_constructor.py`
**Failures:** 1 test
**Issue:** Default labels/baskets not created on wallet initialization

**Tasks:**
1. Check `Wallet.__init__()` - ensure default labels created
2. Check `Wallet.__init__()` - ensure default basket created  
3. Verify storage.insert_tx_label and storage.insert_output_basket called
4. Run test and verify passes

**Expected Result:** ✅ 1 test fixed

---

### **Step 1.2: Fix Wallet Create Action Tests** (10-15 calls)

**File:** `tests/wallet/test_wallet_create_action.py`
**Failures:** 4 tests
**Issues:**
- Test mocks expect old format (before BRC-100 changes)
- Signable transaction structure changed

**Tasks:**
1. Review test `test_repeatable_txid` - adjust mock expectations
2. Review test `test_signable_transaction` - update signable format
3. Review test `test_create_action_defaults_options_and_returns_signable` - fix options
4. Review test `test_create_action_sign_and_process_flow` - update end-to-end flow
5. Update mocked storage.create_action return format to match BRC-100
6. Run tests and verify all 4 pass

**Expected Result:** ✅ 4 tests fixed

---

### **Step 1.3: Fix Wallet Core Tests** (30-40 calls)

**Files:**
- `tests/wallet/test_abort_action.py` (1 failure)
- `tests/wallet/test_certificates.py` (6 failures)
- `tests/wallet/test_internalize_action.py` (1 failure)
- `tests/wallet/test_list_actions.py` (1 failure)
- `tests/wallet/test_list_certificates.py` (4 failures)
- `tests/wallet/test_relinquish_output.py` (1 failure)
- `tests/wallet/test_sign_process_action.py` (4 failures)

**Issues:**
- Tests need seeded data (actions, certificates, outputs)
- Mocks need adjustment for BRC-100 format
- Pending action recovery integration

**Tasks:**

#### Abort Action (2-3 calls)
1. Check test expectations vs abort_action implementation
2. Verify storage mocking
3. Fix and run

#### Certificates (12-15 calls)
1. Seed test certificates in storage
2. Fix acquire_certificate test expectations
3. Fix list_certificates filtering tests
4. Fix prove_certificate expectations
5. Update certificate mocks for BRC-100
6. Run all 6 tests

#### Internalize Action (2-3 calls)
1. Fix basket insertion test
2. Verify BEEF parsing
3. Run test

#### List Actions (2-3 calls)
1. Seed test actions in storage
2. Fix label filtering test
3. Run test

#### List Certificates (6-8 calls)
1. Seed test certificates with various types
2. Fix certifier filtering (uppercase/lowercase)
3. Fix type filtering
4. Run all 4 tests

#### Relinquish Output (2-3 calls)
1. Seed output to relinquish
2. Fix test expectations
3. Run test

#### Sign/Process Action (8-10 calls)
1. Create pending action setup in tests
2. Fix sign_action with valid reference test
3. Fix sign_action with spend authorizations test
4. Fix process_action tests (3 tests)
5. Update mocks for out-of-session recovery
6. Run all 4 tests

**Expected Result:** ✅ 18 tests fixed

---

### **Step 1.4: Optional - Key Universal Vector Tests** (15-20 calls)

**Files:** Select 5-10 key universal vector tests  
**Issues:** Need deterministic setup

**Tasks:**
1. Use UNIVERSAL_TEST_VECTORS_ROOT_KEY in test fixtures
2. Seed exact UTXOs for create_action test
3. Seed exact data for list tests
4. Run 5-10 key tests and verify deterministic results

**Expected Result:** ✅ 5-10 tests fixed (optional)

---

## 🎯 PHASE 1 SUCCESS CRITERIA

After Phase 1:
- ✅ **23-33 tests fixed** (or 28-38 with universal vectors)
- ✅ **Core wallet operations fully tested**
- ✅ **Production-ready for basic usage**
- ✅ **613-623 tests passing** (out of 809)

**Phase 1 Completion: ~60-80 tool calls over 2-3 hours**

---

## 📋 PHASE 2: SUPPORTING SYSTEMS (MEDIUM PRIORITY)

### Estimated Effort: 100-150 tool calls
### Impact: Production-ready with monitoring and blockchain tracking

---

### **Step 2.1: Fix Utils Tests** (15-20 calls)

**Files:**
- `tests/utils/test_height_range.py` (5 failures)
- `tests/utils/test_bitrails.py` (2 failures)

**Tasks:**

#### HeightRange (8-10 calls)
1. Implement HeightRange.copy() method
2. Implement HeightRange.intersect() method
3. Implement HeightRange.length property
4. Implement HeightRange.subtract() method
5. Implement HeightRange.union() method
6. Run all 5 tests

#### Bitrails (7-10 calls)
1. Implement get_merkle_path utility
2. Implement verify_merkle_proof_to_merkle_path
3. Run both tests

**Expected Result:** ✅ 7 tests fixed

---

### **Step 2.2: Fix Services Tests** (20-30 calls)

**Files:**
- `tests/services/test_exchange_rates.py` (1 failure)
- `tests/services/test_get_merkle_path.py` (1 failure)
- `tests/services/test_get_raw_tx.py` (1 failure)
- `tests/services/test_local_services_hash_and_locktime.py` (1 failure)
- `tests/services/test_post_beef.py` (2 failures)
- `tests/services/test_verify_beef.py` (2 failures)

**Tasks:**
1. Mock external service calls (exchange rates, merkle paths)
2. Implement BEEF posting mocks
3. Implement BEEF verification utilities
4. Implement locktime validation
5. Implement raw transaction fetching mock
6. Run all 8 tests

**Expected Result:** ✅ 8 tests fixed

---

### **Step 2.3: Fix Chaintracks Tests** (40-60 calls)

**Files:**
- `tests/chaintracks/test_chaintracks.py` (2 failures)
- `tests/chaintracks/test_client_api.py` (11 failures)
- `tests/chaintracks/test_fetch.py` (4 failures)
- `tests/chaintracks/test_service_client.py` (2 failures)

**Tasks:**
1. Implement ChaintracksClient core methods (10-15 calls)
2. Implement header tracking utilities (10-15 calls)
3. Implement fetch/download utilities (8-10 calls)
4. Implement service client integration (8-10 calls)
5. Mock blockchain data sources
6. Run all 18 tests

**Expected Result:** ✅ 18 tests fixed

---

### **Step 2.4: Fix Monitor Tests** (30-40 calls)

**Files:**
- `tests/monitor/test_monitor.py` (8 failures)
- `tests/monitor/test_live_ingestor_whats_on_chain_poll.py` (1 failure)

**Tasks:**
1. Implement Monitor task system (async jobs) (15-20 calls)
2. Implement proof checking task (5-7 calls)
3. Implement header monitoring task (5-7 calls)
4. Implement send waiting task (3-5 calls)
5. Implement live ingestor (5-7 calls)
6. Run all 9 tests

**Expected Result:** ✅ 9 tests fixed

---

## 🎯 PHASE 2 SUCCESS CRITERIA

After Phase 2:
- ✅ **42 additional tests fixed**
- ✅ **Production-ready with monitoring**
- ✅ **Full blockchain tracking**
- ✅ **Service integrations complete**
- ✅ **655-665 tests passing** (out of 809)

**Phase 2 Completion: ~100-150 tool calls over 3-4 hours**

---

## 📋 PHASE 3: ENTERPRISE FEATURES (LOW PRIORITY - OPTIONAL)

### Estimated Effort: 230-360 tool calls
### Impact: Enterprise-ready with permissions and advanced features

---

### **Step 3.1: Fix Permissions Manager Tests** (150-200 calls)

**Files:** All `tests/permissions/test_wallet_permissions_manager_*.py`
**Failures:** 103 tests

**Major Components:**
1. Token system (DPACP, DSAP, DBAP, DCAP) (40-50 calls)
2. Callback system (20-30 calls)
3. Permission checks (30-40 calls)
4. Metadata encryption (15-20 calls)
5. Proxy methods (35-45 calls)
6. Flow management (10-15 calls)

**Expected Result:** ✅ 103 tests fixed

---

### **Step 3.2: Fix Integration Tests** (80-100 calls)

**Files:**
- `tests/integration/test_cwi_style_wallet_manager.py` (22 failures)
- `tests/integration/test_bulk_file_data_manager.py` (2 failures)
- `tests/integration/test_local_kv_store.py` (3 failures)
- `tests/integration/test_single_writer_multi_reader_lock.py` (1 failure)

**Tasks:**
1. Implement CWIStyleWalletManager (50-60 calls)
2. Implement UMP token system (15-20 calls)
3. Implement BulkFileDataManager (5-8 calls)
4. Implement LocalKVStore (5-7 calls)
5. Implement lock system (5-7 calls)

**Expected Result:** ✅ 28 tests fixed

---

### **Step 3.3: Fix Remaining Tests** (40-60 calls)

**Files:**
- `tests/wallet/test_sync.py` (3 errors)
- `tests/utils/test_pushdrop.py` (1 failure)
- Remaining universal vector tests (22 failures)

**Tasks:**
1. Implement sync system (25-35 calls)
2. Fix pushdrop integration (5-10 calls)
3. Complete universal vector determinism (10-15 calls)

**Expected Result:** ✅ 26 tests fixed

---

## 🎯 PHASE 3 SUCCESS CRITERIA

After Phase 3:
- ✅ **157 additional tests fixed**
- ✅ **ALL 809 tests passing**
- ✅ **100% test coverage**
- ✅ **Enterprise-ready**

**Phase 3 Completion: ~230-360 tool calls over 6-8 hours**

---

## 📊 EXECUTION TIMELINE

| Phase | Tests Fixed | Cumulative Passing | Effort | Time |
|-------|-------------|-------------------|--------|------|
| **Start** | - | 590/809 (73%) | - | - |
| **Phase 1** | 23-33 | 613-623/809 (76-77%) | 60-80 calls | 2-3 hrs |
| **Phase 2** | 42 | 655-665/809 (81-82%) | 100-150 calls | 3-4 hrs |
| **Phase 3** | 157 | 809/809 (100%) ✅ | 230-360 calls | 6-8 hrs |

---

## 🚀 QUICK START RECOMMENDATION

**Start with these files in order:**

1. ✅ `tests/unit/test_wallet_constructor.py` (1 test, 5-10 calls)
2. ✅ `tests/wallet/test_wallet_create_action.py` (4 tests, 10-15 calls)  
3. ✅ `tests/utils/test_height_range.py` (5 tests, 8-10 calls)
4. ✅ `tests/wallet/test_list_actions.py` (1 test, 2-3 calls)
5. ✅ `tests/wallet/test_abort_action.py` (1 test, 2-3 calls)

**First 30 calls = 12 tests fixed = Quick momentum!** 🎯

---

## 💡 KEY SUCCESS FACTORS

1. **Systematic Approach:** Fix by category, not randomly
2. **Test-Driven:** Run tests after each fix to verify
3. **Build on Success:** Later phases depend on earlier ones
4. **Focus:** Complete Phase 1 before moving to Phase 2
5. **Document:** Track progress as you go

---

**Ready to begin Phase 1? Let's fix the core functionality first!** 🚀

