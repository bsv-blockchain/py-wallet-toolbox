"""Randomizer interface and implementations.

Provides pluggable randomization with test implementations,
following the Go randomizer pattern.

Reference: go-wallet-toolbox/pkg/randomizer/
"""

import secrets
from abc import ABC, abstractmethod
from typing import Any


class Randomizer(ABC):
    """Interface for randomization operations.

    Provides pluggable randomization for cryptographic and testing purposes.
    Implementations can use secure random generation or deterministic values for testing.

    Reference: go-wallet-toolbox/pkg/randomizer/randomizer.go
    """

    @abstractmethod
    def random_bytes(self, length: int) -> bytes:
        """Generate random bytes.

        Args:
            length: Number of random bytes to generate

        Returns:
            Random bytes
        """
        ...

    @abstractmethod
    def random_int(self, min_value: int, max_value: int) -> int:
        """Generate random integer in range.

        Args:
            min_value: Minimum value (inclusive)
            max_value: Maximum value (exclusive)

        Returns:
            Random integer in range
        """
        ...

    @abstractmethod
    def shuffle(self, items: list[Any]) -> list[Any]:
        """Shuffle a list in place and return it.

        Args:
            items: List to shuffle

        Returns:
            Shuffled list (same object)
        """
        ...


class SecureRandomizer(Randomizer):
    """Secure randomizer using system entropy.

    Uses secrets module for cryptographically secure random generation.
    Suitable for production use.
    """

    def random_bytes(self, length: int) -> bytes:
        """Generate cryptographically secure random bytes."""
        return secrets.token_bytes(length)

    def random_int(self, min_value: int, max_value: int) -> int:
        """Generate cryptographically secure random integer."""
        if min_value >= max_value:
            raise ValueError("min_value must be less than max_value")
        return secrets.randbelow(max_value - min_value) + min_value

    def shuffle(self, items: list[Any]) -> list[Any]:
        """Shuffle list using cryptographically secure random."""
        # Create a copy to avoid modifying the original
        shuffled = items.copy()
        # Fisher-Yates shuffle with secure random
        for i in range(len(shuffled) - 1, 0, -1):
            j = self.random_int(0, i + 1)
            shuffled[i], shuffled[j] = shuffled[j], shuffled[i]
        return shuffled


class DeterministicRandomizer(Randomizer):
    """Deterministic randomizer for testing - Go compatible.

    This implementation matches the Go TestRandomizer exactly to ensure
    deterministic, reproducible results across Python and Go implementations.

    Reference: go-wallet-toolbox/pkg/randomizer/test_randomizer.go
    """

    MIN_RANDOMIZE_LENGTH = 3  # minimum length for randomization to avoid early overflow

    def __init__(self, seed: int | None = None) -> None:
        """Initialize test randomizer matching Go's NewTestRandomizer().

        Args:
            seed: Optional seed value for API compatibility (currently unused)
        """
        self._base_character = ord("a")  # 0x61
        self._roll_counter = 0

    def random_bytes(self, length: int) -> bytes:
        """Generate deterministic bytes matching Go's Bytes().

        Each call returns bytes filled with the current base character,
        then increments the character for the next call.

        Args:
            length: Number of bytes to generate

        Returns:
            Deterministic byte sequence

        Raises:
            ValueError: If length is zero
        """
        if length == 0:
            raise ValueError("length cannot be zero")

        return self._next_bytes(length)

    def _next_bytes(self, length: int) -> bytes:
        """Internal method to generate next byte sequence - matches Go exactly."""
        if length == 0:
            raise RuntimeError("length cannot be zero for random bytes generation")

        current = self._base_character
        current_roll_counter = self._roll_counter

        # Increment base character for next call
        if self._base_character < 0x7F:
            self._base_character += 1
        else:
            self._base_character = 0x21

            if length < self.MIN_RANDOMIZE_LENGTH:
                raise RuntimeError("test randomizes base character overflow - too short length for randomization")
            if self._roll_counter == 0xFF:
                raise RuntimeError("test randomizes base character overflow - too many calls for randomization")
            self._roll_counter += 1

        # Build result - all bytes are the current character
        result = bytearray([current] * length)

        # Apply roll counter encoding if needed
        if current_roll_counter > 0:
            result[0] = 0x20
            result[1] = current_roll_counter % 0xFF

        return bytes(result)

    def base64(self, length: int) -> str:
        """Generate base64-encoded deterministic string.

        Args:
            length: Number of raw bytes to encode

        Returns:
            Base64-encoded string
        """
        import base64

        random_bytes = self.random_bytes(length)
        return base64.b64encode(random_bytes).decode("ascii")

    def random_int(self, min_value: int, max_value: int) -> int:
        """Generate deterministic "random" integer.

        For Go compatibility, this returns min_value (equivalent to Go returning 0
        for Uint64(max) which then gets added to min).
        """
        if min_value >= max_value:
            raise ValueError("min_value must be less than max_value")
        return min_value  # Go's Uint64(max) always returns 0

    def uint64(self, max_value: int) -> int:
        """Generate deterministic uint64 - always returns 0 like Go.

        Args:
            max_value: Maximum value (unused, always returns 0)

        Returns:
            Always 0
        """
        return 0

    def shuffle(self, items: list[Any]) -> list[Any]:
        """Shuffle list using Go-compatible deterministic algorithm.

        Go's TestRandomizer.Shuffle does a double-swap for each pair,
        which effectively preserves the original order.

        Args:
            items: List to shuffle

        Returns:
            Same list (order preserved due to double-swap)
        """
        result = items.copy()
        n = len(result)
        for i in range(n - 1):
            # Double swap = no change (matches Go behavior)
            result[i], result[i + 1] = result[i + 1], result[i]
            result[i], result[i + 1] = result[i + 1], result[i]
        return result


# Alias for Go naming convention compatibility
TestRandomizer = DeterministicRandomizer

# Keep old name for backward compatibility
_TestRandomizer = DeterministicRandomizer


# Global instances for convenience
secure_randomizer = SecureRandomizer()
test_randomizer = _TestRandomizer()

# Default randomizer (can be changed for testing)
_default_randomizer = secure_randomizer


def get_default_randomizer() -> Randomizer:
    """Get the default randomizer instance."""
    return _default_randomizer


def set_default_randomizer(randomizer: Randomizer) -> None:
    """Set the default randomizer instance.

    Args:
        randomizer: Randomizer instance to use as default
    """
    global _default_randomizer
    _default_randomizer = randomizer


def use_test_randomizer(seed: int = 42) -> None:
    """Switch to test randomizer for testing.

    Args:
        seed: Seed for deterministic generation
    """
    global test_randomizer
    test_randomizer = _TestRandomizer(seed)
    set_default_randomizer(test_randomizer)


def use_secure_randomizer() -> None:
    """Switch to secure randomizer for production."""
    set_default_randomizer(secure_randomizer)
