"""Merkle path conversion utilities.

Convert TSC (Transaction Status Chain) proof format to MerklePath format.

Reference: toolbox/ts-wallet-toolbox/src/utility/tscProofToMerklePath.ts
"""

from __future__ import annotations

from typing import Any, TypedDict


class TscMerkleProofApi(TypedDict, total=False):
    """TSC Merkle proof API format."""

    height: int
    index: int
    nodes: list[str]


class MerkleLeaf(TypedDict, total=False):
    """Single merkle tree leaf."""

    offset: int
    hash: str | None
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
            leaf["hash"] = node

        path[level].append(leaf)

        # At level 0, add txid leaf
        if level == 0:
            txid_leaf: MerkleLeaf = {
                "offset": proof["index"],
                "hash": txid,
                "txid": True,
            }
            if is_odd:
                path[0].append(txid_leaf)
            else:
                path[0].insert(0, txid_leaf)

        # Move to next level (divide index by 2 with bit shift)
        index = index >> 1

    return {"blockHeight": block_height, "path": path}
