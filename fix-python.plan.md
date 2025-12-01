# Fix Remaining 273 Test Failures

## Current State
- **273 failing tests** across 6 major categories
- Core BRC-100 implementation complete
- Missing: async permission handling, service validation, integration scenarios

## Failure Categories by Priority

| Category | Failures | Files | Priority |
|----------|----------|-------|----------|
| Services (post_beef, get_raw_tx, etc.) | ~120 | 17 files | High |
| Wallet Validation | ~50 | 10 files | High |
| Permissions Manager | ~25 | 5 files | Medium |
| Universal Signatures | ~5 | 3 files | Medium |
| Integration/Edge Cases | ~5 | 3 files | Low |

---

## Phase 1: Services Layer Fixes (~120 failures)

### 1.1 Post BEEF Service
**Files**: `services/services.py`, `test_post_beef.py`

Tests expect `post_beef` to raise exceptions for invalid input:
- Change return dict to raise `InvalidParameterError` for None/wrong types
- Keep returning `{accepted: False}` for network errors

### 1.2 Get Raw Tx Service
**File**: `services/services.py`

Add `get_raw_tx` method with:
- Txid validation (64-char hex)
- Provider failover
- Error handling (500, 429, timeout)

### 1.3 Get Merkle Path Service
**File**: `services/services.py`

Add `get_merkle_path` method with:
- Txid validation
- Provider failover
- Response structure validation

### 1.4 Exchange Rates Service
**File**: `services/services.py`

Fix `update_fiat_exchange_rates` method:
- Add currency validation
- Handle network errors
- Return proper rate structure

### 1.5 Local Services (Hash/Locktime)
**File**: `services/services.py`

Fix `n_lock_time_is_final` and `hash_output_script`:
- Handle edge cases (no inputs, mixed sequences)
- Validate locktime values

---

## Phase 2: Wallet Validation Fixes (~50 failures)

### 2.1 HMAC/Signature Methods
**File**: `utils/validation.py`

Fix remaining validation issues:
- `validate_create_signature_args`: Missing data validation
- `validate_verify_signature_args`: Missing signature validation
- Empty counterparty handling

### 2.2 Crypto Methods
**File**: `utils/validation.py`

Fix:
- `validate_encrypt_args`: Invalid counterparty hex validation
- `validate_decrypt_args`: Empty ciphertext handling

### 2.3 Certificate Methods
**File**: `utils/validation.py`

Fix:
- `validate_list_certificates_args`: Invalid hex certifiers, empty types
- `validate_discover_by_attributes_args`: Zero limit handling

### 2.4 List Methods
**File**: `utils/validation.py`

Fix:
- `validate_list_actions_args`: Invalid labelQueryMode values
- `validate_list_outputs_args`: Invalid include values

---

## Phase 3: Permissions Manager (~25 failures)

### 3.1 Async Permission Flow
**File**: `manager/wallet_permissions_manager.py`

The core issue: Tests use async callbacks but current implementation is sync.

Fix `create_signature` and other methods:
```python
def create_signature(self, args, originator=None):
    # Skip permission for secLevel=0
    protocol_id = args.get("protocolID", [])
    if isinstance(protocol_id, list) and len(protocol_id) >= 1:
        if protocol_id[0] == 0:
            return self._underlying_wallet.create_signature(args, originator)
    
    # For secLevel >= 1, trigger permission callback
    request_id = self._generate_request_id()
    self._active_requests[request_id] = {"pending": True}
    
    # Fire callback and wait for grant/deny
    self._trigger_permission_callback("onProtocolPermissionRequested", {...})
    
    # Check if granted
    if not self._active_requests.get(request_id, {}).get("granted"):
        raise RuntimeError("Permission denied")
```

### 3.2 Callback Mechanism
**File**: `manager/wallet_permissions_manager.py`

Fix `bind_callback` to properly store and invoke callbacks:
- Store callbacks in `_callbacks` dict
- Invoke async callbacks with `asyncio.create_task`

### 3.3 Grant/Deny Flow
**File**: `manager/wallet_permissions_manager.py`

Fix `grant_permission` and `deny_permission`:
- Update `_active_requests` with grant status
- Resume waiting operations

### 3.4 Admin-Only Checks
**File**: `manager/wallet_permissions_manager.py`

Fix admin-only protocol/basket checks:
- Check for "admin." prefix in protocol names
- Check for reserved basket names ("default")

---

## Phase 4: Universal Signatures (~5 failures)

### 4.1 Signature Roundtrip
**File**: `wallet.py`

Fix `verify_signature` to properly verify signatures created by `create_signature`:
- Ensure consistent key derivation
- Handle counterparty="self" correctly

### 4.2 Direct Hash Signing
**File**: `wallet.py`

Support `hashToDirectlySign` parameter in `create_signature`

---

## Phase 5: Integration/Edge Cases (~5 failures)

### 5.1 CWI Manager Snapshot
**File**: `manager/cwi_style_wallet_manager.py`

Fix snapshot save/load cycle

### 5.2 Wallet Constructor
**File**: `wallet.py`

Fix invalid private_key format validation

---

## Key Files to Modify

1. `src/bsv_wallet_toolbox/services/services.py` - Service methods
2. `src/bsv_wallet_toolbox/utils/validation.py` - Validation
3. `src/bsv_wallet_toolbox/manager/wallet_permissions_manager.py` - Permissions
4. `src/bsv_wallet_toolbox/wallet.py` - Wallet methods

## Estimated Effort

- Phase 1 (Services): ~4-5 hours
- Phase 2 (Validation): ~2-3 hours
- Phase 3 (Permissions): ~3-4 hours
- Phase 4 (Signatures): ~1-2 hours
- Phase 5 (Integration): ~1 hour

**Total: ~12-15 hours of implementation**

## TODO List

- [ ] Fix post_beef to raise exceptions for invalid input types
- [ ] Implement get_raw_tx with validation and provider failover
- [ ] Implement get_merkle_path with validation
- [ ] Fix exchange rates service with currency validation
- [ ] Fix n_lock_time_is_final and hash_output_script edge cases
- [ ] Fix HMAC/signature validation edge cases
- [ ] Fix encrypt/decrypt validation edge cases
- [ ] Fix certificate and list method validation
- [ ] Fix permissions manager async callback flow
- [ ] Fix grant/deny permission mechanism
- [ ] Fix admin-only protocol/basket checks
- [ ] Fix signature creation/verification roundtrip
- [ ] Fix CWI manager and wallet constructor edge cases

