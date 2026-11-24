"""The Wallet keeps a BeefParty of everything storage returned (parity report rank 80, BEEF part).

TS Wallet holds ``new BeefParty([userParty])``, merges createAction's tx and listOutputs' BEEF with
``mergeBeefFromParty(storageParty, ...)``, and with ``autoKnownTxids`` passes ``getKnownTxids()`` to
storage so it can answer with txid-only entries. Python held a plain Beef, did not merge listOutputs'
BEEF, and its merge of createAction's ``list[int]`` tx silently did nothing before bsv-sdk 2.5.0.
"""

from __future__ import annotations

from bsv.transaction.beef import parse_beef
from bsv.transaction.beef_party import BeefParty

from bsv_wallet_toolbox import Wallet
from tests.integration.test_atomic_beef_results import create_args, storage, wallet  # pytest fixtures
from tests.testabilities.tsgenerated import PARENT_BEEF_TXID


def test_wallet_beef_is_a_beef_party_with_the_user_party(wallet: Wallet) -> None:
    assert isinstance(wallet.beef, BeefParty)
    assert wallet.beef.is_party(wallet.user_party)


def test_create_action_tx_is_known_from_storage_party(wallet: Wallet) -> None:
    r = wallet.create_action(create_args(noSend=True))

    known = wallet.beef.get_known_txids_for_party(wallet.storage_party)
    assert r["txid"] in known
    assert r["txid"] in wallet.get_known_txids()


def test_list_outputs_beef_is_merged_and_auto_known_txids_are_sent(wallet: Wallet, storage) -> None:
    r = wallet.list_outputs({"basket": "default", "include": "entire transactions"})
    assert PARENT_BEEF_TXID in wallet.beef.get_known_txids_for_party(wallet.storage_party)
    assert PARENT_BEEF_TXID in parse_beef(bytes(r["BEEF"])).txs

    wallet.auto_known_txids = True
    sent: list[dict] = []
    original = storage.list_outputs

    def spy(auth, args):
        sent.append(args)
        return original(auth, args)

    storage.list_outputs = spy
    r2 = wallet.list_outputs({"basket": "default", "include": "entire transactions"})

    assert PARENT_BEEF_TXID in sent[0]["knownTxids"]
    # The listed output's own tx stays whole (knownTxids only shorten its inputs).
    btx = parse_beef(bytes(r2["BEEF"])).find_transaction(PARENT_BEEF_TXID)
    assert btx is not None and btx.data_format != 2


def test_explicit_empty_known_txids_is_kept(wallet: Wallet, storage) -> None:
    wallet.get_known_txids(["ab" * 32])  # some txid the wallet claims to know
    wallet.auto_known_txids = True
    sent: list[dict] = []
    original = storage.list_outputs

    def spy(auth, args):
        sent.append(args)
        return original(auth, args)

    storage.list_outputs = spy
    wallet.list_outputs({"basket": "default", "include": "entire transactions", "knownTxids": []})
    wallet.list_outputs({"basket": "default", "include": "entire transactions"})

    assert sent[0]["knownTxids"] == []  # an explicit [] asks for whole transactions
    assert "ab" * 32 in sent[1]["knownTxids"]
