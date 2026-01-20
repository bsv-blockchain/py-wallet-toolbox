# BSV BLOCKCHAIN | Wallet Toolbox for Python

[![Build](https://github.com/bsv-blockchain/py-wallet-toolbox/actions/workflows/build.yml/badge.svg?branch=master)](https://github.com/bsv-blockchain/py-wallet-toolbox/actions/workflows/build.yml)
[![PyPI version](https://img.shields.io/pypi/v/bsv-wallet-toolbox)](https://pypi.org/project/bsv-wallet-toolbox)
[![Python versions](https://img.shields.io/pypi/pyversions/bsv-wallet-toolbox)](https://pypi.org/project/bsv-wallet-toolbox)
[![Coverage](https://img.shields.io/badge/coverage-71%25-yellowgreen)](https://github.com/bsv-blockchain/py-wallet-toolbox/actions/workflows/build.yml)

> **🔗 Cross-SDK Interoperability (v2.0.0)**
>
> BRC-100 compliance with cross-SDK interoperability.
> Compatible with [TypeScript SDK](https://github.com/bsv-blockchain/ts-sdk) and [Go SDK](https://github.com/bsv-blockchain/go-sdk) (v2.0.0+).
> Compatible with [wallet-toolbox](https://github.com/bsv-blockchain/wallet-toolbox) v2.0.0+.
>
> **Installation:**
> ```bash
> pip install bsv-wallet-toolbox --pre
> ```
> The `--pre` flag is required because this package depends on `bsv-sdk>=2.0.0b1` (beta).

BRC-100 conforming wallet implementation providing production-ready, persistent storage components. Built on top of the official [Python SDK](https://github.com/bsv-blockchain/py-sdk), this toolbox helps you assemble scalable wallet-backed applications and services.

## Table of Contents

- [Objective](#objective)
- [Current Status](#current-status)
- [Getting Started](#getting-started)
- [Features](#features)
- [Architecture](#architecture)
- [Compatibility](#compatibility)
- [Contribution Guidelines](#contribution-guidelines)
- [Support & Contacts](#support--contacts)
- [License](#license)

## Objective

The BSV Wallet Toolbox builds on the [BSV SDK for Python](https://github.com/bsv-blockchain/py-sdk) and provides:

- **Production-Ready Wallet**: Full BRC-100 WalletInterface implementation with persistent storage
- **Database Persistence**: SQLAlchemy-based storage compatible with SQLite, PostgreSQL, and MySQL
- **Cross-Language Compatibility**: 100% compatible with TypeScript and Go implementations
- **Universal Test Vectors**: Validated against official BRC-100 test data
- **SPV-Friendly Workflows**: Privacy-preserving, scalable wallet operations

## Current Status

**Version**: 2.0.0

| Metric | Status |
|--------|--------|
| Lint Critical Errors | ✅ 0 |
| Test Suite | ✅ 846 tests |
| Manual Tests | ✅ 29 tests |
| Reference Unification | ✅ 851 locations (TS/Go compliant) |

See [CHANGELOG.md](./CHANGELOG.md) for detailed version history.

## Getting Started

### Prerequisites

- Python 3.11 or higher
- pip package manager
- SQLite (included with Python) or PostgreSQL/MySQL (optional)

### Installation

#### From PyPI

```bash
pip install bsv-wallet-toolbox
```

#### From Source

```bash
git clone https://github.com/bsv-blockchain/py-wallet-toolbox.git
cd py-wallet-toolbox

python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# or .venv\Scripts\activate on Windows

pip install -e .[dev]
```

### Quick Start

```python
import asyncio
from bsv_wallet_toolbox import Wallet

async def main():
    wallet = Wallet(chain="main")  # or chain="test" for testnet
    
    result = await wallet.get_version({})
    print(f"Wallet version: {result['version']}")

if __name__ == "__main__":
    asyncio.run(main())
```

### Error Handling

```python
from bsv_wallet_toolbox import Wallet, InvalidParameterError

async def example():
    wallet = Wallet(chain="main")
    
    try:
        result = await wallet.get_version({}, originator="x" * 251)
    except InvalidParameterError as e:
        print(f"Error: {e}")
```

## Features

### Current Features

- ✅ BRC-100 compliant WalletInterface
- ✅ Full type hints with mypy strict mode
- ✅ Async/await with asyncio
- ✅ Cross-platform (Linux, macOS, Windows)
- ✅ pytest-based testing framework

### Planned Features

- ⏳ 28 BRC-100 methods (full WalletInterface)
- ⏳ SQLAlchemy-based storage (SQLite/PostgreSQL/MySQL)
- ⏳ Pluggable service layer (ARC, ChainTracker, Overlay)
- ⏳ Storage synchronization
- ⏳ JSON-RPC server

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Application Layer                     │
└───────────────────────┬─────────────────────────────────┘
                        │
                BRC-100 WalletInterface
                        │
                        ▼
┌─────────────────────────────────────────────────────────┐
│                     Wallet Class                         │
│  ┌────────────────────────────────────────────────────┐ │
│  │  • getVersion()    • createAction()               │ │
│  │  • getNetwork()    • signAction()                 │ │
│  │  • ... 24 more methods                            │ │
│  └────────────────────────────────────────────────────┘ │
│                        │                                 │
│       ┌────────────────┼────────────────┐               │
│       ▼                ▼                ▼               │
│  ┌─────────┐    ┌──────────┐    ┌──────────┐           │
│  │ Storage │    │ Services │    │ Monitor  │           │
│  └─────────┘    └──────────┘    └──────────┘           │
└─────────────────────────────────────────────────────────┘
         │                │               │
         ▼                ▼               ▼
      Database        Blockchain      Background
     (SQLAlchemy)      Services         Tasks
```

### Design Principles

1. **Framework Neutral**: No web framework dependencies
2. **Async First**: All I/O uses async/await
3. **Type Safe**: Complete type hints for IDE support
4. **Test Driven**: Universal Test Vectors + comprehensive tests
5. **Cross-Language Compatible**: 100% compatible with TypeScript and Go

## Compatibility

This Python implementation is 100% compatible with:

| Implementation | Repository | Status |
|----------------|------------|--------|
| TypeScript | [wallet-toolbox](https://github.com/bsv-blockchain/wallet-toolbox) | ✅ API compatible |
| Go | [go-wallet-toolbox](https://github.com/bsv-blockchain/go-wallet-toolbox) | ✅ API compatible |

All three implementations share:
- Same BRC-100 WalletInterface API (28 methods)
- Identical behavior and error handling
- Same database schema
- Universal Test Vectors validation

## Contribution Guidelines

We welcome contributions! See [CONTRIBUTING.md](./CONTRIBUTING.md) for detailed guidelines.

### Quick Start for Contributors

```bash
# Setup
pip install -e .[dev]

# Run tests
pytest tests/ -v

# Quality checks
black src/ tests/
ruff check src/ tests/
mypy src/
```

### Important Notes

- Reference the TypeScript implementation when porting features
- All methods must pass official BRC-100 test vectors
- All code must pass mypy strict mode
- All docstrings and comments must be in English

## Support & Contacts

**Project Owners**: Thomas Giacomo and Darren Kellenschwiler

For questions, bug reports, or feature requests:
- Open an issue on [GitHub](https://github.com/bsv-blockchain/py-wallet-toolbox/issues)

### Documentation

- [BSV SDK Documentation](https://github.com/bsv-blockchain/py-sdk)
- [BRC-100 Specification](https://github.com/bitcoin-sv/BRCs/blob/master/wallet/0100.md)
- [Universal Test Vectors](https://github.com/bsv-blockchain/universal-test-vectors)

## License

The license for the code in this repository is the Open BSV License version 4. See [license.md](./license.md) for details.
