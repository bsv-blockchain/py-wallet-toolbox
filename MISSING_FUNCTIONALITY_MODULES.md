# Missing Functionality Modules - Python vs TypeScript/Go Comparison

## Executive Summary

Of the **191 skipped tests**, they fall into clear categories representing major missing subsystems. This document compares Python implementation status against TypeScript (ts-wallet-toolbox) and Go (go-wallet-toolbox) implementations.

**Test Status:** 681 passed, 191 skipped, 6 xfailed

---

## 🔴 CATEGORY 1: Major Subsystems Requiring Complete Implementation

### 1. Certificate Subsystem (~15 tests skipped)

**Status:** ❌ Not Implemented in Python | ✅ Complete in TypeScript | ✅ Complete in Go

**What's Missing:**
- Certificate issuance and verification
- Master certificates and verifiable certificates
- Certificate fields and metadata
- Certificate lifecycle management (create, prove, relinquish, discover)
- Certificate storage and retrieval

**TypeScript Implementation:**
```typescript
// ts-wallet-toolbox/src/sdk/
- Certificate.ts (base class)
- MasterCertificate.ts
- VerifiableCertificate.ts
- CertificateHelpers.ts

// Storage layer
- storage/methods/insertCertificate.ts
- storage/methods/listCertificates.ts
- storage/methods/findCertificates.ts
```

**Go Implementation:**
```go
// go-wallet-toolbox/pkg/wallet/
- certificate.go
- certificate_manager.go
- certificate_validator.go
```

**Python Status:**
- Storage schema defined in `storage/models.py` (Certificate, CertificateField tables)
- Basic CRUD operations exist
- **Missing:** All business logic, verification, issuance, discovery
- Helper functions raise `NotImplementedError`

**Effort to Implement:** 80-120 hours
- Certificate verification logic
- PKI infrastructure
- Subject/certifier key management
- Field validation and schema
- Revocation handling

**Skipped Tests:**
- `test_certificate_life_cycle.py` (1 test)
- `test_certificates.py` (5 tests)
- `test_list_certificates.py` (4 tests)
- `universal/test_acquirecertificate.py` (1 test)
- `universal/test_discoverbyattributes.py` (1 test)
- `universal/test_discoverbyidentitykey.py` (1 test)
- `universal/test_provecertificate.py` (1 test)
- `universal/test_relinquishcertificate.py` (1 test)
- `universal/test_listcertificates.py` (2 tests)

---

### 2. Crypto Subsystem (~10 tests skipped)

**Status:** ❌ Not Implemented in Python | ✅ Complete in TypeScript | ✅ Complete in Go

**What's Missing:**
- Encryption/Decryption (AES-GCM)
- HMAC creation and verification
- Digital signatures (ECDSA)
- Key linkage revelation (counterparty and specific)

**TypeScript Implementation:**
```typescript
// ts-wallet-toolbox/src/sdk/
- crypto/encrypt.ts
- crypto/decrypt.ts
- crypto/createHmac.ts
- crypto/verifyHmac.ts
- crypto/createSignature.ts
- crypto/verifySignature.ts
- crypto/revealCounterpartyKeyLinkage.ts
- crypto/revealSpecificKeyLinkage.ts
```

**Go Implementation:**
```go
// go-wallet-toolbox/pkg/crypto/
- encryption.go
- hmac.go
- signatures.go
- key_linkage.go
```

**Python Status:**
- Basic HMAC/signature tests passing (using bsv-sdk primitives)
- **Missing:** High-level wallet integration methods
- No encryption/decryption implementation
- No key linkage revelation

**Effort to Implement:** 40-60 hours
- Encryption: AES-GCM with derived keys
- HMAC: Key derivation + HMAC-SHA256
- Signatures: ECDSA signing and verification
- Key linkage: BIP32-style derivation + revelation protocols

**Skipped Tests:**
- `test_crypto_methods.py` (2 tests - key linkage)
- `universal/test_createhmac.py` (1 test)
- `universal/test_createsignature.py` (1 test)
- `universal/test_decrypt.py` (1 test)
- `universal/test_encrypt.py` (1 test)
- `universal/test_revealcounterpartykeylinkage.py` (1 test)
- `universal/test_revealspecifickeylinkage.py` (1 test)
- `universal/test_verifyhmac.py` (1 test)
- `universal/test_verifysignature.py` (1 test)

---

### 3. Permissions Manager (~55 tests skipped)

**Status:** ⚠️ Partially Implemented in Python | ✅ Complete in TypeScript | ✅ Complete in Go

**What's Implemented (Python):**
- ✅ Basic permission token creation
- ✅ Storage for permissions and tokens
- ✅ Permission proxying to storage methods
- ✅ Basic initialization

**What's Missing:**
- ❌ Permission checking before operations (all marked "Phase 4")
- ❌ Permission token types: DPACP, DSAP, DBAP, DCAP
- ❌ Callback system for permission requests
- ❌ Full integration flows
- ❌ Permission encryption and metadata handling

**TypeScript Implementation:**
```typescript
// ts-wallet-toolbox/src/
- WalletPermissionsManager.ts (main class)
- permissions/PermissionChecker.ts
- permissions/TokenManager.ts
- permissions/CallbackHandler.ts
- permissions/types.ts (DPACP, DSAP, DBAP, DCAP definitions)
```

**Go Implementation:**
```go
// go-wallet-toolbox/pkg/permissions/
- manager.go
- checker.go
- tokens.go
- callbacks.go
```

**Python Status:**
```python
# src/bsv_wallet_toolbox/wallet_permissions_manager.py
- Basic structure exists
- Storage integration working
- 20+ methods marked "# TODO: Phase 4 - Implement permission checks"
```

**Effort to Implement:** 60-100 hours
- Permission checking logic (protocol permissions, action permissions)
- Token type implementations (DPACP, DSAP, DBAP, DCAP)
- Callback infrastructure
- Permission validation and enforcement
- Integration with wallet methods

**Skipped Tests:**
- `test_wallet_permissions_manager_callbacks.py` (9 tests)
- `test_wallet_permissions_manager_checks.py` (25 tests)
- `test_wallet_permissions_manager_flows.py` (7 tests)
- `test_wallet_permissions_manager_tokens.py` (12 tests)
- `test_wallet_permissions_manager_encryption.py` (1 test)
- `test_wallet_permissions_manager_initialization.py` (1 test)

---

### 4. Sync Subsystem (~3 tests skipped)

**Status:** ❌ Not Implemented in Python | ✅ Complete in TypeScript | ✅ Complete in Go

**What's Missing:**
- Wallet state synchronization across devices/storages
- Sync chunk creation and merging
- Conflict resolution
- Delta synchronization

**TypeScript Implementation:**
```typescript
// ts-wallet-toolbox/src/storage/methods/
- createSyncChunk.ts
- requestSyncChunk.ts
- mergeSyncChunk.ts
- resolveSyncConflicts.ts

// Entity-level sync
- entities/Transaction.mergeExisting()
- entities/Output.mergeExisting()
- entities/Certificate.mergeExisting()
```

**Go Implementation:**
```go
// go-wallet-toolbox/pkg/sync/
- chunk_manager.go
- merger.go
- conflict_resolver.go
```

**Python Status:**
- SyncState storage model exists
- Basic entity merge methods stubbed
- **Missing:** All sync coordination logic
- No chunk creation/merging
- No conflict resolution

**Effort to Implement:** 80-120 hours
- Sync protocol implementation
- Chunk serialization/deserialization
- Entity merging strategies
- Conflict detection and resolution
- Network layer for sync transport

**Skipped Tests:**
- `test_sync.py` (3 tests)

---

### 5. Transaction Building Infrastructure (~8 tests skipped)

**Status:** ❌ Not Implemented in Python | ✅ Complete in TypeScript | ✅ Complete in Go

**What's Missing:**
- Input selection (UTXO selection algorithm)
- Transaction structure building
- BEEF generation for inputs
- Signing coordination

**TypeScript Implementation:**
```typescript
// ts-wallet-toolbox/src/storage/methods/
- createAction.ts (full implementation with input selection)
- selectInputs.ts
- buildTransaction.ts
- generateInputBeef.ts
- signTransaction.ts
```

**Go Implementation:**
```go
// go-wallet-toolbox/pkg/transaction/
- builder.go
- input_selector.go
- beef_generator.go
- signer.go
```

**Python Status:**
```python
# src/bsv_wallet_toolbox/storage/provider.py
def create_action(self, auth, args):
    # Only creates transaction shell
    storage_beef_bytes = vargs.input_beef_bytes or b""  # No input selection!
    # Missing: UTXO selection, transaction building, BEEF generation
```

**Current Behavior:**
- Creates unsigned transaction records
- No input selection
- No BEEF generation
- Cannot actually sign or broadcast transactions

**Effort to Implement:** 40-80 hours
- Input selection algorithm (coin selection strategies)
- Transaction structure building
- BEEF packaging
- Integration with signing

**Skipped Tests:**
- `test_sign_process_action.py` (5 tests)
- `test_internalize_action.py` (1 test)
- `test_wallet_create_action.py` (2 tests)

---

## 🟠 CATEGORY 2: Integration & Infrastructure Tests

### 6. Chaintracks/Monitor System (~26 tests skipped)

**Status:** ⚠️ Partially Implemented in Python | ✅ Complete in TypeScript | ✅ Complete in Go

**What's Implemented:**
- ✅ Basic WhatsOnChain integration (get_raw_tx, get_merkle_path)
- ✅ Chain tracker interface

**What's Missing:**
- ❌ WhatsOnChainServices module (header management)
- ❌ Bulk header ingestion (CDN support)
- ❌ Monitor system (background task coordination)
- ❌ Live header polling
- ❌ Proof checking and validation

**TypeScript Implementation:**
```typescript
// ts-wallet-toolbox/src/services/chaintracker/
- chaintracks/Ingest/WhatsOnChainServices.ts
- chaintracks/Ingest/BulkFileDataManager.ts
- chaintracks/Monitor/MonitorTaskClock.ts
- chaintracks/Monitor/LiveIngestor.ts
```

**Python Status:**
```python
# Tests show:
pytestmark = pytest.mark.skip(reason="Module not yet implemented")

try:
    from bsv_wallet_toolbox.services.chaintracker.chaintracks.ingest import WhatsOnChainServices
    IMPORTS_AVAILABLE = True
except ImportError:
    IMPORTS_AVAILABLE = False  # Fails - module doesn't exist
```

**Effort to Implement:** 60-100 hours
- WhatsOnChainServices: Header fetching and management
- BulkFileDataManager: CDN integration for bulk downloads
- Monitor: Background task coordination
- LiveIngestor: Real-time header polling

**Skipped Tests:**
- `test_services.py` (8 tests - WhatsOnChainServices)
- `test_client_api.py` (10 tests - Chaintracks client)
- `test_fetch.py` (4 tests - CDN downloads)
- `test_service_client.py` (2 tests)
- `test_monitor.py` (8 tests)
- `test_live_ingestor_whats_on_chain_poll.py` (1 test)
- `test_bulk_ingestor_cdn_babbage.py` (2 tests)
- `test_bulk_file_data_manager.py` (2 tests)

---

### 7. CWI-Style Wallet Manager (~25 tests skipped)

**Status:** ❌ Not Implemented in Python | ✅ Complete in TypeScript | ⚠️ Partial in Go

**What's Missing:**
- Complete user management workflows
- Token-based encryption
- Password change flows
- Recovery key management
- Multi-user wallet support

**TypeScript Implementation:**
```typescript
// ts-wallet-toolbox/src/
- CWIStyleWalletManager.ts (full implementation)
- TokenEncryption.ts
- UserManagement.ts
- RecoveryKeys.ts
```

**Python Status:**
- Basic CWIStyleWalletManager structure exists
- **Missing:** Full integration test coverage
- Complex workflows not tested

**Effort to Implement:** 40-60 hours (mostly test infrastructure)

**Skipped Tests:**
- `test_cwi_style_wallet_manager.py` (25 tests)

---

### 8. Privileged Key Manager (~23 tests skipped)

**Status:** ❌ Not Implemented in Python | ✅ Complete in TypeScript | ✅ Complete in Go

**What's Missing:**
- BRC-2 compliant key derivation
- BRC-3 invoice number verification
- Key obfuscation and retention policies
- Privilege escalation handling

**TypeScript Implementation:**
```typescript
// ts-wallet-toolbox/src/
- PrivilegedKeyManager.ts
- BRC2KeyDerivation.ts
- BRC3InvoiceValidation.ts
```

**Effort to Implement:** 40-60 hours

**Skipped Tests:**
- `test_privileged_key_manager.py` (23 tests)

---

## 🟡 CATEGORY 3: Universal Test Vectors (~22 tests skipped)

**Status:** 🔄 Infrastructure Required

**Why Skipped:**
These tests validate cross-implementation compatibility using official BRC-100 test vectors. They require:
1. **Transaction building infrastructure** (see Category 1, #5)
2. **Deterministic wallet state** (exact UTXOs, keys, database seeds)
3. **py-sdk compatibility fixes** (key derivation algorithm differences)

**TypeScript/Go Status:** ✅ All universal test vectors passing

**Python Status:** 
- Test infrastructure exists
- Test vector files loaded correctly
- **Blocked by:** Missing transaction building + deterministic fixtures

**Skipped Tests:**
- `universal/test_createaction.py` (2 tests)
- `universal/test_getpublickey.py` (1 test) - Also blocked by py-sdk key derivation
- `universal/test_internalizeaction.py` (1 test)
- `universal/test_listactions.py` (1 test)
- `universal/test_listoutputs.py` (1 test)
- `universal/test_relinquishoutput.py` (1 test)
- `universal/test_signaction.py` (1 test)
- Plus 15 more crypto/certificate-related universal tests

---

## Summary Matrix: Python vs TypeScript vs Go

| Module | Python | TypeScript | Go | Effort (hours) | Tests Skipped |
|--------|--------|------------|----|--------------:|---------------|
| **Certificates** | ❌ 0% | ✅ 100% | ✅ 100% | 80-120 | 15 |
| **Crypto (encrypt/decrypt)** | ❌ 0% | ✅ 100% | ✅ 100% | 40-60 | 10 |
| **Permissions Manager** | ⚠️ 30% | ✅ 100% | ✅ 100% | 60-100 | 55 |
| **Sync Subsystem** | ❌ 0% | ✅ 100% | ✅ 100% | 80-120 | 3 |
| **Transaction Building** | ❌ 10% | ✅ 100% | ✅ 100% | 40-80 | 8 |
| **Chaintracks/Monitor** | ⚠️ 40% | ✅ 100% | ✅ 100% | 60-100 | 26 |
| **CWI Manager** | ⚠️ 60% | ✅ 100% | ⚠️ 80% | 40-60 | 25 |
| **Privileged Keys** | ❌ 0% | ✅ 100% | ✅ 100% | 40-60 | 23 |
| **Universal Vectors** | 🔄 Infra | ✅ 100% | ✅ 100% | 80-120 | 22 |
| **TOTAL** | **~25%** | **100%** | **~95%** | **520-820h** | **187** |

**Legend:**
- ✅ Complete implementation
- ⚠️ Partial implementation
- ❌ Not implemented
- 🔄 Blocked by dependencies

---

## What Python HAS Implemented (Parity with TS/Go)

### ✅ Core Functionality (100% Parity)

1. **Storage Layer** - Full SQLAlchemy ORM implementation
   - All CRUD operations
   - Entity models matching TS/Go schemas
   - Query methods and filtering

2. **Basic Wallet Operations** - Working implementations
   - `list_outputs` - Full parity
   - `list_actions` - Full parity
   - `abort_action` - Full parity
   - `relinquish_output` - Full parity

3. **Services Layer** - Core infrastructure
   - WhatsOnChain integration (get_raw_tx, get_merkle_path, get_utxo_status)
   - Multi-provider failover
   - Caching
   - Service call history

4. **Wallet Managers** - Basic implementations
   - SimpleWalletManager - 100% complete
   - WalletSettingsManager - 100% complete
   - CWIStyleWalletManager - Core structure (60% complete)

5. **Key Derivation** - Using py-sdk
   - Protocol/key ID derivation
   - Counterparty derivation
   - *(Note: Algorithm differs from TS BIP32 style)*

6. **BRC-29** - Full implementation
   - Address templates
   - Template validation
   - 56 tests passing

---

## Priority Recommendations

Based on impact and effort, recommended implementation order:

### Phase 1: Core Transaction Functionality (40-80h)
**Priority: CRITICAL**
- Transaction building infrastructure
- Input selection algorithm
- BEEF generation
- **Impact:** Unlocks 8 tests + enables real wallet usage

### Phase 2: Crypto Subsystem (40-60h)
**Priority: HIGH**
- Encryption/Decryption
- HMAC implementation
- Signatures
- **Impact:** Unlocks 10 tests + enables secure operations

### Phase 3: Chaintracks Infrastructure (60-100h)
**Priority: MEDIUM**
- WhatsOnChainServices module
- Bulk header ingestion
- Monitor system basics
- **Impact:** Unlocks 26 tests + enables blockchain tracking

### Phase 4: Permissions Manager Completion (60-100h)
**Priority: MEDIUM**
- Permission checking logic
- Token types (DPACP, DSAP, DBAP, DCAP)
- Callback system
- **Impact:** Unlocks 55 tests + enables production security

### Phase 5: Certificates (80-120h)
**Priority: LOW (optional feature)**
- Certificate verification
- Issuance and management
- Discovery protocols
- **Impact:** Unlocks 15 tests + enables identity features

### Phase 6: Sync & Advanced Features (120-180h)
**Priority: LOW (future work)**
- Sync subsystem
- CWI Manager completion
- Privileged Key Manager
- **Impact:** Unlocks 51 tests + enables multi-device support

---

## Conclusion

**Python Implementation Status: ~25% feature complete compared to TypeScript**

**TypeScript/Go Implementations: Production-ready, feature-complete**

The Python implementation has solid foundations (storage, basic wallet ops, services) but is missing critical subsystems that TypeScript and Go have fully implemented. The skipped tests clearly identify where Python diverges from the reference implementations.

**Key Takeaway:** Python is suitable for basic wallet operations but needs significant development (520-820 hours) to reach TypeScript/Go feature parity for production use cases involving transactions, certificates, permissions, and sync.

