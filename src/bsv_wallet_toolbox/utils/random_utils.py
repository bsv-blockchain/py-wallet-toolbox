"""Random and utility functions for cryptographic operations.

This module provides utilities for generating cryptographically secure random data,
time delays, and other helper functions.

Reference: toolbox/ts-wallet-toolbox/src/utility/utilityHelpers.ts
"""

import asyncio
import base64
import hashlib
import secrets
import time

from bsv_wallet_toolbox.errors import InvalidParameterError


def wait_async(milliseconds: int) -> asyncio.sleep:
    """Return an awaitable that resolves after the given milliseconds.

    Args:
        milliseconds: Number of milliseconds to wait
                     Must be greater than 0 and less than 120,000 (2 minutes)

    Returns:
        Coroutine that resolves after the delay

    Raises:
        InvalidParameterError: If milliseconds is out of valid range

    Reference:
        - toolbox/ts-wallet-toolbox/src/utility/utilityHelpers.ts (wait function)
    """
    min_wait = 0
    max_wait = 2 * 60 * 1000  # 120,000 milliseconds (2 minutes)

    if not isinstance(milliseconds, int) or milliseconds < min_wait or milliseconds > max_wait:
        raise InvalidParameterError(
            "milliseconds",
            f"a number between {min_wait} and {max_wait}, not {milliseconds}",
        )

    seconds = milliseconds / 1000.0
    return asyncio.sleep(seconds)


def random_bytes(count: int) -> list[int]:
    """Generate cryptographically secure random bytes.

    Args:
        count: Number of random bytes to generate

    Returns:
        List of random bytes as integers (0-255)

    Reference:
        - toolbox/ts-wallet-toolbox/src/utility/utilityHelpers.ts (randomBytes function)
    """
    if not isinstance(count, int) or count < 0:
        raise InvalidParameterError("count", "a non-negative integer")

    random_data = secrets.token_bytes(count)
    return list(random_data)


def random_bytes_hex(count: int) -> str:
    """Generate cryptographically secure random bytes as hex string.

    Args:
        count: Number of random bytes to generate

    Returns:
        Hex-encoded string of random bytes

    Reference:
        - toolbox/ts-wallet-toolbox/src/utility/utilityHelpers.ts (randomBytesHex function)
    """
    if not isinstance(count, int) or count < 0:
        raise InvalidParameterError("count", "a non-negative integer")

    random_data = secrets.token_bytes(count)
    return random_data.hex()


def random_bytes_base64(count: int) -> str:
    """Generate cryptographically secure random bytes as base64 string.

    Args:
        count: Number of random bytes to generate

    Returns:
        Base64-encoded string of random bytes

    Reference:
        - toolbox/ts-wallet-toolbox/src/utility/utilityHelpers.ts (randomBytesBase64 function)
    """
    if not isinstance(count, int) or count < 0:
        raise InvalidParameterError("count", "a non-negative integer")

    random_data = secrets.token_bytes(count)
    return base64.b64encode(random_data).decode("utf-8")


def sha256_hash(data: bytes | list[int]) -> list[int]:
    """Calculate SHA256 hash of data.

    Args:
        data: Bytes or list of integers to hash

    Returns:
        SHA256 hash as list of integers

    Reference:
        - toolbox/ts-wallet-toolbox/src/utility/utilityHelpers.ts (sha256Hash function)
    """
    if isinstance(data, list):
        data = bytes(data)
    elif not isinstance(data, bytes):
        raise InvalidParameterError("data", "bytes or list of integers")

    hash_result = hashlib.sha256(data).digest()
    return list(hash_result)


def double_sha256_le(data: bytes | list[int]) -> list[int]:
    """Calculate double SHA256 hash (little-endian).

    Args:
        data: Bytes or list of integers to hash

    Returns:
        Double SHA256 hash as list of integers (little-endian, byte 0 first)

    Reference:
        - toolbox/ts-wallet-toolbox/src/utility/utilityHelpers.ts (doubleSha256LE function)
    """
    if isinstance(data, list):
        data = bytes(data)
    elif not isinstance(data, bytes):
        raise InvalidParameterError("data", "bytes or list of integers")

    first_hash = hashlib.sha256(data).digest()
    second_hash = hashlib.sha256(first_hash).digest()
    return list(second_hash)


def double_sha256_be(data: bytes | list[int]) -> list[int]:
    """Calculate double SHA256 hash (big-endian).

    Args:
        data: Bytes or list of integers to hash

    Returns:
        Double SHA256 hash as list of integers (big-endian, byte 31 first)

    Reference:
        - toolbox/ts-wallet-toolbox/src/utility/utilityHelpers.ts (doubleSha256BE function)
    """
    le_result = double_sha256_le(data)
    # Reverse to convert from little-endian to big-endian
    return list(reversed(le_result))


def validate_seconds_since_epoch(timestamp: int) -> time.struct_time:
    """Validate and convert unix timestamp to datetime.

    Args:
        timestamp: Seconds since epoch (unix timestamp)

    Returns:
        Time struct representing the datetime

    Raises:
        InvalidParameterError: If timestamp is outside valid range
                              (must be between 1600000000 and 100000000000)

    Reference:
        - toolbox/ts-wallet-toolbox/src/utility/utilityHelpers.ts (validateSecondsSinceEpoch function)
    """
    min_time = 1600000000
    max_time = 100000000000

    if not isinstance(timestamp, int) or timestamp < min_time or timestamp > max_time:
        raise InvalidParameterError("timestamp", f"valid unix timestamp (between {min_time} and {max_time})")

    return time.gmtime(timestamp)


__all__ = [
    "double_sha256_be",
    "double_sha256_le",
    "random_bytes",
    "random_bytes_base64",
    "random_bytes_hex",
    "sha256_hash",
    "validate_seconds_since_epoch",
    "wait_async",
]
