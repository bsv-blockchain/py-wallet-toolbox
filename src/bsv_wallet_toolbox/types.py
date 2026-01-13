"""Type definitions for wallet toolbox.

Reference: wallet-toolbox/src/sdk/types/
"""

from typing import TypedDict


class TscMerkleProofApi(TypedDict):
    """TSC merkle proof format.

    Reference: wallet-toolbox/src/sdk/types/
    """

    index: int
    """Position in the merkle tree."""
    height: int
    """Block height."""
    nodes: list[str]
    """Merkle path nodes (hex strings)."""
