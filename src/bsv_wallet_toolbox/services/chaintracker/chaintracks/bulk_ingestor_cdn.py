"""CDN bulk ingestor for blockchain headers.

Provides bulk ingestion of blockchain headers from Project Babbage CDN.

Reference: go-wallet-toolbox/pkg/services/chaintracks/ingest/bulk_ingestor_cdn.go
"""

import asyncio
import logging
from collections.abc import Callable
from typing import Any

from ...wallet_services import Chain
from .bulk_ingestor_interface import BulkHeaderMinimumInfo, BulkIngestor
from .cdn_reader import CDNReader

logger = logging.getLogger(__name__)


class BulkIngestorCDN(BulkIngestor):
    """Bulk ingestor that downloads headers from Project Babbage CDN."""

    def __init__(self, chain: Chain, source_url: str | None = None):
        """Initialize CDN bulk ingestor.

        Args:
            chain: Blockchain network
            source_url: CDN base URL (defaults to Project Babbage)
        """
        self.chain = chain
        self.source_url = source_url or CDNReader.BABBAGE_CDN_BASE_URL
        self.reader = CDNReader(self.source_url)

        logger.info("BulkIngestorCDN initialized for %s chain", chain)

    async def synchronize(
        self, present_height: int, range_to_fetch: Any
    ) -> tuple[list[BulkHeaderMinimumInfo], Callable]:
        """Synchronize bulk headers for the given height range.

        Args:
            present_height: Current blockchain height
            range_to_fetch: HeightRange to synchronize

        Returns:
            Tuple of (file_infos, downloader_func)

        Raises:
            Exception: If synchronization fails
        """
        try:
            # Fetch available files info
            files_info = await asyncio.get_event_loop().run_in_executor(
                None, self.reader.fetch_bulk_header_files_info, self.chain
            )

            # Filter files that overlap with requested range
            bulk_info = []
            for file in files_info.files:
                file_range = file.bulk_header_minimum_info.to_height_range()
                if file_range.overlaps(range_to_fetch):
                    logger.info(
                        "Found bulk header file %s (heights %d-%d)",
                        file.file_name,
                        file_range.min_height,
                        file_range.max_height,
                    )
                    bulk_info.append(file.bulk_header_minimum_info)
                else:
                    logger.debug("Skipping bulk header file %s - no overlap", file.file_name)

            return bulk_info, self._bulk_file_downloader()

        except Exception as e:
            raise Exception(f"Failed to synchronize bulk headers: {e}") from e

    def _bulk_file_downloader(self) -> Callable:
        """Create bulk file downloader function.

        Returns:
            Function that downloads bulk files
        """

        def downloader(file_info: BulkHeaderMinimumInfo) -> bytes:
            logger.info(f"Downloading bulk header file {file_info.file_name}")
            return self.reader.download_bulk_header_file(file_info.file_name)

        return downloader
