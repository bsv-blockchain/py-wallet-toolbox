"""Tests for randomizer interface and implementations."""

import pytest

from bsv_wallet_toolbox.utils.randomizer import (
    SecureRandomizer,
    _TestRandomizer,
    get_default_randomizer,
    set_default_randomizer,
    use_secure_randomizer,
    use_test_randomizer,
)


class TestSecureRandomizer:
    """Test SecureRandomizer functionality."""

    def test_random_bytes(self):
        """Test random bytes generation."""
        randomizer = SecureRandomizer()
        bytes1 = randomizer.random_bytes(10)
        bytes2 = randomizer.random_bytes(10)

        assert len(bytes1) == 10
        assert len(bytes2) == 10
        # Very unlikely to be the same (cryptographically secure)
        assert bytes1 != bytes2

    def test_random_int(self):
        """Test random integer generation."""
        randomizer = SecureRandomizer()

        for _ in range(10):
            value = randomizer.random_int(0, 100)
            assert 0 <= value < 100

    def test_random_int_invalid_range(self):
        """Test random_int with invalid range."""
        randomizer = SecureRandomizer()

        with pytest.raises(ValueError):
            randomizer.random_int(10, 5)  # min > max

    def test_random_int_equal_min_max(self):
        """Test random_int with min_value equal to max_value."""
        randomizer = SecureRandomizer()

        with pytest.raises(ValueError, match="min_value must be less than max_value"):
            randomizer.random_int(5, 5)  # min == max

    def test_shuffle(self):
        """Test list shuffling."""
        randomizer = SecureRandomizer()
        original = [1, 2, 3, 4, 5]
        shuffled = randomizer.shuffle(original.copy())

        assert len(shuffled) == len(original)
        assert set(shuffled) == set(original)  # Same elements


class TestTestRandomizer:
    """Test TestRandomizer deterministic behavior."""

    def test_deterministic_bytes(self):
        """Test that test randomizer produces deterministic results."""
        rand1 = _TestRandomizer(seed=42)
        rand2 = _TestRandomizer(seed=42)

        bytes1 = rand1.random_bytes(10)
        bytes2 = rand2.random_bytes(10)

        assert bytes1 == bytes2

    def test_deterministic_int(self):
        """Test that test randomizer produces deterministic integers."""
        rand1 = _TestRandomizer(seed=123)
        rand2 = _TestRandomizer(seed=123)

        for _ in range(5):
            assert rand1.random_int(0, 100) == rand2.random_int(0, 100)

    def test_deterministic_shuffle(self):
        """Test that test randomizer produces deterministic shuffles."""
        original = [1, 2, 3, 4, 5]

        rand1 = _TestRandomizer(seed=99)
        rand2 = _TestRandomizer(seed=99)

        shuffled1 = rand1.shuffle(original.copy())
        shuffled2 = rand2.shuffle(original.copy())

        assert shuffled1 == shuffled2
        assert set(shuffled1) == set(original)


class TestRandomizerManagement:
    """Test randomizer management functions."""

    def test_default_randomizer(self):
        """Test default randomizer management."""
        original = get_default_randomizer()

        # Set a test randomizer
        test_rand = _TestRandomizer()
        set_default_randomizer(test_rand)
        assert get_default_randomizer() is test_rand

        # Restore original
        set_default_randomizer(original)
        assert get_default_randomizer() is original

    def test_use_test_randomizer(self):
        """Test use_test_randomizer convenience function."""
        original = get_default_randomizer()

        use_test_randomizer(seed=42)
        current = get_default_randomizer()

        assert isinstance(current, _TestRandomizer)
        # Note: seed parameter is accepted for API compatibility but not stored as attribute

        # Restore
        set_default_randomizer(original)

    def test_use_secure_randomizer(self):
        """Test use_secure_randomizer convenience function."""
        use_test_randomizer()  # Set to test first
        use_secure_randomizer()  # Switch to secure

        current = get_default_randomizer()
        assert isinstance(current, SecureRandomizer)
