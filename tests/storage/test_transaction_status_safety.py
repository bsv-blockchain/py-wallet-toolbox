"""Monitor safety: find_* filters and the 'failed' transition (parity report rank 1 and rank 15).

find_* used to drop filters it did not recognise, so TaskFailAbandoned's
``{"txStatus": [...]}`` matched every transaction and failed completed ones.
The 'failed' transition had no guards, so a completed transaction could be
failed and ReviewStatus would then release the outputs it had spent.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta, timezone
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy import update

from bsv_wallet_toolbox.errors import InvalidParameterError
from bsv_wallet_toolbox.monitor.tasks import TaskFailAbandoned
from bsv_wallet_toolbox.storage.db import create_engine_from_url, session_scope
from bsv_wallet_toolbox.storage.models import Base
from bsv_wallet_toolbox.storage.models import Transaction as TransactionModel
from bsv_wallet_toolbox.storage.provider import StorageProvider


@pytest.fixture
def storage() -> StorageProvider:
    engine = create_engine_from_url("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    sp = StorageProvider(engine=engine, chain="test", storage_identity_key="status-safety")
    sp.make_available()
    return sp


def _user(sp: StorageProvider) -> int:
    return sp.get_or_create_user_id("03" + "c" * 62)


def _tx(sp: StorageProvider, user_id: int, status: str, ref: str, *, age_minutes: int = 0, **extra: Any) -> int:
    tx_id = sp.insert_transaction(
        {
            "userId": user_id,
            "status": status,
            "reference": ref,
            "isOutgoing": True,
            "satoshis": 0,
            "description": ref,
            "txid": ref.ljust(64, "0")[:64],
            **extra,
        }
    )
    if age_minutes:
        old = datetime.now(UTC).replace(tzinfo=None) - timedelta(minutes=age_minutes)
        with session_scope(sp.SessionLocal) as s:
            s.execute(update(TransactionModel).where(TransactionModel.transaction_id == tx_id).values(updated_at=old))
    return tx_id


def _output(sp: StorageProvider, user_id: int, tx_id: int, vout: int, *, spendable: bool, spent_by: int | None) -> int:
    return sp.insert_output(
        {
            "transactionId": tx_id,
            "userId": user_id,
            "spendable": spendable,
            "change": True,
            "vout": vout,
            "satoshis": 1000,
            "providedBy": "storage",
            "purpose": "change",
            "type": "P2PKH",
            "spentBy": spent_by,
        }
    )


def _req(sp: StorageProvider, txid: str, status: str) -> int:
    return sp.insert_proven_tx_req(
        {
            "txid": txid,
            "status": status,
            "attempts": 0,
            "notified": False,
            "rawTx": b"\x00",
            "history": "{}",
            "notify": "{}",
        }
    )


def _status(sp: StorageProvider, tx_id: int) -> str:
    return sp.find_transactions({"partial": {"transactionId": tx_id}})[0]["status"]


def _out(sp: StorageProvider, output_id: int) -> dict[str, Any]:
    return sp.find_outputs({"partial": {"outputId": output_id}})[0]


# --- rank 1: find_* filters -------------------------------------------------


def test_find_transactions_honours_status_extra(storage: StorageProvider) -> None:
    uid = _user(storage)
    _tx(storage, uid, "completed", "done")
    unsigned = _tx(storage, uid, "unsigned", "open")

    found = storage.find_transactions({"partial": {}, "status": ["unprocessed", "unsigned"]})

    assert [t["transactionId"] for t in found] == [unsigned]
    assert storage.count_transactions({"partial": {}, "status": ["unsigned"]}) == 1


def test_find_proven_tx_reqs_honours_status_extra(storage: StorageProvider) -> None:
    for i, status in enumerate(["unsent", "completed", "sending"]):
        _req(storage, f"{i:064x}", status)

    found = storage.find_proven_tx_reqs({"partial": {}, "status": ["unsent", "sending"]})

    assert sorted(r["status"] for r in found) == ["sending", "unsent"]


@pytest.mark.parametrize(
    "query",
    [
        {"txStatus": ["unprocessed", "unsigned"]},  # what TaskFailAbandoned used to send
        {"partial": {}, "txStatus": ["unsigned"]},
        {"partial": {"noSuchColumn": 1}},
        {"partial": {"__tablename__": "transactions"}},  # a class attribute, not a column
        {"partial": {"user": 1}},  # a relationship
    ],
)
def test_find_rejects_unknown_filters(storage: StorageProvider, query: dict[str, Any]) -> None:
    _tx(storage, _user(storage), "completed", "done")

    with pytest.raises(InvalidParameterError):
        storage.find_transactions(query)


def test_find_transactions_paged_and_since(storage: StorageProvider) -> None:
    uid = _user(storage)
    ids = [_tx(storage, uid, "unsigned", f"r{i}") for i in range(5)]
    old = _tx(storage, uid, "unsigned", "old", age_minutes=60)

    page = storage.find_transactions({"partial": {}, "paged": {"limit": 2, "offset": 1}})
    assert [t["transactionId"] for t in page] == ids[1:3]

    since = datetime.now(UTC).replace(tzinfo=None) - timedelta(minutes=30)
    recent = storage.find_transactions({"partial": {}, "since": since})
    assert old not in {t["transactionId"] for t in recent}
    assert set(ids) <= {t["transactionId"] for t in recent}


def test_fail_abandoned_spares_completed_transactions(storage: StorageProvider) -> None:
    uid = _user(storage)
    completed = _tx(storage, uid, "completed", "done", age_minutes=60)
    abandoned = _tx(storage, uid, "unsigned", "stale", age_minutes=60)
    fresh = _tx(storage, uid, "unprocessed", "fresh")

    monitor = MagicMock()
    monitor.storage = storage
    TaskFailAbandoned(monitor).run_task()

    assert _status(storage, completed) == "completed"
    assert _status(storage, abandoned) == "failed"
    assert _status(storage, fresh) == "unprocessed"


# --- rank 15: the 'failed' transition ------------------------------------------


def test_failed_releases_inputs_and_neutralises_outputs(storage: StorageProvider) -> None:
    uid = _user(storage)
    source = _tx(storage, uid, "completed", "src")
    spending = _tx(storage, uid, "unsigned", "spend")
    spent_input = _output(storage, uid, source, 0, spendable=False, spent_by=spending)
    new_change = _output(storage, uid, spending, 0, spendable=True, spent_by=None)

    storage.update_transaction_status("failed", spending)

    assert _status(storage, spending) == "failed"
    assert _out(storage, spent_input)["spendable"] is True
    assert _out(storage, spent_input)["spentBy"] is None
    assert _out(storage, new_change)["spendable"] is False


@pytest.mark.parametrize(
    ("current", "new", "proven"),
    [
        ("completed", "failed", False),
        ("unproven", "failed", True),  # a proof makes it completed whatever the status says
        ("failed", "unproven", False),
    ],
)
def test_status_guards(storage: StorageProvider, current: str, new: str, proven: bool) -> None:
    uid = _user(storage)
    extra: dict[str, Any] = {}
    if proven:
        extra["provenTxId"] = storage.insert_proven_tx(
            {
                "txid": "p" * 64,
                "height": 1,
                "index": 0,
                "merklePath": b"\x00",
                "rawTx": b"\x00",
                "blockHash": "0" * 64,
                "merkleRoot": "0" * 64,
            }
        )
    tx_id = _tx(storage, uid, current, "guarded", **extra)

    with pytest.raises(Exception, match="cannot be changed|un-failed"):
        storage.update_transaction_status(new, tx_id)
    with pytest.raises(Exception, match="cannot be changed|un-failed"):
        storage.update_transactions_status([tx_id], new)
    assert _status(storage, tx_id) == current


def test_update_transaction_status_by_user_and_reference(storage: StorageProvider) -> None:
    uid = _user(storage)
    tx_id = _tx(storage, uid, "unsigned", "by-ref")

    storage.update_transaction_status("unprocessed", user_id=uid, reference="by-ref")

    assert _status(storage, tx_id) == "unprocessed"


def test_review_status_keeps_inputs_of_failed_tx_with_live_req(storage: StorageProvider) -> None:
    uid = _user(storage)
    source = _tx(storage, uid, "completed", "src")
    failed = _tx(storage, uid, "failed", "live")
    _req(storage, "live".ljust(64, "0"), "unsent")
    still_spent = _output(storage, uid, source, 0, spendable=False, spent_by=failed)

    storage.review_status({})

    assert _out(storage, still_spent)["spentBy"] == failed


def test_review_status_releases_inputs_of_failed_tx_with_terminal_req(storage: StorageProvider) -> None:
    uid = _user(storage)
    source = _tx(storage, uid, "completed", "src")
    failed = _tx(storage, uid, "failed", "rejected")
    _req(storage, "rejected".ljust(64, "0"), "invalid")
    released = _output(storage, uid, source, 0, spendable=False, spent_by=failed)

    storage.review_status({})

    assert _out(storage, released)["spentBy"] is None
    assert _out(storage, released)["spendable"] is True


def test_review_status_neutralises_outputs_of_failed_tx(storage: StorageProvider) -> None:
    uid = _user(storage)
    failed = _tx(storage, uid, "failed", "dead")
    phantom = _output(storage, uid, failed, 0, spendable=True, spent_by=None)

    storage.review_status({})

    assert _out(storage, phantom)["spendable"] is False


def test_create_action_failure_marks_tx_failed_and_releases_change(
    storage_seeded: tuple[StorageProvider, dict[str, Any]],
) -> None:
    sp, seed = storage_seeded
    user_id = seed["user1"]["userId"]
    args = {
        "description": "fails after funding",
        "outputs": [{"satoshis": 1000, "lockingScript": "76a914" + "33" * 20 + "88ac", "outputDescription": "pay"}],
        "options": {"signAndProcess": True, "noSend": True, "randomizeOutputs": False},
    }
    before = {o["outputId"] for o in sp.find_outputs({"partial": {"userId": user_id, "spendable": True}})}

    with patch.object(sp, "_create_new_inputs", side_effect=RuntimeError("boom")), pytest.raises(RuntimeError):
        sp.create_action({"userId": user_id}, args)

    new_tx = max(sp.find_transactions({"partial": {"userId": user_id}}), key=lambda t: t["transactionId"])
    assert new_tx["status"] == "failed"
    assert sp.find_outputs({"partial": {"spentBy": new_tx["transactionId"]}}) == []
    after = {o["outputId"] for o in sp.find_outputs({"partial": {"userId": user_id, "spendable": True}})}
    assert before <= after


# --- review round 1 (codex) ---------------------------------------------------


def test_count_uses_the_same_extras_as_find(storage: StorageProvider) -> None:
    uid = _user(storage)
    done = _tx(storage, uid, "completed", "done")
    open_tx = _tx(storage, uid, "unsigned", "open")
    _output(storage, uid, done, 0, spendable=True, spent_by=None)
    _output(storage, uid, open_tx, 0, spendable=False, spent_by=None)

    assert storage.count_outputs({"partial": {}, "txStatus": ["completed"]}) == 1
    assert len(storage.find_outputs({"partial": {}, "txStatus": ["completed"]})) == 1


def test_from_to_accept_aware_and_iso_dates(storage: StorageProvider) -> None:
    uid = _user(storage)
    tx_id = _tx(storage, uid, "unsigned", "now")
    old = _tx(storage, uid, "unsigned", "old")
    with session_scope(storage.SessionLocal) as s:
        three_hours_ago = datetime.now(UTC).replace(tzinfo=None) - timedelta(hours=3)
        s.execute(
            update(TransactionModel).where(TransactionModel.transaction_id == old).values(created_at=three_hours_ago)
        )
    an_hour_ago_jst = datetime.now(UTC).astimezone(timezone(timedelta(hours=9))) - timedelta(hours=1)
    in_an_hour = (datetime.now(UTC) + timedelta(hours=1)).isoformat()

    found = storage.find_transactions({"partial": {}, "from": an_hour_ago_jst, "to": in_an_hour})

    assert [t["transactionId"] for t in found] == [tx_id]


def test_map_tables_page_by_tag_then_output(storage: StorageProvider) -> None:
    uid = _user(storage)
    tx_id = _tx(storage, uid, "completed", "tagged")
    out1 = _output(storage, uid, tx_id, 0, spendable=True, spent_by=None)
    out2 = _output(storage, uid, tx_id, 1, spendable=True, spent_by=None)
    tag1 = storage.insert_output_tag({"userId": uid, "tag": "one", "isDeleted": False})
    tag2 = storage.insert_output_tag({"userId": uid, "tag": "two", "isDeleted": False})
    storage.insert_output_tag_map({"outputId": out1, "outputTagId": tag2, "isDeleted": False})
    storage.insert_output_tag_map({"outputId": out2, "outputTagId": tag1, "isDeleted": False})

    first = storage.find_output_tag_maps({"partial": {}, "paged": {"limit": 1}})

    assert [(m["outputTagId"], m["outputId"]) for m in first] == [(tag1, out2)]  # TS pagingKey order


def test_crud_reader_paging_reaches_storage(storage: StorageProvider) -> None:
    from bsv_wallet_toolbox.storage.crud import TransactionReader

    uid = _user(storage)
    ids = [_tx(storage, uid, "unsigned", f"c{i}") for i in range(4)]

    page = TransactionReader(storage).paged(2, 1).find()

    assert [t["transactionId"] for t in page] == ids[1:3]


def test_arcade_sse_skips_rows_that_cannot_change(storage: StorageProvider) -> None:
    from bsv_wallet_toolbox.monitor.tasks import TaskArcadeSSE

    sender = _user(storage)
    receiver = storage.get_or_create_user_id("03" + "d" * 62)
    sending = _tx(storage, sender, "sending", "shared")
    completed = _tx(storage, receiver, "completed", "shared-in", txid="shared".ljust(64, "0"))
    monitor = MagicMock()
    monitor.storage = storage

    TaskArcadeSSE(monitor)._update_transactions({"txid": "shared".ljust(64, "0")}, "unproven")

    assert _status(storage, sending) == "unproven"
    assert _status(storage, completed) == "completed"


def test_fail_abandoned_walks_every_page(storage: StorageProvider) -> None:
    uid = _user(storage)
    stale = [_tx(storage, uid, "unsigned", f"s{i}", age_minutes=60) for i in range(130)]
    fresh = [_tx(storage, uid, "unprocessed", f"f{i}") for i in range(110)]
    monitor = MagicMock()
    monitor.storage = storage

    TaskFailAbandoned(monitor).run_task()

    assert {_status(storage, t) for t in stale} == {"failed"}
    assert {_status(storage, t) for t in fresh} == {"unprocessed"}
