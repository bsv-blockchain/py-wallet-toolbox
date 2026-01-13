"""Merkle path utilities for TSC proof conversion.

Reference: wallet-toolbox/src/services/Services.ts
"""

from __future__ import annotations

import hashlib
from typing import Any, TypedDict


class TscMerkleProofApi(TypedDict):
    """TSC merkle proof format."""

    index: int
    height: int
    nodes: list[str]


class MerklePath:
    """Simple merkle path for root computation.

    Represents a merkle proof path that can compute the merkle root
    from a transaction ID.
    """

    def __init__(self, index: int, nodes: list[str], height: int | None = None):
        """Initialize merkle path.

        Args:
            index: Position in the merkle tree
            nodes: List of sibling hashes (hex strings)
            height: Optional block height
        """
        self.index = index
        self.nodes = nodes
        self.height = height

    def compute_root(self, txid: str) -> str:
        """Compute merkle root from transaction ID.

        Args:
            txid: Transaction ID (hex string)

        Returns:
            Computed merkle root (hex string)
        """
        # Convert txid from hex to bytes (reverse for bitcoin endianness)
        current = bytes.fromhex(txid)[::-1]

        # Position in tree
        pos = self.index

        # Traverse up the tree
        for node_hex in self.nodes:
            node = bytes.fromhex(node_hex)[::-1]

            # Determine if current is left or right child
            if pos % 2 == 0:
                # Current is left child
                combined = current + node
            else:
                # Current is right child
                combined = node + current

            # Double SHA256
            current = hashlib.sha256(hashlib.sha256(combined).digest()).digest()

            # Move up to parent
            pos = pos // 2

        # Return as hex (reverse back to standard bitcoin format)
        return current[::-1].hex()


def convert_proof_to_merkle_path(txid: str, proof: TscMerkleProofApi | dict[str, Any]) -> MerklePath:
    """Convert TSC merkle proof to MerklePath object.

    Args:
        txid: Transaction ID (hex string) - not used in conversion but kept for API compatibility
        proof: TSC merkle proof with index, height, and nodes

    Returns:
        MerklePath object that can compute the merkle root

    Reference: wallet-toolbox/src/services/Services.ts
    """
    return MerklePath(
        index=proof["index"],
        nodes=proof["nodes"],
        height=proof.get("height"),
    )
