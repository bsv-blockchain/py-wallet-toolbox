"""Universal Test Vector Database Fixtures.

Provides pre-seeded database state matching Universal Test Vector expectations.
Used for tests that require deterministic database contents.

Fixtures include:
- Certificate data for listCertificates tests
- Output data for listOutputs and relinquishOutput tests
- Transaction data supporting the outputs
"""

from datetime import UTC, datetime
from typing import Any


def get_universal_certificates() -> list[dict[str, Any]]:
    """Get certificate fixtures matching Universal Test Vector expectations.

    Returns certificates that should be returned by listCertificates tests.
    """
    now = datetime.now(UTC)

    return [
        {
            "type": "test-type",
            "serialNumber": "test-serial-number",
            "certifier": "0294c479f762f6baa97fbcd4393564c1d7bd8336ebd15928135bbcf575cd1a71a1",
            "subject": "025ad43a22ac38d0bc1f8bacaabb323b5d634703b7a774c4268f6a09e4ddf79097",
            "revocationOutpoint": "aec245f27b7640c8b1865045107731bfb848115c573f7da38166074b1c9e475d.0",
            "signature": "3045022100a6f09ee70382ab364f3f6b040aebb8fe7a51dbc3b4c99cfeb2f7756432162833022067349b91a6319345996faddf36d1b2f3a502e4ae002205f9d2db85474f9aed5a",
            "fields": {"name": "Alice", "email": "alice@example.com"},
            "createdAt": now,
            "updatedAt": now,
        }
    ]


def get_universal_outputs() -> list[dict[str, Any]]:
    """Get output fixtures matching Universal Test Vector expectations.

    Returns outputs that should be returned by listOutputs tests.
    """
    now = datetime.now(UTC)

    return [
        {
            "transactionId": 1,  # Will be set by caller
            "userId": 1,
            "basketId": 1,
            "vout": 0,
            "satoshis": 1000,
            "spendable": True,
            "change": False,
            "providedBy": "test",
            "purpose": "payment",
            "type": "standard",
            "txid": "1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef",
            "lockingScript": bytes([0x76, 0xA9, 0x14] + [0xAA] * 20 + [0x88, 0xAC]),  # P2PKH
            "createdAt": now,
            "updatedAt": now,
        },
        {
            "transactionId": 2,  # Will be set by caller
            "userId": 1,
            "basketId": 1,
            "vout": 0,
            "satoshis": 5000,
            "spendable": True,
            "change": False,
            "providedBy": "test",
            "purpose": "payment",
            "type": "standard",
            "txid": "abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890",
            "lockingScript": bytes([0x76, 0xA9, 0x14] + [0xBB] * 20 + [0x88, 0xAC]),  # P2PKH
            "createdAt": now,
            "updatedAt": now,
        },
    ]


def get_universal_transactions() -> list[dict[str, Any]]:
    """Get transaction fixtures supporting the universal outputs."""
    now = datetime.now(UTC)

    return [
        {
            "userId": 1,
            "txid": "1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef",
            "status": "confirmed",
            "reference": "universal-test-tx-1",
            "isOutgoing": False,
            "satoshis": 1000,
            "description": "Universal test transaction 1",
            "version": 1,
            "lockTime": 0,
            "rawTx": bytes([1, 0, 0, 0, 0, 0, 0, 0, 0, 0] + [0] * 50),  # Minimal valid tx
            "createdAt": now,
            "updatedAt": now,
        },
        {
            "userId": 1,
            "txid": "abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890",
            "status": "confirmed",
            "reference": "universal-test-tx-2",
            "isOutgoing": False,
            "satoshis": 5000,
            "description": "Universal test transaction 2",
            "version": 1,
            "lockTime": 0,
            "rawTx": bytes([1, 0, 0, 0, 0, 0, 0, 0, 0, 0] + [0] * 50),  # Minimal valid tx
            "createdAt": now,
            "updatedAt": now,
        },
    ]


def seed_universal_certificates(storage, user_id: int = 1) -> list[int]:
    """Seed universal test certificates into storage.

    Args:
        storage: StorageProvider instance
        user_id: User ID to associate certificates with

    Returns:
        List of certificate IDs
    """
    certificates = get_universal_certificates()
    cert_ids = []

    for cert_data in certificates:
        # Convert to storage format (exclude fields - they're stored separately)
        storage_cert = {
            "userId": user_id,
            "type": cert_data["type"],
            "serialNumber": cert_data["serialNumber"],
            "certifier": cert_data["certifier"],
            "subject": cert_data["subject"],
            "revocationOutpoint": cert_data["revocationOutpoint"],
            "signature": cert_data["signature"],
            "createdAt": cert_data["createdAt"],
            "updatedAt": cert_data["updatedAt"],
        }

        cert_id = storage.insert_certificate(storage_cert)
        cert_ids.append(cert_id)

    return cert_ids


def seed_universal_outputs(storage) -> list[int]:
    """Seed universal test outputs into storage.

    Args:
        storage: StorageProvider instance

    Returns:
        List of output IDs
    """
    # First seed the supporting transactions
    transactions = get_universal_transactions()
    tx_ids = []

    for tx_data in transactions:
        storage_tx = {
            "userId": tx_data["userId"],
            "txid": tx_data["txid"],
            "status": tx_data["status"],
            "reference": tx_data["reference"],
            "isOutgoing": tx_data["isOutgoing"],
            "satoshis": tx_data["satoshis"],
            "description": tx_data["description"],
            "version": tx_data["version"],
            "lockTime": tx_data["lockTime"],
            "rawTx": tx_data["rawTx"],
            "createdAt": tx_data["createdAt"],
            "updatedAt": tx_data["updatedAt"],
        }

        tx_id = storage.insert_transaction(storage_tx)
        tx_ids.append(tx_id)

    # Then seed the outputs
    outputs = get_universal_outputs()
    output_ids = []

    for i, output_data in enumerate(outputs):
        storage_output = output_data.copy()
        storage_output["transactionId"] = tx_ids[i]

        output_id = storage.insert_output(storage_output)
        output_ids.append(output_id)

    return output_ids
