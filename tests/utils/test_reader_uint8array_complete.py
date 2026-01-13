"""Complete coverage tests for ReaderUint8Array.

This file provides comprehensive tests to achieve 100% coverage of reader_uint8array.py.
"""

import pytest

from bsv_wallet_toolbox.utils.reader_uint8array import ReaderUint8Array


class TestReaderUint8ArrayInitialization:
    """Test ReaderUint8Array initialization."""

    def test_init_with_bytes(self) -> None:
        """Test initialization with bytes."""
        data = b"\x01\x02\x03\x04"
        reader = ReaderUint8Array(data)
        assert reader.data == [1, 2, 3, 4]
        assert reader.position == 0

    def test_init_with_list(self) -> None:
        """Test initialization with list."""
        data = [1, 2, 3, 4]
        reader = ReaderUint8Array(data)
        assert reader.data == [1, 2, 3, 4]
        assert reader.position == 0

    def test_init_empty_data(self) -> None:
        """Test initialization with empty data."""
        reader = ReaderUint8Array(b"")
        assert reader.data == []
        assert reader.position == 0


class TestReadUint8:
    """Test read_uint8 method."""

    def test_read_uint8_single_byte(self) -> None:
        """Test reading single byte."""
        reader = ReaderUint8Array([0xFF])
        assert reader.read_uint8() == 0xFF
        assert reader.position == 1

    def test_read_uint8_multiple_bytes(self) -> None:
        """Test reading multiple bytes sequentially."""
        reader = ReaderUint8Array([0x01, 0x02, 0x03])
        assert reader.read_uint8() == 0x01
        assert reader.read_uint8() == 0x02
        assert reader.read_uint8() == 0x03
        assert reader.position == 3

    def test_read_uint8_at_end_raises(self) -> None:
        """Test reading past end raises IndexError."""
        reader = ReaderUint8Array([0x01])
        reader.read_uint8()  # Read the only byte

        with pytest.raises(IndexError, match="past end of data"):
            reader.read_uint8()


class TestReadUint16LE:
    """Test read_uint16_le method."""

    def test_read_uint16_le_basic(self) -> None:
        """Test reading little-endian uint16."""
        reader = ReaderUint8Array([0x01, 0x02])
        result = reader.read_uint16_le()
        assert result == 0x0201  # Little endian: 02 01
        assert reader.position == 2

    def test_read_uint16_le_max_value(self) -> None:
        """Test reading maximum uint16 value."""
        reader = ReaderUint8Array([0xFF, 0xFF])
        result = reader.read_uint16_le()
        assert result == 0xFFFF

    def test_read_uint16_le_insufficient_data(self) -> None:
        """Test reading uint16 with insufficient data."""
        reader = ReaderUint8Array([0x01])

        with pytest.raises(IndexError, match="past end of data"):
            reader.read_uint16_le()


class TestReadUint32LE:
    """Test read_uint32_le method."""

    def test_read_uint32_le_basic(self) -> None:
        """Test reading little-endian uint32."""
        reader = ReaderUint8Array([0x01, 0x02, 0x03, 0x04])
        result = reader.read_uint32_le()
        assert result == 0x04030201
        assert reader.position == 4

    def test_read_uint32_le_max_value(self) -> None:
        """Test reading maximum uint32 value."""
        reader = ReaderUint8Array([0xFF, 0xFF, 0xFF, 0xFF])
        result = reader.read_uint32_le()
        assert result == 0xFFFFFFFF

    def test_read_uint32_le_insufficient_data(self) -> None:
        """Test reading uint32 with insufficient data."""
        reader = ReaderUint8Array([0x01, 0x02, 0x03])

        with pytest.raises(IndexError, match="past end of data"):
            reader.read_uint32_le()


class TestReadUint64LE:
    """Test read_uint64_le method."""

    def test_read_uint64_le_basic(self) -> None:
        """Test reading little-endian uint64."""
        reader = ReaderUint8Array([0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08])
        result = reader.read_uint64_le()
        assert result == 0x0807060504030201
        assert reader.position == 8

    def test_read_uint64_le_max_value(self) -> None:
        """Test reading maximum uint64 value."""
        reader = ReaderUint8Array([0xFF] * 8)
        result = reader.read_uint64_le()
        assert result == 0xFFFFFFFFFFFFFFFF

    def test_read_uint64_le_insufficient_data(self) -> None:
        """Test reading uint64 with insufficient data."""
        reader = ReaderUint8Array([0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07])

        with pytest.raises(IndexError, match="past end of data"):
            reader.read_uint64_le()


class TestReadBytes:
    """Test read_bytes method."""

    def test_read_bytes_basic(self) -> None:
        """Test reading specific number of bytes."""
        reader = ReaderUint8Array([0x01, 0x02, 0x03, 0x04, 0x05])
        result = reader.read_bytes(3)
        assert result == [0x01, 0x02, 0x03]
        assert reader.position == 3

    def test_read_bytes_all(self) -> None:
        """Test reading all bytes."""
        data = [0x01, 0x02, 0x03]
        reader = ReaderUint8Array(data)
        result = reader.read_bytes(3)
        assert result == data
        assert reader.is_at_end()

    def test_read_bytes_zero(self) -> None:
        """Test reading zero bytes."""
        reader = ReaderUint8Array([0x01, 0x02])
        result = reader.read_bytes(0)
        assert result == []
        assert reader.position == 0

    def test_read_bytes_insufficient_data(self) -> None:
        """Test reading more bytes than available."""
        reader = ReaderUint8Array([0x01, 0x02])

        with pytest.raises(IndexError, match="past end of data"):
            reader.read_bytes(3)


class TestSkip:
    """Test skip method."""

    def test_skip_forward(self) -> None:
        """Test skipping forward."""
        reader = ReaderUint8Array([0x01, 0x02, 0x03, 0x04])
        reader.skip(2)
        assert reader.position == 2
        assert reader.read_uint8() == 0x03

    def test_skip_zero(self) -> None:
        """Test skipping zero bytes."""
        reader = ReaderUint8Array([0x01, 0x02])
        reader.skip(0)
        assert reader.position == 0

    def test_skip_past_end(self) -> None:
        """Test skipping past end (allowed by skip)."""
        reader = ReaderUint8Array([0x01, 0x02])
        reader.skip(5)
        assert reader.position == 5
        assert reader.is_at_end()


class TestPositionMethods:
    """Test position-related methods."""

    def test_get_position(self) -> None:
        """Test getting current position."""
        reader = ReaderUint8Array([0x01, 0x02, 0x03])
        assert reader.get_position() == 0
        reader.read_uint8()
        assert reader.get_position() == 1

    def test_set_position(self) -> None:
        """Test setting position."""
        reader = ReaderUint8Array([0x01, 0x02, 0x03, 0x04])
        reader.set_position(2)
        assert reader.position == 2
        assert reader.read_uint8() == 0x03

    def test_set_position_to_start(self) -> None:
        """Test resetting position to start."""
        reader = ReaderUint8Array([0x01, 0x02, 0x03])
        reader.read_uint8()
        reader.read_uint8()
        reader.set_position(0)
        assert reader.position == 0
        assert reader.read_uint8() == 0x01

    def test_get_remaining(self) -> None:
        """Test getting remaining bytes."""
        reader = ReaderUint8Array([0x01, 0x02, 0x03, 0x04])
        assert reader.get_remaining() == 4
        reader.read_uint8()
        assert reader.get_remaining() == 3
        reader.read_uint8()
        reader.read_uint8()
        assert reader.get_remaining() == 1
        reader.read_uint8()
        assert reader.get_remaining() == 0

    def test_get_remaining_past_end(self) -> None:
        """Test get_remaining when past end."""
        reader = ReaderUint8Array([0x01])
        reader.skip(5)
        assert reader.get_remaining() == 0

    def test_is_at_end_initially_false(self) -> None:
        """Test is_at_end initially returns False."""
        reader = ReaderUint8Array([0x01, 0x02])
        assert not reader.is_at_end()

    def test_is_at_end_after_reading_all(self) -> None:
        """Test is_at_end returns True after reading all."""
        reader = ReaderUint8Array([0x01])
        reader.read_uint8()
        assert reader.is_at_end()

    def test_is_at_end_on_empty_data(self) -> None:
        """Test is_at_end returns True on empty data."""
        reader = ReaderUint8Array([])
        assert reader.is_at_end()


class TestMixedReads:
    """Test mixed reading operations."""

    def test_mixed_reads(self) -> None:
        """Test combination of different read operations."""
        # Create data with specific layout
        data = [
            0x01,  # uint8
            0x02,
            0x03,  # uint16_le: 0x0302
            0x04,
            0x05,
            0x06,
            0x07,  # uint32_le: 0x07060504
            0xAA,
            0xBB,  # 2 bytes
        ]
        reader = ReaderUint8Array(data)

        assert reader.read_uint8() == 0x01
        assert reader.read_uint16_le() == 0x0302
        assert reader.read_uint32_le() == 0x07060504
        assert reader.read_bytes(2) == [0xAA, 0xBB]
        assert reader.is_at_end()

    def test_mixed_with_skip(self) -> None:
        """Test reads combined with skip."""
        reader = ReaderUint8Array([0x01, 0x02, 0x03, 0x04, 0x05])

        assert reader.read_uint8() == 0x01
        reader.skip(2)
        assert reader.read_uint8() == 0x04
        assert reader.get_position() == 4
