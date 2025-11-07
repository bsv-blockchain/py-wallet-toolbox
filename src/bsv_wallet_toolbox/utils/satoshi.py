"""Satoshi arithmetic utilities.

Safe arithmetic operations for Bitcoin Satoshi values with overflow checks.

References:
- TypeScript: toolbox/ts-wallet-toolbox/src/utility/utilityHelpers.ts (satoshi helpers)
- Go: go-wallet-toolbox/pkg/internal/satoshi/
"""

from __future__ import annotations

from collections.abc import Iterable

from bsv_wallet_toolbox.errors import InvalidParameterError

# Maximum absolute Satoshi value allowed by the toolbox (per spec/tests)
MAX_SATOSHIS: int = 2_100_000_000_000_000


def _ensure_within_bounds(value: int) -> None:
    """Validate that a Satoshi value is within allowed bounds.

    Raises InvalidParameterError if the absolute value exceeds MAX_SATOSHIS.
    """
    if not isinstance(value, int):
        raise InvalidParameterError("value", "an integer")
    if value > MAX_SATOSHIS or value < -MAX_SATOSHIS:
        raise InvalidParameterError("value", f"absolute value must be <= {MAX_SATOSHIS}")


def _ensure_no_overflow(value: int) -> None:
    """Ensure the given result does not overflow the allowed Satoshi range."""
    if value > MAX_SATOSHIS or value < -MAX_SATOSHIS:
        # Overflow conditions use OverflowError in tests, but InvalidParameterError is also accepted
        raise OverflowError("satoshi value overflow")


def satoshi_from(value: int) -> int:
    """Validate and return a Satoshi value.

    Allows negative values but enforces |value| <= MAX_SATOSHIS.
    """
    _ensure_within_bounds(value)
    return value


def satoshi_add(a: int, b: int) -> int:
    """Return a + b with overflow checks within Satoshi bounds."""
    _ensure_within_bounds(a)
    _ensure_within_bounds(b)
    result = a + b
    _ensure_no_overflow(result)
    return result


def satoshi_subtract(a: int, b: int) -> int:
    """Return a - b with overflow checks within Satoshi bounds."""
    _ensure_within_bounds(a)
    _ensure_within_bounds(b)
    result = a - b
    _ensure_no_overflow(result)
    return result


def satoshi_sum(values: Iterable[int]) -> int:
    """Sum an iterable of Satoshi values with overflow checks."""
    total = 0
    for v in values:
        _ensure_within_bounds(v)
        total = total + v
        _ensure_no_overflow(total)
    return total


def satoshi_multiply(a: int, b: int) -> int:
    """Return a * b with overflow checks within Satoshi bounds."""
    _ensure_within_bounds(a)
    _ensure_within_bounds(b)
    result = a * b
    _ensure_no_overflow(result)
    return result


def satoshi_equal(a: int, b: int) -> bool:
    """Check equality after validating inputs are within Satoshi bounds."""
    _ensure_within_bounds(a)
    _ensure_within_bounds(b)
    return a == b


def satoshi_to_uint64(value: int) -> int:
    """Convert a Satoshi value to an unsigned 64-bit integer.

    Negative values are invalid. Upper bound is enforced by MAX_SATOSHIS.
    """
    _ensure_within_bounds(value)
    if value < 0:
        raise InvalidParameterError("value", "must be non-negative for uint64 conversion")
    # Still ensure it fits into uint64 mathematically (MAX_SATOSHIS << 2^64-1)
    if value > (2**64 - 1):
        raise OverflowError("value does not fit into uint64")
    return value


def satoshi_must_equal(a: int, b: int) -> None:
    """Verify that two Satoshi values are equal.

    Reference: toolbox/ts-wallet-toolbox/src/utility/satoshiUtils.ts
               function satoshiMustEqual

    Raises InvalidParameterError if values are not equal or invalid.

    Args:
        a: First Satoshi value
        b: Second Satoshi value

    Raises:
        InvalidParameterError: If values are not equal or out of bounds
    """
    _ensure_within_bounds(a)
    _ensure_within_bounds(b)
    if a != b:
        raise InvalidParameterError("satoshi values", f"{a} must equal {b}")


def satoshi_must_uint64(value: int) -> int:
    """Verify a Satoshi value is valid for uint64 conversion and return it.

    Reference: toolbox/ts-wallet-toolbox/src/utility/satoshiUtils.ts
               function satoshiMustUInt64

    Returns the validated value if it's convertible to uint64.

    Args:
        value: Satoshi value to validate

    Returns:
        The input value if valid

    Raises:
        InvalidParameterError: If value is negative or exceeds uint64 bounds
    """
    return satoshi_to_uint64(value)


def satoshi_must_multiply(a: int, b: int) -> int:
    """Multiply two Satoshi values and return the result, or raise an error.

    Reference: toolbox/ts-wallet-toolbox/src/utility/satoshiUtils.ts
               function satoshiMustMultiply

    Verifies that both inputs and the result are within valid Satoshi bounds.

    Args:
        a: First Satoshi value
        b: Second Satoshi value

    Returns:
        The product a * b

    Raises:
        InvalidParameterError: If inputs are out of bounds
        OverflowError: If the product overflows Satoshi bounds
    """
    _ensure_within_bounds(a)
    _ensure_within_bounds(b)
    result = a * b
    _ensure_no_overflow(result)
    return result
