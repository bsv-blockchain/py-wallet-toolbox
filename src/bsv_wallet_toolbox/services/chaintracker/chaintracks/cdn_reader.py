"""CDN reader for downloading bulk header files.

Downloads bulk header files from CDN endpoints with retry logic and
progress tracking.

Reference: go-wallet-toolbox/pkg/services/chaintracks/ingest/cdn_reader.go
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional
import aiohttp

logger = logging.getLogger(__name__)


class CDNReaderOptions:
    """Options for CDN reader configuration."""

    def __init__(
        self,
        base_url: str = "https://headers.chaintracks.io",
        timeout_seconds: int = 30,
        max_retries: int = 3,
        retry_delay_seconds: float = 1.0,
        user_agent: str = "Python-ChainTracks/1.0",
    ):
        self.base_url = base_url
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self.retry_delay_seconds = retry_delay_seconds
        self.user_agent = user_agent


class BulkFileInfo:
    """Information about a bulk header file."""

    def __init__(
        self,
        filename: str,
        url: str,
        start_height: int,
        end_height: int,
        size_bytes: Optional[int] = None,
        checksum: Optional[str] = None,
    ):
        self.filename = filename
        self.url = url
        self.start_height = start_height
        self.end_height = end_height
        self.size_bytes = size_bytes
        self.checksum = checksum

    def __repr__(self) -> str:
        return f"BulkFileInfo(filename='{self.filename}', range={self.start_height}-{self.end_height})"


class CDNReader:
    """CDN reader for downloading bulk header files.

    Provides methods to discover available bulk files and download them
    with retry logic and progress tracking.

    Reference: go-wallet-toolbox/pkg/services/chaintracks/ingest/cdn_reader.go
    """

    def __init__(self, options: Optional[CDNReaderOptions] = None):
        """Initialize CDN reader.

        Args:
            options: Configuration options for CDN access
        """
        self.options = options or CDNReaderOptions()
        self.logger = logging.getLogger(f"{__name__}.CDNReader")
        self._session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        """Async context manager entry."""
        timeout = aiohttp.ClientTimeout(total=self.options.timeout_seconds)
        self._session = aiohttp.ClientSession(
            timeout=timeout,
            headers={"User-Agent": self.options.user_agent}
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self._session:
            await self._session.close()

    async def fetch_bulk_header_files_info(self) -> List[BulkFileInfo]:
        """Fetch information about available bulk header files.

        Queries the CDN for available bulk files and their metadata.

        Returns:
            List of BulkFileInfo objects describing available files

        Raises:
            Exception: If CDN query fails
        """
        url = f"{self.options.base_url}/bulk-files/index.json"

        self.logger.debug(f"Fetching bulk files index from {url}")

        # TODO: Implement actual CDN index fetching
        # For now, return mock data based on typical bulk file structure
        bulk_files = []

        # Generate mock bulk files for heights 0-800,000 in 10,000 header chunks
        chunk_size = 10000
        max_height = 800000  # Approximate current BSV height

        for start_height in range(0, max_height, chunk_size):
            end_height = min(start_height + chunk_size - 1, max_height)
            filename = "06d"
            url = f"{self.options.base_url}/bulk-files/{filename}"

            bulk_files.append(BulkFileInfo(
                filename=filename,
                url=url,
                start_height=start_height,
                end_height=end_height,
                size_bytes=None,  # Unknown size
                checksum=None     # No checksum validation yet
            ))

        self.logger.info(f"Found {len(bulk_files)} bulk files available")
        return bulk_files

    async def fetch_bulk_header_file(self, file_info: BulkFileInfo) -> bytes:
        """Fetch a specific bulk header file.

        Downloads the bulk header file with retry logic.

        Args:
            file_info: Information about the file to download

        Returns:
            Raw file content as bytes

        Raises:
            Exception: If download fails after all retries
        """
        if not self._session:
            raise RuntimeError("CDNReader must be used as async context manager")

        for attempt in range(self.options.max_retries):
            try:
                self.logger.debug(f"Downloading {file_info.filename} (attempt {attempt + 1})")

                async with self._session.get(file_info.url) as response:
                    if response.status != 200:
                        raise aiohttp.ClientResponseError(
                            request_info=response.request_info,
                            history=response.history,
                            status=response.status,
                            message=f"HTTP {response.status}: {response.reason}",
                            headers=response.headers
                        )

                    content = await response.read()
                    self.logger.debug(f"Downloaded {file_info.filename} ({len(content)} bytes)")
                    return content

            except Exception as e:
                if attempt == self.options.max_retries - 1:
                    # Last attempt failed
                    self.logger.error(f"Failed to download {file_info.filename} after {self.options.max_retries} attempts: {e}")
                    raise

                # Wait before retry
                self.logger.warning(f"Download attempt {attempt + 1} failed for {file_info.filename}: {e}")
                await asyncio.sleep(self.options.retry_delay_seconds * (2 ** attempt))  # Exponential backoff

        # Should not reach here
        raise RuntimeError(f"Unexpected error downloading {file_info.filename}")

    async def fetch_bulk_header_files_info_parallel(
        self,
        files: List[BulkFileInfo],
        max_concurrent: int = 3
    ) -> Dict[str, bytes]:
        """Fetch multiple bulk header files in parallel.

        Args:
            files: List of files to download
            max_concurrent: Maximum number of concurrent downloads

        Returns:
            Dict mapping filename to file content
        """
        if not self._session:
            raise RuntimeError("CDNReader must be used as async context manager")

        semaphore = asyncio.Semaphore(max_concurrent)
        results = {}

        async def download_file(file_info: BulkFileInfo) -> None:
            async with semaphore:
                content = await self.fetch_bulk_header_file(file_info)
                results[file_info.filename] = content

        tasks = [download_file(file_info) for file_info in files]
        await asyncio.gather(*tasks, return_exceptions=True)

        self.logger.info(f"Downloaded {len(results)} bulk files")
        return results
