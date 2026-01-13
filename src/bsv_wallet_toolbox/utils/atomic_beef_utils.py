"""AtomicBEEF helpers.

Build AtomicBEEF from rawTx and (optionally) a merkle path. For unmined/mempool
transactions, merkle paths are naturally unavailable; rawTx-only AtomicBEEF is
still useful for internalizeAction flows.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from bsv.transaction.beef import BEEF_V2, Beef
from bsv.transaction.beef_builder import merge_bump, merge_raw_tx
from bsv.transaction.beef_serialize import to_binary_atomic

from bsv_wallet_toolbox.utils.raw_tx_utils import RawTxRetryConfig, fetch_raw_tx_with_retry


@dataclass(frozen=True)
class AtomicBeefBuildResult:
    """Result wrapper for building AtomicBEEF for internalize flows."""

    atomic_bytes: bytes
    has_merkle_path: bool
    parents_total: int
    parents_with_proof: int


def try_fetch_merkle_path(services: Any, txid: str) -> dict[str, Any] | None:
    """Best-effort merkle path fetch. Returns None if unavailable/unmined."""
    try:
        merkle_result = services.get_merkle_path_for_transaction(txid)
    except Exception:
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


def build_internalize_atomic_beef(
    services: Any,
    tx: Any,
    txid: str,
    *,
    retry: RawTxRetryConfig | None = None,
    max_inputs: int = 16,
    max_depth: int = 4,
    max_txs: int = 64,
) -> AtomicBeefBuildResult:
    """Build AtomicBEEF for internalizeAction with best-effort validation anchoring.

    Strategy:
    - Prefer including parent transactions (inputs) and their merkle proofs when available.
      This can satisfy strict validators even if the subject tx is still in mempool.
    - Fall back to raw-tx-only AtomicBEEF if parents can't be fetched.
    """
    retry = retry or RawTxRetryConfig()

    # 1) Try "parents anchored" build
    try:
        atomic_bytes, parents_total, parents_with_proof = build_atomic_beef_from_tx_with_proven_inputs(
            services,
            tx,
            txid,
            retry=retry,
            max_inputs=max_inputs,
            max_depth=max_depth,
            max_txs=max_txs,
        )
        # Subject merkle path is usually absent for mempool tx; we don't treat that as failure.
        return AtomicBeefBuildResult(
            atomic_bytes=atomic_bytes,
            has_merkle_path=False,
            parents_total=parents_total,
            parents_with_proof=parents_with_proof,
        )
    except Exception:
        pass

    # 2) Fallback: raw tx only (optional subject merkle path if already mined)
    subject_merkle_path = try_fetch_merkle_path(services, txid)
    atomic_bytes = build_atomic_beef_from_raw_tx(tx.serialize().hex(), txid, merkle_path=subject_merkle_path)
    return AtomicBeefBuildResult(
        atomic_bytes=atomic_bytes,
        has_merkle_path=bool(subject_merkle_path),
        parents_total=0,
        parents_with_proof=0,
    )


def build_atomic_beef_from_tx_with_proven_inputs(
    services: Any,
    tx: Any,
    txid: str,
    *,
    retry: RawTxRetryConfig | None = None,
    max_inputs: int = 16,
    max_depth: int = 4,
    max_txs: int = 64,
) -> tuple[bytes, int, int]:
    """Build AtomicBEEF for a (possibly unmined) tx by including proven parents.

    Why:
        Some validators (including go-wallet-toolbox storage) require a BEEF to be
        "valid" even when the subject tx is still in mempool and has no merkle path.
        To make the set verifiable, we include input source transactions (parents)
        and attach merkle paths to them when available. This provides an anchor to
        the proven chain so the subject tx can be validated transitively.

    Notes:
        - If parent merkle paths are unavailable, the returned BEEF may still be rejected.
        - This is best-effort; it won't raise if a parent can't be fetched.
    """
    retry = retry or RawTxRetryConfig()
    beef = Beef(version=BEEF_V2)

    parents_total = 0
    parents_with_proof = 0

    # Strategy note (TS parity / Go server behavior):
    # Storage validates AtomicBEEF via Beef.verify(chaintracker, allowTxidOnly=false).
    # For mempool tx, the subject has no merkle path. To still be "valid", the BEEF must
    # include at least one ancestry chain that anchors to a proven transaction (with merkle path).
    #
    # So we recursively include parents until we reach transactions that have merkle paths, or we
    # hit safety limits (depth / total txs).

    def _enqueue_inputs(t: Any, depth: int) -> list[tuple[str, int]]:
        nxt: list[tuple[str, int]] = []
        for txin in list(getattr(t, "inputs", []) or [])[:max_inputs]:
            parent_txid = getattr(txin, "source_txid", None)
            if isinstance(parent_txid, str) and len(parent_txid) == 64:
                nxt.append((parent_txid, depth))
        return nxt

    visited: set[str] = set()
    queue: list[tuple[str, int]] = _enqueue_inputs(tx, 1)

    while queue and len(visited) < max_txs:
        parent_txid, depth = queue.pop(0)
        if parent_txid in visited:
            continue
        visited.add(parent_txid)
        parents_total += 1

        try:
            raw_hex = fetch_raw_tx_with_retry(services, parent_txid, retry=retry)
        except Exception:
            continue

        bump_index = None
        merkle_path = try_fetch_merkle_path(services, parent_txid)
        if merkle_path and "blockHeight" in merkle_path:
            try:
                from bsv.merkle_path import MerklePath as PyMerklePath

                bump_path = PyMerklePath(merkle_path["blockHeight"], merkle_path.get("path", []))
                bump_index = merge_bump(beef, bump_path)
                parents_with_proof += 1
            except Exception:
                bump_index = None

        try:
            btx = merge_raw_tx(beef, bytes.fromhex(raw_hex), bump_index)
        except Exception:
            continue

        # If this parent is also unmined (no bump), try to expand its parents too.
        # This is essential when the subject spends an unconfirmed output (common in
        # roundtrip E2E: Bob->Alice spends Alice->Bob), and we need to reach a proven ancestor.
        if bump_index is None and depth < max_depth:
            parent_tx_obj = getattr(btx, "tx_obj", None)
            if parent_tx_obj is not None:
                queue.extend(_enqueue_inputs(parent_tx_obj, depth + 1))

    # Finally, merge the subject tx (typically without a bump if unmined)
    merge_raw_tx(beef, tx.serialize(), None)

    return to_binary_atomic(beef, txid), parents_total, parents_with_proof


def build_atomic_beef_for_txid(services: Any, txid: str, retry: RawTxRetryConfig | None = None) -> bytes:
    """Fetch rawTx (with retry) and merklePath (best-effort) then build AtomicBEEF."""
    raw_hex = fetch_raw_tx_with_retry(services, txid, retry=retry)
    merkle_path = try_fetch_merkle_path(services, txid)
    return build_atomic_beef_from_raw_tx(raw_hex, txid, merkle_path=merkle_path)
