"""Complete coverage tests for buffer_utils module.

This file provides comprehensive tests to achieve 100% coverage of buffer_utils.py.
"""

import base64

import pytest

from bsv_wallet_toolbox.utils.buffer_utils import as_array, as_buffer, as_string, as_uint8array


class TestAsBuffer:
    """Test as_buffer function."""

    def test_as_buffer_with_bytes(self) -> None:
        """Test as_buffer with bytes input."""
        data = b"hello"
        result = as_buffer(data)
        assert result == b"hello"
        assert isinstance(result, bytes)

    def test_as_buffer_with_list(self) -> None:
        """Test as_buffer with list input."""
        data = [0x48, 0x65, 0x6C, 0x6C, 0x6F]
        result = as_buffer(data)
        assert result == b"Hello"

    def test_as_buffer_with_hex_string(self) -> None:
        """Test as_buffer with hex string."""
        data = "48656c6c6f"
        result = as_buffer(data, encoding="hex")
        assert result == b"Hello"

    def test_as_buffer_with_utf8_string(self) -> None:
        """Test as_buffer with utf8 string."""
        data = "Hello"
        result = as_buffer(data, encoding="utf8")
        assert result == b"Hello"

    def test_as_buffer_with_base64_string(self) -> None:
        """Test as_buffer with base64 string."""
        data = base64.b64encode(b"Hello").decode("ascii")
        result = as_buffer(data, encoding="base64")
        assert result == b"Hello"

    def test_as_buffer_with_invalid_type(self) -> None:
        """Test as_buffer with invalid type raises TypeError."""
        with pytest.raises(TypeError, match="Cannot convert"):
            as_buffer(123)  # type: ignore

    def test_as_buffer_empty_bytes(self) -> None:
        """Test as_buffer with empty bytes."""
        result = as_buffer(b"")
        assert result == b""

    def test_as_buffer_empty_list(self) -> None:
        """Test as_buffer with empty list."""
        result = as_buffer([])
        assert result == b""


class TestAsString:
    """Test as_string function."""

    def test_as_string_bytes_to_hex(self) -> None:
        """Test as_string converts bytes to hex."""
        data = b"Hello"
        result = as_string(data, enc="hex", return_enc="hex")
        assert result == "48656c6c6f"

    def test_as_string_bytes_to_base64(self) -> None:
        """Test as_string converts bytes to base64."""
        data = b"Hello"
        result = as_string(data, enc="hex", return_enc="base64")
        assert result == base64.b64encode(b"Hello").decode("ascii")

    def test_as_string_bytes_to_utf8(self) -> None:
        """Test as_string converts bytes to utf8."""
        data = b"Hello"
        result = as_string(data, enc="hex", return_enc="utf8")
        assert result == "Hello"

    def test_as_string_hex_to_hex(self) -> None:
        """Test as_string with hex input and output."""
        data = "48656c6c6f"
        result = as_string(data, enc="hex", return_enc="hex")
        assert result == "48656c6c6f"

    def test_as_string_hex_to_utf8(self) -> None:
        """Test as_string converts hex to utf8."""
        data = "48656c6c6f"
        result = as_string(data, enc="hex", return_enc="utf8")
        assert result == "Hello"

    def test_as_string_utf8_to_hex(self) -> None:
        """Test as_string converts utf8 to hex."""
        data = "Hello"
        result = as_string(data, enc="utf8", return_enc="hex")
        assert result == "48656c6c6f"

    def test_as_string_utf8_to_utf8(self) -> None:
        """Test as_string with utf8 input and output (no conversion)."""
        data = "Hello"
        result = as_string(data, enc="utf8", return_enc="utf8")
        assert result == "Hello"

    def test_as_string_base64_to_hex(self) -> None:
        """Test as_string converts base64 to hex."""
        data = base64.b64encode(b"Hello").decode("ascii")
        result = as_string(data, enc="base64", return_enc="hex")
        assert result == "48656c6c6f"

    def test_as_string_list_to_hex(self) -> None:
        """Test as_string converts list to hex."""
        data = [0x48, 0x65, 0x6C, 0x6C, 0x6F]
        result = as_string(data, enc="hex", return_enc="hex")
        assert result == "48656c6c6f"

    def test_as_string_list_to_utf8(self) -> None:
        """Test as_string converts list to utf8."""
        data = [0x48, 0x65, 0x6C, 0x6C, 0x6F]
        result = as_string(data, enc="hex", return_enc="utf8")
        assert result == "Hello"

    def test_as_string_list_to_base64(self) -> None:
        """Test as_string converts list to base64."""
        data = [0x48, 0x65, 0x6C, 0x6C, 0x6F]
        result = as_string(data, enc="hex", return_enc="base64")
        assert result == base64.b64encode(b"Hello").decode("ascii")

    def test_as_string_defaults_return_enc_to_enc(self) -> None:
        """Test as_string defaults return_enc to enc."""
        data = b"Hello"
        result = as_string(data, enc="hex")
        assert result == "48656c6c6f"

    def test_as_string_with_unsupported_encoding(self) -> None:
        """Test as_string with unsupported encoding raises ValueError."""
        # When enc and return_enc differ, it tries to convert and should raise ValueError
        with pytest.raises(ValueError, match="Unsupported input encoding"):
            as_string("Hello", enc="invalid", return_enc="hex")  # type: ignore

    def test_as_string_with_invalid_type(self) -> None:
        """Test as_string with invalid type raises TypeError."""
        with pytest.raises(TypeError, match="Cannot convert"):
            as_string(123, enc="hex")  # type: ignore


class TestAsArray:
    """Test as_array function."""

    def test_as_array_with_list(self) -> None:
        """Test as_array with list input."""
        data = [0x48, 0x65, 0x6C, 0x6C, 0x6F]
        result = as_array(data)
        assert result == [0x48, 0x65, 0x6C, 0x6C, 0x6F]
        assert isinstance(result, list)

    def test_as_array_with_bytes(self) -> None:
        """Test as_array with bytes input."""
        data = b"Hello"
        result = as_array(data)
        assert result == [0x48, 0x65, 0x6C, 0x6C, 0x6F]

    def test_as_array_with_hex_string(self) -> None:
        """Test as_array with hex string."""
        data = "48656c6c6f"
        result = as_array(data, encoding="hex")
        assert result == [0x48, 0x65, 0x6C, 0x6C, 0x6F]

    def test_as_array_with_utf8_string(self) -> None:
        """Test as_array with utf8 string."""
        data = "Hello"
        result = as_array(data, encoding="utf8")
        assert result == [0x48, 0x65, 0x6C, 0x6C, 0x6F]

    def test_as_array_with_base64_string(self) -> None:
        """Test as_array with base64 string."""
        data = base64.b64encode(b"Hello").decode("ascii")
        result = as_array(data, encoding="base64")
        assert result == [0x48, 0x65, 0x6C, 0x6C, 0x6F]

    def test_as_array_with_invalid_type(self) -> None:
        """Test as_array with invalid type raises TypeError."""
        with pytest.raises(TypeError, match="Cannot convert"):
            as_array(123)  # type: ignore

    def test_as_array_empty(self) -> None:
        """Test as_array with empty input."""
        assert as_array([]) == []
        assert as_array(b"") == []
        assert as_array("", encoding="hex") == []


class TestAsUint8Array:
    """Test as_uint8array function."""

    def test_as_uint8array_with_bytes(self) -> None:
        """Test as_uint8array with bytes input."""
        data = b"Hello"
        result = as_uint8array(data)
        assert result == b"Hello"
        assert isinstance(result, bytes)

    def test_as_uint8array_with_list(self) -> None:
        """Test as_uint8array with list input."""
        data = [0x48, 0x65, 0x6C, 0x6C, 0x6F]
        result = as_uint8array(data)
        assert result == b"Hello"

    def test_as_uint8array_with_hex_string(self) -> None:
        """Test as_uint8array with hex string."""
        data = "48656c6c6f"
        result = as_uint8array(data, encoding="hex")
        assert result == b"Hello"

    def test_as_uint8array_with_utf8_string(self) -> None:
        """Test as_uint8array with utf8 string."""
        data = "Hello"
        result = as_uint8array(data, encoding="utf8")
        assert result == b"Hello"

    def test_as_uint8array_with_base64_string(self) -> None:
        """Test as_uint8array with base64 string."""
        data = base64.b64encode(b"Hello").decode("ascii")
        result = as_uint8array(data, encoding="base64")
        assert result == b"Hello"

    def test_as_uint8array_with_invalid_type(self) -> None:
        """Test as_uint8array with invalid type raises TypeError."""
        with pytest.raises(TypeError, match="Cannot convert"):
            as_uint8array(123)  # type: ignore

    def test_as_uint8array_empty(self) -> None:
        """Test as_uint8array with empty input."""
        assert as_uint8array([]) == b""
        assert as_uint8array(b"") == b""


class TestEdgeCases:
    """Test edge cases and special scenarios."""

    def test_round_trip_conversions(self) -> None:
        """Test round-trip conversions maintain data integrity."""
        original = b"Test Data 123!"

        # bytes -> hex -> bytes
        hex_str = as_string(original, enc="hex", return_enc="hex")
        recovered = as_buffer(hex_str, encoding="hex")
        assert recovered == original

        # bytes -> base64 -> bytes
        b64_str = as_string(original, enc="hex", return_enc="base64")
        recovered = as_buffer(b64_str, encoding="base64")
        assert recovered == original

        # bytes -> list -> bytes
        arr = as_array(original)
        recovered = as_buffer(arr)
        assert recovered == original

    def test_unicode_string_handling(self) -> None:
        """Test handling of unicode strings."""
        data = "Hello 世界"
        result = as_buffer(data, encoding="utf8")
        recovered = as_string(result, enc="hex", return_enc="utf8")
        assert recovered == data

    def test_large_data(self) -> None:
        """Test with large data."""
        large_data = bytes(range(256)) * 100  # 25.6KB

        # Test as_array
        arr = as_array(large_data)
        assert len(arr) == 25600

        # Test as_string
        hex_str = as_string(large_data, enc="hex", return_enc="hex")
        assert len(hex_str) == 51200  # 2 chars per byte

        # Test round-trip
        recovered = as_buffer(hex_str, encoding="hex")
        assert recovered == large_data
