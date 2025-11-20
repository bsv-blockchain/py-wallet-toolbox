"""Height range utility for blockchain operations.

Reference: wallet-toolbox/src/services/chaintracker/chaintracks/util/HeightRange.ts
"""

from __future__ import annotations


class HeightRange:
    """Represents a range of block heights [min, max].

    Reference: wallet-toolbox/src/services/chaintracker/chaintracks/util/HeightRange.ts
    """

    def __init__(self, min_height: int, max_height: int):
        """Initialize height range.

        Args:
            min_height: Minimum block height (inclusive)
            max_height: Maximum block height (inclusive)
        """
        self.min = min_height
        self.max = max_height
        # Aliases for compatibility
        self.min_height = min_height
        self.max_height = max_height

    @property
    def length(self) -> int:
        """Get length of range (max - min + 1), or 0 if invalid.

        Returns:
            Number of blocks in range, or 0 if min > max
        """
        if self.min > self.max:
            return 0
        return self.max - self.min + 1

    @property
    def is_empty(self) -> bool:
        """Check if range is empty (min > max).

        Returns:
            True if range is empty
        """
        return self.min > self.max

    def copy(self) -> HeightRange:
        """Create a copy of this range.

        Returns:
            New HeightRange instance with same min/max
        """
        return HeightRange(self.min, self.max)

    def intersect(self, other: HeightRange) -> HeightRange:
        """Get intersection of this range with another.

        Args:
            other: Another HeightRange

        Returns:
            HeightRange representing intersection (may be empty)
        """
        new_min = max(self.min, other.min)
        new_max = min(self.max, other.max)
        return HeightRange(new_min, new_max)

    def union(self, other: HeightRange) -> HeightRange:
        """Get union of this range with another.

        Args:
            other: Another HeightRange

        Returns:
            HeightRange representing union

        Raises:
            Exception: If ranges have a gap between them
        """
        # Check if one or both ranges are empty
        if self.is_empty and other.is_empty:
            return HeightRange(self.min, self.max)  # Return empty range
        if self.is_empty:
            return other.copy()
        if other.is_empty:
            return self.copy()

        # Check if ranges are adjacent or overlapping
        if self.max + 1 < other.min or other.max + 1 < self.min:
            raise Exception("Cannot union ranges with gap")

        new_min = min(self.min, other.min)
        new_max = max(self.max, other.max)
        return HeightRange(new_min, new_max)

    def subtract(self, other: HeightRange) -> HeightRange:
        """Subtract another range from this one.

        Args:
            other: HeightRange to subtract

        Returns:
            Remaining HeightRange after subtraction

        Raises:
            Exception: If subtraction would create a hole in the middle
        """
        # Handle empty ranges
        if self.is_empty or other.is_empty:
            return self.copy()

        # No overlap - return original
        if other.max < self.min or other.min > self.max:
            return self.copy()

        # Check if subtraction would create a hole in the middle
        if other.min > self.min and other.max < self.max:
            raise Exception("Cannot subtract range that creates hole")

        # Complete removal
        if other.min <= self.min and other.max >= self.max:
            return HeightRange(self.min, self.min - 1)  # Empty range

        # Left side subtraction
        if other.min <= self.min:
            return HeightRange(other.max + 1, self.max)

        # Right side subtraction
        return HeightRange(self.min, other.min - 1)

    def __eq__(self, other: object) -> bool:
        """Check equality with another HeightRange.

        Args:
            other: Another HeightRange

        Returns:
            True if both have same min and max
        """
        if not isinstance(other, HeightRange):
            return False
        return self.min == other.min and self.max == other.max

    def __repr__(self) -> str:
        """String representation.

        Returns:
            String like "HeightRange(min=4, max=8)"
        """
        return f"HeightRange(min={self.min}, max={self.max})"

