"""Helpers for interacting with wallet services in the Go-port examples."""

from __future__ import annotations

from typing import Any

from bsv.merkle_path import MerklePath as PyMerklePath
from bsv.transaction.beef import BEEF_V2, Beef
from bsv.transaction.beef_builder import merge_bump, merge_raw_tx
from bsv.transaction.beef_serialize import to_binary_atomic
from bsv_wallet_toolbox.services import Services
from bsv_wallet_toolbox.utils.merkle_path_utils import convert_proof_to_merkle_path


def normalize_chain(network: str) -> str:
    """Map toolbox environment network names to Services chain names."""
    normalized = (network or "").lower()
    if normalized in {"main", "mainnet", "livenet"}:
        return "main"
    return "test"


def create_services(network: str) -> Services:
    """Create a Services instance for the provided toolbox environment network."""
    chain = normalize_chain(network)
    return Services(chain)


def build_atomic_beef_for_txid(services: Services, txid: str) -> bytes:
    """Fetch raw tx + merkle path for txid and return Atomic BEEF bytes."""
    raw_hex = services.get_raw_tx(txid)
    if not raw_hex:
        raise RuntimeError(f"Failed to fetch raw transaction for txid '{txid}'")

    beef = Beef(version=BEEF_V2)

    merkle_result = services.get_merkle_path_for_transaction(txid)
    merkle_path = _convert_merkle_result(txid, merkle_result)
    bump_index = merge_bump(beef, merkle_path) if merkle_path else None

    merge_raw_tx(beef, bytes.fromhex(raw_hex), bump_index)
    return to_binary_atomic(beef, txid)


def _convert_merkle_result(txid: str, result: dict[str, Any]) -> PyMerklePath | None:
    """Convert services.get_merkle_path_for_transaction result into MerklePath."""
    if not isinstance(result, dict):
        return None

    proof = result.get("merklePath") or {}
    if not isinstance(proof, dict):
        return None

    # WhatsOnChain returns blockHeight/path which already matches py-sdk expectations
    if "blockHeight" in proof and "path" in proof:
        return PyMerklePath(proof["blockHeight"], proof["path"])

    nodes = proof.get("nodes")
    index = proof.get("index")
    height = proof.get("height")

    header = result.get("header")
    if height is None and isinstance(header, dict):
        height = header.get("height")

    if nodes is None or index is None or height is None:
        return None

    tsc_proof = {"height": height, "index": index, "nodes": nodes}
    mp_dict = convert_proof_to_merkle_path(txid, tsc_proof)
    return PyMerklePath(mp_dict["blockHeight"], mp_dict["path"])

