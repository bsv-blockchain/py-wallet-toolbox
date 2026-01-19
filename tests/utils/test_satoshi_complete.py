"""Complete coverage tests for satoshi utilities.

This file provides comprehensive tests to achieve 100% coverage of satoshi.py.
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
    """Test satoshi_from function."""

    def test_satoshi_from_valid_positive(self) -> None:
        """Test satoshi_from with valid positive value."""
        assert satoshi_from(1000) == 1000
        assert satoshi_from(MAX_SATOSHIS) == MAX_SATOSHIS

    def test_satoshi_from_valid_negative(self) -> None:
        """Test satoshi_from with valid negative value."""
        assert satoshi_from(-1000) == -1000
        assert satoshi_from(-MAX_SATOSHIS) == -MAX_SATOSHIS

    def test_satoshi_from_zero(self) -> None:
        """Test satoshi_from with zero."""
        assert satoshi_from(0) == 0

    def test_satoshi_from_exceeds_max(self) -> None:
        """Test satoshi_from with value exceeding max."""
        with pytest.raises(InvalidParameterError):
            satoshi_from(MAX_SATOSHIS + 1)

    def test_satoshi_from_exceeds_min(self) -> None:
        """Test satoshi_from with value below min."""
        with pytest.raises(InvalidParameterError):
            satoshi_from(-MAX_SATOSHIS - 1)

    def test_satoshi_from_non_integer(self) -> None:
        """Test satoshi_from with non-integer type."""
        with pytest.raises(InvalidParameterError, match="an integer"):
            satoshi_from(100.5)  # type: ignore


class TestSatoshiAdd:
    """Test satoshi_add function."""

    def test_satoshi_add_positive_values(self) -> None:
        """Test adding positive values."""
        assert satoshi_add(100, 200) == 300
        assert satoshi_add(1000, 2000) == 3000

    def test_satoshi_add_negative_values(self) -> None:
        """Test adding negative values."""
        assert satoshi_add(-100, -200) == -300

    def test_satoshi_add_mixed_signs(self) -> None:
        """Test adding values with different signs."""
        assert satoshi_add(500, -300) == 200
        assert satoshi_add(-500, 300) == -200

    def test_satoshi_add_with_zero(self) -> None:
        """Test adding zero."""
        assert satoshi_add(1000, 0) == 1000
        assert satoshi_add(0, 1000) == 1000

    def test_satoshi_add_overflow(self) -> None:
        """Test satoshi_add overflow detection."""
        with pytest.raises(OverflowError):
            satoshi_add(MAX_SATOSHIS, 1)

    def test_satoshi_add_underflow(self) -> None:
        """Test satoshi_add underflow detection."""
        with pytest.raises(OverflowError):
            satoshi_add(-MAX_SATOSHIS, -1)

    def test_satoshi_add_invalid_input(self) -> None:
        """Test satoshi_add with invalid inputs."""
        with pytest.raises(InvalidParameterError):
            satoshi_add(MAX_SATOSHIS + 1, 0)


class TestSatoshiSubtract:
    """Test satoshi_subtract function."""

    def test_satoshi_subtract_positive_values(self) -> None:
        """Test subtracting positive values."""
        assert satoshi_subtract(500, 300) == 200
        assert satoshi_subtract(1000, 1000) == 0

    def test_satoshi_subtract_negative_values(self) -> None:
        """Test subtracting negative values."""
        assert satoshi_subtract(-100, -200) == 100

    def test_satoshi_subtract_mixed_signs(self) -> None:
        """Test subtracting values with different signs."""
        assert satoshi_subtract(500, -300) == 800
        assert satoshi_subtract(-500, 300) == -800

    def test_satoshi_subtract_overflow(self) -> None:
        """Test satoshi_subtract overflow detection."""
        with pytest.raises(OverflowError):
            satoshi_subtract(MAX_SATOSHIS, -1)

    def test_satoshi_subtract_underflow(self) -> None:
        """Test satoshi_subtract underflow detection."""
        with pytest.raises(OverflowError):
            satoshi_subtract(-MAX_SATOSHIS, 1)


class TestSatoshiSum:
    """Test satoshi_sum function."""

    def test_satoshi_sum_positive_values(self) -> None:
        """Test summing positive values."""
        assert satoshi_sum([100, 200, 300]) == 600
        assert satoshi_sum([1000]) == 1000

    def test_satoshi_sum_empty_list(self) -> None:
        """Test summing empty list."""
        assert satoshi_sum([]) == 0

    def test_satoshi_sum_with_negatives(self) -> None:
        """Test summing with negative values."""
        assert satoshi_sum([100, -50, 200]) == 250
        assert satoshi_sum([-100, -200, -300]) == -600

    def test_satoshi_sum_with_zeros(self) -> None:
        """Test summing with zeros."""
        assert satoshi_sum([100, 0, 200, 0]) == 300

    def test_satoshi_sum_overflow(self) -> None:
        """Test satoshi_sum overflow detection."""
        with pytest.raises(OverflowError):
            satoshi_sum([MAX_SATOSHIS, 1])

    def test_satoshi_sum_invalid_value_in_list(self) -> None:
        """Test satoshi_sum with invalid value in list."""
        with pytest.raises(InvalidParameterError):
            satoshi_sum([MAX_SATOSHIS + 1, 0])


class TestSatoshiMultiply:
    """Test satoshi_multiply function."""

    def test_satoshi_multiply_positive_values(self) -> None:
        """Test multiplying positive values."""
        assert satoshi_multiply(10, 20) == 200
        assert satoshi_multiply(100, 100) == 10000

    def test_satoshi_multiply_by_zero(self) -> None:
        """Test multiplying by zero."""
        assert satoshi_multiply(1000, 0) == 0
        assert satoshi_multiply(0, 1000) == 0

    def test_satoshi_multiply_by_one(self) -> None:
        """Test multiplying by one."""
        assert satoshi_multiply(1000, 1) == 1000
        assert satoshi_multiply(1, 1000) == 1000

    def test_satoshi_multiply_negative_values(self) -> None:
        """Test multiplying negative values."""
        assert satoshi_multiply(-10, 20) == -200
        assert satoshi_multiply(10, -20) == -200
        assert satoshi_multiply(-10, -20) == 200

    def test_satoshi_multiply_overflow(self) -> None:
        """Test satoshi_multiply overflow detection."""
        with pytest.raises(OverflowError):
            satoshi_multiply(MAX_SATOSHIS, 2)

    def test_satoshi_multiply_invalid_input(self) -> None:
        """Test satoshi_multiply with invalid inputs."""
        with pytest.raises(InvalidParameterError):
            satoshi_multiply(MAX_SATOSHIS + 1, 1)


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_max_satoshis_constant(self) -> None:
        """Test MAX_SATOSHIS constant value."""
        assert MAX_SATOSHIS == 2_100_000_000_000_000

    def test_operations_at_boundaries(self) -> None:
        """Test operations at MAX_SATOSHIS boundaries."""
        # These should work
        assert satoshi_from(MAX_SATOSHIS) == MAX_SATOSHIS
        assert satoshi_from(-MAX_SATOSHIS) == -MAX_SATOSHIS
        assert satoshi_add(MAX_SATOSHIS, 0) == MAX_SATOSHIS
        assert satoshi_subtract(MAX_SATOSHIS, 0) == MAX_SATOSHIS

        # These should overflow
        with pytest.raises(OverflowError):
            satoshi_add(MAX_SATOSHIS, 1)
        with pytest.raises(OverflowError):
            satoshi_subtract(-MAX_SATOSHIS, 1)

    def test_chained_operations(self) -> None:
        """Test chaining multiple operations."""
        result = satoshi_add(100, 200)
        result = satoshi_subtract(result, 50)
        result = satoshi_multiply(result, 2)
        assert result == 500

    def test_sum_with_generator(self) -> None:
        """Test satoshi_sum with generator expression."""
        gen = (i * 100 for i in range(1, 6))
        result = satoshi_sum(gen)
        assert result == 1500  # 100 + 200 + 300 + 400 + 500
