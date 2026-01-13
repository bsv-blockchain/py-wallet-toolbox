"""Bulk headers container for efficient header storage and retrieval.

Provides memory-efficient storage and fast lookup of bulk block header data.

Reference: go-wallet-toolbox/pkg/services/chaintracks/bulk_headers_container.go
"""

import logging
from collections import defaultdict
from typing import Any

logger = logging.getLogger(__name__)


class BulkHeadersContainer:
    """Container for bulk block header data with efficient storage and retrieval.

    Stores block headers in chunks for memory efficiency and provides
    fast height-based lookups.

    Reference: go-wallet-toolbox/pkg/services/chaintracks/bulk_headers_container.go
    """

    def __init__(self, chunk_size: int = 10000):
        """Initialize bulk headers container.

        Args:
            chunk_size: Number of headers per chunk for memory efficiency
        """
        self.chunk_size = chunk_size
        self.chunks: dict[int, list[dict[str, Any]]] = defaultdict(list)
        self.chunk_ranges: dict[int, tuple[int, int]] = {}  # chunk_id -> (start_height, end_height)
        self.logger = logging.getLogger(f"{__name__}.BulkHeadersContainer")

    def add(self, headers: list[dict[str, Any]]) -> None:
        """Add headers to the container.

        Headers are organized into chunks based on height ranges for efficient storage.

        Args:
            headers: List of header data dicts with 'height' field
        """
        if not headers:
            return

        # Sort headers by height
        sorted_headers = sorted(headers, key=lambda h: h["height"])

        # Group into chunks
        current_chunk: list[dict[str, Any]] = []
        current_chunk_start = sorted_headers[0]["height"]
        current_chunk_id = current_chunk_start // self.chunk_size

        for header in sorted_headers:
            height = header["height"]
            chunk_id = height // self.chunk_size

            if chunk_id != current_chunk_id:
                # Save current chunk
                if current_chunk:
                    self._save_chunk(current_chunk_id, current_chunk)

                # Start new chunk
                current_chunk = [header]
                current_chunk_start = height
                current_chunk_id = chunk_id
            else:
                current_chunk.append(header)

        # Save final chunk
        if current_chunk:
            self._save_chunk(current_chunk_id, current_chunk)

        self.logger.debug(f"Added {len(headers)} headers in {len(self.chunks)} chunks")

    def _save_chunk(self, chunk_id: int, headers: list[dict[str, Any]]) -> None:
        """Save a chunk of headers.

        Args:
            chunk_id: Unique identifier for the chunk
            headers: List of headers in this chunk
        """
        if not headers:
            return

        self.chunks[chunk_id] = headers
        start_height = headers[0]["height"]
        end_height = headers[-1]["height"]
        self.chunk_ranges[chunk_id] = (start_height, end_height)

    def get(self, height: int) -> dict[str, Any] | None:
        """Get header for specific height.

        Args:
            height: Block height to retrieve

        Returns:
            Header data dict or None if not found
        """
        chunk_id = height // self.chunk_size

        if chunk_id not in self.chunks:
            return None

        # Binary search within chunk
        chunk = self.chunks[chunk_id]
        left, right = 0, len(chunk) - 1

        while left <= right:
            mid = (left + right) // 2
            mid_height = chunk[mid]["height"]

            if mid_height == height:
                return chunk[mid]
            elif mid_height < height:
                left = mid + 1
            else:
                right = mid - 1

        return None

    def get_range(self, start_height: int, end_height: int) -> list[dict[str, Any]]:
        """Get all headers in a height range.

        Args:
            start_height: Starting block height (inclusive)
            end_height: Ending block height (inclusive)

        Returns:
            List of header data dicts in the range
        """
        result = []

        # Find relevant chunks
        start_chunk = start_height // self.chunk_size
        end_chunk = end_height // self.chunk_size

        for chunk_id in range(start_chunk, end_chunk + 1):
            if chunk_id not in self.chunks:
                continue

            chunk = self.chunks[chunk_id]
            chunk_start, chunk_end = self.chunk_ranges[chunk_id]

            # Skip chunks that don't overlap with requested range
            if chunk_end < start_height or chunk_start > end_height:
                continue

            # Find headers in this chunk that are in the requested range
            for header in chunk:
                height = header["height"]
                if start_height <= height <= end_height:
                    result.append(header)

        return result

    def has_height(self, height: int) -> bool:
        """Check if container has data for specific height.

        Args:
            height: Block height to check

        Returns:
            True if height exists in container
        """
        return self.get(height) is not None

    def get_height_range(self) -> tuple[int, int] | None:
        """Get the overall height range covered by this container.

        Returns:
            Tuple of (min_height, max_height) or None if empty
        """
        if not self.chunk_ranges:
            return None

        min_height = min(start for start, _ in self.chunk_ranges.values())
        max_height = max(end for _, end in self.chunk_ranges.values())

        return (min_height, max_height)

    def count(self) -> int:
        """Get total number of headers stored.

        Returns:
            Total count of headers across all chunks
        """
        return sum(len(chunk) for chunk in self.chunks.values())

    def clear(self) -> None:
        """Clear all stored headers."""
        self.chunks.clear()
        self.chunk_ranges.clear()
        self.logger.debug("Cleared all bulk headers")

    def get_chunk_count(self) -> int:
        """Get number of chunks.

        Returns:
            Number of stored chunks
        """
        return len(self.chunks)
