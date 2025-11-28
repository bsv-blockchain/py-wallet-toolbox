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
