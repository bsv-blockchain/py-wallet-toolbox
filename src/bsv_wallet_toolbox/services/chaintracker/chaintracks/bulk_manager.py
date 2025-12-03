"""Bulk Manager for block header synchronization.

Manages bulk header synchronization, storage, and migration from live headers.

Reference: toolbox/go-wallet-toolbox/pkg/services/chaintracks/bulk_manager.go
"""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING, Any

from .models import HeightRanges
from .util.height_range import HeightRange
from .util.bulk_file_data_manager import BulkFileDataManager, BulkFileDataManagerOptions

if TYPE_CHECKING:
    from .ingest import NamedBulkIngestor
    from .models import LiveBlockHeader
    from ..wallet_services import Chain

logger = logging.getLogger(__name__)

BULK_CHUNK_SIZE = 100000


class BulkManager:
    """Manages bulk block header synchronization and storage.

    This class is responsible for:
    - Synchronizing bulk headers from ingestors
    - Managing bulk header storage
    - Migrating live headers to bulk storage
    - Providing access to bulk header data

    Reference: toolbox/go-wallet-toolbox/pkg/services/chaintracks/bulk_manager.go
    """

    def __init__(
        self,
        chain: Chain,
        bulk_ingestors: list[NamedBulkIngestor] | None = None,
        bulk_chunk_size: int = BULK_CHUNK_SIZE,
    ):
        """Initialize BulkManager.

        Args:
            chain: Blockchain network
            bulk_ingestors: List of bulk ingestors
            bulk_chunk_size: Size of bulk chunks
        """
        self.chain = chain
        self.bulk_ingestors = bulk_ingestors or []
        self.bulk_chunk_size = bulk_chunk_size

        # Initialize bulk file data manager
        options = BulkFileDataManagerOptions(
            chain=chain,
            max_per_file=bulk_chunk_size,
            max_retained=2,  # Keep 2 files in memory as in Go
        )
        self.file_manager = BulkFileDataManager(options)

        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    async def sync_bulk_storage(
        self,
        present_height: int,
        initial_ranges: HeightRanges,
        live_height_threshold: int,
    ) -> None:
        """Synchronize bulk storage with current blockchain state.

        Args:
            present_height: Current blockchain height
            initial_ranges: Initial height ranges
            live_height_threshold: Threshold for live headers

        Raises:
            RuntimeError: If synchronization fails
        """
        if present_height <= live_height_threshold:
            self.logger.info(
                "Skipping bulk synchronization - present height below live height threshold",
                extra={
                    "present_height": present_height,
                    "live_height_threshold": live_height_threshold,
                }
            )
            return

        self.logger.info(
            "Starting bulk synchronization",
            extra={
                "present_height": present_height,
                "initial_ranges": initial_ranges,
            }
        )

        # Calculate missing range
        target_max_height = present_height - live_height_threshold
        missing_range = HeightRange(0, target_max_height).subtract(initial_ranges.bulk)

        for ingestor in self.bulk_ingestors:
            if missing_range.is_empty():
                break

            try:
                # Synchronize with ingestor
                bulk_chunks = await ingestor.ingestor.synchronize(
                    present_height, missing_range
                )

                # Process bulk chunks
                await self._process_bulk_chunks(bulk_chunks, missing_range.max_height)

                # Update missing range
                current_range = self.get_height_range()
                missing_range = missing_range.subtract(current_range)

            except Exception as e:
                self.logger.error(
                    "Error during bulk synchronization",
                    extra={
                        "ingestor_name": ingestor.name,
                        "error": str(e),
                    }
                )
                raise RuntimeError(f"Bulk synchronization failed for ingestor {ingestor.name}: {e}") from e

        # Update file manager
        await self.file_manager.update()

    def get_height_range(self) -> HeightRange:
        """Get the height range covered by bulk storage.

        Returns:
            HeightRange of bulk storage
        """
        return self.file_manager.get_height_range()

    def find_header_for_height(self, height: int) -> dict[str, Any] | None:
        """Find header for given height in bulk storage.

        Args:
            height: Block height

        Returns:
            Block header or None if not found
        """
        return self.file_manager.find_header_for_height(height)

    def last_header(self) -> tuple[dict[str, Any] | None, Any]:
        """Get the last header in bulk storage.

        Returns:
            Tuple of (header, chain_work) or (None, None)
        """
        return self.file_manager.last_header()

    def bulk_files_info(self) -> dict[str, Any]:
        """Get information about bulk files.

        Returns:
            Dictionary with bulk file information
        """
        return {
            "headers_per_file": self.bulk_chunk_size,
            "files": self.file_manager.files_info(),
        }

    def bulk_file_data_by_index(self, index: int) -> Any:
        """Get bulk file data by index.

        Args:
            index: File index

        Returns:
            Bulk file data
        """
        return self.file_manager.get_file_data_by_index(index)

    async def migrate_from_live_headers(self, live_headers: list[LiveBlockHeader]) -> None:
        """Migrate live headers to bulk storage.

        Args:
            live_headers: List of live headers to migrate

        Raises:
            RuntimeError: If migration fails
        """
        if not live_headers:
            return

        # Convert headers to bytes
        data = bytearray()
        for header in live_headers:
            header_bytes = header.to_bytes()
            data.extend(header_bytes)

        # Create height range
        height_range = HeightRange(
            live_headers[0].height,
            live_headers[-1].height
        )

        # Add to file manager
        try:
            await self.file_manager.add(data, height_range)
        except Exception as e:
            raise RuntimeError(f"Failed to migrate live headers to bulk storage: {e}") from e

    async def _process_bulk_chunks(
        self,
        bulk_chunks: list[Any],
        max_height: int
    ) -> None:
        """Process bulk chunks from ingestor.

        Args:
            bulk_chunks: List of bulk chunks
            max_height: Maximum height to process
        """
        # Implementation would depend on the specific ingestor interface
        # For now, this is a placeholder
        pass
