"""Coverage tests for format_utils.

This module tests the Format class utilities.
"""

from bsv_wallet_toolbox.utils.format_utils import Format


class TestFormat:
    """Test Format class utility methods."""

    def test_align_left_basic(self) -> None:
        """Test basic left alignment."""
        result = Format.align_left("test", 10)
        assert len(result) == 10
        assert result.startswith("test")
        assert result == "test      "

    def test_align_left_exact_width(self) -> None:
        """Test left alignment with exact width match."""
        result = Format.align_left("test", 4)
        assert result == "test"

    def test_align_left_truncate(self) -> None:
        """Test left alignment truncates long strings."""
        result = Format.align_left("verylongstring", 5)
        assert len(result) == 5
        assert result.endswith("…")

    def test_align_left_with_numbers(self) -> None:
        """Test left alignment with numeric input."""
        result = Format.align_left(12345, 8)
        assert len(result) == 8
        assert result.startswith("12345")

    def test_align_right_basic(self) -> None:
        """Test basic right alignment."""
        result = Format.align_right("test", 10)
        assert len(result) == 10
        assert result.endswith("test")
        assert result == "      test"

    def test_align_right_exact_width(self) -> None:
        """Test right alignment with exact width match."""
        result = Format.align_right("test", 4)
        assert result == "test"

    def test_align_right_truncate(self) -> None:
        """Test right alignment truncates long strings."""
        result = Format.align_right("verylongstring", 5)
        assert len(result) == 5
        # Truncated string starts with ellipsis
        assert result.startswith("…")

    def test_align_right_with_numbers(self) -> None:
        """Test right alignment with numeric input."""
        result = Format.align_right(12345, 8)
        assert len(result) == 8
        assert result.endswith("12345")

    def test_align_operations(self) -> None:
        """Test alignment operations."""
        # Only test methods that exist
        left_result = Format.align_left("test", 10)
        assert len(left_result) == 10

        right_result = Format.align_right("test", 10)
        assert len(right_result) == 10

    def test_zero_width(self) -> None:
        """Test formatting with zero or negative width."""
        result = Format.align_left("test", 0)
        assert result.endswith("…")

    def test_empty_string_alignment(self) -> None:
        """Test aligning empty string."""
        result = Format.align_left("", 5)
        assert len(result) == 5
        assert result == "     "

    def test_format_large_values(self) -> None:
        """Test formatting with large numeric values."""
        large_num = 999999999999
        result = Format.align_right(large_num, 20)
        assert len(result) == 20
        assert str(large_num) in result

    def test_format_float_values(self) -> None:
        """Test formatting with float values."""
        float_val = 123.456
        result = Format.align_left(float_val, 10)
        assert "123.456" in result
