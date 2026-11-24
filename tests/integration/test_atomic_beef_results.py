"""createAction / signAction return AtomicBEEF, and signAction stores its tx (parity report rank 11 and rank 3).

BRC-100 and TS return ``tx`` as AtomicBEEF (``beef.toBinaryAtomic(txid)``); Python returned the raw tx,
which TS internalizeAction, payment-express and 402-pay cannot read. signAction's merged args lacked
isNewTx and the other flags, so storage returned early: the signed tx was neither stored nor sent and
its inputs stayed locked. ``returnTXIDOnly`` was read as ``returnTxidOnly``.
"""

from __future__ import annotations

from typing import Any

import pytest
from bsv.keys import PrivateKey
from bsv.transaction.beef import BEEF_V2, parse_beef_ex
from bsv.wallet import KeyDeriver

from bsv_wallet_toolbox import Wallet
from tests.integration.test_beef_spv import FakeServices, atomic_beef, chain, internalize_args
from tests.testabilities.testservices import create_in_memory_storage_provider
from tests.testabilities.testusers import ALICE
from tests.testabilities.tsgenerated import PARENT_BEEF_TXID

ATOMIC_PREFIX = bytes.fromhex("01010101")


@pytest.fixture
def storage():
    sp, cleanup = create_in_memory_storage_provider(chain="testnet")
    user_id = sp.find_or_insert_user(ALICE.identity_key())["user"]["userId"]
    sp.auth = {"identityKey": ALICE.identity_key(), "userId": user_id}
    sp.configure_basket(sp.auth, {"name": "default", "numberOfDesiredUTXOs": 1, "minimumDesiredUTXOValue": 1000})
    sp.set_services(FakeServices(chain()))
    yield sp
    cleanup()


@pytest.fixture
def wallet(storage) -> Wallet:
    """ALICE's wallet holding the received fixture payment as its only change output."""
    kd = KeyDeriver(PrivateKey(bytes.fromhex(ALICE.priv_key)))
    w = Wallet(chain="test", key_deriver=kd, storage_provider=storage, services=FakeServices(chain()))
    assert w.internalize_action(internalize_args(atomic_beef(), protocol="wallet payment"))["accepted"]
    return w


def create_args(**options: Any) -> dict[str, Any]:
    return {
        "description": "pay out",
        "outputs": [{"satoshis": 42, "lockingScript": "76a914" + "00" * 20 + "88ac", "outputDescription": "pay fred"}],
        "options": {"randomizeOutputs": False, **options},
    }


def assert_atomic_beef(tx: list[int], txid: str) -> None:
    data = bytes(tx)
    assert data[:4] == ATOMIC_PREFIX
    beef, subject, subject_tx = parse_beef_ex(data)
    assert subject == txid
    assert beef.version == BEEF_V2
    assert subject_tx.txid() == txid
    assert beef.find_transaction(PARENT_BEEF_TXID) is not None


def stored(storage, txid: str) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    txs = storage.find_transactions({"partial": {"txid": txid}})
    reqs = storage.find_proven_tx_reqs({"partial": {"txid": txid}})
    assert len(txs) == 1
    return txs[0], reqs


def test_create_action_returns_atomic_beef(wallet: Wallet) -> None:
    r = wallet.create_action(create_args(noSend=True))

    assert_atomic_beef(r["tx"], r["txid"])


def test_create_action_return_txid_only(wallet: Wallet) -> None:
    r = wallet.create_action(create_args(noSend=True, returnTXIDOnly=True))

    assert r["txid"]
    assert "tx" not in r


def test_signable_transaction_is_atomic_beef(wallet: Wallet) -> None:
    r = wallet.create_action(create_args(signAndProcess=False))

    data = bytes(r["signableTransaction"]["tx"])
    beef, subject, _ = parse_beef_ex(data)
    assert data[:4] == ATOMIC_PREFIX
    assert beef.version == BEEF_V2
    assert beef.find_transaction(subject) is not None
    assert beef.find_transaction(PARENT_BEEF_TXID) is not None


def test_sign_action_returns_atomic_beef_and_stores_the_tx(wallet: Wallet, storage) -> None:
    signable = wallet.create_action(create_args(signAndProcess=False))["signableTransaction"]

    r = wallet.sign_action({"reference": signable["reference"], "spends": {}})

    assert_atomic_beef(r["tx"], r["txid"])
    tx, reqs = stored(storage, r["txid"])
    # acceptDelayedBroadcast defaults to true: the req waits for TaskSendWaiting.
    assert tx["status"] != "unsigned"
    assert [q["status"] for q in reqs] == ["unsent"]


def test_sign_action_inherits_create_action_options(wallet: Wallet, storage) -> None:
    signable = wallet.create_action(create_args(signAndProcess=False, noSend=True, returnTXIDOnly=True))[
        "signableTransaction"
    ]

    r = wallet.sign_action({"reference": signable["reference"], "spends": {}})

    assert "tx" not in r
    tx, reqs = stored(storage, r["txid"])
    assert tx["status"] == "nosend"
    assert [q["status"] for q in reqs] == ["nosend"]


def test_sign_action_options_override_create_action_options(wallet: Wallet, storage) -> None:
    signable = wallet.create_action(create_args(signAndProcess=False, returnTXIDOnly=True))["signableTransaction"]

    r = wallet.sign_action(
        {"reference": signable["reference"], "spends": {}, "options": {"returnTXIDOnly": False, "noSend": True}}
    )

    assert_atomic_beef(r["tx"], r["txid"])
    assert stored(storage, r["txid"])[0]["status"] == "nosend"


def test_verify_returned_txid_only_atomic_beef_accepts_byte_list(wallet: Wallet) -> None:
    """Wallet results carry tx as list[int]; txid-only ancestors must still be filled in from wallet.beef."""
    full, subject, _ = parse_beef_ex(atomic_beef())
    wallet.beef = full
    parent = next(t for t in full.txs if t != subject)
    trimmed, _, _ = parse_beef_ex(atomic_beef())
    trimmed.make_txid_only(parent)

    r = wallet.verify_returned_txid_only_atomic_beef(list(trimmed.to_binary_atomic(subject)))

    assert isinstance(r, list)
    assert parse_beef_ex(bytes(r))[0].find_transaction(parent).data_format != 2
