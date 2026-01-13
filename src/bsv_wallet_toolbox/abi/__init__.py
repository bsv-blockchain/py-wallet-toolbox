"""BRC-100 ABI Wire Format Serialization/Deserialization.

This module implements the binary wire format encoding/decoding for BRC-100
wallet interface methods, following the protocol specification.

The wire format uses a compact binary encoding for efficient network transport
and deterministic serialization for testing and compatibility.
"""

from .serializer import (
    deserialize_request,
    deserialize_response,
    serialize_request,
    serialize_response,
)

__all__ = [
    "deserialize_request",
    "deserialize_response",
    "serialize_request",
    "serialize_response",
]
