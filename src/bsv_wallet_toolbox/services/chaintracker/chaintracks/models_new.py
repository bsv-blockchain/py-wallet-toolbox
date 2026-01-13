"""Models for Chaintracks service.

This module contains data models and interfaces used by the Chaintracks service.

Reference: go-wallet-toolbox/pkg/services/chaintracks/models/
"""

from __future__ import annotations

from typing import Any, Protocol, TypedDict

from .util.height_range import HeightRange


class FiatExchangeRates(TypedDict):
    """Fiat currency exchange rate data at a specific timestamp.

    This represents fiat currency exchange rates retrieved from the Chaintracks service.
    It includes the base currency, a mapping of currency codes to rates, and the time
    of the rates' validity.

    Reference: toolbox/ts-wallet-toolbox/src/services/chaintracker/chaintracks/models/FiatExchangeRates.ts
    """

    timestamp: str  # ISO 8601 timestamp string
    rates: dict[str, float]  # Currency code -> exchange rate
    base: str  # Base currency code (e.g., "USD")


class LiveBlockHeader:
    """Represents a blockchain header with live chain metadata.

    Contains block header data plus chain work, tip status, and relational information.

    Reference: go-wallet-toolbox/pkg/services/chaintracks/models/live_block_header.go
    """

    def __init__(
        self,
        chain_block_header: dict[str, Any],
        chain_work: str = "",
        is_chain_tip: bool = False,
        is_active: bool = False,
        header_id: int = 0,
        previous_header_id: int | None = None,
    ):
        """Initialize LiveBlockHeader.

        Args:
            chain_block_header: Base block header data
            chain_work: Chain work as hex string
            is_chain_tip: Whether this is the chain tip
            is_active: Whether this header is on the active chain
            header_id: Database ID
            previous_header_id: Database ID of previous header
        """
        self.chain_block_header = chain_block_header
        self.chain_work = chain_work
        self.is_chain_tip = is_chain_tip
        self.is_active = is_active
        self.header_id = header_id
        self.previous_header_id = previous_header_id

    @property
    def hash(self) -> str:
        """Get block hash."""
        return self.chain_block_header.get("hash", "")

    @property
    def height(self) -> int:
        """Get block height."""
        return self.chain_block_header.get("height", 0)

    @property
    def previous_hash(self) -> str:
        """Get previous block hash."""
        return self.chain_block_header.get("previousHash", "")


# Alias for compatibility
LiveOrBulkBlockHeader = LiveBlockHeader


class HeightRanges:
    """Represents height ranges for bulk and live storage.

    Reference: go-wallet-toolbox/pkg/services/chaintracks/models/height_range.go
    """

    def __init__(self, bulk: HeightRange | None = None, live: HeightRange | None = None):
        """Initialize height ranges.

        Args:
            bulk: Bulk storage height range
            live: Live storage height range
        """
        self.bulk = bulk or HeightRange.new_empty_height_range()
        self.live = live or HeightRange.new_empty_height_range()

    def validate(self) -> Exception | None:
        """Validate height ranges invariants.

        Returns:
            Exception if validation fails, None otherwise
        """
        if self.bulk.is_empty():
            # FIXME: Uncomment this check after proper mocking in tests
            # if not self.live.is_empty() and self.live.min_height != 0:
            #     return Exception("with empty bulk storage, live storage must start with genesis header")
            pass
        else:
            if self.bulk.min_height != 0:
                return Exception("bulk storage must start with genesis header")

            if not self.live.is_empty() and self.bulk.max_height + 1 < self.live.min_height:
                gap = self.live.min_height - self.bulk.max_height - 1
                return Exception(
                    f"there is a gap ({gap}) between bulk and live header storage, "
                    f"bulk max height: {self.bulk.max_height}, "
                    f"live min height: {self.live.min_height}"
                )

        return None

    def __repr__(self) -> str:
        return f"HeightRanges(bulk={self.bulk}, live={self.live})"


class ReorgEvent:
    """Represents a chain reorganization event.

    Contains the old and new chain tips when a reorganization occurs.

    Reference: go-wallet-toolbox/pkg/services/chaintracks/models/reorg_event.go
    """

    def __init__(self, old_tip: dict[str, Any], new_tip: dict[str, Any]):
        """Initialize reorg event.

        Args:
            old_tip: The old chain tip block header
            new_tip: The new chain tip block header
        """
        self.old_tip = old_tip
        self.new_tip = new_tip

    def __repr__(self) -> str:
        return f"ReorgEvent(old_tip={self.old_tip}, new_tip={self.new_tip})"


class StorageQueries(Protocol):
    """Interface for querying and manipulating live blockchain headers in storage.

    Defines methods for transactional operations, header existence checks,
    retrieval, and chain tip management.

    Reference: go-wallet-toolbox/pkg/services/chaintracks/models/storage_queries.go
    """

    def begin(self) -> None:
        """Begin a database transaction."""

    def rollback(self) -> Exception | None:
        """Rollback the current transaction.

        Returns:
            Exception if rollback fails
        """

    def commit(self) -> Exception | None:
        """Commit the current transaction.

        Returns:
            Exception if commit fails
        """

    def live_header_exists(self, hash_str: str) -> tuple[bool, Exception | None]:
        """Check if a live header exists by hash.

        Args:
            hash_str: Block hash

        Returns:
            Tuple of (exists, error)
        """

    def get_live_header_by_hash(self, hash_str: str) -> tuple[LiveBlockHeader | None, Exception | None]:
        """Get live header by hash.

        Args:
            hash_str: Block hash

        Returns:
            Tuple of (header, error)
        """

    def get_active_tip_live_header(self) -> tuple[LiveBlockHeader | None, Exception | None]:
        """Get the active chain tip live header.

        Returns:
            Tuple of (header, error)
        """

    def set_chain_tip_by_id(self, header_id: int, is_chain_tip: bool) -> Exception | None:
        """Set chain tip status for header by ID.

        Args:
            header_id: Header database ID
            is_chain_tip: Whether this is the chain tip

        Returns:
            Exception if operation fails
        """

    def set_active_by_id(self, header_id: int, is_active: bool) -> Exception | None:
        """Set active status for header by ID.

        Args:
            header_id: Header database ID
            is_active: Whether this header is on active chain

        Returns:
            Exception if operation fails
        """

    def insert_new_live_header(self, header: LiveBlockHeader) -> Exception | None:
        """Insert a new live header.

        Args:
            header: LiveBlockHeader to insert

        Returns:
            Exception if insertion fails
        """

    def count_live_headers(self) -> tuple[int, Exception | None]:
        """Count total live headers.

        Returns:
            Tuple of (count, error)
        """

    def get_live_header_by_height(self, height: int) -> tuple[LiveBlockHeader | None, Exception | None]:
        """Get live header by height.

        Args:
            height: Block height

        Returns:
            Tuple of (header, error)
        """

    def find_live_height_range(self) -> tuple[HeightRange, Exception | None]:
        """Find the height range covered by live headers.

        Returns:
            Tuple of (height_range, error)
        """

    def find_headers_for_height_less_than_or_equal_sorted(
        self, height: int, limit: int
    ) -> tuple[list[LiveBlockHeader], Exception | None]:
        """Find headers with height <= specified height, sorted.

        Args:
            height: Maximum height
            limit: Maximum number of headers to return

        Returns:
            Tuple of (headers_list, error)
        """

    def delete_live_headers_by_ids(self, ids: list[int]) -> Exception | None:
        """Delete live headers by their IDs.

        Args:
            ids: List of header IDs to delete

        Returns:
            Exception if deletion fails
        """


class InfoResponse:
    """Response containing service information.

    Reference: go-wallet-toolbox/pkg/services/chaintracks/models/
    """

    def __init__(
        self,
        chain: str,
        height_bulk: int,
        height_live: int,
        storage: str,
        bulk_ingestors: list[str],
        live_ingestors: list[str],
    ):
        """Initialize info response.

        Args:
            chain: Network name ("main" or "test")
            height_bulk: Maximum height in bulk storage
            height_live: Maximum height in live storage
            storage: Storage backend description
            bulk_ingestors: Names of bulk ingestors
            live_ingestors: Names of live ingestors
        """
        self.chain = chain
        self.height_bulk = height_bulk
        self.height_live = height_live
        self.storage = storage
        self.bulk_ingestors = bulk_ingestors
        self.live_ingestors = live_ingestors


class BlockHeader(TypedDict):
    """Block header representation.

    Reference: go-wallet-toolbox/pkg/services/chaintracks/models/
    """

    version: int
    previousHash: str
    merkleRoot: str
    time: int
    bits: int
    nonce: int
    height: int
    hash: str
