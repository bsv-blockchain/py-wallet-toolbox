"""Bitails postBeef / getMerklePath return what TS returns (parity report rank 41).

post_raws put the Beef object into the JSON body (TypeError, so every broadcast failed), Services read the
PostBeefResult object as a dict (so Bitails never succeeded), and get_merkle_path looked for a
``merklePath`` key in Bitails' TSC proof ({index, txOrId, target, nodes}) and returned an object that
Services.get_merkle_path could not read.
"""

from __future__ import annotations

import hashlib
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from bsv.merkle_path import MerklePath
from bsv.transaction.beef import parse_beef_ex

from bsv_wallet_toolbox.services import Services
from bsv_wallet_toolbox.services.providers.bitails import Bitails
from tests.testabilities.tsgenerated import PARENT_BEEF_TXID, parent_transaction_atomic_beef

BEEF, _, CHILD = parse_beef_ex(parent_transaction_atomic_beef())
PARENT = next(t for t in BEEF.txs if t != PARENT_BEEF_TXID)


def _response(status: int, body: Any) -> MagicMock:
    r = MagicMock(status_code=status, ok=200 <= status < 300, reason="OK" if status == 200 else "Error")
    r.json.return_value = body
    r.content = b"x"
    r.text = str(body)
    return r


@pytest.fixture
def services() -> Services:
    s = Services(Services.create_default_options("main"))
    s.arcade = s.arc_taal = s.arc_gorillapool = None
    return s


def _post(services: Services, body: Any, status: int = 201) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    sent: list[dict[str, Any]] = []

    def post(url: str, json: dict[str, Any], **_: Any) -> MagicMock:
        sent.append(json)
        return _response(status, body)

    with patch("bsv_wallet_toolbox.services.providers.bitails.requests.post", side_effect=post):
        return services.post_beef(parent_transaction_atomic_beef().hex()), sent


def test_post_beef_sends_the_raws_parents_first(services: Services) -> None:
    r, sent = _post(services, [{"txid": PARENT}, {"txid": PARENT_BEEF_TXID}])

    assert r["accepted"] is True
    assert sent == [{"raws": [BEEF.txs[PARENT].tx_obj.hex(), CHILD.hex()]}]


def test_already_in_mempool_is_success(services: Services) -> None:
    r, _ = _post(
        services,
        [{"txid": PARENT, "error": {"code": -27, "message": "already-in-mempool"}}, {"txid": PARENT_BEEF_TXID}],
    )

    assert r["accepted"] is True


@pytest.mark.parametrize(
    ("body", "status", "expected"),
    [
        # missing-inputs may only mean the parent hasn't reached Bitails: retried, not failed (no confirmDoubleSpend)
        (
            [{"txid": PARENT}, {"txid": PARENT_BEEF_TXID, "error": {"code": -25, "message": "missing-inputs"}}],
            201,
            {"serviceError": True, "doubleSpend": None},
        ),
        (
            [{"txid": PARENT}, {"txid": PARENT_BEEF_TXID, "error": {"code": -26, "message": "bad-txns"}}],
            201,
            {"serviceError": False},
        ),
        ({"message": "upstream down"}, 502, {"serviceError": True}),
    ],
)
def test_failures_are_classified(services: Services, body: Any, status: int, expected: dict[str, Any]) -> None:
    r, _ = _post(services, body, status)

    assert r["accepted"] is False
    assert {k: r.get(k) for k in expected} == expected


def test_get_merkle_path_converts_the_tsc_proof() -> None:
    sibling = "11" * 32
    root = (
        hashlib.sha256(hashlib.sha256(bytes.fromhex(PARENT_BEEF_TXID)[::-1] + bytes.fromhex(sibling)[::-1]).digest())
        .digest()[::-1]
        .hex()
    )
    header = {"height": 800000, "merkleRoot": root, "hash": "22" * 32}
    services = MagicMock()
    services.hash_to_header.return_value = header
    proof = {"index": 0, "txOrId": PARENT_BEEF_TXID, "target": header["hash"], "nodes": [sibling]}

    with patch("bsv_wallet_toolbox.services.providers.bitails.requests.get", return_value=_response(200, proof)):
        r = Bitails("main").get_merkle_path(PARENT_BEEF_TXID, services)

    assert r["name"] == "BitailsTsc"
    assert r["header"] == header
    mp = MerklePath(r["merklePath"]["blockHeight"], r["merklePath"]["path"])
    assert mp.compute_root(PARENT_BEEF_TXID) == root
    services.hash_to_header.assert_called_once_with(header["hash"])


def test_get_merkle_path_not_found_has_no_path() -> None:
    with patch("bsv_wallet_toolbox.services.providers.bitails.requests.get", return_value=_response(404, {})):
        r = Bitails("main").get_merkle_path(PARENT_BEEF_TXID, MagicMock())

    assert "merklePath" not in r
    assert r["notes"][-1]["what"] == "getMerklePathNotFound"


@pytest.mark.parametrize(
    "body",
    [
        # Rows out of order: the error belongs to the parent, not to the subject.
        [{"txid": PARENT_BEEF_TXID}, {"error": {"code": -25, "message": "missing-inputs"}}],
        # Too many rows.
        [{"txid": PARENT}, {"txid": PARENT_BEEF_TXID}, {"txid": PARENT_BEEF_TXID, "error": {"code": -26}}],
        # Not an array: a single row for a batch of two, or a summary object.
        {"txid": PARENT_BEEF_TXID, "error": {"code": -26, "message": "bad-txns"}},
        {"success": True, "txids": [PARENT, PARENT_BEEF_TXID]},
    ],
)
def test_mismatched_rows_are_a_service_error(services: Services, body: Any) -> None:
    r, _ = _post(services, body)

    assert r["accepted"] is False
    assert r["serviceError"] is True
    assert not r.get("doubleSpend")
