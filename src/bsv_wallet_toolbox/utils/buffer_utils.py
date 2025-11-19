"""Buffer/bytes conversion utilities.

Convert between different byte representations: bytes, hex strings, base64, etc.

Reference: toolbox/ts-wallet-toolbox/src/utility/utilityHelpers.buffer.ts
"""

from __future__ import annotations

import base64
from typing import Literal


def as_buffer(value: bytes | str | list[int], encoding: Literal["hex", "utf8", "base64"] = "hex") -> bytes:
    """Convert value to bytes buffer.

    Args:
        value: Value to convert (bytes, hex string, utf8 string, list of ints, or base64)
        encoding: Encoding of input if value is string ('hex', 'utf8', or 'base64')

    Returns:
        bytes object

    Reference: toolbox/ts-wallet-toolbox/src/utility/utilityHelpers.buffer.ts:8-22
    """
    if isinstance(value, bytes):
        return value
    if isinstance(value, list):
        return bytes(value)
    if isinstance(value, str):
        if encoding == "hex":
            return bytes.fromhex(value)
        elif encoding == "base64":
            return base64.b64decode(value)
        else:  # utf8
            return value.encode("utf-8")
    raise TypeError(f"Cannot convert {type(value)} to buffer")


def as_string(value: bytes | str | list[int], encoding: Literal["hex", "utf8", "base64"] = "hex") -> str:
    """Convert value to string in specified encoding.

    Args:
        value: Value to convert (bytes, hex string, utf8 string, or list of ints)
        encoding: Output encoding ('hex', 'utf8', or 'base64')

    Returns:
        string object

    Reference: toolbox/ts-wallet-toolbox/src/utility/utilityHelpers.buffer.ts:23-27
    """
    if isinstance(value, str):
        return value
    if isinstance(value, bytes):
        buf = value
    elif isinstance(value, list):
        buf = bytes(value)
    else:
        raise TypeError(f"Cannot convert {type(value)} to string")

    if encoding == "hex":
        return buf.hex()
    elif encoding == "base64":
        return base64.b64encode(buf).decode("ascii")
    else:  # utf8
        return buf.decode("utf-8")


def as_array(value: bytes | str | list[int], encoding: Literal["hex", "utf8", "base64"] = "hex") -> list[int]:
    """Convert value to list of integers (byte array).

    Args:
        value: Value to convert (bytes, hex string, utf8 string, or list of ints)
        encoding: Encoding of input if value is string ('hex', 'utf8', or 'base64')

    Returns:
        list of integers (0-255)

    Reference: toolbox/ts-wallet-toolbox/src/utility/utilityHelpers.buffer.ts:28-32
    """
    if isinstance(value, list):
        return value
    if isinstance(value, bytes):
        return list(value)
    if isinstance(value, str):
        buf = as_buffer(value, encoding)
        return list(buf)
    raise TypeError(f"Cannot convert {type(value)} to array")


def as_uint8array(value: bytes | str | list[int], encoding: Literal["hex", "utf8", "base64"] = "hex") -> bytes:
    """Convert value to bytes (Uint8Array equivalent in Python).

    Args:
        value: Value to convert (bytes, hex string, utf8 string, or list of ints)
        encoding: Encoding of input if value is string ('hex', 'utf8', or 'base64')

    Returns:
        bytes object

    Reference: toolbox/ts-wallet-toolbox/src/utility/utilityHelpers.noBuffer.ts:54-60
    """
    if isinstance(value, list):
        return bytes(value)
    if isinstance(value, bytes):
        return value
    if isinstance(value, str):
        return as_buffer(value, encoding)
    raise TypeError(f"Cannot convert {type(value)} to Uint8Array")
