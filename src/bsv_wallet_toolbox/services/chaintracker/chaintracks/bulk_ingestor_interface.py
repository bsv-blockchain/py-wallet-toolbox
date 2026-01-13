"""Bulk ingestor interfaces for blockchain data.

Defines interfaces for bulk synchronization of block headers from external sources.

Reference: go-wallet-toolbox/pkg/services/chaintracks/models/bulk_ingestor.go
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Any


class BulkIngestor(ABC):
    """Interface for bulk synchronization of block headers.

    Provides methods for synchronizing block headers within specified height ranges.
    """

    @abstractmethod
    async def synchronize(self, present_height: int, range_to_fetch: Any) -> tuple[list[Any], Callable]:
        """Synchronize bulk headers for the given height range.

        Args:
            present_height: Current blockchain height
            range_to_fetch: HeightRange to synchronize

        Returns:
            Tuple of (file_infos, downloader_func)
        """
        ...


class NamedBulkIngestor:
    """Associates a descriptive name with a BulkIngestor interface."""

    def __init__(self, name: str, ingestor: BulkIngestor):
        """Initialize named bulk ingestor.

        Args:
            name: Human-readable name
            ingestor: Bulk ingestor instance
        """
        self.name = name
        self.ingestor = ingestor


class BulkHeaderMinimumInfo:
    """Essential metadata for a bulk block header file."""

    def __init__(self, first_height: int, count: int, file_name: str, source_url: str = ""):
        """Initialize bulk header file info.

        Args:
            first_height: First block height in file
            count: Number of headers in file
            file_name: Name of the file
            source_url: URL to download the file from
        """
        self.first_height = first_height
        self.count = count
        self.file_name = file_name
        self.source_url = source_url

    def to_height_range(self) -> Any:
        """Convert to HeightRange."""
        from .util.height_range import HeightRange

        return HeightRange.new_height_range(self.first_height, self.first_height + self.count - 1)
