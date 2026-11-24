"""Delayed and immediate broadcast of processed actions (parity report rank 12).

acceptDelayedBroadcast (the default) left the transaction 'unprocessed' with an
empty notify, and TaskSendWaiting called ``post_beef(raw_tx, [txid])`` against
``Services.post_beef(beef)``, so the TypeError was logged and nothing was sent.
An immediate send of a transaction with an inputBEEF always failed with "no raw
transaction available". Both paths now post an AtomicBEEF of the transaction.
"""

from __future__ import annotations

import json
from typing import Any
from unittest.mock import patch

import pytest
from bsv.transaction import Transaction
from bsv.transaction.beef import parse_beef_ex
from sqlalchemy import update

from bsv_wallet_toolbox.monitor import Monitor, MonitorOptions
from bsv_wallet_toolbox.monitor.tasks import TaskSendWaiting
from bsv_wallet_toolbox.services import Services
from bsv_wallet_toolbox.storage.db import create_engine_from_url, session_scope
from bsv_wallet_toolbox.storage.models import Base
from bsv_wallet_toolbox.storage.models import Transaction as TransactionModel
from bsv_wallet_toolbox.storage.provider import StorageProvider
from tests.testabilities.tsgenerated import PARENT_BEEF_TXID, SIGNED_TRANSACTION_HEX, parent_transaction_atomic_beef

TXID = Transaction.from_hex(SIGNED_TRANSACTION_HEX).txid()


@pytest.fixture
def storage() -> StorageProvider:
    engine = create_engine_from_url("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    sp = StorageProvider(engine=engine, chain="test", storage_identity_key="delayed-broadcast")
    sp.make_available()
    return sp


@pytest.fixture
def services() -> Services:
    return Services(Services.create_default_options("test"))


def _post(results: list[dict[str, Any]], posted: list[str]):
    """Stand-in for Services.post_beef that keeps its signature (autospec) and records the BEEF."""

    def post_beef(_self: Services, beef: str) -> dict[str, Any]:
        posted.append(beef)
        return results.pop(0)

    return post_beef


def _process(storage: StorageProvider, *, delayed: bool) -> tuple[dict[str, Any], int, dict[str, Any]]:
    user_id = storage.get_or_create_user_id("03" + "d" * 62)
    tx_id = storage.insert_transaction(
        {
            "userId": user_id,
            "status": "unsigned",
            "reference": "ref-rank12",
            "isOutgoing": True,
            "satoshis": -1000,
            "description": "rank 12",
            "inputBEEF": parse_beef_ex(parent_transaction_atomic_beef())[0].to_binary(),
        }
    )
    auth = {"userId": user_id}
    r = storage.process_action(
        auth,
        {
            "isNewTx": True,
            "isSendWith": False,
            "isNoSend": False,
            "isDelayed": delayed,
            "reference": "ref-rank12",
            "txid": TXID,
            "rawTx": list(bytes.fromhex(SIGNED_TRANSACTION_HEX)),
            "sendWith": [],
        },
    )
    return r, tx_id, auth


def _req(storage: StorageProvider) -> dict[str, Any]:
    return storage.find_proven_tx_reqs({"partial": {"txid": TXID}})[0]


def _tx_status(storage: StorageProvider, tx_id: int) -> str:
    return storage.find_transactions({"partial": {"transactionId": tx_id}})[0]["status"]


def _assert_atomic_beef_of_tx(beef_hex: str) -> None:
    beef, subject, _ = parse_beef_ex(bytes.fromhex(beef_hex))
    assert subject == TXID
    assert beef.find_transaction(PARENT_BEEF_TXID) is not None


def test_delayed_action_is_sending_and_records_notify(storage: StorageProvider) -> None:
    r, tx_id, _ = _process(storage, delayed=True)

    assert r["sendWithResults"] == [{"txid": TXID, "status": "sending"}]
    req = _req(storage)
    assert req["status"] == "unsent"
    assert json.loads(req["notify"])["transactionIds"] == [tx_id]
    # 'unprocessed' would let TaskFailAbandoned fail it (and release its inputs) before it is sent.
    assert _tx_status(storage, tx_id) == "sending"


def test_send_waiting_posts_delayed_action_as_atomic_beef(storage: StorageProvider, services: Services) -> None:
    _, tx_id, _ = _process(storage, delayed=True)
    monitor = Monitor(MonitorOptions(chain="test", storage=storage, services=services))
    broadcasted: list[dict[str, Any]] = []
    monitor.on_transaction_broadcasted = broadcasted.append
    posted: list[str] = []

    with patch.object(Services, "post_beef", autospec=True, side_effect=_post([{"accepted": True}], posted)):
        log = TaskSendWaiting(monitor, 1, 0).run_task()

    assert len(posted) == 1, log
    _assert_atomic_beef_of_tx(posted[0])
    assert _req(storage)["status"] == "unmined"
    assert _tx_status(storage, tx_id) == "unproven"
    assert broadcasted == [{"status": "success", "txid": TXID}]


def test_immediate_send_with_input_beef_posts_atomic_beef(storage: StorageProvider, services: Services) -> None:
    storage.set_services(services)
    posted: list[str] = []

    with patch.object(Services, "post_beef", autospec=True, side_effect=_post([{"accepted": True}], posted)):
        r, tx_id, _ = _process(storage, delayed=False)

    assert r["sendWithResults"] == [{"txid": TXID, "status": "unproven"}]
    assert r["notDelayedResults"][0]["status"] == "success"
    assert len(posted) == 1
    _assert_atomic_beef_of_tx(posted[0])
    assert _req(storage)["status"] == "unmined"
    assert _tx_status(storage, tx_id) == "unproven"


def test_service_error_leaves_action_sending_for_retry(storage: StorageProvider, services: Services) -> None:
    _, tx_id, _ = _process(storage, delayed=True)
    monitor = Monitor(MonitorOptions(chain="test", storage=storage, services=services))
    failure = {"accepted": False, "message": "ARC: HTTP 503 - unavailable"}

    with patch.object(Services, "post_beef", autospec=True, side_effect=_post([failure], [])):
        TaskSendWaiting(monitor, 1, 0).run_task()

    req = _req(storage)
    assert (req["status"], req["attempts"]) == ("sending", 1)
    assert _tx_status(storage, tx_id) == "sending"


@pytest.mark.parametrize(
    ("result", "req_status"),
    [
        ({"accepted": False, "doubleSpend": True, "message": "double spend"}, "doubleSpend"),
        ({"accepted": False, "message": "ARC: HTTP 461 - mandatory-script-verify-flag failed"}, "invalid"),
    ],
)
def test_rejected_action_fails(
    storage: StorageProvider, services: Services, result: dict[str, Any], req_status: str
) -> None:
    _, tx_id, _ = _process(storage, delayed=True)
    monitor = Monitor(MonitorOptions(chain="test", storage=storage, services=services))

    with patch.object(Services, "post_beef", autospec=True, side_effect=_post([result], [])):
        TaskSendWaiting(monitor, 1, 0).run_task()

    assert _req(storage)["status"] == req_status
    assert _tx_status(storage, tx_id) == "failed"


@pytest.mark.parametrize("tx_status", ["unprocessed", "failed"])
def test_req_without_notify_is_not_sent(storage: StorageProvider, services: Services, tx_status: str) -> None:
    """A req written before notify was recorded (or whose transaction was already abandoned) is not broadcast.

    Its transaction may already be 'failed' with its inputs released; broadcasting it would put a tx the
    wallet has given up on onto the chain (TS validateReqsAndMergeBeefs marks such reqs invalid).
    """
    _, tx_id, _ = _process(storage, delayed=True)
    req = _req(storage)
    storage.update_proven_tx_req(req["provenTxReqId"], {"notify": "{}"})
    with session_scope(storage.SessionLocal) as s:
        s.execute(update(TransactionModel).where(TransactionModel.transaction_id == tx_id).values(status=tx_status))
    monitor = Monitor(MonitorOptions(chain="test", storage=storage, services=services))
    posted: list[str] = []

    with patch.object(Services, "post_beef", autospec=True, side_effect=_post([{"accepted": True}], posted)):
        TaskSendWaiting(monitor, 1, 0).run_task()

    assert posted == []
    assert _req(storage)["status"] == "invalid"
    assert _tx_status(storage, tx_id) == tx_status


def test_failed_transaction_is_not_sent(storage: StorageProvider, services: Services) -> None:
    _, tx_id, _ = _process(storage, delayed=True)
    storage.update_transaction_status("failed", tx_id)
    monitor = Monitor(MonitorOptions(chain="test", storage=storage, services=services))
    posted: list[str] = []

    with patch.object(Services, "post_beef", autospec=True, side_effect=_post([{"accepted": True}], posted)):
        TaskSendWaiting(monitor, 1, 0).run_task()

    assert posted == []
    assert _req(storage)["status"] == "invalid"


def test_broadcast_callback_from_monitor_options(storage: StorageProvider, services: Services) -> None:
    _process(storage, delayed=True)
    broadcasted: list[dict[str, Any]] = []
    monitor = Monitor(
        MonitorOptions(chain="test", storage=storage, services=services, on_transaction_broadcasted=broadcasted.append)
    )

    with patch.object(Services, "post_beef", autospec=True, side_effect=_post([{"accepted": True}], [])):
        TaskSendWaiting(monitor, 1, 0).run_task()

    assert broadcasted == [{"status": "success", "txid": TXID}]


@pytest.mark.parametrize(
    ("result", "req_status", "tx_status"),
    [
        # A service error is retried even when its text looks fatal: the parent may just not be there yet.
        ({"accepted": False, "serviceError": True, "message": "ARC: HTTP 503 - missing inputs"}, "sending", "sending"),
        # A provider that refused the tx itself fails it even without a known fatal phrase (TS statusError).
        ({"accepted": False, "serviceError": False, "message": "ARC: HTTP 465 - fee too low"}, "invalid", "failed"),
    ],
)
def test_services_service_error_flag_decides(
    storage: StorageProvider, services: Services, result: dict[str, Any], req_status: str, tx_status: str
) -> None:
    _, tx_id, _ = _process(storage, delayed=True)
    monitor = Monitor(MonitorOptions(chain="test", storage=storage, services=services))

    with patch.object(Services, "post_beef", autospec=True, side_effect=_post([result], [])):
        TaskSendWaiting(monitor, 1, 0).run_task()

    assert _req(storage)["status"] == req_status
    assert _tx_status(storage, tx_id) == tx_status
