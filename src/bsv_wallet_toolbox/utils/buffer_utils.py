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


def as_string(
    value: bytes | str | list[int],
    enc: Literal["hex", "utf8", "base64"] = "hex",
    return_enc: Literal["hex", "utf8", "base64"] | None = None,
) -> str:
    """Convert value to string in specified encoding.

    Args:
        value: Value to convert (bytes, hex string, utf8 string, or list of ints)
        enc: Input encoding if value is string ('hex', 'utf8', or 'base64'), defaults to 'hex'
        return_enc: Output encoding ('hex', 'utf8', or 'base64'), defaults to enc

    Returns:
        string object

    Reference: toolbox/ts-wallet-toolbox/src/utility/utilityHelpers.noBuffer.ts:11-30
    """
    # Default return encoding to input encoding
    if return_enc is None:
        return_enc = enc

    # If already a string and encodings match, return as-is
    if isinstance(value, str) and enc == return_enc:
        return value

    # Convert string to bytes using input encoding
    if isinstance(value, str):
        if enc == "hex":
            value = bytes.fromhex(value)
        elif enc == "utf8":
            value = value.encode("utf-8")
        elif enc == "base64":
            value = base64.b64decode(value)
        else:
            msg = f"Unsupported input encoding: {enc}"
            raise ValueError(msg)

    # Convert list to bytes
    if isinstance(value, list):
        value = bytes(value)

    # Now value is bytes
    if not isinstance(value, bytes):
        raise TypeError(f"Cannot convert {type(value)} to string")

    # Encode as requested
    if return_enc == "hex":
        return value.hex()
    elif return_enc == "base64":
        return base64.b64encode(value).decode("ascii")
    else:  # utf8
        return value.decode("utf-8")


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
