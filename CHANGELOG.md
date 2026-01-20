# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [2.0.0] - 2026-01-20

> **Installation:**
> ```bash
> pip install bsv-wallet-toolbox --pre
> ```
> The `--pre` flag is required because this package depends on `bsv-sdk>=2.0.0b1` (beta).

Compatible with TypeScript [wallet-toolbox v2.0.0+](https://github.com/bsv-blockchain/wallet-toolbox/tree/2.0.0)
Cross-SDK interoperability with [TypeScript SDK](https://github.com/bsv-blockchain/ts-sdk) and [Go SDK](https://github.com/bsv-blockchain/go-sdk) (v2.0.0+).

### Added
- Complete test suite implementation (846 tests)
- Manual tests directory with 29 integration tests
- Type safety improvements (dict → dict[str, Any])

### Changed
- Reference format unified across 851 locations (TS/Go compliant)
- Code quality improvements:
  - Resolved all critical lint errors (F821, E501)
  - Fixed type annotations for better mypy compatibility
  - Improved code formatting and line length compliance

### Fixed
- ImportError in conftest.py (added `from __future__ import annotations`)
- Line length violations in wallet.py
- Undefined name errors in error classes

## [0.6.0] - 2025-10-23

### Added
- Test infrastructure complete (Phase 0 finished)
- 4 basic WalletInterface methods: getVersion, getNetwork, isAuthenticated, waitForAuthentication
- Comprehensive test suite with 846 automated tests
- Universal Test Vectors integration (155 tests)
- Manual test framework (29 tests in manual_tests/ directory)
- Code quality checks: ruff, mypy
- Reference format standardization (wallet-toolbox/, go-wallet-toolbox/)

### Technical Details
- Python 3.11+ support
- BRC-100 WalletInterface compliance
- Compatible with TypeScript and Go implementations
- Type hints with mypy strict mode
- pytest framework with asyncio support
- 100% lint critical error resolution

## [0.1.0] - 2025-01-16

### Added
- Initial release
- Level 1 implementation: `getVersion` method
- Basic Wallet class with originator validation
- InvalidParameterError exception class
- Unit tests (5 test cases)
- Universal Test Vectors integration
- Full type hints with mypy support
- GitHub Actions CI/CD setup
- Comprehensive documentation

### Technical Details
- Python 3.11+ support
- BRC-100 WalletInterface compliance
- Compatible with TypeScript and Go implementations
- Universal Test Vectors validation
- 100% test coverage for implemented methods

[Unreleased]: https://github.com/bsv-blockchain/py-wallet-toolbox/compare/v2.0.0...HEAD
[2.0.0]: https://github.com/bsv-blockchain/py-wallet-toolbox/compare/v0.6.0...v2.0.0
[0.6.0]: https://github.com/bsv-blockchain/py-wallet-toolbox/compare/v0.1.0...v0.6.0
[0.1.0]: https://github.com/bsv-blockchain/py-wallet-toolbox/releases/tag/v0.1.0
