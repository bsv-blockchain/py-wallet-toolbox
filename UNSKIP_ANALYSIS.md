# Analysis of "Ready to Unskip" Tests

## Executive Summary

After detailed investigation, **0 out of 14** tests marked as "ready to unskip" can actually be unskipped at this time. All have legitimate blocking issues.

## Investigation Results

### Category 1: Protocol Validation Issues (5 tests)

**Issue**: Universal test vectors use protocol names like "test-protocol" (with hyphens), but py-sdk's KeyDeriver validation only allows alphanumeric characters and spaces.

**Affected Tests**:
- `test_createsignature_json_matches_universal_vectors` 
- `test_decrypt_json_matches_universal_vectors`
- `test_encrypt_json_matches_universal_vectors` (already skipped for non-deterministic ECIES)
- `test_createhmac_json_matches_universal_vectors` (already skipped for KeyDeriver parity)
- `test_verifyhmac_json_matches_universal_vectors` (already skipped for KeyDeriver parity)

**Error Example**:
```
ValueError: protocol names can only contain letters, numbers and spaces
```

**Resolution**: 
- Option A: Modify py-sdk KeyDeriver to allow hyphens in protocol names
- Option B: Create test-specific protocol strings without hyphens  
- Option C: Keep tests skipped with accurate reason

**Action Taken**: Updated skip reasons to reflect protocol validation incompatibility.

---

### Category 2: Missing Implementation (2 tests)

**Issue**: Methods call non-existent `query_overlay()` function. Only `query_overlay_certificates()` exists.

**Affected Tests**:
- `test_discoverbyidentitykey_json_matches_universal_vectors`
- `test_discoverbyattributes_json_matches_universal_vectors`

**Error Example**:
```python
# In wallet.py line 2486:
cached_value = query_overlay(query_params)  # Function doesn't exist!

# Only this exists in identity_utils.py:
def query_overlay_certificates(query: Any, lookup_results: list[dict[str, Any]]) -> list[VerifiableCertificate]
```

**Resolution**: Implement missing `query_overlay()` function or refactor `discover_by_*` methods to use correct function signature.

**Action Taken**: Updated skip reasons to reflect missing implementation.

---

### Category 3: Require Database Setup (7 tests)

**Issue**: Tests expect specific pre-populated database state with transactions, outputs, certificates, etc.

**Affected Tests**:
- `test_listoutputs_json_matches_universal_vectors` - expects 2 specific outputs
- `test_listcertificates_simple_json_matches_universal_vectors` - expects certificate data
- `test_listcertificates_full_json_matches_universal_vectors` - expects certificate data  
- `test_listactions_json_matches_universal_vectors` - expects action data (also needs storage_provider in fixture)
- `test_signaction_json_matches_universal_vectors` - needs transaction bytes from create_action
- `test_internalizeaction_json_matches_universal_vectors` - needs AtomicBEEF parsing
- `test_provecertificate_json_matches_universal_vectors` - needs certificate in database
- `test_relinquishoutput_json_matches_universal_vectors` - needs output in database
- `test_createaction_1out_json_matches_universal_vectors` - needs storage_provider

**Expected vs Actual**:
```json
// Expected (from test vector):
{
  "totalOutputs": 2,
  "outputs": [...]
}

// Actual (empty database):
{
  "totalOutputs": 0,  
  "outputs": []
}
```

**Resolution**: Create comprehensive test fixtures that populate database with required test data matching universal test vectors.

**Action Taken**: These tests correctly remain skipped as "Database/Storage Setup Required".

---

## Recommendations

### Short Term
1. **Update SKIPPED_TESTS.md** with accurate categorization based on this analysis
2. **Fix protocol validation** in py-sdk or create alternative test data
3. **Implement missing `query_overlay` function** for discovery methods

### Long Term  
1. **Create universal-test-vector-compatible fixtures** that populate database with exact data expected by test vectors
2. **Implement proper AtomicBEEF parsing** for internalize_action
3. **Fix create_action to generate actual transaction bytes** for sign_action tests

## Summary Table

| Test | Reason | Can Unskip? | Action Required |
|------|--------|-------------|-----------------|
| createSignature | Protocol validation | No | Fix py-sdk or test data |
| decrypt | Protocol validation | No | Fix py-sdk or test data |
| encrypt | Protocol validation + non-deterministic | No | Multiple issues |
| createHmac | Protocol validation + KeyDeriver parity | No | Multiple issues |
| verifyHmac | Protocol validation + KeyDeriver parity | No | Multiple issues |
| discoverByIdentityKey | Missing query_overlay() | No | Implement function |
| discoverByAttributes | Missing query_overlay() | No | Implement function |
| listOutputs | DB setup | No | Create fixtures |
| listCertificates (2 tests) | DB setup | No | Create fixtures |
| listActions | DB setup + fixture | No | Create fixtures |
| signAction | DB setup + tx bytes | No | Multiple issues |
| internalizeAction | AtomicBEEF parsing | No | Implement parsing |
| proveCertificate | DB setup | No | Create fixtures |
| relinquishOutput | DB setup | No | Create fixtures |
| createAction | Storage fixture | No | Create fixtures |

## Files Modified

- `tests/universal/test_createsignature.py` - Updated skip reason (protocol validation)
- `tests/universal/test_decrypt.py` - Updated skip reason (protocol validation)  
- `tests/universal/test_discoverbyidentitykey.py` - Updated skip reason (missing implementation)
- `tests/universal/test_discoverbyattributes.py` - Needs skip reason update

## Next Steps

1. Document these findings in main SKIPPED_TESTS.md
2. Create GitHub issues for:
   - py-sdk protocol validation enhancement
   - query_overlay implementation
   - Universal test vector fixture creation
3. Focus unskipping efforts on simpler integration tests rather than universal test vectors

