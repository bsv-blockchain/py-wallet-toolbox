"""WhatsOnChain bulk ingestor for blockchain headers.

Provides bulk ingestion of blockchain headers from WhatsOnChain API.

Reference: go-wallet-toolbox/pkg/services/chaintracks/ingest/bulk_ingestor_woc.go
"""

import asyncio
import logging
import re
from collections.abc import Callable
from typing import Any

from ...wallet_services import Chain
from .bulk_ingestor_interface import BulkHeaderMinimumInfo, BulkIngestor
from .woc_client import WOCClient

logger = logging.getLogger(__name__)


class BulkIngestorWOC(BulkIngestor):
    """Bulk ingestor that downloads headers from WhatsOnChain API."""

    def __init__(self, chain: Chain, api_key: str | None = None):
        """Initialize WOC bulk ingestor.

        Args:
            chain: Blockchain network
            api_key: Optional WhatsOnChain API key
        """
        self.chain = chain
        self.api_key = api_key
        self.woc_client = WOCClient(chain, api_key)

        logger.info(f"BulkIngestorWOC initialized for {chain} chain")

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
            # Fetch available bulk files
            all_files = await asyncio.get_event_loop().run_in_executor(None, self._fetch_bulk_header_files_info)

            if not all_files:
                raise Exception("No bulk header files available from WhatsOnChain")

            # Filter files that overlap with requested range
            needed_files = []
            for file_info in all_files:
                if file_info["heightRange"].overlaps(range_to_fetch):
                    needed_files.append(file_info)

            # Convert to BulkHeaderMinimumInfo
            result = []
            for file_info in needed_files:
                hr = file_info["heightRange"]
                result.append(
                    BulkHeaderMinimumInfo(
                        first_height=hr.min_height,
                        count=hr.length,
                        file_name=file_info["filename"],
                        source_url=file_info["url"],
                    )
                )

            return result, self._bulk_file_downloader()

        except Exception as e:
            raise Exception(f"Failed to synchronize bulk headers: {e}") from e

    def _fetch_bulk_header_files_info(self) -> list[dict[str, Any]]:
        """Fetch metadata about available bulk header files.

        Returns:
            List of file info dictionaries
        """
        try:
            files = self.woc_client.get_headers_resource_list()
        except Exception:
            # Return empty list on any API error
            return []

        if not isinstance(files, list):
            return []

        result = []
        # Parse filenames like "mainNet_0.headers", "testNet_4.headers"
        pattern = r"^(main|test)Net_(\d+)\.headers$"

        for filename in files:
            if not isinstance(filename, str):
                continue
            match = re.match(pattern, filename)
            if match:
                network = match.group(1)
                file_id = int(match.group(2))

                # Skip if network doesn't match our chain
                if network == "main" and self.chain != "main":
                    continue
                if network == "test" and self.chain != "test":
                    continue

                # Calculate height range (assuming 100,000 headers per file like Go implementation)
                headers_per_file = 100000
                first_height = file_id * headers_per_file
                count = headers_per_file

                # Create download URL
                url = f"{self.woc_client._get_base_url()}/block/headers/download/{filename}"

                from .util.height_range import HeightRange

                height_range = HeightRange.new_height_range(first_height, first_height + count - 1)

                result.append({"filename": filename, "url": url, "heightRange": height_range, "fileId": file_id})

        return result

    def _bulk_file_downloader(self) -> Callable:
        """Create bulk file downloader function.

        Returns:
            Function that downloads bulk files
        """

        def downloader(file_info: BulkHeaderMinimumInfo) -> bytes:
            if not file_info.source_url:
                raise Exception("SourceURL is required for WhatsOnChain bulk file downloader")
            logger.info(f"Downloading bulk header file {file_info.file_name}")
            return self.woc_client.download_header_file(file_info.source_url)

        return downloader
