"""Coverage tests for satoshi arithmetic utilities.

This module tests safe arithmetic operations on satoshi values.
"""

import pytest

from bsv_wallet_toolbox.errors import InvalidParameterError
from bsv_wallet_toolbox.utils.satoshi import (
    MAX_SATOSHIS,
    satoshi_add,
    satoshi_from,
    satoshi_multiply,
    satoshi_subtract,
    satoshi_sum,
)


class TestSatoshiFrom:
    """Test satoshi_from validation."""

    def test_valid_positive_satoshis(self) -> None:
        """Test valid positive satoshi amount."""
        result = satoshi_from(100_000_000)
        assert result == 100_000_000

    def test_valid_negative_satoshis(self) -> None:
        """Test valid negative satoshi amount."""
        result = satoshi_from(-100_000_000)
        assert result == -100_000_000

    def test_zero_satoshis(self) -> None:
        """Test zero satoshis."""
        result = satoshi_from(0)
        assert result == 0

    def test_max_satoshis(self) -> None:
        """Test maximum allowed satoshis."""
        result = satoshi_from(MAX_SATOSHIS)
        assert result == MAX_SATOSHIS

    def test_exceeds_max_satoshis(self) -> None:
        """Test value exceeding maximum."""
        with pytest.raises((InvalidParameterError, OverflowError)):
            satoshi_from(MAX_SATOSHIS + 1)

    def test_exceeds_min_satoshis(self) -> None:
        """Test value exceeding minimum (negative)."""
        with pytest.raises((InvalidParameterError, OverflowError)):
            satoshi_from(-MAX_SATOSHIS - 1)

    def test_non_integer_input(self) -> None:
        """Test non-integer input."""
        with pytest.raises(InvalidParameterError):
            satoshi_from(100.5)  # type: ignore


class TestSatoshiAdd:
    """Test satoshi addition."""

    def test_add_positive_values(self) -> None:
        """Test adding two positive values."""
        result = satoshi_add(100, 200)
        assert result == 300

    def test_add_negative_values(self) -> None:
        """Test adding two negative values."""
        result = satoshi_add(-100, -200)
        assert result == -300

    def test_add_mixed_values(self) -> None:
        """Test adding positive and negative values."""
        result = satoshi_add(500, -300)
        assert result == 200

    def test_add_zero(self) -> None:
        """Test adding zero."""
        result = satoshi_add(100, 0)
        assert result == 100

    def test_add_overflow(self) -> None:
        """Test addition overflow."""
        with pytest.raises((OverflowError, InvalidParameterError)):
            satoshi_add(MAX_SATOSHIS, 1)

    def test_add_underflow(self) -> None:
        """Test addition underflow."""
        with pytest.raises((OverflowError, InvalidParameterError)):
            satoshi_add(-MAX_SATOSHIS, -1)


class TestSatoshiSubtract:
    """Test satoshi subtraction."""

    def test_subtract_positive_values(self) -> None:
        """Test subtracting positive values."""
        result = satoshi_subtract(500, 200)
        assert result == 300

    def test_subtract_to_negative(self) -> None:
        """Test subtraction resulting in negative."""
        result = satoshi_subtract(100, 200)
        assert result == -100

    def test_subtract_zero(self) -> None:
        """Test subtracting zero."""
        result = satoshi_subtract(100, 0)
        assert result == 100

    def test_subtract_from_zero(self) -> None:
        """Test subtracting from zero."""
        result = satoshi_subtract(0, 100)
        assert result == -100

    def test_subtract_overflow(self) -> None:
        """Test subtraction overflow."""
        with pytest.raises((OverflowError, InvalidParameterError)):
            satoshi_subtract(MAX_SATOSHIS, -1)


class TestSatoshiMultiply:
    """Test satoshi multiplication."""

    def test_multiply_positive_values(self) -> None:
        """Test multiplying positive values."""
        result = satoshi_multiply(100, 10)
        assert result == 1000

    def test_multiply_by_zero(self) -> None:
        """Test multiplying by zero."""
        result = satoshi_multiply(1000, 0)
        assert result == 0

    def test_multiply_by_one(self) -> None:
        """Test multiplying by one."""
        result = satoshi_multiply(1000, 1)
        assert result == 1000

    def test_multiply_by_negative(self) -> None:
        """Test multiplying by negative."""
        result = satoshi_multiply(100, -10)
        assert result == -1000

    def test_multiply_overflow(self) -> None:
        """Test multiplication overflow."""
        with pytest.raises((OverflowError, InvalidParameterError)):
            satoshi_multiply(MAX_SATOSHIS, 2)


class TestSatoshiSum:
    """Test summing multiple satoshi values."""

    def test_sum_positive_values(self) -> None:
        """Test summing positive values."""
        result = satoshi_sum([100, 200, 300])
        assert result == 600

    def test_sum_mixed_values(self) -> None:
        """Test summing mixed values."""
        result = satoshi_sum([500, -200, 100])
        assert result == 400

    def test_sum_empty_list(self) -> None:
        """Test summing empty list."""
        result = satoshi_sum([])
        assert result == 0

    def test_sum_single_value(self) -> None:
        """Test summing single value."""
        result = satoshi_sum([100])
        assert result == 100

    def test_sum_overflow(self) -> None:
        """Test sum overflow."""
        with pytest.raises((OverflowError, InvalidParameterError)):
            satoshi_sum([MAX_SATOSHIS, 1])


class TestConstants:
    """Test satoshi constants."""

    def test_max_satoshis_value(self) -> None:
        """Test MAX_SATOSHIS constant."""
        assert MAX_SATOSHIS == 2_100_000_000_000_000

    def test_max_represents_21m_bitcoin(self) -> None:
        """Test MAX_SATOSHIS represents 21 million Bitcoin."""
        btc_supply = 21_000_000
        satoshis_per_btc = 100_000_000
        assert btc_supply * satoshis_per_btc == MAX_SATOSHIS


class TestEdgeCases:
    """Test edge cases in satoshi operations."""

    def test_add_to_max_then_subtract(self) -> None:
        """Test operations near maximum value."""
        # Can't add to MAX, but can subtract
        result = satoshi_subtract(MAX_SATOSHIS, 1)
        assert result == MAX_SATOSHIS - 1

    def test_alternating_operations(self) -> None:
        """Test alternating add and subtract."""
        value = satoshi_from(1000)
        value = satoshi_add(value, 500)
        value = satoshi_subtract(value, 200)
        value = satoshi_add(value, 100)
        assert value == 1400

    def test_identity_operations(self) -> None:
        """Test identity operations."""
        value = 12345
        assert satoshi_add(value, 0) == value
        assert satoshi_subtract(value, 0) == value
        assert satoshi_multiply(value, 1) == value
