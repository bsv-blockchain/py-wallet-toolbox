# Python Wallet Toolbox - Implementation Roadmap

**Last Updated**: 2025-10-22  
**Current Version**: 0.6.0  
**Implementation Status**: Phase 0 Complete (100%), Phase 1 Ready to Start

---

## 🎯 Development Strategy

This Python implementation follows a **list-based, test-driven approach** porting from TypeScript.

### Core Principles

1. **TypeScript Implementation as Source of Truth**
   - Port all functionality from `toolbox/ts-wallet-toolbox/`
   - Maintain 100% API compatibility with TypeScript implementation
   - Follow TypeScript's architecture and module structure

2. **List-Based Development**
   - All APIs, features, and tests are inventoried in comprehensive lists
   - Implementation proceeds in dependency order (least dependent first)
   - Progress tracked in `doc/implementation_progress.md` (separate repository)

3. **Test-First Approach**
   - 856 test cases identified (TypeScript: 794, Go unique: 62)
   - Tests created before implementation (mock level acceptable)
   - Universal Test Vectors validated for BRC-100 compliance

4. **Speed Over Perfection**
   - Get working implementation first
   - Detailed code review and refactoring comes later
   - Focus on interface correctness and test coverage

---

## 📊 Current Implementation Status

### Summary

| Category | Total | Completed | In Progress | Not Started | On Hold |
|----------|-------|-----------|-------------|-------------|---------|
| WalletInterface | 28 | 0 | 6 | 22 | 0 |
| WalletStorageProvider | 22 | 0 | 0 | 19 | 3 |
| WalletServices | 15 | 0 | 0 | 15 | 0 |
| Storage Layer (Tables) | 16 | 0 | 0 | 16 | 0 |
| Storage Layer (CRUD) | 30 | 0 | 0 | 30 | 0 |
| Monitor | 6 | 0 | 0 | 3 | 3 |
| Internal Utilities | 38 | 0 | 0 | 38 | 0 |
| **Total** | **130** | **0** | **6** | **118** | **6** |

**Overall Progress**: 4.6% (6/130 APIs implemented, tests pending)

### Test Infrastructure

- ✅ **MockWalletServices**: Implemented for interface testing without real API calls
- ✅ **Test Fixtures**: pytest fixtures for common test scenarios
- ✅ **Universal Test Vectors**: Integrated from official BRC-100 test data
- ✅ **Test Standards**: Documented (no doc/ references, no sequential IDs)

**Test Progress**:
- Total test cases: 856 (TypeScript: 794, Go adopted: 62)
- Skipped tests: 10 (8 ABI wire format tests intentionally skipped, 2 pending implementation)
- Passing tests: 17/28 currently executable

---

## 🏗️ Architecture Overview

### Layer Structure

```
┌─────────────────────────────────────────────────────────────┐
│                    Application Layer                        │
│                  (User's wallet app)                        │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                   WalletInterface (BRC-100)                 │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Wallet Class (28 methods)                          │   │
│  │  - getVersion, getNetwork                           │   │
│  │  - createAction, signAction                         │   │
│  │  - listOutputs, listCertificates                    │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
          │                           │
          │                           │
          ▼                           ▼
┌──────────────────────┐   ┌─────────────────────────────────┐
│   WalletServices     │   │  WalletStorageProvider          │
│                      │   │                                 │
│  - get_height()      │   │  - Database operations          │
│  - get_header()      │   │  - Transaction management       │
│  - get_chain_tracker│   │  - Output/Certificate CRUD      │
│                      │   │                                 │
│  Providers:          │   │  Backend: SQLAlchemy            │
│  ✅ WhatsOnChain     │   │  ✅ SQLite                      │
│  ❌ ARC (planned)    │   │  ✅ PostgreSQL                  │
│  ❌ Bitails (planned)│   │  ✅ MySQL                       │
└──────────────────────┘   └─────────────────────────────────┘
```

### Module Organization (TypeScript-aligned)

```
src/bsv_wallet_toolbox/
├── wallet.py                 # Wallet class (WalletInterface implementation)
├── errors/                   # Error classes (WERR_* errors)
│   ├── __init__.py
│   ├── invalid_parameter.py
│   └── internal_error.py
├── services/                 # Blockchain data services
│   ├── __init__.py
│   ├── wallet_services.py   # WalletServices ABC
│   ├── services.py          # Services implementation
│   └── providers/
│       ├── __init__.py
│       └── whatsonchain.py  # WhatsOnChain provider
├── storage/                  # Database persistence (not yet implemented)
│   ├── __init__.py
│   ├── provider.py          # WalletStorageProvider ABC
│   └── models/              # SQLAlchemy models
└── utils/                    # Internal utilities (not yet implemented)
    ├── __init__.py
    ├── validation.py
    └── transaction.py
```

**TypeScript Reference**: `toolbox/ts-wallet-toolbox/src/`

---

## 🚀 Implementation Phases

### ✅ Phase 0: Foundation (Week 1) - COMPLETE

**Goal**: Establish development infrastructure and documentation

**Deliverables**:
- ✅ Development strategy document
- ✅ Complete API inventory (130 APIs)
- ✅ Complete test inventory (856 test cases)
- ✅ Implementation progress tracker
- ✅ Test infrastructure (MockWalletServices, fixtures)
- ✅ Updated development rules and standards

**Status**: 100% Complete (11/11 tasks)

### 🎯 Phase 1: Core WalletInterface (Week 2-3) - READY TO START

**Goal**: Implement P0 priority WalletInterface methods

**Target APIs** (4 methods):
- `getVersion()` - Return wallet version
- `getNetwork()` - Return blockchain network
- `isAuthenticated()` - Check authentication status
- `waitForAuthentication()` - Wait for authentication

**Current Status**:
- ✅ Implementation: 4/4 complete
- ❌ Tests: 0/4 complete (needs proper test coverage)
- ❌ Documentation: Docstrings complete, examples needed

**Next Steps**:
1. Create comprehensive test suites for 4 P0 methods
2. Validate against Universal Test Vectors
3. Add usage examples to README

### 🔄 Phase 2: WalletServices + Height/Header (Week 4-5)

**Goal**: Complete blockchain data access layer

**Target APIs** (2 WalletInterface methods + 3 Services methods):
- WalletInterface:
  - `getHeight()` - Get current blockchain height
  - `getHeaderForHeight()` - Get block header at height
- WalletServices:
  - `get_height()` - Internal services method
  - `get_header_for_height()` - Internal services method
  - `get_chain_tracker()` - Get ChainTracker instance

**Dependencies**:
- WhatsOnChain provider (✅ implemented)
- MockWalletServices for testing (✅ implemented)

**Status**: 2/5 APIs implemented (Services complete, Wallet methods pending tests)

### 📦 Phase 3: Storage Layer (Week 6-8)

**Goal**: Implement database persistence

**Target Components**:
- Database schema (16 tables)
- CRUD operations (30 methods)
- WalletStorageProvider interface (22 methods)

**Status**: Not started (0/68 components)

### 🔐 Phase 4: Transaction Operations (Week 9-12)

**Goal**: Core transaction functionality

**Target APIs** (8 WalletInterface methods):
- `createAction()` - Create new transaction
- `signAction()` - Sign transaction
- `abortAction()` - Cancel transaction
- `processAction()` - Submit transaction
- `internalizeAction()` - Import external transaction
- `listActions()` - List transactions
- `getTransaction()` - Get transaction details
- `sendTransaction()` - Broadcast transaction

**Status**: Not started (0/8 methods)

### 📜 Phase 5: Outputs & Certificates (Week 13-15)

**Goal**: UTXO and certificate management

**Target APIs** (10 WalletInterface methods):
- Output management: 5 methods
- Certificate management: 5 methods

**Status**: Not started (0/10 methods)

### 🔍 Phase 6: Advanced Features (Week 16-18)

**Goal**: Advanced wallet operations

**Target APIs** (6 WalletInterface methods):
- Identity operations: 2 methods
- Sync operations: 2 methods
- Disclosure operations: 2 methods

**Status**: Not started (0/6 methods)

---

## 🧪 Testing Strategy

### Test Sources

1. **TypeScript Tests** (Primary)
   - Location: `toolbox/ts-wallet-toolbox/test/`
   - Total: 794 test cases
   - Status: Being ported to Python

2. **Go Tests** (Secondary - Safety Enhancement)
   - Location: `toolbox/go-wallet-toolbox/wallet/`
   - Adopted: 62 unique test cases (validation, BRC-29, Satoshi arithmetic)
   - Excluded: 449 Go-specific tests (config, logging, HTTP details)

3. **Universal Test Vectors** (Validation)
   - Official BRC-100 test data
   - Used for compliance validation
   - Location: `tests/data/universal-test-vectors/`

### Test Structure

```
tests/
├── unit/                          # Unit tests (ported from TypeScript)
│   ├── test_wallet_getversion.py
│   ├── test_wallet_getnetwork.py
│   ├── test_wallet_isauthenticated.py
│   ├── test_wallet_waitforauthentication.py
│   ├── test_wallet_getheight.py
│   └── test_wallet_getheaderforheight.py
│
├── universal/                     # Universal Test Vectors
│   ├── test_getversion.py
│   ├── test_getnetwork.py
│   ├── test_isauthenticated.py
│   ├── test_waitforauthentication.py
│   ├── test_getheight.py
│   └── test_getheaderforheight.py
│
├── conftest.py                    # Shared fixtures and MockWalletServices
└── data/
    └── universal-test-vectors/    # Official BRC-100 test data
```

### Test Standards

**Requirements**:
- ✅ Given-When-Then pattern (mandatory)
- ✅ TypeScript test reference (file path + test name)
- ✅ Universal Test Vector validation where applicable
- ❌ No doc/ references (separate repository)
- ❌ No sequential test IDs (maintainability)

**Example**:
```python
@pytest.mark.asyncio
async def test_returns_correct_version(self) -> None:
    """Given: Wallet instance
       When: Call getVersion
       Then: Returns correct version string
       
    Reference: toolbox/ts-wallet-toolbox/test/Wallet/get/getVersion.test.ts
               test('should return the correct wallet version')
    """
    # Given
    wallet = Wallet(chain="main")
    
    # When
    result = await wallet.get_version({})
    
    # Then
    assert result["version"] == Wallet.VERSION
```

---

## 🛠️ Development Tools

### Required Tools

- **Python 3.11+**: Core language
- **pytest**: Test framework
- **black**: Code formatter (120 char line length)
- **ruff**: Linter
- **mypy**: Type checker
- **SQLAlchemy 2.0+**: Database ORM

### Development Workflow

```bash
# 1. Format code
black src/ tests/

# 2. Lint code
ruff check --fix src/ tests/

# 3. Type check
mypy src/

# 4. Run tests
pytest

# 5. Run tests with coverage
pytest --cov=src/bsv_wallet_toolbox --cov-report=html
```

### Coding Standards

- **Style**: PEP 8 (with 120 char line length)
- **Naming**: snake_case for functions/variables, PascalCase for classes
- **Documentation**: Google-style docstrings in English
- **Type Hints**: Required for all public APIs
- **Comments**: English only (no Japanese in code)

---

## 📚 Key Reference Documents

### Primary References (TypeScript Implementation)

- **Wallet Class**: `toolbox/ts-wallet-toolbox/src/Wallet.ts`
- **WalletInterface**: TypeScript SDK types
- **Services**: `toolbox/ts-wallet-toolbox/src/services/Services.ts`
- **Tests**: `toolbox/ts-wallet-toolbox/test/`

### Implementation Guides (Separate Repository)

These documents are in a separate documentation repository:
- Development strategy and principles
- Complete API inventory (130 APIs)
- Complete test inventory (856 test cases)
- Implementation progress tracker
- Database schema design

**Note**: Reference TypeScript implementation directly; avoid cross-repository documentation dependencies.

---

## 🎯 Current Focus (Week 2)

### Immediate Priorities

1. **Complete P0 Method Tests**
   - Write comprehensive test suites for 4 basic methods
   - Validate against Universal Test Vectors
   - Ensure all edge cases are covered

2. **Implement Internal Utilities (P1)**
   - Validation functions (14 functions)
   - Start with `validateOriginator()` (used by all methods)
   - Add comprehensive error handling

3. **Begin Phase 2 Planning**
   - Review WalletServices implementation
   - Plan Storage layer architecture
   - Identify additional dependencies

### Weekly Goals

- ✅ Phase 0: Complete (100%)
- 🎯 Phase 1: Start P0 method testing
- 📋 Phase 2: Design and planning

---

## 🔮 Future Enhancements

### v0.7.0 - Core Transaction Operations
- Action creation and signing
- Transaction management
- Basic storage layer

### v0.8.0 - Advanced Features
- Certificate management
- Identity operations
- Sync operations

### v0.9.0 - Production Readiness
- Performance optimization
- Security audit
- Comprehensive error handling
- Production-grade logging

### v1.0.0 - First Stable Release
- All 28 WalletInterface methods implemented
- 90%+ test coverage
- Complete documentation
- Universal Test Vectors passing
- Cross-implementation compatibility validated

---

## 🤝 Compatibility

### Cross-Implementation Compatibility

| Feature | TypeScript | Go | Python | Status |
|---------|-----------|-----|--------|--------|
| WalletInterface (28 methods) | ✅ Complete | ✅ Complete | 🚧 21% (6/28) | In Progress |
| Storage Layer | ✅ IndexedDB | ✅ SQL | ❌ SQLAlchemy | Planned |
| WalletServices | ✅ Multiple | ✅ Multiple | 🚧 WhatsOnChain | In Progress |
| Universal Test Vectors | ✅ Validated | ✅ Validated | 🚧 Partial | In Progress |

### Data Compatibility

- ✅ **JSON-RPC 2.0**: Primary communication protocol (implemented)
- 🚧 **BRC-100 ABI**: Wire protocol (planned for browser extensions)
- ✅ **Database Schema**: Compatible with TypeScript/Go schemas
- ✅ **Key Derivation**: BIP32/BIP39 compatible (via py-sdk)

---

## 📞 Support & Resources

### Community

- **GitHub Issues**: Bug reports and feature requests
- **Discussions**: Architecture and design discussions
- **Documentation**: Inline docstrings and README

### Contributing

Contributions are welcome! Please:
1. Follow the coding standards (English only, PEP 8)
2. Write tests for new features
3. Update documentation
4. Reference TypeScript implementation for consistency

---

**Version**: 0.6.0  
**Last Updated**: 2025-10-22  
**Status**: Phase 0 Complete (100%), Phase 1 Ready to Start

**Progress**: 6/130 APIs implemented (4.6%) | 17/856 tests passing
