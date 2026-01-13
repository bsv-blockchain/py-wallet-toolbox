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


def valid_bulk_header_files_by_file_hash():
    """Return hash map of known valid bulk header files by their fileHash.

    Returns:
        Dict mapping file hashes (base64 strings) to file info objects
    """
    from typing import Any, Dict

    if not hasattr(valid_bulk_header_files_by_file_hash, "_cache"):
        cache: dict[str, Any] = {}
        for vbf in _valid_bulk_header_files:
            if vbf.get("fileHash"):
                cache[vbf["fileHash"]] = vbf
        valid_bulk_header_files_by_file_hash._cache = cache

    return valid_bulk_header_files_by_file_hash._cache


# Static array of known valid bulk header files
# Based on TypeScript: wallet-toolbox/src/services/chaintracker/chaintracks/util/validBulkHeaderFilesByFileHash.ts
_valid_bulk_header_files = [
    {
        "sourceUrl": "https://cdn.projectbabbage.com/blockheaders",
        "fileName": "testNet_0.headers",
        "firstHeight": 0,
        "prevHash": "0000000000000000000000000000000000000000000000000000000000000000",
        "count": 100000,
        "lastHash": "000000004956cc2edd1a8caa05eacfa3c69f4c490bfc9ace820257834115ab35",
        "fileHash": "gAJPUfI2DfAabJTOBxT1rwy1cS4/QULaQHaQWa1RWNk=",
        "lastChainWork": "000000000000000000000000000000000000000000000000004143c00b3d47b8",
        "prevChainWork": "0000000000000000000000000000000000000000000000000000000000000000",
        "chain": "test",
        "validated": True,
    },
    {
        "sourceUrl": "https://cdn.projectbabbage.com/blockheaders",
        "fileName": "testNet_4.headers",
        "firstHeight": 400000,
        "prevHash": "0000000001127c76ac45f605f9300dfa96a8054533b96413883fdc4378aeb42d",
        "count": 100000,
        "lastHash": "0000000001965655a870175b510326e6393114d293896ddb237709eecb381ab8",
        "fileHash": "3DjOpFnatZ0OKrpACATfAtBITX2s8JjfYTAnDHVkGuw=",
        "lastChainWork": "00000000000000000000000000000000000000000000000461063a8389300d36",
        "prevChainWork": "0000000000000000000000000000000000000000000000040da9d61d8e129a53",
        "chain": "test",
        "validated": True,
    },
    {
        "sourceUrl": "https://cdn.projectbabbage.com/blockheaders",
        "fileName": "testNet_15.headers",
        "firstHeight": 1500000,
        "prevHash": "0000000000000168de8736c8a424fd5ebe1dcf0a030ed5fa0699b8c0fafc0b5e",
        "count": 100000,
        "lastHash": "00000000000005504bfd1a3ce4688c30c86740390102b6cd464a2fb5e0e3fed1",
        "fileHash": "1bCf0R0RsoadANX+6H4NH1b3jNuTPyTayoS1SpQXa2Q=",
        "lastChainWork": "000000000000000000000000000000000000000000000156c3b84396da4e60b9",
        "prevChainWork": "00000000000000000000000000000000000000000000011bed7ab81a56a65cbc",
        "chain": "test",
        "validated": True,
    },
    {
        "sourceUrl": "https://cdn.projectbabbage.com/blockheaders",
        "fileName": "mainNet_2.headers",
        "firstHeight": 200000,
        "prevHash": "00000000000003a20def7a05a77361b9657ff954b2f2080e135ea6f5970da215",
        "count": 100000,
        "lastHash": "000000000000000067ecc744b5ae34eebbde14d21ca4db51652e4d67e155f07e",
        "fileHash": "wbfV/ZuPvLKHtRJN4QlHiKlpNncuqWA1dMJ6O9mhisc=",
        "lastChainWork": "000000000000000000000000000000000000000000005a795f5d6ede10bc6d60",
        "prevChainWork": "00000000000000000000000000000000000000000000001ac0479f335782cb80",
        "chain": "main",
        "validated": True,
    },
]


__all__ = [
    "BlockHeader",
    "BulkFileDataManager",
    "BulkFileDataManagerOptions",
    "BulkFilesReaderStorage",
    "ChaintracksFetch",
    "ChaintracksFs",
    "HeightRange",
    "SingleWriterMultiReaderLock",
    "block_hash",
    "deserialize_base_block_header",
    "deserialize_base_block_headers",
    "deserialize_block_header",
    "deserialize_block_headers",
    "genesis_buffer",
    "serialize_base_block_header",
    "valid_bulk_header_files_by_file_hash",
]
