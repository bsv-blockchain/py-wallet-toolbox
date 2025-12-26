"""Integration-style tests for StorageProvider update operations."""

from datetime import datetime


def _first(records):
    return records[0]


def test_update_proventx(storage_seeded) -> None:
    storage, seed = storage_seeded
    record = seed["provenTx"]
    new_time = datetime(2001, 1, 2, 12, 0, 0)

    updated = storage.update_proven_tx(
        record["provenTxId"],
        {
            "blockHash": "updated-block-hash",
            "updatedAt": new_time,
        },
    )
    assert updated == 1

    refreshed = _first(storage.find_proven_txs({"partial": {"provenTxId": record["provenTxId"]}}))
    assert refreshed["blockHash"] == "updated-block-hash"
    assert refreshed["updatedAt"] == new_time


def test_update_proventx_all_fields(storage_seeded) -> None:
    storage, seed = storage_seeded
    record = seed["provenTx"]
    updated = storage.update_proven_tx(
        record["provenTxId"],
        {
            "txid": "updated-txid",
            "height": 321,
            "index": 5,
            "merklePath": b"\x09\x09",
            "rawTx": b"\x01\x02",
            "blockHash": "f" * 64,
            "merkleRoot": "e" * 64,
        },
    )
    assert updated == 1

    refreshed = _first(storage.find_proven_txs({"partial": {"provenTxId": record["provenTxId"]}}))
    assert refreshed["txid"] == "updated-txid"
    assert refreshed["height"] == 321
    assert refreshed["index"] == 5
    assert refreshed["merklePath"] == b"\x09\x09"
    assert refreshed["rawTx"] == b"\x01\x02"


def test_update_proventxreq(storage_seeded) -> None:
    storage, seed = storage_seeded
    record = seed["provenTxReqs"]["pending"]
    updated = storage.update_proven_tx_req(
        record["provenTxReqId"],
        {
            "status": "completed",
            "attempts": 5,
            "notified": True,
            "batch": "batch-updated",
            "history": '{"updated":true}',
        },
    )
    assert updated == 1

    refreshed = _first(storage.find_proven_tx_reqs({"partial": {"provenTxReqId": record["provenTxReqId"]}}))
    assert refreshed["status"] == "completed"
    assert refreshed["attempts"] == 5
    assert refreshed["notified"] is True
    assert refreshed.get("batch") == "batch-updated"


def test_update_user(storage_seeded) -> None:
    storage, seed = storage_seeded
    user_id = seed["user1"]["userId"]
    updated = storage.update_user(
        user_id,
        {
            "identityKey": "03" + "9" * 64,
            "activeStorage": "remote",
        },
    )
    assert updated == 1

    refreshed = _first(storage.find_users({"partial": {"userId": user_id}}))
    assert refreshed["identityKey"] == "03" + "9" * 64
    assert refreshed["activeStorage"] == "remote"


def test_update_certificate(storage_seeded) -> None:
    storage, seed = storage_seeded
    cert = seed["certificates"]["primary"]
    updated = storage.update_certificate(
        cert["certificateId"],
        {
            "type": "updated-type",
            "subject": "updated-subject",
            "serialNumber": "updated-serial",
        },
    )
    assert updated == 1

    refreshed = _first(storage.find_certificates({"partial": {"certificateId": cert["certificateId"]}}))
    assert refreshed["type"] == "updated-type"
    assert refreshed["subject"] == "updated-subject"
    assert refreshed["serialNumber"] == "updated-serial"


def test_update_certificate_field(storage_seeded) -> None:
    storage, seed = storage_seeded
    field = seed["certificateFields"]["primaryName"]
    field_id = field["certificateFieldId"]
    updated = storage.update_certificate_field(
        field_id,
        {
            "fieldName": field["fieldName"],
            "fieldValue": "updated-value",
            "masterKey": "updated-key",
        },
    )
    assert updated == 1

    refreshed = _first(storage.find_certificate_fields({"partial": {"certificateFieldId": field_id}}))
    assert refreshed["fieldValue"] == "updated-value"
    assert refreshed["masterKey"] == "updated-key"


def test_update_output_basket(storage_seeded) -> None:
    storage, seed = storage_seeded
    basket = seed["outputBaskets"][0]
    updated = storage.update_output_basket(
        basket["basketId"],
        {
            "numberOfDesiredUTXOs": 42,
            "minimumDesiredUTXOValue": 2048,
            "name": "updated-basket",
        },
    )
    assert updated == 1

    refreshed = _first(storage.find_output_baskets({"partial": {"basketId": basket["basketId"]}}))
    assert refreshed["numberOfDesiredUTXOs"] == 42
    assert refreshed["minimumDesiredUTXOValue"] == 2048
    assert refreshed["name"] == "updated-basket"


def test_update_transaction(storage_seeded) -> None:
    storage, seed = storage_seeded
    tx = seed["transactions"]["tx1"]
    updated = storage.update_transaction(
        tx["transactionId"],
        {
            "status": "completed",
            "description": "updated description",
            "satoshis": 9999,
        },
    )
    assert updated == 1

    refreshed = _first(storage.find_transactions({"partial": {"transactionId": tx["transactionId"]}}))
    assert refreshed["status"] == "completed"
    assert refreshed["description"] == "updated description"
    assert refreshed["satoshis"] == 9999


def test_update_commission(storage_seeded) -> None:
    storage, seed = storage_seeded
    commission = seed["commissions"]["tx1"]
    updated = storage.update_commission(
        commission["commissionId"],
        {
            "satoshis": 777,
            "isRedeemed": True,
        },
    )
    assert updated == 1

    refreshed = _first(storage.find_commissions({"partial": {"commissionId": commission["commissionId"]}}))
    assert refreshed["satoshis"] == 777
    assert refreshed["isRedeemed"] is True


def test_update_output(storage_seeded) -> None:
    storage, seed = storage_seeded
    output = seed["outputs"]["o1"]
    updated = storage.update_output(
        output["outputId"],
        {
            "spendable": False,
            "purpose": "updated-purpose",
        },
    )
    assert updated == 1

    refreshed = _first(storage.find_outputs({"partial": {"outputId": output["outputId"]}}))
    assert refreshed["spendable"] is False
    assert refreshed["purpose"] == "updated-purpose"


def test_update_output_tag(storage_seeded) -> None:
    storage, seed = storage_seeded
    tag = seed["outputTags"]["tag1"]
    updated = storage.update_output_tag(
        tag["outputTagId"],
        {
            "tag": "updated-tag",
        },
    )
    assert updated == 1

    refreshed = _first(storage.find_output_tags({"partial": {"outputTagId": tag["outputTagId"]}}))
    assert refreshed["tag"] == "updated-tag"


def test_update_monitor_event(storage_seeded) -> None:
    storage, seed = storage_seeded
    event = seed["monitorEvent"]
    updated = storage.update_monitor_event(
        event["id"],
        {
            "details": "updated",
        },
    )
    assert updated == 1

    refreshed = _first(storage.find_monitor_events({"partial": {"id": event["id"]}}))
    assert refreshed["details"] == "updated"


def test_update_sync_state(storage_seeded) -> None:
    storage, seed = storage_seeded
    sync_state = seed["syncState"]
    updated = storage.update_sync_state(
        sync_state["syncStateId"],
        {
            "status": "resync",
            "init": False,
        },
    )
    assert updated == 1

    refreshed = _first(storage.find_sync_states({"partial": {"syncStateId": sync_state["syncStateId"]}}))
    assert refreshed["status"] == "resync"
    assert refreshed["init"] is False


def test_update_tx_label(storage_seeded) -> None:
    storage, seed = storage_seeded
    label = seed["txLabels"]["label1"]
    updated = storage.update_tx_label(
        label["txLabelId"],
        {
            "label": "updated-label",
        },
    )
    assert updated == 1

    refreshed = _first(storage.find_tx_labels({"partial": {"txLabelId": label["txLabelId"]}}))
    assert refreshed["label"] == "updated-label"
