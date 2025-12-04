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


class _TestRandomizer(Randomizer):
    """Deterministic randomizer for testing.

    Provides predictable, deterministic "random" values for testing.
    Useful for reproducible test results.
    """

    def __init__(self, seed: int = 42):
        """Initialize test randomizer.

        Args:
            seed: Seed value for deterministic generation
        """
        self.seed = seed
        self.counter = 0

    def _next_int(self) -> int:
        """Generate next deterministic integer."""
        self.counter += 1
        # Simple linear congruential generator for determinism
        return (self.seed * 1103515245 + 12345 + self.counter) % (2**31)

    def random_bytes(self, length: int) -> bytes:
        """Generate deterministic "random" bytes."""
        result = bytearray()
        for _ in range(length):
            result.append(self._next_int() % 256)
        return bytes(result)

    def random_int(self, min_value: int, max_value: int) -> int:
        """Generate deterministic "random" integer."""
        if min_value >= max_value:
            raise ValueError("min_value must be less than max_value")
        return (self._next_int() % (max_value - min_value)) + min_value

    def shuffle(self, items: list[Any]) -> list[Any]:
        """Shuffle list using deterministic algorithm."""
        # Use a simple deterministic shuffle
        shuffled = items.copy()
        n = len(shuffled)
        for i in range(n - 1, 0, -1):
            # Use deterministic swap position
            swap_val = self._next_int() % (i + 1)
            shuffled[i], shuffled[swap_val] = shuffled[swap_val], shuffled[i]
        return shuffled


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
