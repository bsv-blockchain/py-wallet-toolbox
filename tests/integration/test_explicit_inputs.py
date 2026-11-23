"""createAction with caller-supplied inputs (parity report rank 18).

Storage called ``vargs.get`` on its normalized args object and raised AttributeError, ``'txid.vout'``
outpoints were rejected, the signer looked the input's source transaction up with a Beef method that
does not exist, and inputs were not validated (TS validateCreateActionInput).
"""

from __future__ import annotations

from typing import Any

import pytest
from bsv.keys import PrivateKey, PublicKey
from bsv.script import P2PKH
from bsv.transaction.beef import parse_beef_ex
from bsv.wallet import Counterparty, CounterpartyType, KeyDeriver, Protocol

from bsv_wallet_toolbox import Wallet
from bsv_wallet_toolbox.errors import InvalidParameterError
from tests.integration.test_atomic_beef_results import assert_atomic_beef, stored
from tests.integration.test_beef_spv import FakeServices, atomic_beef, chain, internalize_args
from tests.testabilities.testservices import create_in_memory_storage_provider
from tests.testabilities.testusers import ALICE
from tests.testabilities.tsgenerated import PARENT_BEEF_TXID
from tests.testabilities.tsgenerated.beef_to_internalize import SENDER_IDENTITY_KEY

OUT = {"satoshis": 42, "lockingScript": "76a914" + "00" * 20 + "88ac", "outputDescription": "pay fred"}


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
    """ALICE's wallet: the fixture's output 0 in a 'received' basket (caller-spent), and no change."""
    kd = KeyDeriver(PrivateKey(bytes.fromhex(ALICE.priv_key)))
    w = Wallet(chain="test", key_deriver=kd, storage_provider=storage, services=FakeServices(chain()))
    assert w.internalize_action(internalize_args(atomic_beef()))["accepted"]
    # Python stores P2PKH basket insertions as change; createAction only accepts non-change user inputs.
    for o in storage.find_outputs({"partial": {"txid": PARENT_BEEF_TXID, "vout": 0}}):
        storage.update_output(o["outputId"], {"change": False})
    return w


def spend_args(**input_fields: Any) -> dict[str, Any]:
    inp = {"outpoint": f"{PARENT_BEEF_TXID}.0", "inputDescription": "received output", **input_fields}
    return {
        "description": "spend received",
        "inputs": [inp],
        "inputBEEF": list(atomic_beef()),
        "outputs": [OUT],
        "options": {"randomizeOutputs": False},
    }


def unlock(signable_tx: list[int]) -> str:
    """The caller's own unlocking script for input 0 (BRC-29 key of the received output)."""
    _, _, tx = parse_beef_ex(bytes(signable_tx))  # subject with its inputs linked to their source txs
    source = tx.inputs[0].source_transaction.outputs[tx.inputs[0].source_output_index]
    tx.inputs[0].locking_script, tx.inputs[0].satoshis = source.locking_script, source.satoshis
    kd = KeyDeriver(PrivateKey(bytes.fromhex(ALICE.priv_key)))
    key = kd.derive_private_key(
        Protocol(2, "3241645161d8"),
        "Pr== Su==",
        Counterparty(CounterpartyType.OTHER, PublicKey(SENDER_IDENTITY_KEY)),
    )
    return P2PKH().unlock(key).sign(tx, 0).hex()


def test_create_and_sign_with_explicit_input(wallet: Wallet, storage) -> None:
    signable = wallet.create_action(spend_args(unlockingScriptLength=108))["signableTransaction"]

    # The signable tx carries the input's source transaction from inputBEEF.
    beef, _, tx = parse_beef_ex(bytes(signable["tx"]))
    assert tx.inputs[0].source_txid == PARENT_BEEF_TXID
    assert beef.find_transaction(PARENT_BEEF_TXID) is not None

    r = wallet.sign_action(
        {"reference": signable["reference"], "spends": {0: {"unlockingScript": unlock(signable["tx"])}}}
    )

    assert_atomic_beef(r["tx"], r["txid"])
    assert stored(storage, r["txid"])[0]["status"] != "unsigned"


@pytest.mark.parametrize(
    ("fields", "name"),
    [
        ({}, "unlockingScript"),
        ({"unlockingScript": "00" * 10, "unlockingScriptLength": 11}, "unlockingScriptLength"),
        ({"unlockingScript": "0x51"}, "unlockingScript"),
        ({"unlockingScriptLength": 108, "inputDescription": "abc"}, "inputDescription"),
    ],
)
def test_invalid_input_is_rejected(wallet: Wallet, storage, fields: dict[str, Any], name: str) -> None:
    args = spend_args(**fields)
    if "inputDescription" in fields:
        args["inputs"][0]["inputDescription"] = fields["inputDescription"]

    with pytest.raises(InvalidParameterError, match=name):
        wallet.create_action(args)
    # Rejected before storage allocated anything.
    assert storage.find_transactions({"partial": {"status": "unsigned"}}) == []
