"""Live ingestor interfaces for blockchain data.

Defines interfaces for streaming and retrieving live blockchain block header data.

Reference: go-wallet-toolbox/pkg/services/chaintracks/models/live_ingestor.go
"""

from __future__ import annotations

from typing import Any, Protocol


class LiveIngestor(Protocol):
    """Interface for streaming and retrieving live blockchain block header data.

    Provides methods for looking up headers by hash and for receiving header events in real-time.
    """

    def start_listening(self, callback: callable) -> None:
        """Start listening for new block headers.

        Args:
            callback: Function to call when new headers are received
        """
        ...

    def stop_listening(self) -> None:
        """Stop listening for new block headers."""
        ...

    def get_header_by_hash(self, block_hash: str) -> dict[str, Any] | None:
        """Get block header by hash.

        Args:
            block_hash: Block hash

        Returns:
            Block header dict or None if not found
        """
        ...

    def get_present_height(self) -> int:
        """Get current blockchain height.

        Returns:
            Current block height
        """
        ...


class NamedLiveIngestor:
    """Associates a human-readable name with a LiveIngestor implementation."""

    def __init__(self, name: str, ingestor: LiveIngestor):
        """Initialize named ingestor.

        Args:
            name: Human-readable name
            ingestor: Live ingestor instance
        """
        self.name = name
        self.ingestor = ingestor
