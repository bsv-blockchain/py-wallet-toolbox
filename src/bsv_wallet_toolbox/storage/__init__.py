"""Storage layer implementation (TypeScript parity).

This module provides wallet storage management with support for transaction
lifecycle, certificate handling, and blockchain data persistence.

Reference:
    - toolbox/ts-wallet-toolbox/src/storage/
"""

from .entities import (
    Certificate,
    CertificateField,
    Output,
    OutputBasket,
    OutputTag,
    OutputTagMap,
    Transaction,
    TxLabelMap,
    User,
)
# Note: Storage methods (process_action, list_actions, etc.) are methods on
# StorageProvider class, not standalone functions. Use StorageProvider instances
# to access these methods.
from .provider import StorageProvider
from .wallet_storage_manager import (
    WalletStorageManager,
    EntitySyncState,
    SyncResult,
    AuthId,
    ManagedStorage,
)

__all__ = [
    "Certificate",
    "CertificateField",
    "Output",
    "OutputBasket",
    "OutputTag",
    "OutputTagMap",
    "StorageProvider",
    "Transaction",
    "TxLabelMap",
    "User",
]
