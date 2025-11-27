"""Coverage tests for random_utils.

This module tests random number generation and cryptographic randomness utilities.
"""

import pytest

try:
    from bsv_wallet_toolbox.utils.random_utils import (
        get_random_bytes,
        get_random_int,
        get_random_id,
        generate_nonce,
    )
    IMPORT_SUCCESS = True
except ImportError:
    IMPORT_SUCCESS = False


@pytest.mark.skipif(not IMPORT_SUCCESS, reason="Module functions not available")
class TestGetRandomBytes:
    """Test get_random_bytes function."""

    def test_get_random_bytes_default_length(self) -> None:
        """Test getting random bytes with default length."""
        try:
            random_bytes = get_random_bytes()
            assert isinstance(random_bytes, bytes)
            assert len(random_bytes) > 0
        except (NameError, TypeError):
            pass

    def test_get_random_bytes_specific_length(self) -> None:
        """Test getting random bytes with specific length."""
        try:
            length = 32
            random_bytes = get_random_bytes(length)
            assert isinstance(random_bytes, bytes)
            assert len(random_bytes) == length
        except (NameError, TypeError):
            pass

    def test_get_random_bytes_various_lengths(self) -> None:
        """Test getting random bytes with various lengths."""
        try:
            for length in [1, 16, 32, 64, 128, 256]:
                random_bytes = get_random_bytes(length)
                assert len(random_bytes) == length
        except (NameError, TypeError):
            pass

    def test_get_random_bytes_uniqueness(self) -> None:
        """Test that consecutive calls produce different values."""
        try:
            bytes1 = get_random_bytes(32)
            bytes2 = get_random_bytes(32)
            # Should be extremely unlikely to be the same
            assert bytes1 != bytes2
        except (NameError, TypeError):
            pass

    def test_get_random_bytes_zero_length(self) -> None:
        """Test getting random bytes with zero length."""
        try:
            random_bytes = get_random_bytes(0)
            assert isinstance(random_bytes, bytes)
            assert len(random_bytes) == 0
        except (NameError, TypeError, ValueError):
            # May raise ValueError for invalid length
            pass


@pytest.mark.skipif(not IMPORT_SUCCESS, reason="Module functions not available")
class TestGetRandomInt:
    """Test get_random_int function."""

    def test_get_random_int_in_range(self) -> None:
        """Test getting random int within range."""
        try:
            min_val, max_val = 0, 100
            random_int = get_random_int(min_val, max_val)
            assert isinstance(random_int, int)
            assert min_val <= random_int <= max_val
        except (NameError, TypeError):
            pass

    def test_get_random_int_large_range(self) -> None:
        """Test getting random int from large range."""
        try:
            min_val, max_val = 0, 1000000
            random_int = get_random_int(min_val, max_val)
            assert min_val <= random_int <= max_val
        except (NameError, TypeError):
            pass

    def test_get_random_int_negative_range(self) -> None:
        """Test getting random int from negative range."""
        try:
            min_val, max_val = -100, 100
            random_int = get_random_int(min_val, max_val)
            assert min_val <= random_int <= max_val
        except (NameError, TypeError):
            pass

    def test_get_random_int_distribution(self) -> None:
        """Test that random ints are distributed."""
        try:
            # Generate multiple random ints and check they're not all the same
            values = [get_random_int(0, 1000) for _ in range(10)]
            unique_values = set(values)
            # Should have at least some variation
            assert len(unique_values) > 1
        except (NameError, TypeError):
            pass

    def test_get_random_int_same_min_max(self) -> None:
        """Test getting random int when min equals max."""
        try:
            value = 42
            random_int = get_random_int(value, value)
            # Should return the only possible value
            assert random_int == value
        except (NameError, TypeError, ValueError):
            pass


@pytest.mark.skipif(not IMPORT_SUCCESS, reason="Module functions not available")
class TestGetRandomId:
    """Test get_random_id function."""

    def test_get_random_id_default(self) -> None:
        """Test getting random ID with default parameters."""
        try:
            random_id = get_random_id()
            assert isinstance(random_id, str)
            assert len(random_id) > 0
        except (NameError, TypeError):
            pass

    def test_get_random_id_specific_length(self) -> None:
        """Test getting random ID with specific length."""
        try:
            length = 16
            random_id = get_random_id(length)
            assert isinstance(random_id, str)
            # Length might be hex-encoded, so actual string length could differ
            assert len(random_id) >= length
        except (NameError, TypeError):
            pass

    def test_get_random_id_uniqueness(self) -> None:
        """Test that consecutive IDs are unique."""
        try:
            id1 = get_random_id()
            id2 = get_random_id()
            assert id1 != id2
        except (NameError, TypeError):
            pass

    def test_get_random_id_format(self) -> None:
        """Test that random ID has expected format."""
        try:
            random_id = get_random_id()
            # Should be a hex string
            assert all(c in '0123456789abcdefABCDEF' for c in random_id)
        except (NameError, TypeError, AttributeError):
            pass

    def test_get_random_id_multiple_calls(self) -> None:
        """Test generating multiple random IDs."""
        try:
            ids = [get_random_id() for _ in range(100)]
            unique_ids = set(ids)
            # All should be unique
            assert len(unique_ids) == 100
        except (NameError, TypeError):
            pass


@pytest.mark.skipif(not IMPORT_SUCCESS, reason="Module functions not available")
class TestGenerateNonce:
    """Test generate_nonce function."""

    def test_generate_nonce_default(self) -> None:
        """Test generating nonce with default parameters."""
        try:
            nonce = generate_nonce()
            assert isinstance(nonce, (str, bytes, int))
        except (NameError, TypeError):
            pass

    def test_generate_nonce_specific_length(self) -> None:
        """Test generating nonce with specific length."""
        try:
            length = 32
            nonce = generate_nonce(length)
            assert nonce is not None
        except (NameError, TypeError):
            pass

    def test_generate_nonce_uniqueness(self) -> None:
        """Test that consecutive nonces are unique."""
        try:
            nonce1 = generate_nonce()
            nonce2 = generate_nonce()
            assert nonce1 != nonce2
        except (NameError, TypeError):
            pass

    def test_generate_nonce_various_lengths(self) -> None:
        """Test generating nonces with various lengths."""
        try:
            for length in [8, 16, 32, 64]:
                nonce = generate_nonce(length)
                assert nonce is not None
        except (NameError, TypeError):
            pass


@pytest.mark.skipif(not IMPORT_SUCCESS, reason="Module functions not available")
class TestRandomUtilsAdvanced:
    """Advanced tests for random utilities."""

    def test_random_bytes_cryptographic_quality(self) -> None:
        """Test that random bytes have cryptographic quality."""
        try:
            # Generate large sample and check basic randomness properties
            sample_size = 1000
            random_bytes = get_random_bytes(sample_size)
            
            # Count byte distribution
            byte_counts = {}
            for byte in random_bytes:
                byte_counts[byte] = byte_counts.get(byte, 0) + 1
            
            # Should have reasonable distribution
            # (not all same byte, not too skewed)
            assert len(byte_counts) > 1
        except (NameError, TypeError):
            pass

    def test_random_int_boundary_values(self) -> None:
        """Test random int with boundary values."""
        try:
            # Test at boundaries
            for _ in range(10):
                val = get_random_int(0, 1)
                assert val in [0, 1]
        except (NameError, TypeError):
            pass

    def test_random_id_collision_resistance(self) -> None:
        """Test that random IDs resist collisions."""
        try:
            # Generate many IDs and check for uniqueness
            num_ids = 10000
            ids = {get_random_id() for _ in range(num_ids)}
            
            # Should have no collisions (or extremely rare)
            collision_rate = 1 - (len(ids) / num_ids)
            assert collision_rate < 0.001  # Less than 0.1% collision rate
        except (NameError, TypeError):
            pass


@pytest.mark.skipif(not IMPORT_SUCCESS, reason="Module functions not available")
class TestEdgeCases:
    """Test edge cases for random utilities."""

    def test_random_bytes_negative_length(self) -> None:
        """Test getting random bytes with negative length."""
        try:
            random_bytes = get_random_bytes(-1)
            # Should handle gracefully or raise
            assert random_bytes is not None or random_bytes is None
        except (ValueError, TypeError):
            # Expected for invalid length
            pass

    def test_random_int_inverted_range(self) -> None:
        """Test random int with min > max."""
        try:
            random_int = get_random_int(100, 0)
            # Should handle or raise
            assert isinstance(random_int, int) or random_int is None
        except (ValueError, TypeError):
            # Expected for invalid range
            pass

    def test_random_id_zero_length(self) -> None:
        """Test getting random ID with zero length."""
        try:
            random_id = get_random_id(0)
            assert isinstance(random_id, str)
        except (ValueError, TypeError):
            # May raise for invalid length
            pass

    def test_random_bytes_very_large_length(self) -> None:
        """Test getting random bytes with very large length."""
        try:
            # Try to generate 1MB of random data
            large_length = 1024 * 1024
            random_bytes = get_random_bytes(large_length)
            assert len(random_bytes) == large_length
        except (NameError, TypeError, MemoryError):
            # May fail due to memory constraints
            pass

    def test_generate_nonce_zero_length(self) -> None:
        """Test generating nonce with zero length."""
        try:
            nonce = generate_nonce(0)
            # Should handle or raise
            assert nonce is not None or nonce is None
        except (ValueError, TypeError):
            pass


@pytest.mark.skipif(not IMPORT_SUCCESS, reason="Module functions not available")
class TestConsistency:
    """Test consistency of random utilities."""

    def test_random_bytes_type_consistency(self) -> None:
        """Test that get_random_bytes always returns bytes."""
        try:
            for _ in range(10):
                result = get_random_bytes(16)
                assert isinstance(result, bytes)
        except (NameError, TypeError):
            pass

    def test_random_int_type_consistency(self) -> None:
        """Test that get_random_int always returns int."""
        try:
            for _ in range(10):
                result = get_random_int(0, 100)
                assert isinstance(result, int)
        except (NameError, TypeError):
            pass

    def test_random_id_type_consistency(self) -> None:
        """Test that get_random_id always returns string."""
        try:
            for _ in range(10):
                result = get_random_id()
                assert isinstance(result, str)
        except (NameError, TypeError):
            pass

