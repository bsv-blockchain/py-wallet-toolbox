"""Chain work calculations for blockchain proof-of-work.

Provides utilities for calculating and manipulating blockchain chain work values,
which represent the cumulative proof-of-work for a chain.

Reference: go-wallet-toolbox/pkg/services/chaintracks/internal/chain_work.go
"""

from __future__ import annotations


class ChainWork:
    """Represents blockchain chain work as a big integer.

    Chain work is the cumulative proof-of-work for a blockchain,
    calculated by summing the work (2^256 / target) for each block.

    Reference: go-wallet-toolbox/pkg/services/chaintracks/internal/chain_work.go
    """

    def __init__(self, value: int | str = 0):
        """Initialize ChainWork.

        Args:
            value: Integer value or hex string representation
        """
        if isinstance(value, str):
            self.value = int(value, 16)
        else:
            self.value = value

    @classmethod
    def from_hex(cls, chainwork_hex: str) -> ChainWork:
        """Create ChainWork from hex string.

        Args:
            chainwork_hex: Hex string representation of chain work

        Returns:
            ChainWork instance

        Raises:
            ValueError: If hex string is invalid
        """
        try:
            return cls(chainwork_hex)
        except ValueError as e:
            raise ValueError(f"invalid chainwork hex: {chainwork_hex}") from e

    @classmethod
    def from_bits(cls, bits: int) -> ChainWork:
        """Create ChainWork from block bits field.

        Converts a block's bits field to chain work using the formula:
        work = 2^256 / (target + 1)

        Args:
            bits: Block bits field (32-bit integer)

        Returns:
            ChainWork representing the work for this block
        """
        return _convert_bits_to_work(bits)

    def add_chain_work(self, other: ChainWork) -> ChainWork:
        """Add another ChainWork to this one.

        Args:
            other: ChainWork to add

        Returns:
            New ChainWork with sum
        """
        return ChainWork(self.value + other.value)

    def cmp_chain_work(self, other: ChainWork) -> int:
        """Compare this ChainWork with another.

        Args:
            other: ChainWork to compare with

        Returns:
            -1 if self < other, 0 if equal, 1 if self > other
        """
        if self.value < other.value:
            return -1
        elif self.value > other.value:
            return 1
        else:
            return 0

    def to_64_pad_hex(self) -> str:
        """Convert to 64-character padded hex string.

        Returns:
            Hex string representation, zero-padded to 64 characters
        """
        return f"{self.value:064x}"

    def __eq__(self, other: object) -> bool:
        """Check equality with another ChainWork."""
        if not isinstance(other, ChainWork):
            return False
        return self.value == other.value

    def __repr__(self) -> str:
        """String representation."""
        return f"ChainWork({self.to_64_pad_hex()})"


def _convert_bits_to_work(bits: int) -> ChainWork:
    """Convert block bits to work value.

    The algorithm:
    1. Extract exponent and mantissa from bits
    2. Calculate target = mantissa * 2^(8 * (exponent - 3))
    3. Calculate work = 2^256 / (target + 1)

    Args:
        bits: 32-bit bits field from block header

    Returns:
        ChainWork representing the work
    """
    # Extract exponent and mantissa from bits
    # bits = [sign][exponent][mantissa]
    # sign = bits >> 31 (always 0 for Bitcoin)
    # exponent = (bits >> 24) & 0xff
    # mantissa = bits & 0x007fffff

    shift = (bits >> 24) & 0xFF
    data = bits & 0x007FFFFF

    # Calculate target: T = mantissa * 2^(8 * (exponent - 3))
    target = data
    if shift <= 3:
        exp = 3 - shift
        target >>= exp * 8
    else:
        exp = shift - 3
        target <<= exp * 8

    # work = 2^256 / (target + 1) (integer division)
    # Since Python integers are arbitrary precision, we can calculate this directly
    two_256 = 1 << 256
    target_plus_one = target + 1
    work = two_256 // target_plus_one

    return ChainWork(work)
