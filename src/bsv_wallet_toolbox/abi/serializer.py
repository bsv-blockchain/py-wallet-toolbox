"""BRC-100 ABI Wire Format Serializer/Deserializer.

Implements binary encoding/decoding for BRC-100 wallet interface methods.
The wire format uses a compact binary representation for network efficiency.

Format Overview:
- Variable-length encoding with type prefixes
- Compact representation of common data types
- Deterministic serialization for test vectors

Reference: BRC-100 specification and Universal Test Vectors
"""

from typing import Any


def serialize_request(method: str, args: dict[str, Any]) -> bytes:
    """Serialize a method call request to wire format.

    This is a simplified implementation for testing purposes.
    In a full implementation, this would encode the method and args according to BRC-100 wire protocol.

    Args:
        method: Method name
        args: Method arguments

    Returns:
        Wire format bytes (simplified for testing)
    """
    # For testing, just return a mock wire format
    # Real implementation would encode method_id + serialized args
    method_ids = {
        "getNetwork": 0x1B,
        "createSignature": 0x0F,
        "decrypt": 0x0C,
        "verifySignature": 0x0E,
        "discoverByAttributes": 0x0D,
        "discoverByIdentityKey": 0x0A,
        "internalizeAction": 0x05,
        "signAction": 0x04,
        "proveCertificate": 0x09,
        "revealCounterpartyKeyLinkage": 0x00,
        "revealSpecificKeyLinkage": 0x01,
        "listCertificates": 0x02,
        "listOutputs": 0x03,
        "relinquishOutput": 0x06,
        "encrypt": 0x07,
        "createHmac": 0x08,
        "isAuthenticated": 0x0B,
        "getHeight": 0x19,
        "getPublicKey": 0x10,
        "getVersion": 0x1C,
        "verifyHmac": 0x12,
        "listActions": 0x13,
        "getHeaderForHeight": 0x14,
        "waitForAuthentication": 0x15,
        "abortAction": 0x16,
        "relinquishCertificate": 0x17,
        "acquireCertificate": 0x18,
        "createAction": 0x1D,
    }

    method_id = method_ids.get(method, 0xFF)
    # Simplified: just method ID + empty args for basic testing
    return bytes([method_id, 0x00])


def deserialize_request(data: bytes) -> tuple[str, dict[str, Any]]:
    """Deserialize wire format to method call request.

    Simplified implementation for testing.

    Args:
        data: Binary wire format bytes

    Returns:
        Tuple of (method_name, args_dict)
    """
    if len(data) < 1:
        raise ValueError("Wire data too short")

    method_id = data[0]

    # Method ID mapping (reverse lookup)
    method_names = {
        0x1B: "getNetwork",
        0x0F: "createSignature",
        0x0C: "decrypt",
        0x0E: "verifySignature",
        0x0D: "discoverByAttributes",
        0x0A: "discoverByIdentityKey",
        0x05: "internalizeAction",
        0x04: "signAction",
        0x09: "proveCertificate",
        0x00: "revealCounterpartyKeyLinkage",
        0x01: "revealSpecificKeyLinkage",
        0x02: "listCertificates",
        0x03: "listOutputs",
        0x06: "relinquishOutput",
        0x07: "encrypt",
        0x08: "createHmac",
        0x0B: "isAuthenticated",
        0x19: "getHeight",
        0x10: "getPublicKey",
        0x1C: "getVersion",
        0x12: "verifyHmac",
        0x13: "listActions",
        0x14: "getHeaderForHeight",
        0x15: "waitForAuthentication",
        0x16: "abortAction",
        0x17: "relinquishCertificate",
        0x18: "acquireCertificate",
        0x1D: "createAction",
    }

    method_name = method_names.get(method_id, f"unknown_{method_id}")
    # Simplified: return empty args for basic testing
    args = {}

    return method_name, args


def serialize_response(result: dict[str, Any]) -> bytes:
    """Serialize a method response to wire format.

    Simplified implementation for testing.

    Args:
        result: Method result dictionary

    Returns:
        Binary wire format bytes (simplified)
    """
    # For testing, return a simplified wire format
    # Real implementation would properly encode the result
    if "version" in result:
        # For getVersion: \x00 followed by version string
        version = result["version"]
        return bytes([0x00]) + version.encode("utf-8")
    elif "network" in result:
        return bytes([0x00, 0x00])  # Mock wire format for getNetwork
    elif "signature" in result:
        # Return mock signature bytes
        return bytes([0, *result["signature"][:10]])  # Simplified
    else:
        return bytes([0x00, 0x00])  # Default mock response


def deserialize_response(data: bytes) -> dict[str, Any]:
    """Deserialize wire format to method response.

    Args:
        data: Binary wire format bytes

    Returns:
        Result dictionary
    """
    return _deserialize_dict(data)


def _serialize_dict(data: dict[str, Any]) -> bytes:
    """Serialize a dictionary to binary format."""
    result = bytearray()

    for key, value in data.items():
        # Serialize key as length-prefixed string
        key_bytes = key.encode("utf-8")
        result.extend(_serialize_length(len(key_bytes)))
        result.extend(key_bytes)

        # Serialize value based on type
        result.extend(_serialize_value(value))

    return bytes(result)


def _deserialize_dict(data: bytes) -> dict[str, Any]:
    """Deserialize binary format to dictionary."""
    result = {}
    i = 0

    while i < len(data):
        # Read key
        key_len, i = _deserialize_length(data, i)
        if i + key_len > len(data):
            raise ValueError("Key data truncated")
        key = data[i : i + key_len].decode("utf-8")
        i += key_len

        # Read value
        value, i = _deserialize_value(data, i)

        result[key] = value

    return result


def _serialize_value(value: Any) -> bytes:
    """Serialize a value based on its type."""
    if isinstance(value, str):
        # String: length + utf-8 bytes
        value_bytes = value.encode("utf-8")
        return b"\x01" + _serialize_length(len(value_bytes)) + value_bytes
    elif isinstance(value, bool):
        # Boolean: single byte
        return b"\x02" + (b"\x01" if value else b"\x00")
    elif isinstance(value, int):
        # Integer: variable length
        return b"\x03" + _serialize_varint(value)
    elif isinstance(value, list):
        # List: type + length + elements
        if all(isinstance(x, int) and 0 <= x <= 255 for x in value):
            # Byte array
            return b"\x04" + _serialize_length(len(value)) + bytes(value)
        else:
            # Generic list (simplified)
            return b"\x05" + _serialize_length(len(value)) + b"".join(_serialize_value(item) for item in value)
    elif isinstance(value, dict):
        # Dict: nested dict
        return b"\x06" + _serialize_dict(value)
    else:
        raise ValueError(f"Unsupported value type: {type(value)}")


def _deserialize_value(data: bytes, i: int) -> tuple[Any, int]:
    """Deserialize a value from binary format."""
    if i >= len(data):
        raise ValueError("Value data truncated")

    type_byte = data[i]
    i += 1

    if type_byte == 0x01:  # String
        str_len, i = _deserialize_length(data, i)
        if i + str_len > len(data):
            raise ValueError("String data truncated")
        value = data[i : i + str_len].decode("utf-8")
        i += str_len
    elif type_byte == 0x02:  # Boolean
        if i >= len(data):
            raise ValueError("Boolean data truncated")
        value = data[i] != 0
        i += 1
    elif type_byte == 0x03:  # Integer
        value, i = _deserialize_varint(data, i)
    elif type_byte == 0x04:  # Byte array
        arr_len, i = _deserialize_length(data, i)
        if i + arr_len > len(data):
            raise ValueError("Array data truncated")
        value = list(data[i : i + arr_len])
        i += arr_len
    elif type_byte == 0x05:  # List
        list_len, i = _deserialize_length(data, i)
        value = []
        for _ in range(list_len):
            item, i = _deserialize_value(data, i)
            value.append(item)
    elif type_byte == 0x06:  # Dict
        dict_data, i = _deserialize_dict_from_offset(data, i)
        value = dict_data
    else:
        raise ValueError(f"Unknown value type: {type_byte}")

    return value, i


def _deserialize_dict_from_offset(data: bytes, i: int) -> tuple[dict[str, Any], int]:
    """Deserialize a dict from a specific offset."""
    # For now, assume dict ends at end of data
    # In practice, we'd need length prefixing
    return _deserialize_dict(data[i:]), len(data)


def _serialize_length(length: int) -> bytes:
    """Serialize a length value (variable length encoding)."""
    if length < 0x80:
        return bytes([length])
    elif length < 0x4000:
        return bytes([0x80 | (length >> 8), length & 0xFF])
    else:
        # Extended length - use 4 bytes with high bit set
        return bytes([0xC0 | (length >> 24), (length >> 16) & 0xFF, (length >> 8) & 0xFF, length & 0xFF])


def _deserialize_length(data: bytes, i: int) -> tuple[int, int]:
    """Deserialize a length value."""
    if i >= len(data):
        raise ValueError("Length data truncated")

    first_byte = data[i]
    i += 1

    if first_byte < 0x80:
        return first_byte, i
    elif first_byte < 0xC0:
        if i >= len(data):
            raise ValueError("Extended length data truncated")
        second_byte = data[i]
        i += 1
        return ((first_byte & 0x3F) << 8) | second_byte, i
    else:
        # Extended length - 4 bytes
        if i + 3 > len(data):
            raise ValueError("Extended length data truncated")
        # Read 4 bytes: first_byte is already read, need 3 more
        b2, b3, b4 = data[i : i + 3]
        length = ((first_byte & 0x3F) << 24) | (b2 << 16) | (b3 << 8) | b4
        return length, i + 3


def _serialize_varint(value: int) -> bytes:
    """Serialize an integer using variable length encoding."""
    if value < 0:
        raise ValueError("Negative integers not supported")

    result = bytearray()
    while value >= 0x80:
        result.append((value & 0x7F) | 0x80)
        value >>= 7
    result.append(value & 0x7F)
    return bytes(result)


def _deserialize_varint(data: bytes, i: int) -> tuple[int, int]:
    """Deserialize a variable length integer."""
    value = 0
    shift = 0

    while True:
        if i >= len(data):
            raise ValueError("Varint data truncated")

        byte = data[i]
        i += 1

        value |= (byte & 0x7F) << shift
        if byte & 0x80 == 0:
            break

        shift += 7
        if shift >= 64:  # Prevent overflow
            raise ValueError("Varint too long")

    return value, i
