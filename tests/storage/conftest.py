from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

import pytest

from bsv_wallet_toolbox.storage.db import create_engine_from_url
from bsv_wallet_toolbox.storage.models import Base
from bsv_wallet_toolbox.storage.provider import StorageProvider


def _ts(base: datetime, minutes: int) -> datetime:
    return base + timedelta(minutes=minutes)


def _record_by_id(storage: StorageProvider, finder: str, identifier_key: str, identifier_value: Any) -> dict[str, Any]:
    finder_method = getattr(storage, finder)
    results = finder_method({"partial": {identifier_key: identifier_value}})
    if not results:
        raise AssertionError(f"No record found for {finder}.{identifier_key}={identifier_value}")
    return results[0]


def seed_storage(storage: StorageProvider) -> dict[str, Any]:
    base_time = datetime(2024, 1, 1, 12, 0, 0)

    # Users
    user1_id = storage.insert_user(
        {
            "identityKey": "03" + "a" * 62,
            "activeStorage": "local-primary",
            "createdAt": _ts(base_time, 0),
            "updatedAt": _ts(base_time, 0),
        }
    )
    user2_id = storage.insert_user(
        {
            "identityKey": "03" + "b" * 62,
            "activeStorage": "local-secondary",
            "createdAt": _ts(base_time, 1),
            "updatedAt": _ts(base_time, 1),
        }
    )

    user1 = _record_by_id(storage, "find_users", "userId", user1_id)
    user2 = _record_by_id(storage, "find_users", "userId", user2_id)

    # Output baskets (user1)
    basket_ids = []
    for idx, name in enumerate(["default", "savings", "spending"]):
        basket_ids.append(
            storage.insert_output_basket(
                {
                    "userId": user1_id,
                    "name": name,
                    "numberOfDesiredUTXOs": 5 + idx,
                    "minimumDesiredUTXOValue": 1_000 + idx,
                    "isDeleted": False,
                    "createdAt": _ts(base_time, 10 + idx),
                    "updatedAt": _ts(base_time, 10 + idx),
                }
            )
        )
    baskets = [_record_by_id(storage, "find_output_baskets", "basketId", basket_id) for basket_id in basket_ids]

    # Transactions
    tx1_id = storage.insert_transaction(
        {
            "userId": user1_id,
            "status": "sending",
            "reference": "ref-u1-1",
            "isOutgoing": True,
            "satoshis": 10_000,
            "description": "User1 primary transaction",
            "version": 1,
            "lockTime": 0,
            "inputBEEF": b"\x01\x02",
            "rawTx": b"\x03\x04",
            "createdAt": _ts(base_time, 20),
            "updatedAt": _ts(base_time, 20),
        }
    )
    tx2_id = storage.insert_transaction(
        {
            "userId": user1_id,
            "status": "confirmed",
            "reference": "ref-u1-2",
            "isOutgoing": False,
            "satoshis": 5_000,
            "description": "User1 secondary transaction",
            "version": 1,
            "lockTime": 0,
            "inputBEEF": b"\x05\x06",
            "rawTx": b"\x07\x08",
            "createdAt": _ts(base_time, 21),
            "updatedAt": _ts(base_time, 21),
        }
    )
    tx3_id = storage.insert_transaction(
        {
            "userId": user2_id,
            "status": "pending",
            "reference": "ref-u2-1",
            "isOutgoing": False,
            "satoshis": 7_500,
            "description": "User2 transaction",
            "version": 2,
            "lockTime": 0,
            "inputBEEF": b"\x09\x0a",
            "rawTx": b"\x0b\x0c",
            "createdAt": _ts(base_time, 22),
            "updatedAt": _ts(base_time, 22),
        }
    )

    # Create additional transaction for user1 with completed status to support larger test amounts
    tx4_id = storage.insert_transaction(
        {
            "userId": user1_id,
            "status": "completed",  # Must be completed/unproven/sending for allocate_funding_input
            "reference": "ref-u1-4",
            "isOutgoing": False,
            "satoshis": 150_000,
            "description": "User1 large transaction for testing",
            "version": 1,
            "lockTime": 0,
            "inputBEEF": b"\x0f\x10",
            "rawTx": b"\x11\x12",
            "createdAt": _ts(base_time, 23),
            "updatedAt": _ts(base_time, 23),
        }
    )

    transactions = {
        "tx1": _record_by_id(storage, "find_transactions", "transactionId", tx1_id),
        "tx2": _record_by_id(storage, "find_transactions", "transactionId", tx2_id),
        "tx3": _record_by_id(storage, "find_transactions", "transactionId", tx3_id),
        "tx4": _record_by_id(storage, "find_transactions", "transactionId", tx4_id),
    }

    # Commissions
    commissions: dict[str, dict[str, Any]] = {}
    for key, tx_id, user_id, sat in (
        ("tx1", tx1_id, user1_id, 900),
        ("tx2", tx2_id, user1_id, 400),
        ("tx3", tx3_id, user2_id, 600),
    ):
        commission_id = storage.insert_commission(
            {
                "transactionId": tx_id,
                "userId": user_id,
                "satoshis": sat,
                "keyOffset": f"offset-{key}",
                "isRedeemed": False,
                "lockingScript": b"\x0d\x0e",
                "createdAt": _ts(base_time, 30),
                "updatedAt": _ts(base_time, 30),
            }
        )
        commissions[key] = _record_by_id(storage, "find_commissions", "commissionId", commission_id)

    # Outputs
    output1_id = storage.insert_output(
        {
            "transactionId": tx1_id,
            "userId": user1_id,
            "basketId": basket_ids[0],
            "spendable": True,
            "change": False,
            "vout": 0,
            "satoshis": 101,
            "providedBy": "storage",
            "purpose": "payment",
            "type": "standard",
            "txid": "a" * 64,
            "lockingScript": b"\x10\x11",
            "createdAt": _ts(base_time, 40),
            "updatedAt": _ts(base_time, 40),
        }
    )
    output2_id = storage.insert_output(
        {
            "transactionId": tx1_id,
            "userId": user1_id,
            "basketId": basket_ids[1],
            "spendable": True,
            "change": True,
            "vout": 1,
            "satoshis": 202,
            "providedBy": "storage",
            "purpose": "change",
            "type": "change",
            "txid": "b" * 64,
            "lockingScript": b"\x12\x13",
            "createdAt": _ts(base_time, 41),
            "updatedAt": _ts(base_time, 41),
        }
    )
    output3_id = storage.insert_output(
        {
            "transactionId": tx3_id,
            "userId": user2_id,
            "basketId": None,
            "spendable": False,
            "change": False,
            "vout": 0,
            "satoshis": 303,
            "providedBy": "user",
            "purpose": "inbound",
            "type": "incoming",
            "txid": "c" * 64,
            "lockingScript": b"\x14\x15",
            "createdAt": _ts(base_time, 42),
            "updatedAt": _ts(base_time, 42),
        }
    )
    # Add additional outputs for user1 to support tests requiring larger amounts
    # Use tx4 which has "completed" status (required for allocate_funding_input)
    # Both outputs must be in basket_ids[0] which is the "default" basket used by create_action
    # Note: allocate_funding_input requires change=True and type="P2PKH" for outputs to be allocatable
    output4_id = storage.insert_output(
        {
            "transactionId": tx4_id,
            "userId": user1_id,
            "basketId": basket_ids[0],  # "default" basket - required for allocate_funding_input
            "spendable": True,
            "change": True,  # Must be True for allocate_funding_input
            "vout": 0,
            "satoshis": 150_000,  # More than enough for test_create_action_known_txids_return_txid_only (90005 needed) + fees + change
            "providedBy": "storage",
            "purpose": "change",  # Changed from "payment" to match change=True
            "type": "P2PKH",  # Must be "P2PKH" for allocate_funding_input
            "txid": "d" * 64,
            "lockingScript": b"\x20\x21",
            "spentBy": None,  # Explicitly set to None to ensure it's allocatable
            "createdAt": _ts(base_time, 43),
            "updatedAt": _ts(base_time, 43),
        }
    )
    output5_id = storage.insert_output(
        {
            "transactionId": tx4_id,
            "userId": user1_id,
            "basketId": basket_ids[0],  # "default" basket - required for allocate_funding_input
            "spendable": True,
            "change": True,  # Must be True for allocate_funding_input
            "vout": 1,
            "satoshis": 2_000,  # Enough for test_create_action_output_tags_persisted (1205 needed)
            "providedBy": "storage",
            "purpose": "change",  # Changed from "payment" to match change=True
            "type": "P2PKH",  # Must be "P2PKH" for allocate_funding_input
            "txid": "e" * 64,
            "lockingScript": b"\x22\x23",
            "spentBy": None,  # Explicitly set to None to ensure it's allocatable
            "createdAt": _ts(base_time, 44),
            "updatedAt": _ts(base_time, 44),
        }
    )

    outputs = {
        "o1": _record_by_id(storage, "find_outputs", "outputId", output1_id),
        "o2": _record_by_id(storage, "find_outputs", "outputId", output2_id),
        "o3": _record_by_id(storage, "find_outputs", "outputId", output3_id),
        "o4": _record_by_id(storage, "find_outputs", "outputId", output4_id),
        "o5": _record_by_id(storage, "find_outputs", "outputId", output5_id),
    }

    # Output tags
    tag1_id = storage.insert_output_tag(
        {
            "userId": user1_id,
            "tag": "primary",
            "isDeleted": False,
            "createdAt": _ts(base_time, 50),
            "updatedAt": _ts(base_time, 50),
        }
    )
    tag2_id = storage.insert_output_tag(
        {
            "userId": user1_id,
            "tag": "secondary",
            "isDeleted": False,
            "createdAt": _ts(base_time, 51),
            "updatedAt": _ts(base_time, 51),
        }
    )
    tags = {
        "tag1": _record_by_id(storage, "find_output_tags", "outputTagId", tag1_id),
        "tag2": _record_by_id(storage, "find_output_tags", "outputTagId", tag2_id),
    }

    # Output tag map
    for output_id, tag_id in ((output1_id, tag1_id), (output1_id, tag2_id), (output2_id, tag1_id)):
        storage.insert_output_tag_map(
            {
                "outputId": output_id,
                "outputTagId": tag_id,
                "isDeleted": False,
                "createdAt": _ts(base_time, 52),
                "updatedAt": _ts(base_time, 52),
            }
        )

    tag_maps = storage.find_output_tag_maps({"partial": {}})

    # Tx labels and maps
    label1_id = storage.insert_tx_label(
        {
            "userId": user1_id,
            "label": "groceries",
            "isDeleted": False,
            "createdAt": _ts(base_time, 60),
            "updatedAt": _ts(base_time, 60),
        }
    )
    label2_id = storage.insert_tx_label(
        {
            "userId": user1_id,
            "label": "rent",
            "isDeleted": False,
            "createdAt": _ts(base_time, 61),
            "updatedAt": _ts(base_time, 61),
        }
    )
    label3_id = storage.insert_tx_label(
        {
            "userId": user2_id,
            "label": "salary",
            "isDeleted": False,
            "createdAt": _ts(base_time, 62),
            "updatedAt": _ts(base_time, 62),
        }
    )

    labels = {
        "label1": _record_by_id(storage, "find_tx_labels", "txLabelId", label1_id),
        "label2": _record_by_id(storage, "find_tx_labels", "txLabelId", label2_id),
        "label3": _record_by_id(storage, "find_tx_labels", "txLabelId", label3_id),
    }

    for tx_id, label_id in ((tx1_id, label1_id), (tx1_id, label2_id), (tx3_id, label3_id)):
        storage.insert_tx_label_map(
            {
                "transactionId": tx_id,
                "txLabelId": label_id,
                "isDeleted": False,
                "createdAt": _ts(base_time, 63),
                "updatedAt": _ts(base_time, 63),
            }
        )

    tx_label_maps = storage.find_tx_label_maps({"partial": {}})

    # Certificates and fields
    cert_primary_id = storage.insert_certificate(
        {
            "userId": user1_id,
            "type": "identity",
            "serialNumber": "SN-001",
            "certifier": "Cert-A",
            "subject": "Alice",
            "verifier": "Verifier-A",
            "revocationOutpoint": "rev-1",
            "signature": "sig-a",
            "isDeleted": False,
            "createdAt": _ts(base_time, 70),
            "updatedAt": _ts(base_time, 70),
        }
    )
    cert_secondary_id = storage.insert_certificate(
        {
            "userId": user1_id,
            "type": "employment",
            "serialNumber": "SN-002",
            "certifier": "Cert-B",
            "subject": "Alice",
            "verifier": "Verifier-B",
            "revocationOutpoint": "rev-2",
            "signature": "sig-b",
            "isDeleted": False,
            "createdAt": _ts(base_time, 71),
            "updatedAt": _ts(base_time, 71),
        }
    )
    cert_tertiary_id = storage.insert_certificate(
        {
            "userId": user1_id,
            "type": "compliance",
            "serialNumber": "SN-003",
            "certifier": "Cert-C",
            "subject": "Alice",
            "verifier": "Verifier-C",
            "revocationOutpoint": "rev-3",
            "signature": "sig-c",
            "isDeleted": False,
            "createdAt": _ts(base_time, 72),
            "updatedAt": _ts(base_time, 72),
        }
    )

    certificates = {
        "primary": _record_by_id(storage, "find_certificates", "certificateId", cert_primary_id),
        "secondary": _record_by_id(storage, "find_certificates", "certificateId", cert_secondary_id),
        "tertiary": _record_by_id(storage, "find_certificates", "certificateId", cert_tertiary_id),
    }

    storage.insert_certificate_field(
        {
            "certificateId": cert_primary_id,
            "userId": user1_id,
            "fieldName": "bob",
            "fieldValue": "your uncle",
            "masterKey": "mk-bob",
            "createdAt": _ts(base_time, 73),
            "updatedAt": _ts(base_time, 73),
        }
    )
    storage.insert_certificate_field(
        {
            "certificateId": cert_primary_id,
            "userId": user1_id,
            "fieldName": "name",
            "fieldValue": "alice",
            "masterKey": "mk-name",
            "createdAt": _ts(base_time, 74),
            "updatedAt": _ts(base_time, 74),
        }
    )
    storage.insert_certificate_field(
        {
            "certificateId": cert_secondary_id,
            "userId": user1_id,
            "fieldName": "name",
            "fieldValue": "alice",
            "masterKey": "mk-name-2",
            "createdAt": _ts(base_time, 75),
            "updatedAt": _ts(base_time, 75),
        }
    )

    certificate_fields = {
        "primaryBob": storage.find_certificate_fields(
            {"partial": {"certificateId": cert_primary_id, "fieldName": "bob"}}
        )[0],
        "primaryName": storage.find_certificate_fields(
            {"partial": {"certificateId": cert_primary_id, "fieldName": "name"}}
        )[0],
        "secondaryName": storage.find_certificate_fields(
            {"partial": {"certificateId": cert_secondary_id, "fieldName": "name"}}
        )[0],
    }

    # Sync state
    sync_state_id = storage.insert_sync_state(
        {
            "userId": user1_id,
            "storageIdentityKey": storage.storage_identity_key,
            "storageName": "default",
            "status": "complete",
            "init": True,
            "refNum": "sync-ref",
            "syncMap": "{}",
            "when": "2024-01-01T12:00:00Z",
            "satoshis": 12_345,
            "errorLocal": None,
            "errorOther": None,
            "createdAt": _ts(base_time, 80),
            "updatedAt": _ts(base_time, 80),
        }
    )
    sync_state = _record_by_id(storage, "find_sync_states", "syncStateId", sync_state_id)

    # Monitor event
    monitor_event_id = storage.insert_monitor_event(
        {
            "event": "send_waiting",
            "details": "initial sweep",
            "createdAt": _ts(base_time, 90),
            "updatedAt": _ts(base_time, 90),
        }
    )
    monitor_event = _record_by_id(storage, "find_monitor_events", "id", monitor_event_id)

    # Proven transactions
    proven_tx_id = storage.insert_proven_tx(
        {
            "txid": "p" * 64,
            "height": 120,
            "index": 0,
            "merklePath": b"\x16\x17",
            "rawTx": b"\x18\x19",
            "blockHash": "d" * 64,
            "merkleRoot": "e" * 64,
            "createdAt": _ts(base_time, 100),
            "updatedAt": _ts(base_time, 100),
        }
    )
    proven_tx = _record_by_id(storage, "find_proven_txs", "provenTxId", proven_tx_id)

    req_pending_id = storage.insert_proven_tx_req(
        {
            "txid": "r" * 64,
            "status": "pending",
            "attempts": 0,
            "notified": False,
            "history": "{}",
            "notify": "{}",
            "rawTx": b"\x1a",
            "inputBEEF": b"\x1b",
            "createdAt": _ts(base_time, 101),
            "updatedAt": _ts(base_time, 101),
        }
    )
    req_completed_id = storage.insert_proven_tx_req(
        {
            "txid": "s" * 64,
            "status": "completed",
            "attempts": 3,
            "notified": True,
            "provenTxId": proven_tx_id,
            "batch": "batch-001",
            "history": '{"validated": true}',
            "notify": '{"email": "test@example.com"}',
            "rawTx": b"\x1c",
            "inputBEEF": b"\x1d",
            "createdAt": _ts(base_time, 102),
            "updatedAt": _ts(base_time, 102),
        }
    )

    proven_tx_reqs = {
        "pending": _record_by_id(storage, "find_proven_tx_reqs", "provenTxReqId", req_pending_id),
        "completed": _record_by_id(storage, "find_proven_tx_reqs", "provenTxReqId", req_completed_id),
    }

    return {
        "user1": user1,
        "user2": user2,
        "outputBaskets": baskets,
        "transactions": transactions,
        "commissions": commissions,
        "outputs": outputs,
        "outputTags": tags,
        "outputTagMaps": tag_maps,
        "txLabels": labels,
        "txLabelMaps": tx_label_maps,
        "certificates": certificates,
        "certificateFields": certificate_fields,
        "syncState": sync_state,
        "monitorEvent": monitor_event,
        "provenTx": proven_tx,
        "provenTxReqs": proven_tx_reqs,
        "sinceAnchor": user1["createdAt"],
    }


@pytest.fixture
def storage_seeded() -> tuple[StorageProvider, dict[str, Any]]:
    engine = create_engine_from_url("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    storage = StorageProvider(engine=engine, chain="test", storage_identity_key="seed-storage")
    storage.make_available()
    seed = seed_storage(storage)
    return storage, seed
