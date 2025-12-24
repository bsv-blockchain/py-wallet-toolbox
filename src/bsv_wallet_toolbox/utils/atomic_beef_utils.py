"""AtomicBEEF helpers.

Build AtomicBEEF from rawTx and (optionally) a merkle path. For unmined/mempool
transactions, merkle paths are naturally unavailable; rawTx-only AtomicBEEF is
still useful for internalizeAction flows.
"""

from __future__ import annotations

from typing import Any

from bsv.transaction.beef import BEEF_V2, Beef
from bsv.transaction.beef_builder import merge_bump, merge_raw_tx
from bsv.transaction.beef_serialize import to_binary_atomic

from bsv_wallet_toolbox.utils.raw_tx_utils import RawTxRetryConfig, fetch_raw_tx_with_retry


def try_fetch_merkle_path(services: Any, txid: str) -> dict[str, Any] | None:
    """Best-effort merkle path fetch. Returns None if unavailable/unmined."""
    try:
        merkle_result = services.get_merkle_path_for_transaction(txid)
    except Exception:  # noqa: BLE001
        return None
    if not isinstance(merkle_result, dict):
        return None
    merkle_path = merkle_result.get("merklePath")
    return merkle_path if isinstance(merkle_path, dict) else None


def build_atomic_beef_from_raw_tx(raw_tx_hex: str, txid: str, merkle_path: dict[str, Any] | None = None) -> bytes:
    """Build an AtomicBEEF from rawTx hex plus optional merkle path dict."""
    beef = Beef(version=BEEF_V2)
    bump_index = None
    if merkle_path and "blockHeight" in merkle_path:
        from bsv.merkle_path import MerklePath as PyMerklePath

        bump_path = PyMerklePath(merkle_path["blockHeight"], merkle_path.get("path", []))
        bump_index = merge_bump(beef, bump_path)
    merge_raw_tx(beef, bytes.fromhex(raw_tx_hex), bump_index)
    return to_binary_atomic(beef, txid)


def build_atomic_beef_for_txid(services: Any, txid: str, retry: RawTxRetryConfig | None = None) -> bytes:
    """Fetch rawTx (with retry) and merklePath (best-effort) then build AtomicBEEF."""
    raw_hex = fetch_raw_tx_with_retry(services, txid, retry=retry)
    merkle_path = try_fetch_merkle_path(services, txid)
    return build_atomic_beef_from_raw_tx(raw_hex, txid, merkle_path=merkle_path)


