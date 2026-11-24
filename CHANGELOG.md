# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Arcade broadcaster provider (opt-in via `arcadeUrl`): `Services.post_beef` tries Arcade first (EF submission) and falls through to ARC / Bitails on service errors; `get_merkle_path` verifies Arcade's BUMP against the block header
- `TaskArcadeSSE` monitor task and `ArcadeSSEClient` for real-time transaction status updates via Arcade SSE (see `docs/ARCADE.md`)

### Changed
- `find_*` / `count_*` take the TS `Find*Args` shape (`partial` plus `since`, `paged`, `orderDescending` and the per-table extras such as `status`, `txids`, `txStatus`, `noRawTx`) and raise `InvalidParameterError` for unknown keys or columns instead of silently dropping them
- `update_transaction_status` / `update_transactions_status` follow TS: a completed (or proven) transaction can't change status, a failed one can't be un-failed, statuses TS doesn't define are rejected, and 'failed' also makes the transaction's own outputs unspendable; a transaction can also be addressed by `user_id` and `reference`
- Bumped minimum bsv-sdk dependency from 2.1.3 to 2.5.0 (2.5.0 fixes the native transaction parser crash in GHSA-49jm-v8w3-4j8c, which affects 2.3.2 through 2.4.0)
- `update_transactions_status(ids, "failed")` releases the outputs the failed transactions had allocated (TS parity)

### Fixed
- `Services.post_beef` stopped at the first ARC that answered 429 instead of trying the next provider, sent ARC only the raw transaction (so a transaction with an unconfirmed parent failed), treated every ARC HTTP error as a service error and a 200 with `txStatus` `REJECTED` as a success. As in TS, any failure but a double spend now moves on to the next provider, ARC gets the BEEF as V1 (or the transaction as EF when the BEEF has txid-only entries), only 408/429/476/5xx and rate-limit/timeout details are service errors, `INVALID`/`MALFORMED`/`REJECTED` refuse the transaction, and `MINED`/`IMMUTABLE` and the other accepted statuses count as accepted in `ARC.post_beef`. The result says whether only services failed (`serviceError`), and the send path retries such failures instead of failing the transaction on a phrase in the message
- The `Wallet` keeps a `BeefParty` (TS parity) instead of a plain `Beef`: `createAction`'s tx and `listOutputs`' BEEF are merged from the storage party, `listOutputs` sends `getKnownTxids()` when `autoKnownTxids` is set and fills txid-only entries back in before returning the BEEF. `get_beef_for_transaction` dropped a txid listed in `knownTxids` instead of adding it to `mergeToBeef` as txid-only, so such a transaction was missing from merged BEEFs
- `listOutputs` ignored BRC-100 `include` (`'locking scripts'` / `'entire transactions'`), and its `BEEF` was raw transactions and BEEF fragments concatenated byte by byte, which no SDK can parse. `include` now sets the storage flags, and the BEEF is one Beef holding every listed output's transaction, built from storage (TS `listOutputsKnex`); `get_valid_beef_for_txid` returns a real BEEF too. Listing with `include: 'locking scripts'` also failed with `TypeError` (`validate_output_script` was called with the wrong keyword)
- Transactions created with `acceptDelayedBroadcast` (the default) were never broadcast: `TaskSendWaiting` called `post_beef(raw_tx, [txid])`, which fails against `Services.post_beef(beef)`, and the ProvenTxReq had no `notify.transactionIds`. An immediate send of a transaction with an inputBEEF always failed with "no raw transaction available". `TaskSendWaiting` and the immediate send now share `StorageProvider.attempt_to_post_reqs_to_network`, which posts an AtomicBEEF of the transaction (TS parity). A delayed transaction is 'sending' instead of 'unprocessed' until it is sent, so `TaskFailAbandoned` no longer fails it, and a service error leaves the transaction and its req 'sending' for the next attempt. A req with no `notify.transactionIds` (written before this fix) or whose transaction is already 'failed' is marked 'invalid' instead of being broadcast (TS parity)
- `Monitor` raised `AttributeError` when calling the broadcast and proven hooks unless they were assigned on the instance; hooks passed in `MonitorOptions` now work
- `TaskFailAbandoned` set every transaction older than five minutes to 'failed', completed ones included: its `txStatus` filter was silently dropped. `TaskSendWaiting`'s `status` filter was dropped the same way. `review_status` now restores inputs and neutralises outputs of a failed transaction only when its ProvenTxReq is terminal (TS), and `create_action` marks its transaction failed when construction throws, releasing the allocated change
- `createAction` and `signAction` returned `tx` as a raw transaction; it is now AtomicBEEF (BEEF V2), as BRC-100 and TS specify, so TS `internalizeAction`, payment middleware and 402 payments can read it. `returnTXIDOnly` is read with its BRC-100 spelling (it was read as `returnTxidOnly` and ignored), and a signable transaction is built with the caller's `inputBEEF` (it was read as `inputBeef`)
- `signAction` did not store or send the signed transaction and left its inputs locked: the merged sign args lacked `isNewTx` and the other flags, so storage returned early. `validate_sign_action_args` now returns the defaulted options and flags (TS `validateSignActionArgs`), and unset signAction options are taken from the createAction options (TS `mergePriorOptions`)
- `createAction` with caller-supplied `inputs` always failed: storage called `.get` on its normalized args (`AttributeError`), `'txid.vout'` outpoints were rejected, and the signer looked up the input's source transaction with a `Beef` method that does not exist. Inputs are now validated and normalized as TS `validateCreateActionInput` does (outpoint string or `{txid, vout}`, `unlockingScript` and/or `unlockingScriptLength`, `inputDescription` of 5-2000 bytes, `sequenceNumber` defaulting to 0xffffffff)
- `Wallet.verify_returned_txid_only_atomic_beef` ignored `tx` given as `list[int]` (the form wallet results use) and raised while filling in txid-only transactions, so they were never filled in
- `purge_data` with `purgeSpent` kept only the txids of unspent outputs, so a spent parent still needed to build a UTXO's BEEF (and its ProvenTx) could be deleted, leaving the UTXO without a valid BEEF. Every txid in each UTXO's BEEF built from local storage is now kept, including proofs stored without a transaction row, and the set is built after `purgeFailed` has released outputs (TS parity). If a UTXO's BEEF needs an ancestor that is not in storage, nothing is purged as spent
- `get_beef_for_transaction` accepts `chainTracker` and `skipInvalidProofs` (TS parity): with a chain tracker, a stored proof whose merkle root the tracker does not know raises, or with `skipInvalidProofs` is ignored and the inputs are followed instead
- Monitor never stored merkle proofs: `TaskNewHeader` now polls the chain tip and calls `Monitor.process_new_block_header` (TS parity), and `TaskCheckForProofs` calls the synchronous `Services.get_merkle_path_for_transaction` directly instead of through `asyncio.run`
- `TaskCheckForProofs` validates dict-form merkle paths against the block header and stores the real BUMP and tx index instead of placeholder bytes and index 0
- WhatsOnChain `current_height` read the chain height from the wrong level of the response and always returned 0; `Services.find_chain_tip_header`, `find_header_for_block_hash` and `find_chain_tip_hash` failed with `AttributeError` on the header dict WhatsOnChain returns

### Removed
- `utils.atomic_beef_utils.build_internalize_atomic_beef`, `build_atomic_beef_from_tx_with_proven_inputs` and `AtomicBeefBuildResult`: `internalizeAction` no longer rebuilds the sender's BEEF from WhatsOnChain

### Security
- `internalizeAction` (signer and storage) and `createAction` `inputBEEF` (storage) now SPV-verify the caller's BEEF with `Beef.verify` against the services' chain tracker (TS parity) and reject it with `InvalidParameterError` otherwise; a forged BUMP or unknown merkle root was previously accepted and could be recorded as `completed`. Storage without services fails closed. Verifying BEEF V1 needs bsv-sdk 2.5.0: earlier releases drop V1 parents and BUMPs while parsing, so the check passes without consulting the chain tracker

## [2.0.2] - 2026-05-20

### Added
- Python 3.13 support
- Dependabot configuration for automated dependency updates

### Changed
- Bumped minimum bsv-sdk dependency from 2.0.0b1 to 2.1.3 (Python 3.13 compatibility fix)

## [2.0.1] - 2026-01-20

### Fixed
- Black formatting issues in chaintracks_storage.py and wallet_permissions_manager.py

## [2.0.0] - 2026-01-20

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

[Unreleased]: https://github.com/bsv-blockchain/py-wallet-toolbox/compare/v2.0.2...HEAD
[2.0.2]: https://github.com/bsv-blockchain/py-wallet-toolbox/compare/v2.0.1...v2.0.2
[2.0.1]: https://github.com/bsv-blockchain/py-wallet-toolbox/compare/v2.0.0...v2.0.1
[2.0.0]: https://github.com/bsv-blockchain/py-wallet-toolbox/compare/v0.6.0...v2.0.0
[0.6.0]: https://github.com/bsv-blockchain/py-wallet-toolbox/compare/v0.1.0...v0.6.0
[0.1.0]: https://github.com/bsv-blockchain/py-wallet-toolbox/releases/tag/v0.1.0
