"""Services.post_beef: failover on 429, BEEF to ARC, TS status classification (parity report rank 32).

A 429 from the first ARC returned at once instead of trying the next provider. ARC got only the raw tx,
so a tx with an unconfirmed parent failed (TS ARC.postBeef sends the BEEF as V1). Every ARC HTTP error was
a service error and a 200 with txStatus REJECTED was a success; TS treats only 408/429/476/5xx (and
rate-limit/timeout details) as service errors and INVALID/MALFORMED/REJECTED as invalid.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from bsv.script import Script
from bsv.transaction import Transaction, TransactionInput, TransactionOutput
from bsv.transaction.beef import BEEF_V1, parse_beef, parse_beef_ex

from bsv_wallet_toolbox.services import Services
from bsv_wallet_toolbox.services.providers.arc import ARC, ArcConfig
from tests.testabilities.tsgenerated import PARENT_BEEF_TXID, parent_transaction_atomic_beef

ATOMIC_HEX = parent_transaction_atomic_beef().hex()
PARENT = next(t for t in parse_beef_ex(parent_transaction_atomic_beef())[0].txs if t != PARENT_BEEF_TXID)


def _response(status: int, body: dict[str, Any]) -> MagicMock:
    r = MagicMock(status_code=status)
    r.json.return_value = body
    r.text = str(body)
    return r


def _ok(tx_status: str = "SEEN_ON_NETWORK") -> MagicMock:
    return _response(200, {"txid": PARENT_BEEF_TXID, "txStatus": tx_status, "extraInfo": ""})


@pytest.fixture
def services() -> Services:
    s = Services(Services.create_default_options("main"))
    s.arcade = None
    s.bitails = None
    s.arc_taal = ARC("https://taal.example", config=ArcConfig(), name="arcTaal")
    s.arc_gorillapool = ARC("https://gp.example", config=ArcConfig(), name="arcGorillaPool")
    return s


def _post(services: Services, *responses: MagicMock) -> tuple[dict[str, Any], list[tuple[str, str]]]:
    calls: list[tuple[str, str]] = []
    queue = list(responses)

    def post(url: str, json: dict[str, Any], **_: Any) -> MagicMock:
        calls.append((url, json["rawTx"]))
        return queue.pop(0)

    with patch("bsv_wallet_toolbox.services.providers.arc.requests.post", side_effect=post):
        return services.post_beef(ATOMIC_HEX), calls


def test_rate_limited_arc_fails_over_to_the_next(services: Services) -> None:
    r, calls = _post(services, _response(429, {"detail": "Too Many Requests"}), _ok())

    assert r["accepted"] is True
    assert [u.split("/")[2] for u, _ in calls] == ["taal.example", "gp.example"]


def test_arc_gets_the_beef_as_v1_with_its_parents(services: Services) -> None:
    _, calls = _post(services, _ok())

    beef = parse_beef(bytes.fromhex(calls[0][1]))
    assert beef.version == BEEF_V1
    assert set(beef.txs) == {PARENT, PARENT_BEEF_TXID}


@pytest.mark.parametrize(
    ("responses", "service_error"),
    [
        ((_response(503, {"detail": "unavailable"}), _response(503, {"detail": "unavailable"})), True),
        ((_response(429, {}), _response(408, {})), True),
        ((_response(461, {"detail": "mandatory-script-verify-flag-failed"}),) * 2, False),
        # A bad key or URL says nothing about the tx (stricter than TS, which would fail the tx).
        ((_response(401, {}), _response(403, {})), True),
        ((_ok("REJECTED"), _ok("REJECTED")), False),
    ],
)
def test_failure_reports_whether_only_services_failed(
    services: Services, responses: tuple[MagicMock, ...], service_error: bool
) -> None:
    r, _ = _post(services, *responses)

    assert r["accepted"] is False
    assert r["serviceError"] is service_error


def test_mined_counts_as_accepted(services: Services) -> None:
    r, _ = _post(services, _ok("MINED"))

    assert r["accepted"] is True


def test_arc_gets_the_atomic_subject_as_the_last_tx(services: Services) -> None:
    """An AtomicBEEF may carry txs after its subject; ARC answers for the last tx it gets."""
    full, _, _ = parse_beef_ex(parent_transaction_atomic_beef())
    extra = Transaction(
        tx_inputs=[TransactionInput(source_txid=PARENT_BEEF_TXID, source_output_index=0, unlocking_script=Script())],
        tx_outputs=[TransactionOutput(locking_script=Script("6a"), satoshis=0)],
    )
    full.merge_transaction(extra)
    atomic = b"\x01\x01\x01\x01" + bytes.fromhex(PARENT_BEEF_TXID)[::-1] + full.to_binary()
    calls: list[str] = []

    def post(url: str, json: dict[str, Any], **_: Any) -> MagicMock:
        calls.append(json["rawTx"])
        return _ok()

    with patch("bsv_wallet_toolbox.services.providers.arc.requests.post", side_effect=post):
        assert services.post_beef(atomic.hex())["accepted"] is True

    sent = parse_beef(bytes.fromhex(calls[0]))
    assert list(sent.txs)[-1] == PARENT_BEEF_TXID
    assert extra.txid() not in sent.txs
