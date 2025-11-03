"""Tests for Satoshi arithmetic utility functions.

Reference: go-wallet-toolbox/pkg/internal/satoshi/satoshi_test.go

These tests verify the safe arithmetic operations for Bitcoin Satoshi values,
including overflow/underflow checks and proper handling of MaxSatoshis constant.
"""

import pytest

from bsv_wallet_toolbox.errors import InvalidParameterError
from bsv_wallet_toolbox.utils.satoshi import (
    satoshi_add,
    satoshi_equal,
    satoshi_from,
    satoshi_multiply,
    satoshi_subtract,
    satoshi_sum,
    satoshi_to_uint64,
)

# MaxSatoshis constant (from BRC-100 specification)
MAX_SATOSHIS = 2100000000000000


class TestSatoshiAdd:
    """Tests for satoshi_add function."""

    def test_add_two_ints(self) -> None:
        """Given: Two positive integers
           When: Call satoshi_add
           Then: Returns their sum

        Reference: TestAdd - add two ints
        """

        result = satoshi_add(1, 2)
        assert result == 3

    def test_add_two_max_satoshis(self) -> None:
        """Given: Two MAX_SATOSHIS values
           When: Call satoshi_add
           Then: Raises OverflowError

        Reference: TestAdd - add two max satoshis
        """

        with pytest.raises((InvalidParameterError, OverflowError)):
            satoshi_add(MAX_SATOSHIS, MAX_SATOSHIS)

    def test_add_two_negative_ints(self) -> None:
        """Given: Two negative integers
           When: Call satoshi_add
           Then: Returns their sum (negative)

        Reference: TestAdd - add two negative ints
        """

        result = satoshi_add(-1, -2)
        assert result == -3

    def test_add_max_satoshis_and_negative_max_satoshis(self) -> None:
        """Given: MAX_SATOSHIS and -MAX_SATOSHIS
           When: Call satoshi_add
           Then: Returns 0

        Reference: TestAdd - add max satoshis and minus-max-satoshis
        """

        result = satoshi_add(MAX_SATOSHIS, -MAX_SATOSHIS)
        assert result == 0


class TestSatoshiSubtract:
    """Tests for satoshi_subtract function."""

    def test_subtract_two_ints(self) -> None:
        """Given: Two integers (5 - 3)
           When: Call satoshi_subtract
           Then: Returns the difference

        Reference: TestSubtract - subtract two ints
        """

        result = satoshi_subtract(5, 3)
        assert result == 2

    def test_subtract_resulting_in_zero(self) -> None:
        """Given: Two equal integers
           When: Call satoshi_subtract
           Then: Returns 0

        Reference: TestSubtract - subtract resulting in zero
        """

        result = satoshi_subtract(2, 2)
        assert result == 0

    def test_subtract_to_obtain_negative_result(self) -> None:
        """Given: Two integers where first < second
           When: Call satoshi_subtract
           Then: Returns negative result

        Reference: TestSubtract - subtract to obtain a negative result
        """

        result = satoshi_subtract(3, 5)
        assert result == -2

    def test_subtract_exceeding_max_positive_value(self) -> None:
        """Given: MAX_SATOSHIS - (-1) which would overflow
           When: Call satoshi_subtract
           Then: Raises OverflowError

        Reference: TestSubtract - subtract exceeding max positive value
        """

        with pytest.raises((InvalidParameterError, OverflowError)):
            satoshi_subtract(MAX_SATOSHIS, -1)


class TestSatoshiFrom:
    """Tests for satoshi_from function (validation)."""

    def test_from_positive_int(self) -> None:
        """Given: Positive integer
           When: Call satoshi_from
           Then: Returns the value

        Reference: TestFrom - from int
        """

        result = satoshi_from(1)
        assert result == 1

    def test_from_negative_int(self) -> None:
        """Given: Negative integer
           When: Call satoshi_from
           Then: Returns the value

        Reference: TestFrom - from negative int
        """

        result = satoshi_from(-1)
        assert result == -1

    def test_from_max_satoshi(self) -> None:
        """Given: MAX_SATOSHIS value
           When: Call satoshi_from
           Then: Returns the value

        Reference: TestFrom - from max satoshi
        """

        result = satoshi_from(MAX_SATOSHIS)
        assert result == MAX_SATOSHIS

    def test_from_max_satoshi_plus_one(self) -> None:
        """Given: MAX_SATOSHIS + 1 (exceeds limit)
           When: Call satoshi_from
           Then: Raises InvalidParameterError

        Reference: TestFrom - from max satoshi + 1
        """

        with pytest.raises(InvalidParameterError):
            satoshi_from(MAX_SATOSHIS + 1)


class TestSatoshiSum:
    """Tests for satoshi_sum function."""

    def test_sum_of_empty_sequence(self) -> None:
        """Given: Empty list
           When: Call satoshi_sum
           Then: Returns 0

        Reference: TestSum - sum of empty sequence
        """

        result = satoshi_sum([])
        assert result == 0

    def test_sum_of_multiple_elements(self) -> None:
        """Given: List of integers [1, 2, 3]
           When: Call satoshi_sum
           Then: Returns 6

        Reference: TestSum - sum of multiple elements
        """

        result = satoshi_sum([1, 2, 3])
        assert result == 6

    def test_sum_of_multiple_elements_with_different_signs(self) -> None:
        """Given: List of integers with mixed signs [1, -2, 3]
           When: Call satoshi_sum
           Then: Returns 2

        Reference: TestSum - sum of multiple elements with different signs
        """

        result = satoshi_sum([1, -2, 3])
        assert result == 2

    def test_sum_exceeding_max_satoshi_value(self) -> None:
        """Given: List [MAX_SATOSHIS, 1] which would overflow
           When: Call satoshi_sum
           Then: Raises OverflowError

        Reference: TestSum - sum exceeding max satoshi value
        """

        with pytest.raises((InvalidParameterError, OverflowError)):
            satoshi_sum([MAX_SATOSHIS, 1])


class TestSatoshiMultiply:
    """Tests for satoshi_multiply function."""

    def test_multiply_two_ints(self) -> None:
        """Given: Two integers (2 * 3)
           When: Call satoshi_multiply
           Then: Returns 6

        Reference: TestMultiply - multiply two ints
        """

        result = satoshi_multiply(2, 3)
        assert result == 6

    def test_multiplication_overflow(self) -> None:
        """Given: MAX_SATOSHIS * 2 which would overflow
           When: Call satoshi_multiply
           Then: Raises OverflowError

        Reference: TestMultiply - multiplication overflow
        """

        with pytest.raises((InvalidParameterError, OverflowError)):
            satoshi_multiply(MAX_SATOSHIS, 2)

    def test_multiply_negative_and_positive(self) -> None:
        """Given: Negative and positive integers (-2 * 4)
           When: Call satoshi_multiply
           Then: Returns -8

        Reference: TestMultiply - multiply negative and positive
        """

        result = satoshi_multiply(-2, 4)
        assert result == -8


class TestSatoshiEqual:
    """Tests for satoshi_equal function."""

    def test_equal_numbers(self) -> None:
        """Given: Two equal numbers (10, 10)
           When: Call satoshi_equal
           Then: Returns True

        Reference: TestEqual - equal numbers
        """

        result = satoshi_equal(10, 10)
        assert result is True

    def test_unequal_numbers(self) -> None:
        """Given: Two unequal numbers (10, 20)
           When: Call satoshi_equal
           Then: Returns False

        Reference: TestEqual - unequal numbers
        """

        result = satoshi_equal(10, 20)
        assert result is False

    def test_try_equal_with_max_satoshis_plus_one(self) -> None:
        """Given: 0 and MAX_SATOSHIS + 1 (invalid)
           When: Call satoshi_equal
           Then: Raises InvalidParameterError

        Reference: TestEqual - try equal with max satoshis + 1
        """

        with pytest.raises(InvalidParameterError):
            satoshi_equal(0, MAX_SATOSHIS + 1)


class TestSatoshiToUint64:
    """Tests for satoshi_to_uint64 function."""

    def test_positive_value(self) -> None:
        """Given: Positive Satoshi value (100)
           When: Call satoshi_to_uint64
           Then: Returns 100 as uint64

        Reference: TestUInt64 - positive value
        """

        result = satoshi_to_uint64(100)
        assert result == 100

    def test_negative_value(self) -> None:
        """Given: Negative Satoshi value (-50)
           When: Call satoshi_to_uint64
           Then: Raises InvalidParameterError (cannot convert negative to uint)

        Reference: TestUInt64 - negative value
        """

        with pytest.raises((InvalidParameterError, ValueError)):
            satoshi_to_uint64(-50)
