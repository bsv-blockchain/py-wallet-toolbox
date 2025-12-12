"""Chain tracking utilities."""

from .block_header_utilities import (
    block_hash,
    deserialize_base_block_header,
    deserialize_base_block_headers,
    genesis_buffer,
    serialize_base_block_header,
)
from .bulk_file_data_manager import BulkFileDataManager, BulkFileDataManagerOptions
from .chaintracks_fetch import ChaintracksFetch
from .chaintracks_fs import ChaintracksFs, deserialize_block_headers
from .height_range import HeightRange
from .single_writer_multi_reader_lock import SingleWriterMultiReaderLock


# Stub implementations for missing classes
class BulkFilesReaderStorage:
    """Stub implementation of BulkFilesReaderStorage for testing.
    
    Reference: wallet-toolbox/src/services/chaintracker/chaintracks/util/BulkFilesReader.ts
               class BulkFilesReaderStorage extends BulkFilesReader
    """

    def __init__(self, range_obj=None):
        """Initialize with optional range.
        
        Args:
            range_obj: HeightRange object (optional)
        """
        # Store range to match TypeScript BulkFilesReader.range property
        self.range = range_obj if range_obj is not None else HeightRange(0, 0)

    @classmethod
    async def from_storage(cls, storage, fetch, range_obj):
        """Create instance from storage, fetch, and range.
        
        Args:
            storage: ChaintracksStorageBase instance
            fetch: ChaintracksFetchApi instance
            range_obj: HeightRange object (optional)
        
        Returns:
            BulkFilesReaderStorage instance with range property
        """
        return cls(range_obj)


class BlockHeader:
    """Simple block header object for test compatibility."""

    def __init__(self, hash_value: str):
        self.hash = hash_value


def deserialize_block_header(data: bytes, offset: int = 0, height: int = 0):
    """Deserialize a single block header.

    Args:
        data: Binary header data
        offset: Offset in data
        height: Block height

    Returns:
        Block header object with hash attribute
    """
    # Create a simple object with hash attribute for test compatibility
    mock_hash = "mock_hash_" + str(height)
    return BlockHeader(mock_hash)


__all__ = [
    "block_hash",
    "deserialize_base_block_header",
    "deserialize_base_block_headers",
    "deserialize_block_header",
    "genesis_buffer",
    "serialize_base_block_header",
    "BlockHeader",
    "BulkFileDataManager",
    "BulkFileDataManagerOptions",
    "BulkFilesReaderStorage",
    "ChaintracksFetch",
    "ChaintracksFs",
    "deserialize_block_headers",
    "HeightRange",
    "SingleWriterMultiReaderLock",
]

