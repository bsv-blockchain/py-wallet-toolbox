"""Height range utility for blockchain operations.

Reference: go-wallet-toolbox/pkg/services/chaintracks/models/height_range.go
"""

from __future__ import annotations


class HeightRange:
    """Represents a contiguous range of block heights.

    A HeightRange defines a range of block heights from MinHeight to MaxHeight (inclusive).
    Can represent an empty range when is_empty is True.

    Reference: go-wallet-toolbox/pkg/services/chaintracks/models/height_range.go
    """

    def __init__(self, min_height: int = 0, max_height: int = 0, is_empty: bool = False):
        """Initialize height range.

        Args:
            min_height: Minimum block height (inclusive)
            max_height: Maximum block height (inclusive)
            is_empty: Whether this represents an empty range
        """
        self.min_height = min_height
        self.max_height = max_height
        self._is_empty = is_empty

    @classmethod
    def new_height_range(
        cls,
        min_height: int,
        max_height: int,
        *,
        allow_empty_on_invalid: bool = True,
    ) -> HeightRange:
        """Create a new HeightRange.

        Args:
            min_height: Minimum block height
            max_height: Maximum block height
            allow_empty_on_invalid: If True (default), an empty range is returned when
                min_height > max_height. If False, a ValueError is raised instead.

        Returns:
            HeightRange instance, or empty range if min_height > max_height and
            allow_empty_on_invalid is True.

        Raises:
            ValueError: If min_height > max_height and allow_empty_on_invalid is False.
        """
        if min_height > max_height:
            if not allow_empty_on_invalid:
                raise ValueError(
                    f"Invalid height range: min_height ({min_height}) " f"is greater than max_height ({max_height})"
                )
            return cls.new_empty_height_range()
        return cls(min_height, max_height)

    @classmethod
    def new_empty_height_range(cls) -> HeightRange:
        """Create an empty HeightRange.

        Returns:
            Empty HeightRange instance
        """
        return cls(is_empty=True)

    @classmethod
    def new_height_range_from_block_headers(cls, headers: list[dict]) -> HeightRange:
        """Create HeightRange from list of block headers.

        Args:
            headers: List of block header dicts with 'height' key

        Returns:
            HeightRange spanning the min/max heights, or empty if no headers
        """
        if not headers:
            return cls.new_empty_height_range()

        min_height = min(h["height"] for h in headers)
        max_height = max(h["height"] for h in headers)
        return cls.new_height_range(min_height, max_height)

    @property
    def is_empty(self) -> bool:
        """Check if range is empty.

        Returns:
            True if range is empty or min_height > max_height
        """
        return self._is_empty or self.min_height > self.max_height

    def not_empty(self) -> bool:
        """Check if range is not empty.

        Returns:
            True if range is not empty
        """
        return not self.is_empty

    @property
    def length(self) -> int:
        """Get the number of heights in this range.

        Returns:
            Number of heights, or 0 if empty
        """
        if self.is_empty:
            return 0
        return self.max_height - self.min_height + 1

    def contains_height(self, height: int) -> bool:
        """Check if height is within this range.

        Args:
            height: Block height to check

        Returns:
            True if height is in range (inclusive)
        """
        if self.is_empty:
            return False
        return height >= self.min_height and height <= self.max_height

    def contains_range(self, other: HeightRange) -> bool:
        """Check if other range is completely contained within this range.

        Args:
            other: Another HeightRange

        Returns:
            True if other is completely within this range
        """
        if self.is_empty or other.is_empty:
            return False
        return other.min_height >= self.min_height and other.max_height <= self.max_height

    def intersect(self, other: HeightRange) -> HeightRange:
        """Get intersection of this range with another.

        Args:
            other: Another HeightRange

        Returns:
            HeightRange representing intersection (may be empty)
        """
        if self.is_empty or other.is_empty:
            return self.new_empty_height_range()

        min_height = max(self.min_height, other.min_height)
        max_height = min(self.max_height, other.max_height)

        if min_height > max_height:
            return self.new_empty_height_range()

        return self.new_height_range(min_height, max_height)

    def union(self, other: HeightRange) -> HeightRange:
        """Get union of this range with another.

        Args:
            other: Another HeightRange

        Returns:
            HeightRange covering both ranges

        Raises:
            ValueError: If ranges are disjoint
        """
        if self.is_empty:
            return other.copy()
        if other.is_empty:
            return self.copy()

        # Check if ranges are disjoint
        if self.max_height + 1 < other.min_height or other.max_height + 1 < self.min_height:
            raise ValueError("cannot union disjoint ranges")

        min_height = min(self.min_height, other.min_height)
        max_height = max(self.max_height, other.max_height)

        return self.new_height_range(min_height, max_height)

    def subtract(self, other: HeightRange) -> HeightRange:
        """Subtract another range from this one.

        Args:
            other: HeightRange to subtract

        Returns:
            HeightRange representing the result of the subtraction

        Raises:
            ValueError: If subtraction would create disjoint ranges
        """
        if self.is_empty:
            return self.new_empty_height_range()
        if other.is_empty:
            return self.copy()

        # Complete overlap - return empty
        if other.min_height <= self.min_height and other.max_height >= self.max_height:
            return self.new_empty_height_range()

        # No overlap - return original
        if other.min_height > self.max_height or other.max_height < self.min_height:
            return self.copy()

        # Partial overlap that would create hole - error
        if other.min_height > self.min_height and other.max_height < self.max_height:
            raise ValueError("subtraction would create disjoint ranges")

        # Left side subtraction
        if other.min_height <= self.min_height:
            return self.new_height_range(other.max_height + 1, self.max_height)

        # Right side subtraction
        return self.new_height_range(self.min_height, other.min_height - 1)

    def above(self, other: HeightRange) -> HeightRange:
        """Get the portion of this range that is strictly above another range.

        Args:
            other: HeightRange to compare against

        Returns:
            HeightRange representing heights above other range
        """
        if self.is_empty or other.is_empty:
            return self.copy()

        if self.min_height > other.max_height:
            return self.copy()

        if self.max_height <= other.max_height:
            return self.new_empty_height_range()

        return self.new_height_range(other.max_height + 1, self.max_height)

    def copy(self) -> HeightRange:
        """Create a copy of this range.

        Returns:
            New HeightRange instance with same values
        """
        return HeightRange(self.min_height, self.max_height, self.is_empty)

    def overlaps(self, other: HeightRange) -> bool:
        """Check if this range overlaps with another.

        Args:
            other: Another HeightRange

        Returns:
            True if ranges overlap
        """
        return not self.intersect(other).is_empty

    def __str__(self) -> str:
        """String representation.

        Returns:
            "empty" for empty ranges, otherwise "[min-max]"
        """
        if self.is_empty:
            return "empty"
        return f"[{self.min_height} - {self.max_height}]"

    def __eq__(self, other: object) -> bool:
        """Check equality with another HeightRange.

        Args:
            other: Another HeightRange

        Returns:
            True if both have same min/max and empty status
        """
        if not isinstance(other, HeightRange):
            return False
        return (
            self.min_height == other.min_height
            and self.max_height == other.max_height
            and self.is_empty == other.is_empty
        )

    def __repr__(self) -> str:
        """String representation for debugging."""
        return f"HeightRange(min_height={self.min_height}, max_height={self.max_height}, is_empty={self.is_empty})"
