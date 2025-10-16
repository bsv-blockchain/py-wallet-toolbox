# BSV BLOCKCHAIN | Wallet Toolbox for Python

Welcome to the BSV Blockchain Wallet Toolbox for Python — BRC-100 conforming wallet implementation providing production-ready, persistent storage components. Built on top of the official [Python SDK](https://github.com/bsv-blockchain/py-sdk), this toolbox helps you assemble scalable wallet-backed applications and services.

## Table of Contents

- [Objective](#objective)
- [Current Status](#current-status)
- [Getting Started](#getting-started)
  - [Installation](#installation)
  - [Quick Start](#quick-start)
  - [Examples & Usage Guides](#examples--usage-guides)
- [Building Blocks](#building-blocks)
- [Features](#features)
- [Architecture](#architecture)
- [Roadmap](#roadmap)
- [Documentation](#documentation)
- [Compatibility](#compatibility)
- [Contribution Guidelines](#contribution-guidelines)
- [Support & Contacts](#support--contacts)
- [License](#license)

## Objective

The BSV Wallet Toolbox builds on the [BSV SDK for Python](https://github.com/bsv-blockchain/py-sdk).

It aims to support building sophisticated applications and services on the BSV Blockchain technology stack by providing:

- **Production-Ready Wallet**: Full BRC-100 WalletInterface implementation with persistent storage
- **Database Persistence**: SQLAlchemy-based storage compatible with SQLite, PostgreSQL, and MySQL
- **Cross-Language Compatibility**: 100% compatible with TypeScript and Go implementations
- **Universal Test Vectors**: Validated against official BRC-100 test data
- **SPV-Friendly Workflows**: Privacy-preserving, scalable wallet operations

By providing interlocking, production-ready building blocks for persistent storage, protocol-based key derivation, and wallet orchestration, it serves as an essential toolbox for developers looking to build on the BSV Blockchain with Python.

## Current Status

**Version**: 0.1.0 (Alpha)

**Implemented Methods** (Level 1):
- ✅ `getVersion` - Get wallet version with originator validation

**In Development** (Levels 2-12):
- ⏳ `getNetwork`, `isAuthenticated`, `waitForAuthentication` (Level 2-3)
- ⏳ `getHeight`, `getHeaderForHeight`, `getPublicKey` (Level 3)
- ⏳ `listActions`, `listOutputs`, `listCertificates` (Level 4)
- ⏳ `createAction`, `signAction`, `internalizeAction` (Levels 7-9)
- ⏳ And 18 more methods...

See [CHANGELOG.md](./CHANGELOG.md) for detailed version history and [Implementation Strategy](../../doc/01_implementation_strategy.md) for the complete roadmap.

## Getting Started

### Installation

#### Prerequisites

- Python 3.11 or higher
- pip package manager
- SQLite (included with Python) or PostgreSQL/MySQL (optional)

#### From Source

```bash
# Clone the repository
git clone https://github.com/bsv-blockchain/wallet-toolbox.git
cd wallet-toolbox/toolbox/py-wallet-toolbox

# Create virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# or
.venv\Scripts\activate  # Windows

# Install in development mode
pip install -e .[dev]
```

### Quick Start

#### Basic Usage

```python
import asyncio
from bsv_wallet_toolbox import Wallet

async def main():
    # Create a wallet instance
    wallet = Wallet()
    
    # Get wallet version
    result = await wallet.get_version({})
    print(f"Wallet version: {result['version']}")
    # Output: Wallet version: 0.1.0
    
    # With originator validation
    result = await wallet.get_version({}, originator="example.com")
    print(f"Version: {result['version']}")

if __name__ == "__main__":
    asyncio.run(main())
```

#### Error Handling

```python
from bsv_wallet_toolbox import Wallet, InvalidParameterError

async def example_with_error_handling():
    wallet = Wallet()
    
    try:
        # This will raise InvalidParameterError
        result = await wallet.get_version({}, originator="x" * 251)
    except InvalidParameterError as e:
        print(f"Error: {e}")
        # Output: Error: Invalid parameter 'originator': must be under 250 bytes
```

### Examples & Usage Guides

Examples and detailed guides are available in:
- [Implementation Guide](../../doc/09_getversion_implementation_guide.md) - Step-by-step implementation of `getVersion`
- [Testing Strategy](../../doc/04_interoperability_testing_strategy.md) - How we ensure compatibility
- [Architecture Clarification](../../doc/10_architecture_clarification.md) - Understanding WalletInterface vs WalletStorageProvider

## Building Blocks

The Python Wallet Toolbox consists of the following components:

### Currently Implemented

- **Wallet** (`src/bsv_wallet_toolbox/wallet.py`): High-level wallet orchestration implementing BRC-100 WalletInterface
  - ✅ Version management with originator validation
  - ⏳ Network configuration
  - ⏳ Authentication state management
  - ⏳ Transaction creation and signing
  
- **Error Handling** (`src/bsv_wallet_toolbox/errors/`): Comprehensive error classes
  - ✅ `InvalidParameterError` for parameter validation
  - ⏳ Additional error types for various failure modes

### Planned Components

- **Storage Layer** (Level 4+): Durable records for actions, outputs, certificates, and related entities
  - SQLAlchemy-based ORM
  - Support for SQLite, PostgreSQL, MySQL
  - 16 database tables matching TypeScript schema
  
- **Services Integration** (Level 3+): Integrations for blockchain services
  - Chain tracker (block height, headers)
  - ARC (transaction broadcast)
  - Overlay services (discovery, certificates)
  
- **Monitor** (Level 10+): Background tasks for SPV-friendly workflows
  - Transaction status monitoring
  - Proof retrieval
  - Storage synchronization
  
- **JSON-RPC Dispatcher** (Level 12): Framework-neutral JSON-RPC server
  - Standard JSON-RPC 2.0 protocol
  - HTTP transport layer
  - Authentication middleware integration

## Features

### Current Features (v0.1.0)

- ✅ **BRC-100 Compliant**: Implements official WalletInterface specification
- ✅ **Type Safe**: Full type hints with mypy strict mode
- ✅ **Async/Await**: Modern asynchronous programming with asyncio
- ✅ **Originator Validation**: Secure parameter validation
- ✅ **Universal Test Vectors**: Validated against official BRC-100 test data
- ✅ **Cross-Platform**: Linux, macOS, Windows support
- ✅ **Well Documented**: Comprehensive English docstrings

### Planned Features

- ⏳ **Database Persistence**: SQLAlchemy-based storage (SQLite/PostgreSQL/MySQL)
- ⏳ **Protocol-Aligned Wallet Flows**: Full BRC-100 method implementation
- ⏳ **Pluggable Service Layer**: ARC, ChainTracker, Overlay Services
- ⏳ **Storage Synchronization**: Multi-device wallet sync
- ⏳ **JSON-RPC Server**: HTTP-based wallet server
- ⏳ **BRC-100 ABI**: Binary communication protocol
- ⏳ **SPV-Friendly Workflows**: Privacy-preserving operations
- ⏳ **Background Tasks**: Automated monitoring and proof management

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Application Layer                     │
│              (Your BSV Blockchain App)                   │
└───────────────────────┬─────────────────────────────────┘
                        │
                BRC-100 WalletInterface
                (28 async methods)
                        │
                        ▼
┌─────────────────────────────────────────────────────────┐
│                   Wallet Class                           │
│  ┌────────────────────────────────────────────────────┐ │
│  │  • getVersion() ✅                                 │ │
│  │  • createAction() ⏳                               │ │
│  │  • signAction() ⏳                                 │ │
│  │  • ... 25 more methods                             │ │
│  └────────────────────────────────────────────────────┘ │
│                        │                                 │
│       ┌────────────────┼────────────────┐               │
│       ▼                ▼                ▼               │
│  ┌─────────┐    ┌──────────┐    ┌──────────┐          │
│  │ Storage │    │ Services │    │  Monitor │          │
│  │ Manager │    │          │    │          │          │
│  └─────────┘    └──────────┘    └──────────┘          │
└─────────────────────────────────────────────────────────┘
         │                │               │
         ▼                ▼               ▼
    Database        Blockchain      Background
   (SQLAlchemy)     Services         Tasks
```

### Key Design Principles

1. **Framework Neutral**: Core library has no web framework dependencies
2. **Async First**: All I/O operations use async/await
3. **Type Safe**: Complete type hints for IDE support and static analysis
4. **Test Driven**: Universal Test Vectors + TypeScript test ports
5. **Cross-Language Compatible**: 100% compatible with TypeScript and Go

## Roadmap

### Phase 1: Core Wallet (v0.1.0 - v0.5.0) 🔄 Current Phase

- [x] Level 0: Project setup, type definitions
- [x] Level 1: `getVersion` ✅ **COMPLETED**
- [ ] Level 2: `getNetwork`, `isAuthenticated`, `waitForAuthentication`
- [ ] Level 3: Services integration (`getHeight`, `getHeaderForHeight`, `getPublicKey`)
- [ ] Level 4-7: Storage operations (list, relinquish, abort, internalize)
- [ ] Level 8-11: Transaction operations (create, sign, certificates, key linkage)

### Phase 2: Advanced Features (v0.6.0 - v1.0.0)

- [ ] Level 12: JSON-RPC dispatcher
- [ ] Level 13+: BRC-100 ABI implementation
- [ ] Storage synchronization
- [ ] Monitor (background tasks)
- [ ] Example applications

### Phase 3: Production Ready (v1.0.0+)

- [ ] Performance optimization
- [ ] Production deployment guides
- [ ] Docker support
- [ ] Comprehensive tutorials
- [ ] Enterprise features

See [Implementation Strategy](../../doc/01_implementation_strategy.md) for detailed breakdown.

## Documentation

### Core Documentation

- [Project Overview](../../doc/00_project_overview.md) - High-level project goals and approach
- [Implementation Strategy](../../doc/01_implementation_strategy.md) - Detailed implementation plan with 12 levels
- [WalletInterface Methods](../../doc/02_wallet_interface_methods.md) - All 28 methods explained
- [Design Decisions](../../doc/03_design_decisions.md) - Why we made certain architectural choices
- [Testing Strategy](../../doc/04_interoperability_testing_strategy.md) - How we ensure quality
- [JSON-RPC & ABI Guide](../../doc/05_library_choices_jsonrpc_wire.md) - Communication protocols
- [Database Schema](../../doc/08_database_schema.md) - Complete database design

### Implementation Guides

- [getVersion Implementation Guide](../../doc/09_getversion_implementation_guide.md) - Complete step-by-step guide
- [Architecture Clarification](../../doc/10_architecture_clarification.md) - WalletInterface vs WalletStorageProvider

### Reference Documentation

- Python SDK: [BSV SDK Documentation](https://github.com/bsv-blockchain/py-sdk)
- BRC-100 Specification: [Wallet Interface Standard](https://github.com/bitcoin-sv/BRCs/blob/master/wallet/0100.md)
- Universal Test Vectors: [Official Test Data](https://github.com/bsv-blockchain/universal-test-vectors)

The repository is richly documented with English docstrings that surface well in editors like VSCode.

## Compatibility

This Python implementation is designed to be 100% compatible with:

### TypeScript Implementation
- **Repository**: [ts-wallet-toolbox](../ts-wallet-toolbox)
- **Status**: ✅ API compatible
- **Testing**: Universal Test Vectors shared
- **Version**: Aligned with TypeScript v1.0.0

### Go Implementation  
- **Repository**: [go-wallet-toolbox](../go-wallet-toolbox)
- **Status**: ✅ API compatible
- **Testing**: Universal Test Vectors shared
- **Version**: Aligned with Go v1.0.0

### Compatibility Guarantees

All three implementations (Python, TypeScript, Go) share:
- ✅ Same BRC-100 WalletInterface API (28 methods)
- ✅ Identical behavior and error handling
- ✅ Same database schema (for Storage Synchronization)
- ✅ Universal Test Vectors validation
- ✅ Cross-implementation testing capability

## Contribution Guidelines

We're always looking for contributors to help us improve the Wallet Toolbox. Whether it's bug reports, feature requests, or pull requests - all contributions are welcome.

### Quick Start for Contributors

1. **Fork & Clone**: Fork this repository and clone it to your local machine.
2. **Set Up**: Run `pip install -e .[dev]` to install all dependencies.
3. **Make Changes**: Create a new branch and make your changes.
4. **Test**: Ensure all tests pass by running `pytest tests/ -v`.
5. **Quality Check**: Run `black src/ tests/`, `ruff check src/ tests/`, and `mypy src/`.
6. **Commit**: Commit your changes and push to your fork.
7. **Pull Request**: Open a pull request from your fork to this repository.

For detailed guidelines, check [CONTRIBUTING.md](./CONTRIBUTING.md).

### Important Notes

- **TypeScript Reference**: When porting features, always reference the TypeScript implementation
- **Universal Test Vectors**: All methods must pass official BRC-100 test vectors
- **Database Schema**: Never change database schema without coordination across all implementations
- **Type Safety**: All code must pass mypy strict mode
- **English Documentation**: All docstrings and comments must be in English

## Support & Contacts

**Project Owners**: Thomas Giacomo and Darren Kellenschwiler

**Development Team Lead**: Ken Sato @ Yenpoint Inc. & Yosuke Sato @ Yenpoint Inc.

For questions, bug reports, or feature requests:
- Open an issue on [GitHub](https://github.com/bsv-blockchain/wallet-toolbox/issues)
- Check existing [documentation](../../doc/)
- Review [TypeScript implementation](../ts-wallet-toolbox) for reference

## License

The license for the code in this repository is the Open BSV License version 4. Refer to [license.md](./license.md) for the license text.

---

Thank you for being a part of the BSV Blockchain Libraries Project. Let's build the future of BSV Blockchain together! 🚀
