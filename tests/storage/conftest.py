from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, Tuple

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


def seed_storage(storage: StorageProvider) -> Dict[str, Any]:
    base_time = datetime(2024, 1, 1, 12, 0, 0)

    # Users
    user1_id = storage.insert_user(
        {
            "identityKey": "03" + "a" * 62,
            "activeStorage": "local-primary",
            "created_at": _ts(base_time, 0),
            "updated_at": _ts(base_time, 0),
        }
    )
    user2_id = storage.insert_user(
        {
            "identityKey": "03" + "b" * 62,
            "activeStorage": "local-secondary",
            "created_at": _ts(base_time, 1),
            "updated_at": _ts(base_time, 1),
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
                    "created_at": _ts(base_time, 10 + idx),
                    "updated_at": _ts(base_time, 10 + idx),
                }
            )
        )
    baskets = [
        _record_by_id(storage, "find_output_baskets", "basketId", basket_id)
        for basket_id in basket_ids
    ]

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
            "created_at": _ts(base_time, 20),
            "updated_at": _ts(base_time, 20),
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
            "created_at": _ts(base_time, 21),
            "updated_at": _ts(base_time, 21),
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
            "inputBEEF": b"\x09\x0A",
            "rawTx": b"\x0B\x0C",
            "created_at": _ts(base_time, 22),
            "updated_at": _ts(base_time, 22),
        }
    )

    transactions = {
        "tx1": _record_by_id(storage, "find_transactions", "transactionId", tx1_id),
        "tx2": _record_by_id(storage, "find_transactions", "transactionId", tx2_id),
        "tx3": _record_by_id(storage, "find_transactions", "transactionId", tx3_id),
    }

    # Commissions
    commissions: Dict[str, dict[str, Any]] = {}
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
                "lockingScript": b"\x0D\x0E",
                "created_at": _ts(base_time, 30),
                "updated_at": _ts(base_time, 30),
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
            "created_at": _ts(base_time, 40),
            "updated_at": _ts(base_time, 40),
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
            "created_at": _ts(base_time, 41),
            "updated_at": _ts(base_time, 41),
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
            "created_at": _ts(base_time, 42),
            "updated_at": _ts(base_time, 42),
        }
    )

    outputs = {
        "o1": _record_by_id(storage, "find_outputs", "outputId", output1_id),
        "o2": _record_by_id(storage, "find_outputs", "outputId", output2_id),
        "o3": _record_by_id(storage, "find_outputs", "outputId", output3_id),
    }

    # Output tags
    tag1_id = storage.insert_output_tag(
        {
            "userId": user1_id,
            "tag": "primary",
            "isDeleted": False,
            "created_at": _ts(base_time, 50),
            "updated_at": _ts(base_time, 50),
        }
    )
    tag2_id = storage.insert_output_tag(
        {
            "userId": user1_id,
            "tag": "secondary",
            "isDeleted": False,
            "created_at": _ts(base_time, 51),
            "updated_at": _ts(base_time, 51),
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
                "created_at": _ts(base_time, 52),
                "updated_at": _ts(base_time, 52),
            }
        )

    tag_maps = storage.find_output_tag_maps({"partial": {}})

    # Tx labels and maps
    label1_id = storage.insert_tx_label(
        {
            "userId": user1_id,
            "label": "groceries",
            "isDeleted": False,
            "created_at": _ts(base_time, 60),
            "updated_at": _ts(base_time, 60),
        }
    )
    label2_id = storage.insert_tx_label(
        {
            "userId": user1_id,
            "label": "rent",
            "isDeleted": False,
            "created_at": _ts(base_time, 61),
            "updated_at": _ts(base_time, 61),
        }
    )
    label3_id = storage.insert_tx_label(
        {
            "userId": user2_id,
            "label": "salary",
            "isDeleted": False,
            "created_at": _ts(base_time, 62),
            "updated_at": _ts(base_time, 62),
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
                "created_at": _ts(base_time, 63),
                "updated_at": _ts(base_time, 63),
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
            "created_at": _ts(base_time, 70),
            "updated_at": _ts(base_time, 70),
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
            "created_at": _ts(base_time, 71),
            "updated_at": _ts(base_time, 71),
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
            "created_at": _ts(base_time, 72),
            "updated_at": _ts(base_time, 72),
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
            "created_at": _ts(base_time, 73),
            "updated_at": _ts(base_time, 73),
        }
    )
    storage.insert_certificate_field(
        {
            "certificateId": cert_primary_id,
            "userId": user1_id,
            "fieldName": "name",
            "fieldValue": "alice",
            "masterKey": "mk-name",
            "created_at": _ts(base_time, 74),
            "updated_at": _ts(base_time, 74),
        }
    )
    storage.insert_certificate_field(
        {
            "certificateId": cert_secondary_id,
            "userId": user1_id,
            "fieldName": "name",
            "fieldValue": "alice",
            "masterKey": "mk-name-2",
            "created_at": _ts(base_time, 75),
            "updated_at": _ts(base_time, 75),
        }
    )

    certificate_fields = {
        "primary_bob": storage.find_certificate_fields(
            {"partial": {"certificateId": cert_primary_id, "fieldName": "bob"}}
        )[0],
        "primary_name": storage.find_certificate_fields(
            {"partial": {"certificateId": cert_primary_id, "fieldName": "name"}}
        )[0],
        "secondary_name": storage.find_certificate_fields(
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
            "created_at": _ts(base_time, 80),
            "updated_at": _ts(base_time, 80),
        }
    )
    sync_state = _record_by_id(storage, "find_sync_states", "syncStateId", sync_state_id)

    # Monitor event
    monitor_event_id = storage.insert_monitor_event(
        {
            "event": "send_waiting",
            "details": "initial sweep",
            "created_at": _ts(base_time, 90),
            "updated_at": _ts(base_time, 90),
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
            "created_at": _ts(base_time, 100),
            "updated_at": _ts(base_time, 100),
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
            "rawTx": b"\x1A",
            "inputBEEF": b"\x1B",
            "created_at": _ts(base_time, 101),
            "updated_at": _ts(base_time, 101),
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
            "rawTx": b"\x1C",
            "inputBEEF": b"\x1D",
            "created_at": _ts(base_time, 102),
            "updated_at": _ts(base_time, 102),
        }
    )

    proven_tx_reqs = {
        "pending": _record_by_id(storage, "find_proven_tx_reqs", "provenTxReqId", req_pending_id),
        "completed": _record_by_id(storage, "find_proven_tx_reqs", "provenTxReqId", req_completed_id),
    }

    return {
        "user1": user1,
        "user2": user2,
        "output_baskets": baskets,
        "transactions": transactions,
        "commissions": commissions,
        "outputs": outputs,
        "output_tags": tags,
        "output_tag_maps": tag_maps,
        "tx_labels": labels,
        "tx_label_maps": tx_label_maps,
        "certificates": certificates,
        "certificate_fields": certificate_fields,
        "sync_state": sync_state,
        "monitor_event": monitor_event,
        "proven_tx": proven_tx,
        "proven_tx_reqs": proven_tx_reqs,
        "since_anchor": user1["created_at"],
    }


@pytest.fixture
def storage_seeded() -> Tuple[StorageProvider, Dict[str, Any]]:
    engine = create_engine_from_url("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    storage = StorageProvider(engine=engine, chain="test", storage_identity_key="seed-storage")
    storage.make_available()
    seed = seed_storage(storage)
    return storage, seed
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

import pytest

from bsv_wallet_toolbox.storage.db import create_engine_from_url
from bsv_wallet_toolbox.storage.models import Base
from bsv_wallet_toolbox.storage.provider import StorageProvider


BASE_TIME = datetime(2024, 1, 1, 12, 0, 0)


def _seed_storage(storage: StorageProvider) -> dict[str, Any]:
    seed_data: dict[str, Any] = {}

    def timestamp(offset_minutes: int = 0) -> datetime:
        return BASE_TIME + timedelta(minutes=offset_minutes)

    # Users
    user1_id = storage.insert_user(
        {
            "identityKey": "03" + "1" * 64,
            "activeStorage": "local",
            "createdAt": timestamp(0),
            "updatedAt": timestamp(0),
        }
    )
    user2_id = storage.insert_user(
        {
            "identityKey": "03" + "2" * 64,
            "activeStorage": "local",
            "createdAt": timestamp(1),
            "updatedAt": timestamp(1),
        }
    )

    seed_data["users"] = {
        "u1": storage.find_users({"partial": {"userId": user1_id}})[0],
        "u2": storage.find_users({"partial": {"userId": user2_id}})[0],
    }

    # Sync state for user1
    storage.insert_sync_state(
        {
            "userId": user1_id,
            "storageIdentityKey": storage.storage_identity_key,
            "storageName": "default",
            "status": "synced",
            "init": True,
            "refNum": "ref-1",
            "syncMap": "{}",
            "when": "2024-01-01T00:00:00Z",
            "satoshis": 1000,
            "errorLocal": None,
            "errorOther": None,
            "createdAt": timestamp(0),
            "updatedAt": timestamp(0),
        }
    )

    # Output baskets
    basket1_id = storage.insert_output_basket(
        {
            "userId": user1_id,
            "name": "default",
            "numberOfDesiredUTXOs": 10,
            "minimumDesiredUTXOValue": 500,
            "isDeleted": False,
            "createdAt": timestamp(0),
            "updatedAt": timestamp(0),
        }
    )
    basket2_id = storage.insert_output_basket(
        {
            "userId": user1_id,
            "name": "savings",
            "numberOfDesiredUTXOs": 5,
            "minimumDesiredUTXOValue": 1000,
            "isDeleted": False,
            "createdAt": timestamp(0),
            "updatedAt": timestamp(0),
        }
    )
    basket3_id = storage.insert_output_basket(
        {
            "userId": user2_id,
            "name": "default",
            "numberOfDesiredUTXOs": 2,
            "minimumDesiredUTXOValue": 200,
            "isDeleted": False,
            "createdAt": timestamp(1),
            "updatedAt": timestamp(1),
        }
    )

    seed_data["baskets"] = {"ids": [basket1_id, basket2_id, basket3_id]}

    # Tx labels
    label1_id = storage.insert_tx_label(
        {
            "userId": user1_id,
            "label": "invoice",
            "isDeleted": False,
            "createdAt": timestamp(0),
            "updatedAt": timestamp(0),
        }
    )
    label2_id = storage.insert_tx_label(
        {
            "userId": user1_id,
            "label": "rent",
            "isDeleted": False,
            "createdAt": timestamp(0),
            "updatedAt": timestamp(0),
        }
    )
    label3_id = storage.insert_tx_label(
        {
            "userId": user2_id,
            "label": "utilities",
            "isDeleted": False,
            "createdAt": timestamp(1),
            "updatedAt": timestamp(1),
        }
    )

    # Output tags
    tag1_id = storage.insert_output_tag(
        {
            "userId": user1_id,
            "tag": "priority",
            "isDeleted": False,
            "createdAt": timestamp(0),
            "updatedAt": timestamp(0),
        }
    )
    tag2_id = storage.insert_output_tag(
        {
            "userId": user1_id,
            "tag": "gift",
            "isDeleted": False,
            "createdAt": timestamp(0),
            "updatedAt": timestamp(0),
        }
    )

    # Transactions
    tx1_id = storage.insert_transaction(
        {
            "userId": user1_id,
            "status": "sending",
            "reference": "ref-u1-1",
            "isOutgoing": True,
            "satoshis": 5000,
            "description": "User1 primary",
            "txid": "a" * 64,
            "createdAt": timestamp(0),
            "updatedAt": timestamp(0),
        }
    )
    tx2_id = storage.insert_transaction(
        {
            "userId": user2_id,
            "status": "confirmed",
            "reference": "ref-u2-1",
            "isOutgoing": True,
            "satoshis": 2000,
            "description": "User2 primary",
            "txid": "b" * 64,
            "createdAt": timestamp(1),
            "updatedAt": timestamp(1),
        }
    )
    tx3_id = storage.insert_transaction(
        {
            "userId": user2_id,
            "status": "confirmed",
            "reference": "ref-u2-2",
            "isOutgoing": False,
            "satoshis": 3500,
            "description": "User2 secondary",
            "txid": "c" * 64,
            "createdAt": timestamp(2),
            "updatedAt": timestamp(2),
        }
    )

    # Commissions
    for tx_id, owner in ((tx1_id, user1_id), (tx2_id, user2_id), (tx3_id, user2_id)):
        storage.insert_commission(
            {
                "transactionId": tx_id,
                "userId": owner,
                "satoshis": 150,
                "keyOffset": f"key-{tx_id}",
                "isRedeemed": False,
                "lockingScript": b"\x51",
                "createdAt": timestamp(0),
                "updatedAt": timestamp(0),
            }
        )

    # Outputs (3 total)
    output1_id = storage.insert_output(
        {
            "transactionId": tx1_id,
            "userId": user1_id,
            "basketId": basket1_id,
            "vout": 0,
            "satoshis": 101,
            "spendable": True,
            "change": False,
            "providedBy": "wallet",
            "purpose": "payment",
            "type": "p2pkh",
            "lockingScript": b"\x51",
            "createdAt": timestamp(0),
            "updatedAt": timestamp(0),
        }
    )
    output2_id = storage.insert_output(
        {
            "transactionId": tx1_id,
            "userId": user1_id,
            "basketId": basket2_id,
            "vout": 1,
            "satoshis": 111,
            "spendable": True,
            "change": True,
            "providedBy": "wallet",
            "purpose": "change",
            "type": "p2pkh",
            "lockingScript": b"\x52",
            "createdAt": timestamp(0),
            "updatedAt": timestamp(0),
        }
    )
    output3_id = storage.insert_output(
        {
            "transactionId": tx2_id,
            "userId": user2_id,
            "basketId": basket3_id,
            "vout": 0,
            "satoshis": 210,
            "spendable": False,
            "change": False,
            "providedBy": "wallet",
            "purpose": "payment",
            "type": "p2pkh",
            "lockingScript": b"\x53",
            "createdAt": timestamp(1),
            "updatedAt": timestamp(1),
        }
    )

    # Output tag maps (3 total)
    storage.insert_output_tag_map(
        {
            "outputId": output1_id,
            "outputTagId": tag1_id,
            "isDeleted": False,
            "createdAt": timestamp(0),
            "updatedAt": timestamp(0),
        }
    )
    storage.insert_output_tag_map(
        {
            "outputId": output1_id,
            "outputTagId": tag2_id,
            "isDeleted": False,
            "createdAt": timestamp(0),
            "updatedAt": timestamp(0),
        }
    )
    storage.insert_output_tag_map(
        {
            "outputId": output2_id,
            "outputTagId": tag1_id,
            "isDeleted": False,
            "createdAt": timestamp(0),
            "updatedAt": timestamp(0),
        }
    )

    # Tx label maps
    storage.insert_tx_label_map(
        {
            "transactionId": tx1_id,
            "txLabelId": label1_id,
            "isDeleted": False,
            "createdAt": timestamp(0),
            "updatedAt": timestamp(0),
        }
    )
    storage.insert_tx_label_map(
        {
            "transactionId": tx1_id,
            "txLabelId": label2_id,
            "isDeleted": False,
            "createdAt": timestamp(0),
            "updatedAt": timestamp(0),
        }
    )
    storage.insert_tx_label_map(
        {
            "transactionId": tx2_id,
            "txLabelId": label3_id,
            "isDeleted": False,
            "createdAt": timestamp(1),
            "updatedAt": timestamp(1),
        }
    )

    # Certificates and fields (3 certs, 3 fields)
    certifier_primary = "certifier-primary"
    certifier_secondary = "certifier-secondary"
    cert1_id = storage.insert_certificate(
        {
            "userId": user1_id,
            "type": "type-primary",
            "serialNumber": "serial-1",
            "certifier": certifier_primary,
            "subject": "subject-1",
            "verifier": None,
            "revocationOutpoint": "rev-1",
            "signature": "sig-1",
            "isDeleted": False,
            "createdAt": timestamp(0),
            "updatedAt": timestamp(0),
        }
    )
    cert2_type = "type-secondary"
    cert2_id = storage.insert_certificate(
        {
            "userId": user1_id,
            "type": cert2_type,
            "serialNumber": "serial-2",
            "certifier": certifier_secondary,
            "subject": "subject-2",
            "verifier": None,
            "revocationOutpoint": "rev-2",
            "signature": "sig-2",
            "isDeleted": False,
            "createdAt": timestamp(0),
            "updatedAt": timestamp(0),
        }
    )
    cert3_id = storage.insert_certificate(
        {
            "userId": user1_id,
            "type": "type-tertiary",
            "serialNumber": "serial-3",
            "certifier": "certifier-tertiary",
            "subject": "subject-3",
            "verifier": None,
            "revocationOutpoint": "rev-3",
            "signature": "sig-3",
            "isDeleted": False,
            "createdAt": timestamp(0),
            "updatedAt": timestamp(0),
        }
    )

    storage.insert_certificate_field(
        {
            "certificateId": cert1_id,
            "userId": user1_id,
            "fieldName": "bob",
            "fieldValue": "your uncle",
            "masterKey": "key",
            "createdAt": timestamp(0),
            "updatedAt": timestamp(0),
        }
    )
    storage.insert_certificate_field(
        {
            "certificateId": cert1_id,
            "userId": user1_id,
            "fieldName": "name",
            "fieldValue": "alice",
            "masterKey": "key",
            "createdAt": timestamp(0),
            "updatedAt": timestamp(0),
        }
    )
    storage.insert_certificate_field(
        {
            "certificateId": cert2_id,
            "userId": user1_id,
            "fieldName": "name",
            "fieldValue": "alice",
            "masterKey": "key",
            "createdAt": timestamp(0),
            "updatedAt": timestamp(0),
        }
    )

    # Proven transactions
    proven_tx_id = storage.insert_proven_tx(
        {
            "txid": "d" * 64,
            "height": 100,
            "index": 0,
            "merklePath": b"\x01\x02\x03",
            "rawTx": b"\x00\x01",
            "blockHash": "e" * 64,
            "merkleRoot": "f" * 64,
            "createdAt": timestamp(0),
            "updatedAt": timestamp(0),
        }
    )

    storage.insert_proven_tx_req(
        {
            "provenTxId": proven_tx_id,
            "status": "pending",
            "attempts": 1,
            "notified": False,
            "txid": "g" * 64,
            "batch": "batch-1",
            "history": "{}",
            "notify": "{}",
            "rawTx": b"\x00",
            "inputBEEF": b"\x01",
            "createdAt": timestamp(0),
            "updatedAt": timestamp(0),
        }
    )
    storage.insert_proven_tx_req(
        {
            "provenTxId": None,
            "status": "queued",
            "attempts": 0,
            "notified": True,
            "txid": "h" * 64,
            "batch": "batch-2",
            "history": "{}",
            "notify": "{}",
            "rawTx": b"\x00",
            "inputBEEF": None,
            "createdAt": timestamp(0),
            "updatedAt": timestamp(0),
        }
    )

    # Monitor event
    storage.insert_monitor_event(
        {
            "event": "startup",
            "details": "seed",
            "createdAt": timestamp(0),
            "updatedAt": timestamp(0),
        }
    )

    seed_data["certifiers"] = {
        "primary": certifier_primary,
        "secondary": certifier_secondary,
        "missing": "none",
    }
    seed_data["types"] = {
        "secondary": cert2_type,
        "missing": "oblongata",
    }
    seed_data["field_names"] = {
        "exists": "name",
        "alternate": "bob",
        "missing": "bob42",
    }
    seed_data["timestamps"] = {
        "base": timestamp(0),
        "future": timestamp(0) + timedelta(days=1),
    }

    return seed_data


@pytest.fixture
def storage_seeded() -> tuple[StorageProvider, dict[str, Any]]:
    engine = create_engine_from_url("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    storage = StorageProvider(engine=engine, chain="test", storage_identity_key="seed")
    storage.make_available()
    seed = _seed_storage(storage)
    try:
        yield storage, seed
    finally:
        engine.dispose()

