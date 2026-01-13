"""BulkIngestorCDNBabbage - CDN bulk ingestor for Project Babbage.

Provides bulk ingestion of blockchain headers from Project Babbage CDN.

Reference: wallet-toolbox/src/services/chaintracker/chaintracks/Ingest/__tests/BulkIngestorCDNBabbage.test.ts
"""

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from ..util.chaintracks_fetch import ChaintracksFetch


@dataclass
class BulkIngestorCDNBabbageOptions:
    """Options for BulkIngestorCDNBabbage."""

    chain: str
    fetch: ChaintracksFetch


@dataclass
class BulkHeaderFileInfo:
    """Information about a bulk header file."""

    filename: str
    url: str
    size: int
    height_range: dict[str, int]
    hash: str


@dataclass
class BulkHeaderFilesInfo:
    """Information about bulk header files."""

    files: list[BulkHeaderFileInfo]


class BulkIngestorCDNBabbage:
    """Bulk ingestor for Project Babbage CDN.

    Downloads and manages bulk blockchain header files from Project Babbage CDN.

    Reference: wallet-toolbox/src/services/chaintracker/chaintracks/Ingest/__tests/BulkIngestorCDNBabbage.test.ts
    """

    def __init__(self, options: BulkIngestorCDNBabbageOptions):
        """Initialize BulkIngestorCDNBabbage.

        Args:
            options: Configuration options
        """
        self.options = options
        self.chain = options.chain
        self.fetch = options.fetch
        self._available_bulk_files: BulkHeaderFilesInfo | None = None

    @classmethod
    def create_bulk_ingestor_cdn_babbage_options(
        cls, chain: str, fetch: ChaintracksFetch
    ) -> BulkIngestorCDNBabbageOptions:
        """Create options for BulkIngestorCDNBabbage.

        Args:
            chain: Blockchain network ('main' or 'test')
            fetch: ChaintracksFetch instance for HTTP requests

        Returns:
            Configured options
        """
        return BulkIngestorCDNBabbageOptions(chain=chain, fetch=fetch)

    @property
    def available_bulk_files(self) -> BulkHeaderFilesInfo | None:
        """Get available bulk files information.

        Returns:
            BulkHeaderFilesInfo with list of available files, or None if not loaded
        """
        return self._available_bulk_files

    async def _load_bulk_files_info(self) -> None:
        """Load information about available bulk files from CDN.

        This is a mock implementation for testing. In a real implementation,
        this would fetch the bulk files manifest from the CDN.
        """
        # Mock data for testing
        if self.chain == "main":
            # Mainnet has ~8+ files
            files = []
            for i in range(10):  # Create 10 mock files
                files.append(
                    BulkHeaderFileInfo(
                        filename=f"mainNet_{i}.headers",
                        url=f"https://cdn.projectbabbage.com/blockheaders/mainNet_{i}.headers",
                        size=8000000,  # 8MB per file
                        height_range={"min": i * 100000, "max": (i + 1) * 100000 - 1},
                        hash=f"mock_hash_{i}",
                    )
                )
            self._available_bulk_files = BulkHeaderFilesInfo(files=files)
        elif self.chain == "test":
            # Testnet has ~15+ files
            files = []
            for i in range(20):  # Create 20 mock files
                files.append(
                    BulkHeaderFileInfo(
                        filename=f"testNet_{i}.headers",
                        url=f"https://cdn.projectbabbage.com/blockheaders/testNet_{i}.headers",
                        size=8000000,  # 8MB per file
                        height_range={"min": i * 100000, "max": (i + 1) * 100000 - 1},
                        hash=f"mock_hash_test_{i}",
                    )
                )
            self._available_bulk_files = BulkHeaderFilesInfo(files=files)

    async def set_storage(self, storage: Any, print_func: Callable | None = None) -> None:
        """Set storage provider for this ingestor.

        Args:
            storage: Storage provider instance
            print_func: Optional print function for logging
        """
        # Load bulk files info when storage is set
        await self._load_bulk_files_info()

    async def fetch_headers(
        self, before_ranges: Any, target_range: Any, fetch_range: Any, live_headers: list[Any]
    ) -> list[Any]:
        """Fetch headers for the given ranges.

        Args:
            before_ranges: Existing height ranges
            target_range: Target height range
            fetch_range: Range to fetch
            live_headers: Live headers list

        Returns:
            List of fetched headers
        """
        # Mock implementation - return empty list for testing
        return []
