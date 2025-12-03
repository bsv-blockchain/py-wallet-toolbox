# Python vs Go SDK TODO Analysis Report

## Overview

This report compares the implementation status of TODO items and not-implemented features between the Python SDK (`py-wallet-toolbox`) and Go SDK (`go-wallet-toolbox`) for BSV wallet functionality.

| Metric | Python SDK | Go SDK |
|--------|------------|--------|
| TODO count | 92 | 57 |
| NotImplemented stubs | ~18 | 6 (panics) |
| Manager modules | 5 (CWI, Permissions, UMP, Settings, WalletInterface) | 0 |
| Certificate methods | Implemented (12 methods) | Not implemented (8 panics) |
| ChainTracks features | HTTP server + WebSocket framework | Basic services only |
| Monitor tasks | 3 tasks implemented | All tasks implemented |
| Storage persistence | SQLite framework ready | Full PostgreSQL/SQLite support |

## Python-only Features

### Manager Modules (5 total)
The Python SDK has comprehensive manager implementations that are absent in Go:

1. **CWI Style Wallet Manager** - Profile switching, UMP token updates, wallet funding
2. **Wallet Permissions Manager** - Protocol permissions, token caching, UI callbacks
3. **UMP Token Interactor** - PushDrop token creation, overlay services integration
4. **Wallet Settings Manager** - Configuration persistence, LocalKVStore integration
5. **Wallet Interface** - Abstract base class for wallet implementations

### ChainTracks HTTP Server
- **FastAPI-based HTTP server** with CORS and health endpoints
- **API endpoints**: `/health`, `/header/height/{height}`, `/tx/{txid}`, `/merkle/{txid}`
- **WebSocket subscription framework** (ready for Phase 4 implementation)

### Advanced Monitor Options
- **MonitorOptions attributes**: `unproven_attempts_limit_test/main`, `abandoned_msecs`, `msecs_wait_per_merkle_proof_service_req`, `chaintracks`
- **Task-specific implementations**: TaskCheckForProofs, TaskSendWaiting, TaskSyncWhenIdle

## Go-only/Stronger Features

### Storage & Sync Capabilities
- **Comprehensive test coverage** for storage operations (27 test files)
- **Full sync implementation** with chunk processing and state management
- **Advanced storage features**: batch operations, reorg detection, transaction safety
- **Database migration framework** with version tracking

### Service Integration
- **Multiple provider support** (WhatsOnChain, Bitails, Arc)
- **Caching infrastructure** for exchange rates and Merkle roots
- **Circuit breaker patterns** and retry strategies

### Wallet Core Features
- **Privileged key manager** support (referenced but not implemented)
- **Complete monitor task implementation** (no TODOs remaining)
- **Advanced transaction assembler** with template creation

## Shared Gaps

### Privileged Key Manager
Both SDKs reference privileged key manager support but neither implements it:
- Python: `sdk.privileged_key_manager` import exists but unused
- Go: Multiple TODO comments referencing PrivilegedKeyManager.ts

### WebSocket Subscriptions
- **Python**: Framework ready but server implementation pending
- **Go**: No WebSocket infrastructure present

### Overlay Services
- **Python**: UMP token interactor has overlay lookup stubs
- **Go**: No overlay service integration

### Advanced Certificate Operations
- **Python**: Full certificate method implementations
- **Go**: All 8 certificate methods panic with "TODO implement me"

## Recommendations

### Priority 1: Go SDK Enhancement
1. **Implement certificate methods** - Go SDK has critical gaps in identity operations
2. **Add manager modules** - CWI, permissions, and UMP token management
3. **WebSocket support** - Real-time ChainTracks subscriptions

### Priority 2: Python SDK Completion
1. **WebSocket server implementation** - Complete ChainTracks real-time features
2. **Overlay services integration** - Decentralized token lookups
3. **Storage optimizations** - Connection pooling, advanced migrations

### Priority 3: Cross-SDK Parity
1. **Privileged key manager** - Implement in both SDKs
2. **Unified test coverage** - Ensure feature parity testing
3. **Shared specifications** - Common interfaces for manager modules

## Conclusion

The Python SDK shows more advanced feature development in wallet management and ChainTracks services, while the Go SDK demonstrates stronger storage and sync capabilities. Both SDKs have significant shared gaps in privileged operations and real-time features. Achieving full parity would require ~25 additional features across both implementations.
