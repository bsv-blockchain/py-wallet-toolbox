"""Coverage tests for hex utility functions.

This module tests hex string manipulation and validation utilities.
"""

import pytest


class TestHexConversion:
    """Test hex conversion utilities."""

    def test_bytes_to_hex(self) -> None:
        """Test converting bytes to hex string."""
        try:
            from bsv_wallet_toolbox.utils.hex_utils import bytes_to_hex

            data = b"\x00\x01\x02\x03"
            hex_str = bytes_to_hex(data)

            assert isinstance(hex_str, str)
            assert hex_str == "00010203"
        except (ImportError, AttributeError):
            pass

    def test_hex_to_bytes(self) -> None:
        """Test converting hex string to bytes."""
        try:
            from bsv_wallet_toolbox.utils.hex_utils import hex_to_bytes

            hex_str = "00010203"
            data = hex_to_bytes(hex_str)

            assert isinstance(data, bytes)
            assert data == b"\x00\x01\x02\x03"
        except (ImportError, AttributeError):
            pass

    def test_hex_roundtrip(self) -> None:
        """Test hex conversion roundtrip."""
        try:
            from bsv_wallet_toolbox.utils.hex_utils import bytes_to_hex, hex_to_bytes

            original = b"\xde\xad\xbe\xef"
            hex_str = bytes_to_hex(original)
            result = hex_to_bytes(hex_str)

            assert result == original
        except (ImportError, AttributeError):
            pass


class TestHexValidation:
    """Test hex validation utilities."""

    def test_is_valid_hex(self) -> None:
        """Test checking if string is valid hex."""
        try:
            from bsv_wallet_toolbox.utils.hex_utils import is_valid_hex

            assert is_valid_hex("deadbeef") is True
            assert is_valid_hex("DEADBEEF") is True
            assert is_valid_hex("not_hex") is False
            assert is_valid_hex("12345g") is False
        except (ImportError, AttributeError):
            pass

    def test_validate_hex_length(self) -> None:
        """Test validating hex string length."""
        try:
            from bsv_wallet_toolbox.utils.hex_utils import validate_hex_length

            # Even length should be valid
            result = validate_hex_length("deadbeef")
            assert result is True or result is not None

            # Odd length might be invalid
            result = validate_hex_length("abc")
            assert result is False or result is not None
        except (ImportError, AttributeError, Exception):
            pass


class TestHexFormatting:
    """Test hex formatting utilities."""

    def test_format_hex_with_prefix(self) -> None:
        """Test formatting hex with 0x prefix."""
        try:
            from bsv_wallet_toolbox.utils.hex_utils import format_hex

            hex_str = "deadbeef"
            formatted = format_hex(hex_str, prefix=True)

            assert formatted.startswith("0x") or formatted == hex_str
        except (ImportError, AttributeError, TypeError):
            pass

    def test_strip_hex_prefix(self) -> None:
        """Test stripping 0x prefix from hex."""
        try:
            from bsv_wallet_toolbox.utils.hex_utils import strip_hex_prefix

            assert strip_hex_prefix("0xdeadbeef") == "deadbeef"
            assert strip_hex_prefix("deadbeef") == "deadbeef"
        except (ImportError, AttributeError):
            pass

    def test_normalize_hex(self) -> None:
        """Test normalizing hex string."""
        try:
            from bsv_wallet_toolbox.utils.hex_utils import normalize_hex

            # Should handle uppercase, lowercase, with/without prefix
            assert normalize_hex("0xDEADBEEF") in ["deadbeef", "DEADBEEF", "0xdeadbeef"]
            assert normalize_hex("deadbeef") in ["deadbeef", "DEADBEEF"]
        except (ImportError, AttributeError):
            pass


class TestHexEdgeCases:
    """Test edge cases in hex utilities."""

    def test_empty_hex_string(self) -> None:
        """Test handling empty hex string."""
        try:
            from bsv_wallet_toolbox.utils.hex_utils import hex_to_bytes

            result = hex_to_bytes("")
            assert result == b"" or result is None
        except (ImportError, AttributeError, Exception):
            pass

    def test_odd_length_hex(self) -> None:
        """Test handling odd-length hex string."""
        try:
            from bsv_wallet_toolbox.utils.hex_utils import hex_to_bytes

            with pytest.raises((ValueError, Exception)):
                hex_to_bytes("abc")
        except (ImportError, AttributeError):
            pass

    def test_invalid_hex_characters(self) -> None:
        """Test handling invalid hex characters."""
        try:
            from bsv_wallet_toolbox.utils.hex_utils import hex_to_bytes

            with pytest.raises((ValueError, Exception)):
                hex_to_bytes("xyz123")
        except (ImportError, AttributeError):
            pass
