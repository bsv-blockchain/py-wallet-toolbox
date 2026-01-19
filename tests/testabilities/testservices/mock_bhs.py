"""Mock Block Header Service (BHS) for testing.

This module provides a mock BHS that can be configured to return
specific merkle root verification responses.

Reference: go-wallet-toolbox/pkg/internal/testabilities/testservices/
"""

from dataclasses import dataclass
from threading import Lock
from typing import Any

# Merkle root verification status constants
BHSMerkleRootConfirmed = "confirmed"
BHSMerkleRootNotFound = "not_found"
BHSMerkleRootInvalid = "invalid"


@dataclass
class MerkleRootResponse:
    """Configured response for a merkle root verification request."""

    height: int
    merkle_root: str
    status: str = BHSMerkleRootConfirmed


class MockBHS:
    """Mock Block Header Service for testing.

    This mock BHS allows configuring specific responses for merkle root
    verification requests, useful for testing BEEF validation.
    """

    def __init__(self):
        """Initialize MockBHS."""
        self._responses: dict[tuple[int, str], MerkleRootResponse] = {}
        self._lock = Lock()

    def on_merkle_root_verify_response(
        self,
        height: int,
        merkle_root: str,
        status: str = BHSMerkleRootConfirmed,
    ) -> "MockBHS":
        """Configure a response for a specific height/merkle_root query.

        Args:
            height: Block height
            merkle_root: Merkle root hex string
            status: Status to return (BHSMerkleRootConfirmed, etc.)

        Returns:
            self for chaining
        """
        with self._lock:
            key = (height, merkle_root)
            self._responses[key] = MerkleRootResponse(
                height=height,
                merkle_root=merkle_root,
                status=status,
            )
        return self

    async def verify_merkle_root(self, height: int, merkle_root: str) -> dict[str, Any]:
        """Verify a merkle root at a given height.

        Args:
            height: Block height
            merkle_root: Merkle root hex string

        Returns:
            dict: Verification result with status
        """
        with self._lock:
            key = (height, merkle_root)
            response = self._responses.get(key)

        if response is None:
            # Default: not found
            return {
                "height": height,
                "merkleRoot": merkle_root,
                "status": BHSMerkleRootNotFound,
                "valid": False,
            }

        return {
            "height": height,
            "merkleRoot": merkle_root,
            "status": response.status,
            "valid": response.status == BHSMerkleRootConfirmed,
        }

    async def get_header_for_height(self, height: int) -> dict[str, Any] | None:
        """Get block header for a specific height.

        Args:
            height: Block height

        Returns:
            dict: Block header info or None
        """
        # Check if we have any response configured for this height
        with self._lock:
            for (h, _), response in self._responses.items():
                if h == height:
                    return {
                        "height": height,
                        "merkleRoot": response.merkle_root,
                        "hash": f"mock-block-hash-{height}",
                        "version": 536870912,
                        "time": 1700000000 + height,
                        "nonce": 12345,
                        "bits": "1d00ffff",
                    }
        return None

    async def get_current_height(self) -> int:
        """Get the current chain height.

        Returns:
            int: Current height (mock value)
        """
        # Return the highest configured height, or a default
        with self._lock:
            if self._responses:
                return max(h for (h, _) in self._responses)
        return 800000  # Default mock height

    def clear(self) -> None:
        """Clear all configured responses."""
        with self._lock:
            self._responses.clear()
