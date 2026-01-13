"""Merkle path conversion utilities.

Convert TSC (Transaction Status Chain) proof format to MerklePath format.

Reference: toolbox/ts-wallet-toolbox/src/utility/tscProofToMerklePath.ts
"""

from __future__ import annotations

import json
from typing import Any, TypedDict


class TscMerkleProofApi(TypedDict, total=False):
    """TSC Merkle proof API format."""

    height: int
    index: int
    nodes: list[str]


class MerkleLeaf(TypedDict, total=False):
    """Single merkle tree leaf."""

    offset: int
    hash_str: str | None
    txid: bool
    duplicate: bool


def convert_proof_to_merkle_path(txid: str, proof: TscMerkleProofApi) -> dict[str, Any]:
    """Convert TSC Merkle proof to MerklePath format.

    Transforms proof nodes into merkle tree structure for py-sdk MerklePath.

    Args:
        txid: Transaction ID being proved
        proof: TSC proof with height, index, and nodes

    Returns:
        Dictionary compatible with bsv.merkle_path.MerklePath initialization

    Reference: toolbox/ts-wallet-toolbox/src/utility/tscProofToMerklePath.ts:9-48
    """
    block_height = proof["height"]
    tree_height = len(proof["nodes"])

    # Initialize path levels
    path: list[list[MerkleLeaf]] = [[] for _ in range(tree_height)]

    index = proof["index"]

    for level in range(tree_height):
        node = proof["nodes"][level]
        is_odd = index % 2 == 1
        offset = index - 1 if is_odd else index + 1

        leaf: MerkleLeaf = {"offset": offset}

        # Check if node is duplicate or actual hash
        if node == "*" or (level == 0 and node == txid):
            leaf["duplicate"] = True
        else:
            leaf["hash_str"] = node

        path[level].append(leaf)

        # At level 0, add txid leaf
        if level == 0:
            txid_leaf: MerkleLeaf = {
                "offset": proof["index"],
                "hash_str": txid,
                "txid": True,
            }
            if is_odd:
                path[0].append(txid_leaf)
            else:
                path[0].insert(0, txid_leaf)

        # Move to next level (divide index by 2 with bit shift)
        index = index >> 1

    return {"blockHeight": block_height, "path": path}


def normalize_merkle_path_value(
    txid: str, merkle_path_value: Any, *, block_height: int | None = None
) -> dict[str, Any] | None:
    """Normalize various merklePath representations into wallet-toolbox MerklePath dict.

    Supported inputs:
    - Already-normalized dict: {"blockHeight": int, "path": list}
    - JSON string containing a dict/list
    - TSC-like dict: {"index": int, "nodes": [hex or '*', ...], ("height" optional)}

    Returns:
        dict compatible with bsv.merkle_path.MerklePath initialization:
          {"blockHeight": int, "path": [...]}
        or None if it cannot be normalized.
    """
    mp: Any = merkle_path_value

    # JSON string → object
    if isinstance(mp, str):
        s = mp.strip()
        if s.startswith(("{", "[")):
            try:
                mp = json.loads(s)
            except Exception:
                return None
        else:
            return None

    # Already-normalized
    if isinstance(mp, dict) and isinstance(mp.get("blockHeight"), int) and isinstance(mp.get("path"), list):
        return mp

    # TSC-like: {"nodes": [...], "index": n, "height": h?}
    if isinstance(mp, dict) and isinstance(mp.get("nodes"), list):
        height_val = mp.get("height", None)
        height = int(height_val) if isinstance(height_val, int) else int(block_height or 0)
        if height <= 0:
            return None
        proof: TscMerkleProofApi = {
            "height": height,
            "index": int(mp.get("index", 0) or 0),
            "nodes": mp.get("nodes") or [],
        }
        return convert_proof_to_merkle_path(txid, proof)

    return None
