"""Storage methods package.

Re-exports from sub-modules.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

# Note: Most storage methods are implemented as methods on the StorageProvider class.
# Import StorageProvider and use its methods (e.g., storage_provider.process_action()).
# The functions exported here are wrappers that delegate to StorageProvider methods.
from .generate_change import (
    GenerateChangeSdkChangeOutput,
    GenerateChangeSdkFundingInput,
    GenerateChangeSdkInput,
    GenerateChangeSdkOutput,
    GenerateChangeSdkParams,
    GenerateChangeSdkResult,
    InsufficientFundsError,
    InternalError,
    StorageFeeModel,
    generate_change_sdk,
)

# Type definitions for storage method arguments and results
# These are used for type hints and testing


@dataclass
class GenerateFundingInput:
    """Input specification for funding generation."""

    satoshis: int
    locking_script: str


@dataclass
class ListActionsArgs:
    """Arguments for listing wallet actions."""

    limit: int = 10
    offset: int = 0
    labels: list[str] | None = None


@dataclass
class ListOutputsArgs:
    """Arguments for listing wallet outputs."""

    limit: int = 10
    offset: int = 0
    basket: str | None = None


@dataclass
class StorageProcessActionArgs:
    """Arguments for processing a storage action."""

    is_new_tx: bool = True
    is_no_send: bool = False
    is_send_with: bool = False
    is_delayed: bool = False
    send_with: list[str] | None = None
    log: dict[str, Any] | None = None


@dataclass
class StorageProcessActionResults:
    """Results from processing a storage action."""

    send_with_results: dict[str, Any] | None = None
    not_delayed_results: dict[str, Any] | None = None


# Wrapper functions that delegate to StorageProvider methods
# These maintain backward compatibility for code expecting standalone functions


def process_action(
    storage: Any,
    auth: dict[str, Any],
    args: dict[str, Any] | StorageProcessActionArgs,
) -> StorageProcessActionResults:
    """Process a transaction action (finalize & sign).

    Wrapper around StorageProvider.process_action().
    """
    # Convert dataclass to dict if needed
    if isinstance(args, StorageProcessActionArgs):
        args_dict = {
            "isNewTx": args.is_new_tx,
            "isNoSend": args.is_no_send,
            "isSendWith": args.is_send_with,
            "isDelayed": args.is_delayed,
            "sendWith": args.send_with or [],
            "log": args.log,
        }
    else:
        args_dict = args

    result = storage.process_action(auth, args_dict)
    return StorageProcessActionResults(
        send_with_results=result.get("sendWithResults"),
        not_delayed_results=result.get("notDelayedResults"),
    )


def list_actions(storage: Any, auth: dict[str, Any], args: dict[str, Any] | ListActionsArgs) -> dict[str, Any]:
    """List wallet actions.

    Wrapper around StorageProvider.list_actions().
    """
    if isinstance(args, ListActionsArgs):
        args_dict = {
            "limit": args.limit,
            "offset": args.offset,
            "labels": args.labels or [],
        }
    else:
        args_dict = args

    return storage.list_actions(auth, args_dict)


def list_outputs(storage: Any, auth: dict[str, Any], args: dict[str, Any] | ListOutputsArgs) -> dict[str, Any]:
    """List wallet outputs.

    Wrapper around StorageProvider.list_outputs().
    """
    if isinstance(args, ListOutputsArgs):
        args_dict = {
            "limit": args.limit,
            "offset": args.offset,
            "basket": args.basket,
        }
    else:
        args_dict = args

    return storage.list_outputs(auth, args_dict)


def list_certificates(storage: Any, auth: dict[str, Any], args: dict[str, Any]) -> dict[str, Any]:
    """List certificates.

    Wrapper around StorageProvider.list_certificates().
    """
    return storage.list_certificates(auth, args)


def internalize_action(storage: Any, auth: dict[str, Any], args: dict[str, Any]) -> dict[str, Any]:
    """Internalize an action.

    Wrapper around StorageProvider.internalize_action().
    """
    return storage.internalize_action(auth, args)


def get_beef_for_transaction(
    storage: Any,
    txid: str,
    auth: dict[str, Any] | None = None,
    options: dict[str, Any] | None = None,
) -> bytes:
    """Get BEEF for a transaction.

    Uses the new TS/Go parity implementation that supports:
    - Recursive input proof gathering
    - Storage and services fallback
    - knownTxids, trustSelf, minProofLevel options
    - Automatic persistence of newly proven transactions

    Args:
        storage: StorageProvider instance
        txid: Transaction ID (64-hex string)
        auth: Authentication context (optional, for API compatibility)
        options: BEEF generation options dict

    Returns:
        bytes: Complete BEEF binary

    Reference:
        - wallet-toolbox/src/storage/methods/getBeefForTransaction.ts
        - go-wallet-toolbox/pkg/storage/internal/actions/get_beef.go
    """
    from bsv_wallet_toolbox.storage.methods_impl import get_beef_for_transaction as _impl

    return _impl(storage, auth or {}, txid, options)


def attempt_to_post_reqs_to_network(storage: Any, reqs: list[dict[str, Any]]) -> dict[str, Any]:
    """Attempt to post requests to network.

    Wrapper around StorageProvider.attempt_to_post_reqs_to_network().
    """
    return storage.attempt_to_post_reqs_to_network(reqs)


def review_status(storage: Any, args: dict[str, Any]) -> dict[str, Any]:
    """Review transaction statuses.

    Wrapper around StorageProvider.review_status().
    """
    result = storage.review_status(args)
    return result or {}


def purge_data(storage: Any, params: dict[str, Any]) -> dict[str, Any]:
    """Purge transient data.

    Wrapper around StorageProvider.purge_data().
    """
    result = storage.purge_data(params)
    return result or {}


def get_sync_chunk(storage: Any, args: dict[str, Any]) -> dict[str, Any]:
    """Get synchronization chunk.

    Wrapper around StorageProvider.get_sync_chunk().
    """
    return storage.get_sync_chunk(args)


def generate_change(storage: Any, params: dict[str, Any]) -> dict[str, Any]:
    """Generate change for a transaction.

    Note: This is a placeholder. Actual change generation uses generate_change_sdk().
    """
    raise NotImplementedError("Use generate_change_sdk() from generate_change module instead")


__all__ = [  # noqa: RUF022
    # Types from generate_change
    "GenerateChangeSdkInput",
    "GenerateChangeSdkOutput",
    "GenerateChangeSdkFundingInput",
    "GenerateChangeSdkChangeOutput",
    "GenerateChangeSdkParams",
    "GenerateChangeSdkResult",
    "StorageFeeModel",
    "generate_change_sdk",
    "InsufficientFundsError",
    "InternalError",
    # Type definitions
    "GenerateFundingInput",
    "ListActionsArgs",
    "ListOutputsArgs",
    "StorageProcessActionArgs",
    "StorageProcessActionResults",
    # Wrapper functions
    "process_action",
    "list_actions",
    "list_outputs",
    "list_certificates",
    "internalize_action",
    "get_beef_for_transaction",
    "attempt_to_post_reqs_to_network",
    "review_status",
    "purge_data",
    "get_sync_chunk",
    "generate_change",
]
