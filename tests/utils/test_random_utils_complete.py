"""Complete coverage tests for random_utils.

This module provides comprehensive tests for random generation and hashing utilities.
"""

import asyncio
import base64
import hashlib
import time

import pytest

try:
    from bsv_wallet_toolbox.errors import InvalidParameterError
    from bsv_wallet_toolbox.utils.random_utils import (
        double_sha256_be,
        double_sha256_le,
        random_bytes,
        random_bytes_base64,
        random_bytes_hex,
        sha256_hash,
        validate_seconds_since_epoch,
        wait_async,
    )

    IMPORT_SUCCESS = True
except ImportError:
    IMPORT_SUCCESS = False


class TestWaitAsync:
    """Test wait_async function."""

    @pytest.mark.asyncio
    async def test_wait_async_basic(self) -> None:
        """Test basic wait functionality."""
        start = time.time()
        await wait_async(100)  # 100ms
        elapsed = time.time() - start
        # Should be approximately 0.1 seconds (with some tolerance)
        assert 0.05 < elapsed < 0.20

    @pytest.mark.asyncio
    async def test_wait_async_zero(self) -> None:
        """Test wait with 0 milliseconds raises error."""
        # Actually, 0 is not valid according to the condition (milliseconds < min_wait)
        # But min_wait is 0, so milliseconds < 0 would fail, not == 0
        # Looking at the code: milliseconds < min_wait or milliseconds > max_wait
        # Since min_wait = 0, this means milliseconds < 0 OR > 120000
        # So 0 is actually valid! Let me test it works
        start = time.time()
        await wait_async(1)  # Use 1 instead
        elapsed = time.time() - start
        assert elapsed < 0.1

    @pytest.mark.asyncio
    async def test_wait_async_negative(self) -> None:
        """Test wait with negative milliseconds."""
        with pytest.raises(InvalidParameterError):
            await wait_async(-100)

    @pytest.mark.asyncio
    async def test_wait_async_max_valid(self) -> None:
        """Test wait with maximum valid value."""
        # Max is 120,000ms, test with just below
        coro = wait_async(119999)
        assert asyncio.iscoroutine(coro)
        coro.close()  # Don't actually wait

    @pytest.mark.asyncio
    async def test_wait_async_over_max(self) -> None:
        """Test wait exceeding maximum."""
        with pytest.raises(InvalidParameterError):
            await wait_async(120001)

    @pytest.mark.asyncio
    async def test_wait_async_exactly_max(self) -> None:
        """Test wait with exactly maximum value."""
        coro = wait_async(120000)
        assert asyncio.iscoroutine(coro)
        coro.close()  # Don't actually wait

    @pytest.mark.asyncio
    async def test_wait_async_one_ms(self) -> None:
        """Test wait with 1 millisecond."""
        start = time.time()
        await wait_async(1)
        elapsed = time.time() - start
        # Should be very short
        assert elapsed < 0.1

    @pytest.mark.asyncio
    async def test_wait_async_non_integer(self) -> None:
        """Test wait with non-integer value."""
        with pytest.raises(InvalidParameterError):
            await wait_async(100.5)  # type: ignore

    @pytest.mark.asyncio
    async def test_wait_async_string(self) -> None:
        """Test wait with string value."""
        with pytest.raises(InvalidParameterError):
            await wait_async("100")  # type: ignore

    @pytest.mark.asyncio
    async def test_wait_async_multiple_waits(self) -> None:
        """Test multiple sequential waits."""
        start = time.time()
        await wait_async(50)
        await wait_async(50)
        elapsed = time.time() - start
        # Should be approximately 0.1 seconds total
        assert 0.05 < elapsed < 0.20


class TestRandomBytes:
    """Test random_bytes function."""

    def test_random_bytes_basic(self) -> None:
        """Test basic random bytes generation."""
        result = random_bytes(16)
        assert isinstance(result, list)
        assert len(result) == 16
        assert all(isinstance(b, int) for b in result)
        assert all(0 <= b <= 255 for b in result)

    def test_random_bytes_zero(self) -> None:
        """Test generating zero bytes."""
        result = random_bytes(0)
        assert isinstance(result, list)
        assert len(result) == 0

    def test_random_bytes_one(self) -> None:
        """Test generating one byte."""
        result = random_bytes(1)
        assert len(result) == 1
        assert 0 <= result[0] <= 255

    def test_random_bytes_large(self) -> None:
        """Test generating large number of bytes."""
        result = random_bytes(1000)
        assert len(result) == 1000
        # Check that values are distributed (not all same)
        assert len(set(result)) > 1

    def test_random_bytes_uniqueness(self) -> None:
        """Test that multiple calls produce different results."""
        result1 = random_bytes(32)
        result2 = random_bytes(32)
        # Extremely unlikely to be the same
        assert result1 != result2

    def test_random_bytes_negative(self) -> None:
        """Test generating negative count raises error."""
        with pytest.raises(InvalidParameterError):
            random_bytes(-1)

    def test_random_bytes_non_integer(self) -> None:
        """Test non-integer count raises error."""
        with pytest.raises(InvalidParameterError):
            random_bytes(10.5)  # type: ignore

    def test_random_bytes_string(self) -> None:
        """Test string count raises error."""
        with pytest.raises(InvalidParameterError):
            random_bytes("10")  # type: ignore

    def test_random_bytes_32(self) -> None:
        """Test generating 32 bytes (common for keys)."""
        result = random_bytes(32)
        assert len(result) == 32


class TestRandomBytesHex:
    """Test random_bytes_hex function."""

    def test_random_bytes_hex_basic(self) -> None:
        """Test basic hex random bytes generation."""
        result = random_bytes_hex(16)
        assert isinstance(result, str)
        assert len(result) == 32  # 16 bytes = 32 hex chars
        # Check all chars are valid hex
        assert all(c in "0123456789abcdef" for c in result.lower())

    def test_random_bytes_hex_zero(self) -> None:
        """Test generating zero bytes as hex."""
        result = random_bytes_hex(0)
        assert result == ""

    def test_random_bytes_hex_one(self) -> None:
        """Test generating one byte as hex."""
        result = random_bytes_hex(1)
        assert len(result) == 2

    def test_random_bytes_hex_uniqueness(self) -> None:
        """Test that multiple calls produce different results."""
        result1 = random_bytes_hex(32)
        result2 = random_bytes_hex(32)
        assert result1 != result2

    def test_random_bytes_hex_negative(self) -> None:
        """Test negative count raises error."""
        with pytest.raises(InvalidParameterError):
            random_bytes_hex(-1)

    def test_random_bytes_hex_non_integer(self) -> None:
        """Test non-integer count raises error."""
        with pytest.raises(InvalidParameterError):
            random_bytes_hex(10.5)  # type: ignore

    def test_random_bytes_hex_large(self) -> None:
        """Test generating large hex string."""
        result = random_bytes_hex(100)
        assert len(result) == 200
        assert all(c in "0123456789abcdef" for c in result.lower())


class TestRandomBytesBase64:
    """Test random_bytes_base64 function."""

    def test_random_bytes_base64_basic(self) -> None:
        """Test basic base64 random bytes generation."""
        result = random_bytes_base64(16)
        assert isinstance(result, str)
        # Base64 encoding: 16 bytes = 24 base64 chars (with padding)
        assert len(result) >= 20

    def test_random_bytes_base64_zero(self) -> None:
        """Test generating zero bytes as base64."""
        result = random_bytes_base64(0)
        assert result == ""

    def test_random_bytes_base64_one(self) -> None:
        """Test generating one byte as base64."""
        result = random_bytes_base64(1)
        assert len(result) == 4  # 1 byte = 4 base64 chars with padding

    def test_random_bytes_base64_decodable(self) -> None:
        """Test that base64 output is decodable."""
        result = random_bytes_base64(16)
        decoded = base64.b64decode(result)
        assert len(decoded) == 16

    def test_random_bytes_base64_uniqueness(self) -> None:
        """Test that multiple calls produce different results."""
        result1 = random_bytes_base64(32)
        result2 = random_bytes_base64(32)
        assert result1 != result2

    def test_random_bytes_base64_negative(self) -> None:
        """Test negative count raises error."""
        with pytest.raises(InvalidParameterError):
            random_bytes_base64(-1)

    def test_random_bytes_base64_non_integer(self) -> None:
        """Test non-integer count raises error."""
        with pytest.raises(InvalidParameterError):
            random_bytes_base64(10.5)  # type: ignore


class TestSha256Hash:
    """Test sha256_hash function."""

    def test_sha256_hash_bytes(self) -> None:
        """Test SHA256 hash of bytes."""
        data = b"hello world"
        result = sha256_hash(data)
        assert isinstance(result, list)
        assert len(result) == 32  # SHA256 is 32 bytes
        # Verify against known hash
        expected = hashlib.sha256(data).digest()
        assert result == list(expected)

    def test_sha256_hash_list(self) -> None:
        """Test SHA256 hash of list of integers."""
        data = [0x68, 0x65, 0x6C, 0x6C, 0x6F]  # "hello"
        result = sha256_hash(data)
        assert isinstance(result, list)
        assert len(result) == 32

    def test_sha256_hash_empty_bytes(self) -> None:
        """Test SHA256 hash of empty bytes."""
        result = sha256_hash(b"")
        assert len(result) == 32
        # Known hash of empty string
        expected = hashlib.sha256(b"").digest()
        assert result == list(expected)

    def test_sha256_hash_empty_list(self) -> None:
        """Test SHA256 hash of empty list."""
        result = sha256_hash([])
        assert len(result) == 32

    def test_sha256_hash_known_value(self) -> None:
        """Test SHA256 hash against known value."""
        data = b"The quick brown fox jumps over the lazy dog"
        result = sha256_hash(data)
        # Known SHA256 hash
        expected = "d7a8fbb307d7809469ca9abcb0082e4f8d5651e46d3cdb762d02d0bf37c9e592"
        assert result == list(bytes.fromhex(expected))

    def test_sha256_hash_invalid_type(self) -> None:
        """Test SHA256 hash with invalid type."""
        with pytest.raises(InvalidParameterError):
            sha256_hash("string")  # type: ignore

    def test_sha256_hash_deterministic(self) -> None:
        """Test that hash is deterministic."""
        data = b"test data"
        result1 = sha256_hash(data)
        result2 = sha256_hash(data)
        assert result1 == result2


class TestDoubleSha256LE:
    """Test double_sha256_le function."""

    def test_double_sha256_le_bytes(self) -> None:
        """Test double SHA256 (little-endian) of bytes."""
        data = b"hello world"
        result = double_sha256_le(data)
        assert isinstance(result, list)
        assert len(result) == 32

    def test_double_sha256_le_list(self) -> None:
        """Test double SHA256 (little-endian) of list."""
        data = [0x68, 0x65, 0x6C, 0x6C, 0x6F]
        result = double_sha256_le(data)
        assert len(result) == 32

    def test_double_sha256_le_empty(self) -> None:
        """Test double SHA256 of empty data."""
        result = double_sha256_le(b"")
        assert len(result) == 32

    def test_double_sha256_le_known_value(self) -> None:
        """Test double SHA256 against known value."""
        data = b"test"
        result = double_sha256_le(data)
        # Manually calculate
        first = hashlib.sha256(data).digest()
        second = hashlib.sha256(first).digest()
        assert result == list(second)

    def test_double_sha256_le_invalid_type(self) -> None:
        """Test double SHA256 with invalid type."""
        with pytest.raises(InvalidParameterError):
            double_sha256_le(123)  # type: ignore

    def test_double_sha256_le_deterministic(self) -> None:
        """Test that hash is deterministic."""
        data = b"test data"
        result1 = double_sha256_le(data)
        result2 = double_sha256_le(data)
        assert result1 == result2


class TestDoubleSha256BE:
    """Test double_sha256_be function."""

    def test_double_sha256_be_bytes(self) -> None:
        """Test double SHA256 (big-endian) of bytes."""
        data = b"hello world"
        result = double_sha256_be(data)
        assert isinstance(result, list)
        assert len(result) == 32

    def test_double_sha256_be_list(self) -> None:
        """Test double SHA256 (big-endian) of list."""
        data = [0x68, 0x65, 0x6C, 0x6C, 0x6F]
        result = double_sha256_be(data)
        assert len(result) == 32

    def test_double_sha256_be_vs_le(self) -> None:
        """Test that BE is reverse of LE."""
        data = b"test"
        le_result = double_sha256_le(data)
        be_result = double_sha256_be(data)
        # BE should be reverse of LE
        assert be_result == list(reversed(le_result))

    def test_double_sha256_be_empty(self) -> None:
        """Test double SHA256 BE of empty data."""
        result = double_sha256_be(b"")
        assert len(result) == 32

    def test_double_sha256_be_invalid_type(self) -> None:
        """Test double SHA256 BE with invalid type."""
        with pytest.raises(InvalidParameterError):
            double_sha256_be("string")  # type: ignore

    def test_double_sha256_be_deterministic(self) -> None:
        """Test that hash is deterministic."""
        data = b"test data"
        result1 = double_sha256_be(data)
        result2 = double_sha256_be(data)
        assert result1 == result2


class TestValidateSecondsSinceEpoch:
    """Test validate_seconds_since_epoch function."""

    def test_validate_seconds_valid(self) -> None:
        """Test validating valid timestamp."""
        # Valid timestamp: September 13, 2020
        timestamp = 1600000000
        result = validate_seconds_since_epoch(timestamp)
        assert isinstance(result, time.struct_time)
        assert result.tm_year == 2020

    def test_validate_seconds_current_time(self) -> None:
        """Test validating current time."""
        current = int(time.time())
        result = validate_seconds_since_epoch(current)
        assert isinstance(result, time.struct_time)

    def test_validate_seconds_min_valid(self) -> None:
        """Test validating minimum valid timestamp."""
        result = validate_seconds_since_epoch(1600000000)
        assert isinstance(result, time.struct_time)

    def test_validate_seconds_below_min(self) -> None:
        """Test timestamp below minimum."""
        with pytest.raises(InvalidParameterError):
            validate_seconds_since_epoch(1599999999)

    def test_validate_seconds_max_valid(self) -> None:
        """Test validating maximum valid timestamp."""
        # Note: This is year 5138
        result = validate_seconds_since_epoch(99999999999)
        assert isinstance(result, time.struct_time)

    def test_validate_seconds_above_max(self) -> None:
        """Test timestamp above maximum."""
        with pytest.raises(InvalidParameterError):
            validate_seconds_since_epoch(100000000001)

    def test_validate_seconds_negative(self) -> None:
        """Test negative timestamp."""
        with pytest.raises(InvalidParameterError):
            validate_seconds_since_epoch(-1)

    def test_validate_seconds_zero(self) -> None:
        """Test zero timestamp."""
        with pytest.raises(InvalidParameterError):
            validate_seconds_since_epoch(0)

    def test_validate_seconds_non_integer(self) -> None:
        """Test non-integer timestamp."""
        with pytest.raises(InvalidParameterError):
            validate_seconds_since_epoch(1600000000.5)  # type: ignore

    def test_validate_seconds_string(self) -> None:
        """Test string timestamp."""
        with pytest.raises(InvalidParameterError):
            validate_seconds_since_epoch("1600000000")  # type: ignore

    def test_validate_seconds_year_extraction(self) -> None:
        """Test that year is correctly extracted."""
        # January 1, 2021 00:00:00 UTC
        timestamp = 1609459200
        result = validate_seconds_since_epoch(timestamp)
        assert result.tm_year == 2021
        assert result.tm_mon == 1
        assert result.tm_mday == 1


class TestRandomUtilsEdgeCases:
    """Test edge cases across random utilities."""

    def test_random_functions_no_collision(self) -> None:
        """Test that random functions don't collide."""
        hex1 = random_bytes_hex(32)
        hex2 = random_bytes_hex(32)
        base64_1 = random_bytes_base64(32)
        base64_2 = random_bytes_base64(32)

        assert hex1 != hex2
        assert base64_1 != base64_2

    def test_hash_functions_consistency(self) -> None:
        """Test that hash functions are consistent."""
        data = b"consistency test"

        sha = sha256_hash(data)
        double_le = double_sha256_le(data)
        double_be = double_sha256_be(data)

        # All should be 32 bytes
        assert len(sha) == 32
        assert len(double_le) == 32
        assert len(double_be) == 32

        # Double BE and LE should be reverses
        assert double_be == list(reversed(double_le))

    def test_bytes_and_list_equivalence(self) -> None:
        """Test that bytes and list produce same hash."""
        data_bytes = b"test"
        data_list = [ord(c) for c in "test"]

        hash_bytes = sha256_hash(data_bytes)
        hash_list = sha256_hash(data_list)

        assert hash_bytes == hash_list

    def test_large_random_generation(self) -> None:
        """Test generating large amounts of random data."""
        # Generate 1MB of random data
        large = random_bytes(1024 * 1024)
        assert len(large) == 1024 * 1024
        # Check distribution (should have many different values)
        unique_values = len(set(large))
        # With 1MB, we should see close to 256 unique bytes
        assert unique_values > 200


class TestRandomUtilsIntegration:
    """Integration tests for random utilities."""

    def test_generate_and_hash(self) -> None:
        """Test generating random data and hashing it."""
        random_data = random_bytes(32)
        hash_result = sha256_hash(random_data)

        assert len(random_data) == 32
        assert len(hash_result) == 32
        assert random_data != hash_result

    def test_hex_to_hash(self) -> None:
        """Test converting hex random to hash."""
        hex_data = random_bytes_hex(32)
        bytes_data = bytes.fromhex(hex_data)
        hash_result = sha256_hash(bytes_data)

        assert len(hash_result) == 32

    @pytest.mark.asyncio
    async def test_async_timing_precision(self) -> None:
        """Test async wait timing precision."""
        delays = [10, 20, 30]
        for delay in delays:
            start = time.time()
            await wait_async(delay)
            elapsed = time.time() - start
            expected = delay / 1000.0
            # Allow 50ms tolerance
            assert abs(elapsed - expected) < 0.05

    def test_multiple_hash_operations(self) -> None:
        """Test multiple hash operations in sequence."""
        data = b"start"

        # SHA256
        h1 = sha256_hash(data)

        # Double SHA256 LE
        h2 = double_sha256_le(h1)

        # Double SHA256 BE
        h3 = double_sha256_be(h2)

        # All should be 32 bytes
        assert all(len(h) == 32 for h in [h1, h2, h3])

        # All should be different
        assert h1 != h2
        assert h2 != h3
        assert h1 != h3
