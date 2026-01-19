"""Transaction test fixtures and utilities.

Provides reusable utilities for seeding transactions in test storage
without SQLAlchemy session conflicts.
"""

from datetime import UTC, datetime
from typing import Any


def create_test_transaction(
    *,
    user_id: int = 1,
    txid: str | None = None,
    reference: str | None = None,
    status: str = "completed",
    is_outgoing: bool = False,
    satoshis: int = 1000,
    description: str = "Test transaction",
    raw_tx: bytes | None = None,
) -> dict[str, Any]:
    """Create a test transaction dict for insertion into storage.

    Args:
        user_id: User ID for the transaction
        txid: Transaction ID (64 hex chars), defaults to 'a' * 64
        reference: Transaction reference, defaults to base64-encoded test value
        status: Transaction status (completed, unsigned, failed, etc.)
        is_outgoing: Whether transaction is outgoing
        satoshis: Transaction amount in satoshis
        description: Transaction description
        raw_tx: Raw transaction bytes, defaults to minimal valid tx

    Returns:
        Dictionary ready for storage.insert_transaction()

    Note: This returns a dict, not a model instance, to avoid session attachment issues.
    """
    if txid is None:
        txid = "a" * 64

    if reference is None:
        reference = "VGVzdFJlZg=="  # Base64 encoded "TestRef"

    if raw_tx is None:
        # Minimal valid transaction bytes
        raw_tx = bytes(
            [
                1,
                0,
                0,
                0,  # version
                0,  # input count
                0,  # output count
                0,
                0,
                0,
                0,  # locktime
            ]
        )

    now = datetime.now(UTC)

    return {
        "userId": user_id,
        "txid": txid,
        "reference": reference,
        "status": status,
        "isOutgoing": is_outgoing,
        "satoshis": satoshis,
        "description": description,
        "version": 1,
        "lockTime": 0,
        "rawTx": raw_tx,
        "createdAt": now,
        "updatedAt": now,
    }


def create_pending_transaction(
    *,
    user_id: int = 1,
    reference: str,
    raw_tx: bytes | None = None,
) -> dict[str, Any]:
    """Create a pending/unsigned transaction for sign_action tests.

    Args:
        user_id: User ID
        reference: Transaction reference (required for sign_action)
        raw_tx: Raw transaction bytes

    Returns:
        Transaction dict with status='unsigned' and isOutgoing=True
    """
    return create_test_transaction(
        user_id=user_id,
        txid="b" * 64,  # Different from default
        reference=reference,
        status="unsigned",
        is_outgoing=True,
        raw_tx=raw_tx,
    )


def create_abortable_transaction(
    *,
    user_id: int = 1,
    reference: str,
) -> dict[str, Any]:
    """Create a transaction that can be aborted.

    Args:
        user_id: User ID
        reference: Transaction reference

    Returns:
        Transaction dict with abortable status
    """
    return create_test_transaction(
        user_id=user_id,
        reference=reference,
        status="unsigned",  # Abortable status
        is_outgoing=True,  # Must be outgoing to abort
    )


def seed_transaction(storage: Any, tx_data: dict[str, Any]) -> int:
    """Seed a transaction into storage safely.

    Args:
        storage: StorageProvider instance
        tx_data: Transaction data dict from create_test_transaction()

    Returns:
        Transaction ID from database

    Note: This uses storage.insert_transaction() which handles sessions properly.
          The returned ID is safe to use; any model instances are detached.
    """
    tx_id = storage.insert_transaction(tx_data)
    # Ensure any internal session state is cleared
    # This helps avoid cross-session conflicts in tests
    return tx_id
