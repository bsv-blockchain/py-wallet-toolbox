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


def test_known_txids_do_not_drop_the_listed_output_tx(wallet: Wallet, storage) -> None:
    r = storage.list_outputs(
        storage.auth, {"basket": "default", "includeTransactions": True, "knownTxids": [PARENT_BEEF_TXID]}
    )

    btx = parse_beef(bytes(r["BEEF"])).find_transaction(PARENT_BEEF_TXID)
    assert btx is not None and btx.data_format != 2


def test_listed_parent_stays_whole_when_a_listed_child_comes_first(storage) -> None:
    """Building the child's BEEF puts a known parent in txid-only; the parent is listed too, so it must be whole."""
    from bsv.transaction.beef import parse_beef_ex

    from tests.testabilities.tsgenerated import parent_transaction_atomic_beef

    full, child_txid, child = parse_beef_ex(parent_transaction_atomic_beef())
    parent_txid = next(t for t in full.txs if t != child_txid)
    bump = full.bumps[full.txs[parent_txid].bump_index]
    user_id = storage.auth["userId"]
    basket_id = storage.find_output_baskets({"partial": {"userId": user_id, "name": "default"}})[0]["basketId"]
    proven_id = storage.insert_proven_tx(
        {
            "txid": parent_txid,
            "height": bump.block_height,
            "index": 0,
            "merklePath": bump.to_binary(),
            "rawTx": full.txs[parent_txid].tx_obj.serialize(),
            "blockHash": "00" * 32,
            "merkleRoot": bump.compute_root(),
        }
    )
    # The child's req has no inputBEEF, so its parent comes from the knownTxids shortcut, not from a stored BEEF.
    storage.insert_proven_tx_req({"txid": child_txid, "status": "unmined", "rawTx": child.serialize()})
    for txid, status, extra in ((child_txid, "unproven", {}), (parent_txid, "completed", {"provenTxId": proven_id})):
        tx_id = storage.insert_transaction(
            {
                "userId": user_id,
                "txid": txid,
                "status": status,
                "reference": txid[:12],
                "isOutgoing": False,
                "satoshis": 0,
                "description": "listed",
                **extra,
            }
        )
        storage.insert_output(
            {
                "transactionId": tx_id,
                "userId": user_id,
                "basketId": basket_id,
                "txid": txid,
                "vout": 0,
                "satoshis": 1000,
                "spendable": True,
                "change": True,
                "providedBy": "storage",
                "purpose": "change",
                "type": "P2PKH",
            }
        )

    r = storage.list_outputs(
        storage.auth, {"basket": "default", "includeTransactions": True, "knownTxids": [parent_txid]}
    )

    assert [o["outpoint"].split(".")[0] for o in r["outputs"]][:2] == [child_txid, parent_txid]
    btx = parse_beef(bytes(r["BEEF"])).find_transaction(parent_txid)
    assert btx is not None and btx.data_format != 2
