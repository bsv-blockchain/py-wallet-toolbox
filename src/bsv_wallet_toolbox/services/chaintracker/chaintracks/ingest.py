"""Ingest interfaces for Chaintracks data sources.

This module defines interfaces for ingesting blockchain data from various sources.

Reference: toolbox/go-wallet-toolbox/pkg/services/chaintracks/ingest/
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol

if TYPE_CHECKING:
    from .models import HeightRange


class NamedBulkIngestor:
    """Named bulk ingestor with name and ingestor instance.

    Reference: toolbox/go-wallet-toolbox/pkg/services/chaintracks/ingest/named_ingestors.go
    """

    def __init__(self, name: str, ingestor: BulkIngestor):
        """Initialize named bulk ingestor.

        Args:
            name: Ingestor name
            ingestor: Bulk ingestor instance
        """
        self.name = name
        self.ingestor = ingestor


class BulkIngestor(Protocol):
    """Protocol for bulk data ingestion.

    Reference: toolbox/go-wallet-toolbox/pkg/services/chaintracks/ingest/bulk_ingestor.go
    """

    async def synchronize(self, present_height: int, missing_range: HeightRange) -> list[Any]:
        """Synchronize bulk data for missing range.

        Args:
            present_height: Current blockchain height
            missing_range: Range of missing heights

        Returns:
            List of bulk header chunks
        """
        ...


class BulkHeaderMinimumInfo:
    """Minimum information about bulk header chunks.

    Reference: toolbox/go-wallet-toolbox/pkg/services/chaintracks/ingest/bulk_header_minimum_info.go
    """

    def __init__(self, file_hash: str, height_range: HeightRange):
        """Initialize bulk header info.

        Args:
            file_hash: Hash of the bulk file
            height_range: Height range covered by this chunk
        """
        self.file_hash = file_hash
        self.height_range = height_range


class BulkFileDownloader(Protocol):
    """Protocol for downloading bulk files.

    Reference: toolbox/go-wallet-toolbox/pkg/services/chaintracks/ingest/bulk_file_downloader.go
    """

    async def download(self, file_hash: str) -> bytes:
        """Download bulk file by hash.

        Args:
            file_hash: Hash of file to download

        Returns:
            File contents as bytes
        """
        ...


class BulkHeaderFilesInfo:
    """Information about bulk header files.

    Reference: toolbox/go-wallet-toolbox/pkg/services/chaintracks/ingest/bulk_header_files_info.go
    """

    def __init__(self, headers_per_file: int, files: list[Any]):
        """Initialize bulk files info.

        Args:
            headers_per_file: Number of headers per file
            files: List of file information
        """
        self.headers_per_file = headers_per_file
        self.files = files


class BulkFileData:
    """Data for a bulk file.

    Reference: toolbox/go-wallet-toolbox/pkg/services/chaintracker/ingest/bulk_file_data.go
    """

    def __init__(self, file_hash: str, data: bytes):
        """Initialize bulk file data.

        Args:
            file_hash: Hash of the file
            data: File contents
        """
        self.file_hash = file_hash
        self.data = data
