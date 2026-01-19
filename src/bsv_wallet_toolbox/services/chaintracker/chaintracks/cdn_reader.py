"""CDN reader for bulk block header files.

Provides HTTP client for fetching bulk block header metadata and files from CDN.

Reference: go-wallet-toolbox/pkg/services/chaintracks/ingest/cdn_reader.go
"""

import logging
from typing import Any

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from ...wallet_services import Chain

logger = logging.getLogger(__name__)


class BulkHeaderFilesInfo:
    """Metadata about bulk block header files collection."""

    def __init__(self, data: dict[str, Any]):
        """Initialize from JSON data.

        Args:
            data: JSON response from CDN
        """
        self.root_folder = data.get("rootFolder", "")
        self.json_filename = data.get("jsonFilename", "")
        self.headers_per_file = data.get("headersPerFile", 0)
        self.files = [BulkHeaderFileInfo(file_data) for file_data in data.get("files", [])]


class BulkHeaderFileInfo:
    """Metadata for a single bulk block header file."""

    def __init__(self, data: dict[str, Any]):
        """Initialize from JSON data.

        Args:
            data: File metadata from JSON
        """
        self.first_height = data.get("firstHeight", 0)
        self.count = data.get("count", 0)
        self.file_name = data.get("fileName", "")
        self.source_url = data.get("sourceUrl", "")
        self.prev_chain_work = data.get("prevChainWork", "")
        self.last_chain_work = data.get("lastChainWork", "")
        self.prev_hash = data.get("prevHash", "")
        self.last_hash = data.get("lastHash")
        self.file_hash = data.get("fileHash", b"")
        self.chain = data.get("chain", "")

    @property
    def bulk_header_minimum_info(self) -> Any:
        """Get the minimum info for bulk operations."""
        from .bulk_ingestor_interface import BulkHeaderMinimumInfo

        return BulkHeaderMinimumInfo(
            first_height=self.first_height, count=self.count, file_name=self.file_name, source_url=self.source_url
        )


class CDNReader:
    """HTTP client for fetching bulk header data from CDN."""

    # Base URL for Project Babbage CDN
    BABBAGE_CDN_BASE_URL = "https://cdn.projectbabbage.com/blockheaders"

    def __init__(self, base_url: str = BABBAGE_CDN_BASE_URL, timeout: int = 30):
        """Initialize CDN reader.

        Args:
            base_url: Base URL for CDN
            timeout: Request timeout in seconds
        """
        self.base_url = base_url
        self.timeout = timeout

        # Setup requests session with retry strategy
        self.session = requests.Session()

        retry_strategy = Retry(total=3, status_forcelist=[429, 500, 502, 503, 504], backoff_factor=1)

        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

        # Set headers
        self.session.headers.update(
            {"Accept": "application/json", "Content-Type": "application/json", "User-Agent": "py-wallet-toolbox"}
        )

    def fetch_bulk_header_files_info(self, chain: Chain) -> BulkHeaderFilesInfo:
        """Fetch metadata about available bulk header files.

        Args:
            chain: Blockchain network

        Returns:
            Bulk header files information

        Raises:
            Exception: If request fails
        """
        url = f"{self.base_url}/{chain}NetBlockHeaders.json"

        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()

            data = response.json()
            return BulkHeaderFilesInfo(data)

        except Exception as e:
            raise Exception(f"Failed to fetch bulk header files info: {e}") from e

    def download_bulk_header_file(self, filename: str) -> bytes:
        """Download a bulk header file.

        Args:
            filename: Name of the file to download

        Returns:
            File contents as bytes

        Raises:
            Exception: If download fails
        """
        url = f"{self.base_url}/{filename}"

        try:
            # Disable debug logging for large binary downloads
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()

            return response.content

        except Exception as e:
            raise Exception(f"Failed to download bulk header file {filename}: {e}") from e
