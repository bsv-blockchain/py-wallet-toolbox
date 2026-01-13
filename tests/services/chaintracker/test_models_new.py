"""Tests for chaintracker models_new.py.

This module provides comprehensive test coverage for all classes and methods
in the models_new.py file.
"""

from unittest.mock import Mock

from bsv_wallet_toolbox.services.chaintracker.chaintracks.models_new import (
    BlockHeader,
    FiatExchangeRates,
    HeightRanges,
    InfoResponse,
    LiveBlockHeader,
    LiveOrBulkBlockHeader,
    ReorgEvent,
    StorageQueries,
)
from bsv_wallet_toolbox.services.chaintracker.chaintracks.util.height_range import HeightRange


class TestFiatExchangeRates:
    """Test FiatExchangeRates TypedDict."""

    def test_fiat_exchange_rates_typed_dict(self) -> None:
        """Test that FiatExchangeRates works as a TypedDict."""
        # Test creating with required fields
        rates: FiatExchangeRates = {
            "timestamp": "2023-01-01T00:00:00Z",
            "rates": {"USD": 50000.0, "EUR": 45000.0},
            "base": "BTC",
        }

        assert rates["timestamp"] == "2023-01-01T00:00:00Z"
        assert rates["rates"]["USD"] == 50000.0
        assert rates["base"] == "BTC"

    def test_fiat_exchange_rates_optional_fields(self) -> None:
        """Test that all fields are accessible."""
        rates: FiatExchangeRates = {"timestamp": "2023-01-01T00:00:00Z", "rates": {}, "base": "BTC"}

        # Test that we can access all expected fields
        assert "timestamp" in rates
        assert "rates" in rates
        assert "base" in rates


class TestLiveBlockHeader:
    """Test LiveBlockHeader class."""

    def test_init_default_values(self) -> None:
        """Test initialization with default values."""
        chain_block_header = {"hash": "abc123", "height": 100}

        header = LiveBlockHeader(chain_block_header)

        assert header.chain_block_header == chain_block_header
        assert header.chain_work == ""
        assert header.is_chain_tip is False
        assert header.is_active is False
        assert header.header_id == 0
        assert header.previous_header_id is None

    def test_init_with_values(self) -> None:
        """Test initialization with provided values."""
        chain_block_header = {"hash": "abc123", "height": 100}

        header = LiveBlockHeader(
            chain_block_header=chain_block_header,
            chain_work="work123",
            is_chain_tip=True,
            is_active=True,
            header_id=42,
            previous_header_id=41,
        )

        assert header.chain_block_header == chain_block_header
        assert header.chain_work == "work123"
        assert header.is_chain_tip is True
        assert header.is_active is True
        assert header.header_id == 42
        assert header.previous_header_id == 41

    def test_hash_property(self) -> None:
        """Test hash property."""
        chain_block_header = {"hash": "abc123", "height": 100}

        header = LiveBlockHeader(chain_block_header)

        assert header.hash == "abc123"

    def test_hash_property_missing(self) -> None:
        """Test hash property when hash is missing."""
        chain_block_header = {"height": 100}

        header = LiveBlockHeader(chain_block_header)

        assert header.hash == ""

    def test_height_property(self) -> None:
        """Test height property."""
        chain_block_header = {"hash": "abc123", "height": 100}

        header = LiveBlockHeader(chain_block_header)

        assert header.height == 100

    def test_height_property_missing(self) -> None:
        """Test height property when height is missing."""
        chain_block_header = {"hash": "abc123"}

        header = LiveBlockHeader(chain_block_header)

        assert header.height == 0

    def test_previous_hash_property(self) -> None:
        """Test previous_hash property."""
        chain_block_header = {"hash": "abc123", "previousHash": "prev123"}

        header = LiveBlockHeader(chain_block_header)

        assert header.previous_hash == "prev123"

    def test_previous_hash_property_missing(self) -> None:
        """Test previous_hash property when previousHash is missing."""
        chain_block_header = {"hash": "abc123"}

        header = LiveBlockHeader(chain_block_header)

        assert header.previous_hash == ""


class TestLiveOrBulkBlockHeader:
    """Test LiveOrBulkBlockHeader alias."""

    def test_alias_is_same_class(self) -> None:
        """Test that LiveOrBulkBlockHeader is an alias for LiveBlockHeader."""
        assert LiveOrBulkBlockHeader is LiveBlockHeader

    def test_can_create_via_alias(self) -> None:
        """Test that we can create instances via the alias."""
        chain_block_header = {"hash": "abc123", "height": 100}

        header = LiveOrBulkBlockHeader(chain_block_header)

        assert isinstance(header, LiveBlockHeader)
        assert header.hash == "abc123"


class TestHeightRanges:
    """Test HeightRanges class."""

    def test_init_default_values(self) -> None:
        """Test initialization with default values."""
        ranges = HeightRanges()

        assert ranges.bulk is not None
        assert ranges.live is not None
        # The exact values depend on HeightRange.new_empty_height_range()

    def test_init_with_values(self) -> None:
        """Test initialization with provided values."""
        bulk_range = Mock(spec=HeightRange)
        live_range = Mock(spec=HeightRange)

        ranges = HeightRanges(bulk=bulk_range, live=live_range)

        assert ranges.bulk == bulk_range
        assert ranges.live == live_range

    def test_validate_empty_bulk_valid_live(self) -> None:
        """Test validation with empty bulk and valid live range."""
        # Create ranges where bulk is empty and live starts at 0
        bulk_range = Mock(spec=HeightRange)
        bulk_range.is_empty.return_value = True

        live_range = Mock(spec=HeightRange)
        live_range.is_empty.return_value = False
        live_range.min_height = 0

        ranges = HeightRanges(bulk=bulk_range, live=live_range)

        # The validation currently has the check commented out, so it should pass
        result = ranges.validate()
        assert result is None

    def test_validate_non_zero_bulk_min_height(self) -> None:
        """Test validation when bulk doesn't start with genesis."""
        bulk_range = Mock(spec=HeightRange)
        bulk_range.is_empty.return_value = False
        bulk_range.min_height = 100  # Should be 0

        live_range = Mock(spec=HeightRange)
        live_range.is_empty.return_value = True

        ranges = HeightRanges(bulk=bulk_range, live=live_range)

        result = ranges.validate()
        assert result is not None
        assert "bulk storage must start with genesis header" in str(result)

    def test_validate_gap_between_bulk_and_live(self) -> None:
        """Test validation when there's a gap between bulk and live ranges."""
        bulk_range = Mock(spec=HeightRange)
        bulk_range.is_empty.return_value = False
        bulk_range.min_height = 0
        bulk_range.max_height = 100

        live_range = Mock(spec=HeightRange)
        live_range.is_empty.return_value = False
        live_range.min_height = 105  # Gap of 4 blocks (101, 102, 103, 104)

        ranges = HeightRanges(bulk=bulk_range, live=live_range)

        result = ranges.validate()
        assert result is not None
        assert "there is a gap (4) between bulk and live header storage" in str(result)

    def test_validate_no_gap(self) -> None:
        """Test validation when there's no gap between bulk and live ranges."""
        bulk_range = Mock(spec=HeightRange)
        bulk_range.is_empty.return_value = False
        bulk_range.min_height = 0
        bulk_range.max_height = 100

        live_range = Mock(spec=HeightRange)
        live_range.is_empty.return_value = False
        live_range.min_height = 101  # No gap

        ranges = HeightRanges(bulk=bulk_range, live=live_range)

        result = ranges.validate()
        assert result is None

    def test_repr(self) -> None:
        """Test string representation."""
        bulk_range = Mock(spec=HeightRange)
        bulk_range.__str__ = Mock(return_value="bulk_range")
        live_range = Mock(spec=HeightRange)
        live_range.__str__ = Mock(return_value="live_range")

        ranges = HeightRanges(bulk=bulk_range, live=live_range)

        repr_str = repr(ranges)
        assert "HeightRanges" in repr_str
        assert "bulk_range" in repr_str
        assert "live_range" in repr_str


class TestReorgEvent:
    """Test ReorgEvent class."""

    def test_init(self) -> None:
        """Test initialization."""
        old_tip = {"hash": "old123", "height": 100}
        new_tip = {"hash": "new456", "height": 101}

        event = ReorgEvent(old_tip, new_tip)

        assert event.old_tip == old_tip
        assert event.new_tip == new_tip

    def test_repr(self) -> None:
        """Test string representation."""
        old_tip = {"hash": "old123"}
        new_tip = {"hash": "new456"}

        event = ReorgEvent(old_tip, new_tip)

        repr_str = repr(event)
        assert "ReorgEvent" in repr_str
        assert "old123" in repr_str
        assert "new456" in repr_str


class TestStorageQueries:
    """Test StorageQueries protocol."""

    def test_protocol_definition(self) -> None:
        """Test that StorageQueries is a Protocol."""
        from typing import Protocol

        # Check if it's a Protocol (works across Python versions)
        assert getattr(StorageQueries, "_is_protocol", False) or issubclass(StorageQueries, Protocol)

    def test_protocol_methods_exist(self) -> None:
        """Test that all expected methods are defined in the protocol."""
        expected_methods = [
            "begin",
            "rollback",
            "commit",
            "live_header_exists",
            "get_live_header_by_hash",
            "get_active_tip_live_header",
            "set_chain_tip_by_id",
            "set_active_by_id",
            "insert_new_live_header",
            "count_live_headers",
            "get_live_header_by_height",
            "find_live_height_range",
            "find_headers_for_height_less_than_or_equal_sorted",
            "delete_live_headers_by_ids",
        ]

        for method in expected_methods:
            assert hasattr(StorageQueries, method), f"Missing method: {method}"


class TestInfoResponse:
    """Test InfoResponse class."""

    def test_init(self) -> None:
        """Test initialization."""
        response = InfoResponse(
            chain="main",
            height_bulk=1000,
            height_live=1100,
            storage="sqlite",
            bulk_ingestors=["cdn", "woc"],
            live_ingestors=["poll"],
        )

        assert response.chain == "main"
        assert response.height_bulk == 1000
        assert response.height_live == 1100
        assert response.storage == "sqlite"
        assert response.bulk_ingestors == ["cdn", "woc"]
        assert response.live_ingestors == ["poll"]

    def test_init_empty_lists(self) -> None:
        """Test initialization with empty lists."""
        response = InfoResponse(
            chain="test", height_bulk=0, height_live=0, storage="memory", bulk_ingestors=[], live_ingestors=[]
        )

        assert response.chain == "test"
        assert response.height_bulk == 0
        assert response.height_live == 0
        assert response.storage == "memory"
        assert response.bulk_ingestors == []
        assert response.live_ingestors == []


class TestBlockHeader:
    """Test BlockHeader TypedDict."""

    def test_block_header_typed_dict(self) -> None:
        """Test that BlockHeader works as a TypedDict."""
        # Test creating with all required fields
        header: BlockHeader = {
            "version": 1,
            "previousHash": "prev123",
            "merkleRoot": "merkle456",
            "time": 1234567890,
            "bits": 0x1D00FFFF,
            "nonce": 12345,
            "height": 100,
            "hash": "header789",
        }

        assert header["version"] == 1
        assert header["previousHash"] == "prev123"
        assert header["merkleRoot"] == "merkle456"
        assert header["time"] == 1234567890
        assert header["bits"] == 0x1D00FFFF
        assert header["nonce"] == 12345
        assert header["height"] == 100
        assert header["hash"] == "header789"

    def test_block_header_partial(self) -> None:
        """Test that BlockHeader can be used partially."""
        partial_header: BlockHeader = {
            "version": 2,
            "previousHash": "abc",
            "merkleRoot": "def",
            "time": 1000000,
            "bits": 0x2000FFFF,
            "nonce": 54321,
            "height": 200,
            "hash": "ghi",
        }

        # Test that we can access all expected fields
        assert "version" in partial_header
        assert "previousHash" in partial_header
        assert "merkleRoot" in partial_header
        assert "time" in partial_header
        assert "bits" in partial_header
        assert "nonce" in partial_header
        assert "height" in partial_header
        assert "hash" in partial_header
