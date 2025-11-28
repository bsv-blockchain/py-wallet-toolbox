"""BRC-100 ABI Wire Format Serialization/Deserialization.

This module implements the binary wire format encoding/decoding for BRC-100
wallet interface methods, following the protocol specification.

The wire format uses a compact binary encoding for efficient network transport
and deterministic serialization for testing and compatibility.
"""

from .serializer import (
    serialize_request,
    deserialize_request,
    serialize_response,
    deserialize_response,
)

__all__ = [
    "serialize_request",
    "deserialize_request",
    "serialize_response",
    "deserialize_response",
]
