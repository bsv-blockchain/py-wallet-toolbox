"""Wallet Signer implementation (TypeScript parity).

This module implements the signing layer that combines KeyDeriver and WalletStorage
to provide high-level transaction signing operations.

Reference:
    - toolbox/ts-wallet-toolbox/src/signer/WalletSigner.ts
    - toolbox/ts-wallet-toolbox/src/signer/methods/
"""

from .methods import (
    CreateActionResultX,
    PendingSignAction,
    PendingStorageInput,
    acquire_direct_certificate,
    build_signable_transaction,
    complete_signed_transaction,
    create_action,
    internalize_action,
    process_action,
    prove_certificate,
    sign_action,
)

__all__ = [
    "CreateActionResultX",
    "PendingSignAction",
    "PendingStorageInput",
    "acquire_direct_certificate",
    "build_signable_transaction",
    "complete_signed_transaction",
    "create_action",
    "internalize_action",
    "process_action",
    "prove_certificate",
    "sign_action",
]
