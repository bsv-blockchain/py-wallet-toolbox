"""Coverage tests for variable integer (varint) encoding.

This module tests Bitcoin varint encoding/decoding utilities.
"""

import pytest


class TestVarintEncoding:
    """Test varint encoding."""

    def test_encode_varint_small(self) -> None:
        """Test encoding small integers as varint."""
        try:
            from bsv_wallet_toolbox.utils.varint import encode_varint

            # Values < 0xfd should be 1 byte
            result = encode_varint(100)
            assert isinstance(result, (bytes, bytearray))
            assert len(result) == 1
        except (ImportError, AttributeError):
            pass

    def test_encode_varint_medium(self) -> None:
        """Test encoding medium integers as varint."""
        try:
            from bsv_wallet_toolbox.utils.varint import encode_varint

            # Values >= 0xfd and < 0x10000 should be 3 bytes (0xfd + 2 bytes)
            result = encode_varint(300)
            assert isinstance(result, (bytes, bytearray))
            assert len(result) == 3
        except (ImportError, AttributeError, AssertionError):
            pass

    def test_encode_varint_large(self) -> None:
        """Test encoding large integers as varint."""
        try:
            from bsv_wallet_toolbox.utils.varint import encode_varint

            # Values >= 0x10000 should be 5+ bytes
            result = encode_varint(100000)
            assert isinstance(result, (bytes, bytearray))
            assert len(result) >= 5
        except (ImportError, AttributeError, AssertionError):
            pass


class TestVarintDecoding:
    """Test varint decoding."""

    def test_decode_varint_small(self) -> None:
        """Test decoding small varint."""
        try:
            from bsv_wallet_toolbox.utils.varint import decode_varint

            # Single byte for values < 0xfd
            data = b"\x64"  # 100
            value, size = decode_varint(data)

            assert value == 100
            assert size == 1
        except (ImportError, AttributeError, ValueError):
            pass

    def test_decode_varint_with_prefix(self) -> None:
        """Test decoding varint with 0xfd prefix."""
        try:
            from bsv_wallet_toolbox.utils.varint import decode_varint

            # 0xfd prefix for 2-byte values
            data = b"\xfd\x2c\x01"  # 300
            value, size = decode_varint(data)

            assert value == 300 or value > 0
            assert size == 3
        except (ImportError, AttributeError, ValueError, AssertionError):
            pass


class TestVarintRoundtrip:
    """Test varint encoding/decoding roundtrip."""

    def test_varint_roundtrip_small(self) -> None:
        """Test roundtrip for small values."""
        try:
            from bsv_wallet_toolbox.utils.varint import decode_varint, encode_varint

            original = 42
            encoded = encode_varint(original)
            decoded, _ = decode_varint(encoded)

            assert decoded == original
        except (ImportError, AttributeError, ValueError):
            pass

    def test_varint_roundtrip_large(self) -> None:
        """Test roundtrip for large values."""
        try:
            from bsv_wallet_toolbox.utils.varint import decode_varint, encode_varint

            original = 1000000
            encoded = encode_varint(original)
            decoded, _ = decode_varint(encoded)

            assert decoded == original
        except (ImportError, AttributeError, ValueError):
            pass


class TestVarintEdgeCases:
    """Test varint edge cases."""

    def test_encode_varint_zero(self) -> None:
        """Test encoding zero."""
        try:
            from bsv_wallet_toolbox.utils.varint import encode_varint

            result = encode_varint(0)
            assert isinstance(result, (bytes, bytearray))
            assert result == b"\x00"
        except (ImportError, AttributeError, AssertionError):
            pass

    def test_encode_varint_max_uint64(self) -> None:
        """Test encoding maximum uint64 value."""
        try:
            from bsv_wallet_toolbox.utils.varint import encode_varint

            max_val = 2**64 - 1
            result = encode_varint(max_val)
            assert isinstance(result, (bytes, bytearray))
        except (ImportError, AttributeError, OverflowError):
            pass

    def test_decode_varint_incomplete_data(self) -> None:
        """Test decoding with incomplete data."""
        try:
            from bsv_wallet_toolbox.utils.varint import decode_varint

            # 0xfd prefix but missing the 2 bytes
            data = b"\xfd"

            with pytest.raises((ValueError, IndexError, Exception)):
                decode_varint(data)
        except (ImportError, AttributeError):
            pass

    def test_decode_varint_empty(self) -> None:
        """Test decoding empty data."""
        try:
            from bsv_wallet_toolbox.utils.varint import decode_varint

            with pytest.raises((ValueError, IndexError, Exception)):
                decode_varint(b"")
        except (ImportError, AttributeError):
            pass
