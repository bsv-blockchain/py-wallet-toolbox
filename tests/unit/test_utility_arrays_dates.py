"""Unit tests for utility array and date helper functions.

Reference: wallet-toolbox/src/utility/utilityHelpers.ts
"""

from datetime import datetime

from bsv_wallet_toolbox.utils import arrays_equal, max_date, optional_arrays_equal


class TestArraysEqual:
    """Test suite for arrays_equal function.

    Note: This test is currently skipped as the arrays_equal utility is not yet implemented.

    Reference: wallet-toolbox/src/utility/utilityHelpers.ts
               function arraysEqual
    """

    def test_returns_true_for_equal_arrays(self) -> None:
        """Given: Two arrays with same values in same order
           When: Call arrays_equal
           Then: Returns True

        Reference: wallet-toolbox/src/utility/utilityHelpers.ts
                   arraysEqual function
        """
        # Given

        arr1 = [1, 2, 3]
        arr2 = [1, 2, 3]

        # When
        result = arrays_equal(arr1, arr2)

        # Then
        assert result is True

    def test_returns_false_for_different_lengths(self) -> None:
        """Given: Two arrays with different lengths
           When: Call arrays_equal
           Then: Returns False

        Reference: wallet-toolbox/src/utility/utilityHelpers.ts
                   arraysEqual function
        """
        # Given

        arr1 = [1, 2, 3]
        arr2 = [1, 2]

        # When
        result = arrays_equal(arr1, arr2)

        # Then
        assert result is False

    def test_returns_false_for_different_values(self) -> None:
        """Given: Two arrays with same length but different values
           When: Call arrays_equal
           Then: Returns False

        Reference: wallet-toolbox/src/utility/utilityHelpers.ts
                   arraysEqual function
        """
        # Given

        arr1 = [1, 2, 3]
        arr2 = [1, 2, 4]

        # When
        result = arrays_equal(arr1, arr2)

        # Then
        assert result is False

    def test_returns_true_for_empty_arrays(self) -> None:
        """Given: Two empty arrays
           When: Call arrays_equal
           Then: Returns True

        Reference: wallet-toolbox/src/utility/utilityHelpers.ts
                   arraysEqual function
        """
        # Given

        arr1 = []
        arr2 = []

        # When
        result = arrays_equal(arr1, arr2)

        # Then
        assert result is True


class TestOptionalArraysEqual:
    """Test suite for optional_arrays_equal function.

    Note: This test is currently skipped as the optional_arrays_equal utility is not yet implemented.

    Reference: wallet-toolbox/src/utility/utilityHelpers.ts
               function optionalArraysEqual
    """

    def test_returns_true_when_both_none(self) -> None:
        """Given: Both arrays are None
           When: Call optional_arrays_equal
           Then: Returns True

        Reference: wallet-toolbox/src/utility/utilityHelpers.ts
                   optionalArraysEqual function
        """
        # Given

        # When
        result = optional_arrays_equal(None, None)

        # Then
        assert result is True

    def test_returns_false_when_one_is_none(self) -> None:
        """Given: One array is None, the other is not
           When: Call optional_arrays_equal
           Then: Returns False

        Reference: wallet-toolbox/src/utility/utilityHelpers.ts
                   optionalArraysEqual function
        """
        # Given

        # When
        result1 = optional_arrays_equal([1, 2, 3], None)
        result2 = optional_arrays_equal(None, [1, 2, 3])

        # Then
        assert result1 is False
        assert result2 is False

    def test_compares_arrays_when_both_exist(self) -> None:
        """Given: Both arrays have values
           When: Call optional_arrays_equal
           Then: Returns result of arrays_equal

        Reference: wallet-toolbox/src/utility/utilityHelpers.ts
                   optionalArraysEqual function
        """
        # Given

        # When
        result1 = optional_arrays_equal([1, 2, 3], [1, 2, 3])
        result2 = optional_arrays_equal([1, 2, 3], [1, 2, 4])

        # Then
        assert result1 is True
        assert result2 is False


class TestMaxDate:
    """Test suite for max_date function.

    Note: This test is currently skipped as the max_date utility is not yet implemented.

    Reference: wallet-toolbox/src/utility/utilityHelpers.ts
               function maxDate
    """

    def test_returns_later_date_when_both_provided(self) -> None:
        """Given: Two dates
           When: Call max_date
           Then: Returns the later date

        Reference: wallet-toolbox/src/utility/utilityHelpers.ts
                   maxDate function
        """
        # Given

        d1 = datetime(2023, 1, 1)
        d2 = datetime(2024, 1, 1)

        # When
        result = max_date(d1, d2)

        # Then
        assert result == d2

    def test_returns_earlier_date_when_later_is_first(self) -> None:
        """Given: Two dates with later date first
           When: Call max_date
           Then: Returns the later date

        Reference: wallet-toolbox/src/utility/utilityHelpers.ts
                   maxDate function
        """
        # Given

        d1 = datetime(2024, 1, 1)
        d2 = datetime(2023, 1, 1)

        # When
        result = max_date(d1, d2)

        # Then
        assert result == d1

    def test_returns_first_date_when_only_first_provided(self) -> None:
        """Given: Only first date provided
           When: Call max_date
           Then: Returns the first date

        Reference: wallet-toolbox/src/utility/utilityHelpers.ts
                   maxDate function
        """
        # Given

        d1 = datetime(2023, 1, 1)

        # When
        result = max_date(d1, None)

        # Then
        assert result == d1

    def test_returns_second_date_when_only_second_provided(self) -> None:
        """Given: Only second date provided
           When: Call max_date
           Then: Returns the second date

        Reference: wallet-toolbox/src/utility/utilityHelpers.ts
                   maxDate function
        """
        # Given

        d2 = datetime(2023, 1, 1)

        # When
        result = max_date(None, d2)

        # Then
        assert result == d2

    def test_returns_none_when_both_none(self) -> None:
        """Given: Both dates are None
           When: Call max_date
           Then: Returns None

        Reference: wallet-toolbox/src/utility/utilityHelpers.ts
                   maxDate function
        """
        # Given

        # When
        result = max_date(None, None)

        # Then
        assert result is None
