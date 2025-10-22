# BSV BLOCKCHAIN | Wallet Toolbox for Python

Welcome to the BSV Blockchain Wallet Toolbox for Python — BRC-100 conforming wallet implementation providing production-ready, persistent storage components. Built on top of the official [Python SDK](https://github.com/bsv-blockchain/py-sdk), this toolbox helps you assemble scalable wallet-backed applications and services.

## Table of Contents

- [Objective](#objective)
- [Current Status](#current-status)
- [Getting Started](#getting-started)
  - [Installation](#installation)
  - [Quick Start](#quick-start)
- [Building Blocks](#building-blocks)
- [Features](#features)
- [Architecture](#architecture)
- [Roadmap](#roadmap)
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

**Implementation Progress**: Phase 0 Complete, Phase 1 Ready to Start

This is an early-stage implementation. The wallet is being built incrementally with a focus on:
- List-based development approach
- Test-driven development
- Cross-implementation compatibility

See [CHANGELOG.md](./CHANGELOG.md) for detailed version history.

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

#### From PyPI (Coming Soon)

```bash
pip install bsv-wallet-toolbox
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

## Building Blocks

The Python Wallet Toolbox consists of the following components:

### Currently Implemented

- **Wallet** (`src/bsv_wallet_toolbox/wallet.py`): High-level wallet orchestration implementing BRC-100 WalletInterface
  - ✅ Basic wallet structure
  - ⏳ 28 BRC-100 methods (in development)
  
- **Error Handling** (`src/bsv_wallet_toolbox/errors/`): Comprehensive error classes
  - ✅ `InvalidParameterError` for parameter validation
  - ⏳ Additional error types for various failure modes

### Planned Components

- **Storage Layer**: Durable records for actions, outputs, certificates, and related entities
  - SQLAlchemy-based ORM
  - Support for SQLite, PostgreSQL, MySQL
  - 16 database tables matching TypeScript schema
  
- **Services Integration**: Integrations for blockchain services
  - Chain tracker (block height, headers)
  - ARC (transaction broadcast)
  - Overlay services (discovery, certificates)
  
- **Monitor**: Background tasks for SPV-friendly workflows
  - Transaction status monitoring
  - Proof retrieval
  - Storage synchronization
  
- **JSON-RPC Dispatcher**: Framework-neutral JSON-RPC server
  - Standard JSON-RPC 2.0 protocol
  - HTTP transport layer
  - Authentication middleware integration

## Features

### Current Features (v0.1.0)

- ✅ **BRC-100 Compliant**: Implements official WalletInterface specification
- ✅ **Type Safe**: Full type hints with mypy strict mode
- ✅ **Async/Await**: Modern asynchronous programming with asyncio
- ✅ **Cross-Platform**: Linux, macOS, Windows support
- ✅ **Well Documented**: Comprehensive English docstrings
- ✅ **Test Infrastructure**: pytest-based testing framework

### Planned Features

- ⏳ **28 BRC-100 Methods**: Full WalletInterface implementation
- ⏳ **Database Persistence**: SQLAlchemy-based storage (SQLite/PostgreSQL/MySQL)
- ⏳ **Protocol-Aligned Wallet Flows**: Complete BRC-100 method implementation
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
│  │  • getVersion()                                    │ │
│  │  • getNetwork()                                    │ │
│  │  • createAction()                                  │ │
│  │  • signAction()                                    │ │
│  │  • ... 24 more methods                             │ │
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
4. **Test Driven**: Universal Test Vectors + comprehensive test suite
5. **Cross-Language Compatible**: 100% compatible with TypeScript and Go

## Roadmap

### Phase 0: Preparation ✅ Complete

- [x] Project structure and build system
- [x] Testing framework setup
- [x] Type definitions
- [x] Development documentation

### Phase 1: Foundation (Current)

- [ ] WalletInterface basic methods (4 methods)
- [ ] Storage layer foundation (16 tables)
- [ ] Basic CRUD operations
- [ ] Validation utilities

### Phase 2: Core Features

- [ ] Network information methods
- [ ] List operations
- [ ] Transaction management
- [ ] Services integration

### Phase 3: Advanced Features

- [ ] Cryptographic operations
- [ ] Certificate management
- [ ] Discovery services
- [ ] Storage synchronization

### Phase 4: Production Ready

- [ ] JSON-RPC dispatcher
- [ ] BRC-100 ABI
- [ ] Monitor (background tasks)
- [ ] Performance optimization

See [IMPLEMENTATION_ROADMAP.md](./IMPLEMENTATION_ROADMAP.md) for detailed breakdown.

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
- Review [TypeScript implementation](../ts-wallet-toolbox) for reference
- Check [Go implementation](../go-wallet-toolbox) for reference

## Documentation

### Reference Documentation

- Python SDK: [BSV SDK Documentation](https://github.com/bsv-blockchain/py-sdk)
- BRC-100 Specification: [Wallet Interface Standard](https://github.com/bitcoin-sv/BRCs/blob/master/wallet/0100.md)
- Universal Test Vectors: [Official Test Data](https://github.com/bsv-blockchain/universal-test-vectors)

The repository is richly documented with English docstrings that surface well in editors like VSCode.

## License

The license for the code in this repository is the Open BSV License version 4. Refer to [license.md](./license.md) for the license text.

---

Thank you for being a part of the BSV Blockchain Libraries Project. Let's build the future of BSV Blockchain together! 🚀
