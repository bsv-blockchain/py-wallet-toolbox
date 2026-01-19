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

# Import storage method wrappers from methods package
from .methods import (
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

# Note: Storage methods (process_action, list_actions, etc.) are methods on
# StorageProvider class, not standalone functions. Use StorageProvider instances
# to access these methods.
from .provider import StorageProvider

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
]
