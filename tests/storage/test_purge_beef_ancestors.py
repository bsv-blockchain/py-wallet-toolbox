"""purgeSpent keeps what a UTXO's BEEF needs; getBeef checks stored proofs (parity report rank 114a, 114b).

purgeSpent protected only the UTXO's own txid, so a spent, completed parent was deleted with its
ProvenTx (an orphan once the transaction row is gone) and the UTXO's BEEF could no longer be built
(TS purgeData.ts protects every txid in each UTXO's BEEF). getBeefForTransaction had no chainTracker /
skipInvalidProofs, so it returned stored proofs whose root the chain does not know.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from bsv.transaction.beef import parse_beef_ex
from sqlalchemy import update

from bsv_wallet_toolbox.errors import WalletError
from bsv_wallet_toolbox.storage.db import create_engine_from_url, session_scope
from bsv_wallet_toolbox.storage.models import Base
from bsv_wallet_toolbox.storage.models import Transaction as TransactionModel
from bsv_wallet_toolbox.storage.provider import StorageProvider
from tests.testabilities.tsgenerated import (
    BEEF_TO_INTERNALIZE_HEIGHT,
    BEEF_TO_INTERNALIZE_MERKLE_ROOT,
    PARENT_BEEF_TXID,
    parent_transaction_atomic_beef,
)

BEEF, _, CHILD = parse_beef_ex(parent_transaction_atomic_beef())
PARENT = next(t for t in BEEF.txs if t != PARENT_BEEF_TXID)  # proven, spent by CHILD


class Tracker:
    def __init__(self, roots: dict[int, str]) -> None:
        self.roots = roots

    async def is_valid_root_for_height(self, root: str, height: int) -> bool:
        return self.roots.get(height) == root


@pytest.fixture
def storage() -> StorageProvider:
    """PARENT: completed, proven, its only output spent by CHILD. CHILD: unproven, holds a UTXO."""
    engine = create_engine_from_url("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    sp = StorageProvider(engine=engine, chain="test", storage_identity_key="purge-ancestors")
    sp.make_available()
    user_id = sp.get_or_create_user_id("03" + "e" * 62)

    btx = BEEF.txs[PARENT]
    bump = BEEF.bumps[btx.bump_index]
    proven_tx_id = sp.insert_proven_tx(
        {
            "txid": PARENT,
            "height": bump.block_height,
            "index": 0,
            "merklePath": bump.to_binary(),
            "rawTx": btx.tx_obj.serialize(),
            "blockHash": "00" * 32,
            "merkleRoot": bump.compute_root(),
        }
    )
    parent_id = _tx(sp, user_id, PARENT, "completed", provenTxId=proven_tx_id)
    child_id = _tx(sp, user_id, PARENT_BEEF_TXID, "unproven")
    _output(sp, user_id, parent_id, PARENT, spendable=False, spent_by=child_id)
    _output(sp, user_id, child_id, PARENT_BEEF_TXID, spendable=True, spent_by=None)
    sp.insert_proven_tx_req(
        {"txid": PARENT_BEEF_TXID, "status": "unmined", "rawTx": CHILD.serialize(), "history": "{}", "notify": "{}"}
    )
    old = datetime.now(UTC).replace(tzinfo=None) - timedelta(days=30)
    with session_scope(sp.SessionLocal) as s:
        s.execute(update(TransactionModel).values(updated_at=old))
    return sp


def _tx(sp: StorageProvider, user_id: int, txid: str, status: str, **extra: Any) -> int:
    return sp.insert_transaction(
        {
            "userId": user_id,
            "txid": txid,
            "status": status,
            "reference": txid[:12],
            "isOutgoing": False,
            "satoshis": 0,
            "description": "purge test",
            **extra,
        }
    )


def _output(sp: StorageProvider, user_id: int, tx_id: int, txid: str, *, spendable: bool, spent_by: int | None) -> int:
    return sp.insert_output(
        {
            "transactionId": tx_id,
            "userId": user_id,
            "txid": txid,
            "vout": 0,
            "satoshis": 1000,
            "spendable": spendable,
            "spentBy": spent_by,
            "change": True,
            "providedBy": "storage",
            "purpose": "change",
            "type": "P2PKH",
        }
    )


def _beef_txids(sp: StorageProvider, txid: str) -> set[str]:
    return set(parse_beef_ex(sp.get_beef_for_transaction(txid, {"ignoreServices": True}))[0].txs)


def test_purge_spent_keeps_beef_ancestors_of_utxos(storage: StorageProvider) -> None:
    assert _beef_txids(storage, PARENT_BEEF_TXID) == {PARENT, PARENT_BEEF_TXID}

    storage.purge_data({"purgeSpent": True, "purgeSpentAge": 1})

    assert _beef_txids(storage, PARENT_BEEF_TXID) == {PARENT, PARENT_BEEF_TXID}
    assert storage.find_transactions({"partial": {"txid": PARENT}})


def test_purge_spent_still_deletes_unneeded_spent_transactions(storage: StorageProvider) -> None:
    # Once the child is proven itself, the parent is no longer part of any UTXO's BEEF.
    child_bump = BEEF.bumps[BEEF.txs[PARENT].bump_index]
    child_proven = storage.insert_proven_tx(
        {
            "txid": PARENT_BEEF_TXID,
            "height": child_bump.block_height,
            "index": 1,
            "merklePath": child_bump.to_binary(),
            "rawTx": CHILD.serialize(),
            "blockHash": "00" * 32,
            "merkleRoot": child_bump.compute_root(),
        }
    )
    storage.update_proven_tx_req(
        storage.find_proven_tx_reqs({"partial": {}})[0]["provenTxReqId"], {"status": "completed"}
    )
    with session_scope(storage.SessionLocal) as s:
        s.execute(
            update(TransactionModel)
            .where(TransactionModel.txid == PARENT_BEEF_TXID)
            .values(proven_tx_id=child_proven, status="completed")
        )

    storage.purge_data({"purgeSpent": True, "purgeSpentAge": 1})

    assert storage.find_transactions({"partial": {"txid": PARENT}}) == []
    assert storage.find_transactions({"partial": {"txid": PARENT_BEEF_TXID}})


def test_get_beef_rejects_proof_unknown_to_chain_tracker(storage: StorageProvider) -> None:
    with pytest.raises(WalletError, match="merkle root"):
        storage.get_beef_for_transaction(PARENT_BEEF_TXID, {"ignoreServices": True, "chainTracker": Tracker({})})


def test_get_beef_skip_invalid_proofs_recurses_past_it(storage: StorageProvider) -> None:
    # The parent's own inputs are not in storage, so recursing past its proof fails on the grandparent.
    with pytest.raises(WalletError, match="not known to storage"):
        storage.get_beef_for_transaction(
            PARENT_BEEF_TXID, {"ignoreServices": True, "chainTracker": Tracker({}), "skipInvalidProofs": True}
        )


def test_get_beef_accepts_proof_known_to_chain_tracker(storage: StorageProvider) -> None:
    tracker = Tracker({BEEF_TO_INTERNALIZE_HEIGHT: BEEF_TO_INTERNALIZE_MERKLE_ROOT})

    beef = parse_beef_ex(
        storage.get_beef_for_transaction(PARENT_BEEF_TXID, {"ignoreServices": True, "chainTracker": tracker})
    )[0]

    assert set(beef.txs) == {PARENT, PARENT_BEEF_TXID}


def _child_output(sp: StorageProvider) -> dict[str, Any]:
    return sp.find_outputs({"partial": {"txid": PARENT_BEEF_TXID}})[0]


def test_purge_failed_then_spent_keeps_ancestors_of_released_outputs(storage: StorageProvider) -> None:
    """purgeFailed releases the outputs a failed tx spent; they are UTXOs again and keep their ancestors."""
    child = _child_output(storage)
    user_id = child["userId"]
    failed_id = _tx(storage, user_id, "f" * 64, "failed")
    storage.update_output(child["outputId"], {"spendable": False, "spentBy": failed_id})
    old = datetime.now(UTC).replace(tzinfo=None) - timedelta(days=30)
    with session_scope(storage.SessionLocal) as s:
        s.execute(update(TransactionModel).values(updated_at=old))

    storage.purge_data({"purgeFailed": True, "purgeFailedAge": 1, "purgeSpent": True, "purgeSpentAge": 1})

    assert _child_output(storage)["spendable"] is True
    assert _beef_txids(storage, PARENT_BEEF_TXID) == {PARENT, PARENT_BEEF_TXID}


def test_purge_spent_is_skipped_when_an_ancestor_is_not_in_storage(storage: StorageProvider) -> None:
    """Without the parent's proof the UTXO's BEEF can't be built, so what it needs is unknown: delete nothing."""
    from bsv_wallet_toolbox.storage.models import ProvenTx

    with session_scope(storage.SessionLocal) as s:
        s.execute(update(TransactionModel).where(TransactionModel.txid == PARENT).values(proven_tx_id=None))
        s.query(ProvenTx).delete()

    r = storage.purge_data({"purgeSpent": True, "purgeSpentAge": 1})

    assert "purgeSpent skipped" in r["log"]
    assert storage.find_transactions({"partial": {"txid": PARENT}})


def test_purge_spent_keeps_a_needed_proof_without_a_transaction_row(storage: StorageProvider) -> None:
    """A proof stored only as a ProvenTx (no transaction row) is still part of the UTXO's BEEF."""
    from bsv_wallet_toolbox.storage.models import Output

    with session_scope(storage.SessionLocal) as s:
        s.query(Output).filter(Output.txid == PARENT).delete()
        s.query(TransactionModel).filter(TransactionModel.txid == PARENT).delete()

    storage.purge_data({"purgeSpent": True, "purgeSpentAge": 1})

    assert _beef_txids(storage, PARENT_BEEF_TXID) == {PARENT, PARENT_BEEF_TXID}
