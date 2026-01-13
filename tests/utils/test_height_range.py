"""Unit tests for HeightRange.

This module tests height range utility functions.

Reference: wallet-toolbox/src/services/chaintracker/chaintracks/util/__tests/HeightRange.test.ts
"""

import pytest

try:
    from bsv_wallet_toolbox.services.chaintracker.chaintracks.util import HeightRange

    IMPORTS_AVAILABLE = True
except ImportError:
    IMPORTS_AVAILABLE = False
    HeightRange = None


def hr(a: int, b: int):
    """Helper function to create HeightRange.

    Reference: wallet-toolbox/src/services/chaintracker/chaintracks/util/__tests/HeightRange.test.ts
               const hr = (a: number, b: number) => new HeightRange(a, b)
    """
    return HeightRange(a, b)


class TestHeightRange:
    """Test suite for HeightRange.

    Reference: wallet-toolbox/src/services/chaintracker/chaintracks/util/__tests/HeightRange.test.ts
               describe('testing HeightRange')
    """

    def test_length(self) -> None:
        """Given: HeightRange instances with various min/max values
           When: Get length property
           Then: Returns correct length (max - min + 1, or 0 if invalid)

        Reference: wallet-toolbox/src/services/chaintracker/chaintracks/util/__tests/HeightRange.test.ts
                   test('length')
        """
        # Given/When/Then
        assert hr(1, 1).length == 1
        assert hr(1, 10).length == 10
        assert hr(1, 0).length == 0
        assert hr(1, -10).length == 0

    def test_copy(self) -> None:
        """Given: HeightRange instance
           When: Call copy()
           Then: Returns equivalent HeightRange

        Reference: wallet-toolbox/src/services/chaintracker/chaintracks/util/__tests/HeightRange.test.ts
                   test('copy')
        """
        # Given/When/Then
        assert hr(4, 8).copy() == hr(4, 8)

    def test_intersect(self) -> None:
        """Given: Two HeightRange instances
           When: Call intersect()
           Then: Returns intersection range or empty if no overlap

        Reference: wallet-toolbox/src/services/chaintracker/chaintracks/util/__tests/HeightRange.test.ts
                   test('intersect')
        """
        # Given/When/Then
        assert hr(4, 8).intersect(hr(1, 2)).is_empty is True
        assert hr(4, 8).intersect(hr(1, 3)).is_empty is True
        assert hr(4, 8).intersect(hr(1, 4)) == hr(4, 4)
        assert hr(4, 8).intersect(hr(1, 7)) == hr(4, 7)
        assert hr(4, 8).intersect(hr(1, 8)) == hr(4, 8)
        assert hr(4, 8).intersect(hr(1, 10)) == hr(4, 8)
        assert hr(4, 8).intersect(hr(4, 10)) == hr(4, 8)
        assert hr(4, 8).intersect(hr(5, 10)) == hr(5, 8)
        assert hr(4, 8).intersect(hr(6, 10)) == hr(6, 8)
        assert hr(4, 8).intersect(hr(7, 10)) == hr(7, 8)
        assert hr(4, 8).intersect(hr(8, 10)) == hr(8, 8)
        assert hr(4, 8).intersect(hr(9, 10)).is_empty is True
        assert hr(4, 8).intersect(hr(10, 10)).is_empty is True
        assert hr(4, -8).intersect(hr(4, 10)).is_empty is True
        assert hr(4, -8).intersect(hr(4, -10)).is_empty is True
        assert hr(4, 8).intersect(hr(9, -10)).is_empty is True

    def test_union(self) -> None:
        """Given: Two HeightRange instances
           When: Call union()
           Then: Returns union range or raises if gap exists

        Reference: wallet-toolbox/src/services/chaintracker/chaintracks/util/__tests/HeightRange.test.ts
                   test('union')
        """
        # Given/When/Then
        with pytest.raises(Exception):
            hr(4, 8).union(hr(1, 2))

        assert hr(4, 8).union(hr(1, 3)) == hr(1, 8)
        assert hr(4, 8).union(hr(1, 4)) == hr(1, 8)
        assert hr(4, 8).union(hr(1, 7)) == hr(1, 8)
        assert hr(4, 8).union(hr(1, 8)) == hr(1, 8)
        assert hr(4, 8).union(hr(1, 10)) == hr(1, 10)
        assert hr(4, 8).union(hr(4, 10)) == hr(4, 10)
        assert hr(4, 8).union(hr(5, 10)) == hr(4, 10)
        assert hr(4, 8).union(hr(6, 10)) == hr(4, 10)
        assert hr(4, 8).union(hr(7, 10)) == hr(4, 10)
        assert hr(4, 8).union(hr(8, 10)) == hr(4, 10)
        assert hr(4, 8).union(hr(9, 10)) == hr(4, 10)

        with pytest.raises(Exception):
            hr(4, 8).union(hr(10, 10))

        assert hr(4, -8).union(hr(4, 10)) == hr(4, 10)
        assert hr(4, -8).union(hr(4, -10)).is_empty is True
        assert hr(4, 8).union(hr(9, -10)) == hr(4, 8)

    def test_subtract(self) -> None:
        """Given: Two HeightRange instances
           When: Call subtract()
           Then: Returns remaining range after subtraction or raises if creates gap

        Reference: wallet-toolbox/src/services/chaintracker/chaintracks/util/__tests/HeightRange.test.ts
                   test('subtract')
        """
        # Given/When/Then
        with pytest.raises(Exception):
            hr(4, 8).subtract(hr(5, 7))

        assert hr(4, 8).subtract(hr(1, 3)) == hr(4, 8)
        assert hr(4, 8).subtract(hr(1, 4)) == hr(5, 8)
        assert hr(4, 8).subtract(hr(1, 7)) == hr(8, 8)
        assert hr(4, 8).subtract(hr(1, 8)).is_empty is True
        assert hr(4, 8).subtract(hr(1, 10)).is_empty is True
        assert hr(4, 8).subtract(hr(4, 10)).is_empty is True
        assert hr(4, 8).subtract(hr(5, 10)) == hr(4, 4)
        assert hr(4, 8).subtract(hr(6, 10)) == hr(4, 5)
        assert hr(4, 8).subtract(hr(7, 10)) == hr(4, 6)
        assert hr(4, 8).subtract(hr(8, 10)) == hr(4, 7)
        assert hr(4, 8).subtract(hr(9, 10)) == hr(4, 8)
        assert hr(4, -8).subtract(hr(4, 10)).is_empty is True
        assert hr(4, -8).subtract(hr(4, -10)).is_empty is True
        assert hr(4, 8).subtract(hr(9, -10)) == hr(4, 8)

    def test_new_height_range_default_behavior(self) -> None:
        """Given: Invalid height range with min_height > max_height
           When: Call new_height_range() with default parameters
           Then: Returns empty range (backward compatibility)

        Reference: Ensures default behavior preserves existing functionality
        """
        # Given/When/Then
        result = HeightRange.new_height_range(10, 5)
        assert result.is_empty is True

    def test_new_height_range_allow_empty_on_invalid_true(self) -> None:
        """Given: Invalid height range with min_height > max_height
           When: Call new_height_range() with allow_empty_on_invalid=True
           Then: Returns empty range

        Reference: Explicit test for allow_empty_on_invalid=True behavior
        """
        # Given/When/Then
        result = HeightRange.new_height_range(10, 5, allow_empty_on_invalid=True)
        assert result.is_empty is True

    def test_new_height_range_allow_empty_on_invalid_false_raises(self) -> None:
        """Given: Invalid height range with min_height > max_height
           When: Call new_height_range() with allow_empty_on_invalid=False
           Then: Raises ValueError with descriptive message

        Reference: Tests strict validation behavior
        """
        # Given/When/Then
        with pytest.raises(
            ValueError, match="Invalid height range: min_height \\(10\\) is greater than max_height \\(5\\)"
        ):
            HeightRange.new_height_range(10, 5, allow_empty_on_invalid=False)

    def test_new_height_range_allow_empty_on_invalid_false_valid_input(self) -> None:
        """Given: Valid height range
           When: Call new_height_range() with allow_empty_on_invalid=False
           Then: Returns valid HeightRange instance

        Reference: Ensures valid input works with strict validation enabled
        """
        # Given/When/Then
        result = HeightRange.new_height_range(5, 10, allow_empty_on_invalid=False)
        assert result.min_height == 5
        assert result.max_height == 10
        assert result.is_empty is False

    def test_new_height_range_error_message_content(self) -> None:
        """Given: Various invalid height ranges
           When: Call new_height_range() with allow_empty_on_invalid=False
           Then: Error message includes both min_height and max_height values

        Reference: Tests error message formatting with different values
        """
        # Given/When/Then
        with pytest.raises(
            ValueError, match="Invalid height range: min_height \\(1\\) is greater than max_height \\(0\\)"
        ):
            HeightRange.new_height_range(1, 0, allow_empty_on_invalid=False)

        with pytest.raises(
            ValueError, match="Invalid height range: min_height \\(100\\) is greater than max_height \\(50\\)"
        ):
            HeightRange.new_height_range(100, 50, allow_empty_on_invalid=False)
