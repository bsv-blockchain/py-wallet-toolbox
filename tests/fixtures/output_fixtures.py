"""Output test fixtures and utilities.

Provides reusable utilities for seeding outputs in test storage.
"""

from datetime import UTC, datetime
from typing import Any


def create_test_output(
    *,
    transaction_id: int,
    user_id: int = 1,
    basket_id: int = 1,
    vout: int = 0,
    satoshis: int = 1000,
    spendable: bool = True,
    txid: str | None = None,
    locking_script: bytes | None = None,
    change: bool = False,
    provided_by: str = "test",
    purpose: str = "payment",
    output_type: str = "standard",
) -> dict[str, Any]:
    """Create a test output dict for insertion into storage.

    Args:
        transaction_id: Database transaction ID
        user_id: User ID
        basket_id: Output basket ID
        vout: Output index in transaction
        satoshis: Output amount in satoshis
        spendable: Whether output is spendable
        txid: Transaction ID (hex), defaults to 'c' * 64
        locking_script: Locking script bytes, defaults to P2PKH
        change: Whether output is change
        provided_by: Provider identifier
        purpose: Output purpose
        output_type: Output type

    Returns:
        Dictionary ready for storage.insert_output()
    """
    if txid is None:
        txid = "c" * 64

    if locking_script is None:
        # Default to a simple P2PKH script
        locking_script = bytes(
            [
                0x76,  # OP_DUP
                0xA9,  # OP_HASH160
                0x14,  # Push 20 bytes
            ]
            + [0xAA] * 20
            + [  # 20-byte pubkey hash
                0x88,  # OP_EQUALVERIFY
                0xAC,  # OP_CHECKSIG
            ]
        )

    now = datetime.now(UTC)

    return {
        "transactionId": transaction_id,
        "userId": user_id,
        "basketId": basket_id,
        "spendable": spendable,
        "change": change,
        "vout": vout,
        "satoshis": satoshis,
        "providedBy": provided_by,
        "purpose": purpose,
        "type": output_type,
        "txid": txid,
        "lockingScript": locking_script,
        "createdAt": now,
        "updatedAt": now,
    }


def create_spendable_utxo(
    *,
    transaction_id: int,
    user_id: int = 1,
    basket_id: int = 1,
    satoshis: int = 2000,
    vout: int = 0,
) -> dict[str, Any]:
    """Create a spendable UTXO for testing transaction creation.

    Args:
        transaction_id: Database transaction ID
        user_id: User ID
        basket_id: Basket ID
        satoshis: Amount (should be enough to cover test outputs)
        vout: Output index

    Returns:
        Output dict with spendable=True
    """
    return create_test_output(
        transaction_id=transaction_id,
        user_id=user_id,
        basket_id=basket_id,
        vout=vout,
        satoshis=satoshis,
        spendable=True,
        change=False,
    )


def create_relinquishable_output(
    *,
    transaction_id: int,
    user_id: int = 1,
    basket_id: int = 1,
    satoshis: int = 1000,
    vout: int = 0,
) -> dict[str, Any]:
    """Create an output that can be relinquished.

    Args:
        transaction_id: Database transaction ID
        user_id: User ID
        basket_id: Basket ID
        satoshis: Amount
        vout: Output index

    Returns:
        Output dict suitable for relinquish tests
    """
    return create_test_output(
        transaction_id=transaction_id,
        user_id=user_id,
        basket_id=basket_id,
        vout=vout,
        satoshis=satoshis,
        spendable=True,
    )


def seed_output(storage: Any, output_data: dict[str, Any]) -> int:
    """Seed an output into storage safely.

    Args:
        storage: StorageProvider instance
        output_data: Output data dict from create_test_output()

    Returns:
        Output ID from database
    """
    return storage.insert_output(output_data)


def seed_utxo_for_spending(
    storage: Any,
    user_id: int = 1,
    basket_id: int = 1,
    satoshis: int = 2000,
) -> tuple[int, int]:
    """Seed a complete transaction with spendable UTXO.

    Creates both the transaction and output in one call.

    Args:
        storage: StorageProvider instance
        user_id: User ID
        basket_id: Basket ID
        satoshis: UTXO amount

    Returns:
        Tuple of (transaction_id, output_id)
    """
    from .transaction_fixtures import create_test_transaction, seed_transaction

    # Create source transaction
    tx_data = create_test_transaction(
        user_id=user_id,
        txid="d" * 64,
        is_outgoing=False,
        satoshis=satoshis,
        description="UTXO source transaction",
    )
    tx_id = seed_transaction(storage, tx_data)

    # Create spendable output
    output_data = create_spendable_utxo(
        transaction_id=tx_id,
        user_id=user_id,
        basket_id=basket_id,
        satoshis=satoshis,
    )
    output_id = seed_output(storage, output_data)

    return tx_id, output_id
