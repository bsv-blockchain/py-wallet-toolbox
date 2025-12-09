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
from .methods import (
    GenerateChangeInput,
    ListActionsArgs,
    ListOutputsArgs,
    StorageProcessActionArgs,
    StorageProcessActionResults,
    attempt_to_post_reqs_to_network,
    generate_change,
    get_beef_for_transaction,
    get_sync_chunk,
    internalize_action,
    list_actions,
    list_certificates,
    list_outputs,
    process_action,
    purge_data,
    review_status,
)
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
    "GenerateChangeInput",
    "ListActionsArgs",
    "ListOutputsArgs",
    "Output",
    "OutputBasket",
    "OutputTag",
    "OutputTagMap",
    "StorageProcessActionArgs",
    "StorageProcessActionResults",
    "StorageProvider",
    "Transaction",
    "TxLabelMap",
    "User",
    "attempt_to_post_reqs_to_network",
    "generate_change",
    "get_beef_for_transaction",
    "get_sync_chunk",
    "internalize_action",
    "list_actions",
    "list_certificates",
    "list_outputs",
    "process_action",
    "purge_data",
    "review_status",
    # WalletStorageManager
    "WalletStorageManager",
    "EntitySyncState",
    "SyncResult",
    "AuthId",
    "ManagedStorage",
]
