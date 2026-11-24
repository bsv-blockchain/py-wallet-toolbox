"""listOutputs honours BRC-100 ``include`` and returns one BEEF (parity report rank 26).

``include: 'locking scripts' | 'entire transactions'`` was ignored (storage only read internal flags), and
the BEEF was rawTx / BEEF fragments concatenated byte by byte, which no SDK can parse. TS merges every
output's BEEF into one Beef and returns ``beef.toBinary()`` (listOutputsKnex.ts).
"""

from __future__ import annotations

from bsv.transaction.beef import parse_beef

from bsv_wallet_toolbox import Wallet
from tests.integration.test_atomic_beef_results import storage, wallet  # pytest fixtures
from tests.testabilities.tsgenerated import PARENT_BEEF_TXID


def test_include_entire_transactions_returns_one_beef(wallet: Wallet) -> None:
    r = wallet.list_outputs({"basket": "default", "include": "entire transactions"})

    assert r["outputs"]
    beef = parse_beef(bytes(r["BEEF"]))
    assert PARENT_BEEF_TXID in beef.txs
    assert beef.find_transaction(PARENT_BEEF_TXID).tx_obj.txid() == PARENT_BEEF_TXID
    assert beef.is_valid(allow_txid_only=False)


def test_include_locking_scripts(wallet: Wallet) -> None:
    r = wallet.list_outputs({"basket": "default", "include": "locking scripts"})

    assert r["outputs"]
    assert all(o.get("lockingScript") for o in r["outputs"])
    assert "BEEF" not in r


def test_no_include_returns_neither(wallet: Wallet) -> None:
    r = wallet.list_outputs({"basket": "default"})

    assert r["outputs"]
    assert not any(o.get("lockingScript") for o in r["outputs"])
    assert "BEEF" not in r


def test_storage_beef_is_one_parsable_beef(wallet: Wallet, storage) -> None:
    r = storage.list_outputs(storage.auth, {"basket": "default", "includeTransactions": True})

    beef = parse_beef(bytes(r["BEEF"]))
    assert PARENT_BEEF_TXID in beef.txs
    assert beef.is_valid(allow_txid_only=False)
