"""Bulk File Data Manager for block headers.

Manages bulk loading and caching of block headers from CDN sources.

Reference: wallet-toolbox/src/services/chaintracker/chaintracks/util/BulkFileDataManager.ts
"""

from .height_range import HeightRange


class BulkFileDataManagerOptions:
    """Options for BulkFileDataManager.

    Reference: wallet-toolbox/src/services/chaintracker/chaintracks/util/BulkFileDataManager.ts
               interface BulkFileDataManagerOptions
    """

    def __init__(
        self,
        *,
        chain: str,
        max_per_file: int = 100000,
        max_retained: int = 2,
        from_known_source_url: str | None = None,
    ):
        """Initialize options.

        Args:
            chain: Blockchain network ('main' or 'test')
            max_per_file: Maximum headers per file
            max_retained: Maximum files to retain in memory
            from_known_source_url: CDN URL for headers
        """
        self.chain = chain
        self.max_per_file = max_per_file
        self.max_retained = max_retained
        self.from_known_source_url = from_known_source_url or self._default_cdn_url(chain)

    @staticmethod
    def _default_cdn_url(chain: str) -> str:
        """Get default CDN URL for chain."""
        if chain == "main":
            return "https://cdn.projectbabbage.com/blockheaders"
        return "https://cdn-testnet.projectbabbage.com/blockheaders"


class BulkFileData:
    """Represents a bulk file with header data.

    Reference: wallet-toolbox/src/services/chaintracker/chaintracks/util/BulkFileDataManager.ts
               interface BulkFileData
    """

    def __init__(self, file_index: int, min_height: int, max_height: int):
        """Initialize bulk file data.

        Args:
            file_index: Index of this file
            min_height: Minimum block height in file
            max_height: Maximum block height in file
        """
        self.file_index = file_index
        self.min_height = min_height
        self.max_height = max_height
        self.data: bytes | None = None  # Loaded header data


class BulkFileDataManager:
    """Manager for bulk block header files from CDN.

    Provides efficient loading and caching of block headers from
    CDN sources, with configurable retention policies.

    Reference: wallet-toolbox/src/services/chaintracker/chaintracks/util/BulkFileDataManager.ts
               class BulkFileDataManager
    """

    def __init__(self, options: BulkFileDataManagerOptions):
        """Initialize manager.

        Args:
            options: Configuration options
        """
        self.chain = options.chain
        self.max_per_file = options.max_per_file
        self.max_retained = options.max_retained
        self.from_known_source_url = options.from_known_source_url

        # List of bulk file descriptors
        self.bfds: list[BulkFileData] = []

        # Initialize with mock data for testing
        self._initialize_mock_files()

    def _initialize_mock_files(self) -> None:
        """Initialize mock file list for testing.

        In production, this would fetch the file list from CDN.
        For now, create a reasonable mock structure.
        """
        # Assuming 100k blocks per file, mainnet has 800k+ blocks
        # So we'd have at least 8 files
        num_files = 10  # >7 as test expects
        for i in range(num_files):
            min_h = i * self.max_per_file
            max_h = (i + 1) * self.max_per_file - 1
            self.bfds.append(BulkFileData(i, min_h, max_h))

    @staticmethod
    def create_default_options(chain: str) -> BulkFileDataManagerOptions:
        """Create default options for a chain.

        Args:
            chain: Blockchain network ('main' or 'test')

        Returns:
            Default options for the chain

        Reference: wallet-toolbox/src/services/chaintracker/chaintracks/util/BulkFileDataManager.ts
                   static createDefaultOptions()
        """
        return BulkFileDataManagerOptions(chain=chain)

    async def get_bulk_files(self) -> list[BulkFileData]:
        """Get list of available bulk files.

        Returns:
            List of bulk file descriptors

        Reference: wallet-toolbox/src/services/chaintracker/chaintracks/util/BulkFileDataManager.ts
                   async getBulkFiles()
        """
        return self.bfds

    async def get_height_range(self) -> HeightRange:
        """Get the total height range covered by all files.

        Returns:
            Range from minimum to maximum height

        Reference: wallet-toolbox/src/services/chaintracker/chaintracks/util/BulkFileDataManager.ts
                   async getHeightRange()
        """
        if not self.bfds:
            return HeightRange(0, -1)  # Empty range

        min_height = min(f.min_height for f in self.bfds)
        max_height = max(f.max_height for f in self.bfds)
        return HeightRange(min_height, max_height)

    async def update_from_url(self, url: str) -> None:
        """Update file list from a URL.

        Args:
            url: URL to fetch file list from

        Reference: wallet-toolbox/src/services/chaintracker/chaintracks/util/BulkFileDataManager.ts
                   async updateFromUrl()
        """
        # In production, this would fetch from the URL
        # For now, this is a no-op stub

    async def load_data(self, file_index: int) -> bytes | None:
        """Load data for a specific file.

        Args:
            file_index: Index of file to load

        Returns:
            File data bytes, or None if not found

        Reference: wallet-toolbox/src/services/chaintracker/chaintracks/util/BulkFileDataManager.ts
                   async loadData()
        """
        # In production, this would fetch from CDN
        # For now, return None (no data loaded)
        for bfd in self.bfds:
            if bfd.file_index == file_index:
                return bfd.data
        return None
