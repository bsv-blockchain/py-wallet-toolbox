"""Unit tests for BRC-100 ABI Wire Format Serializer/Deserializer.

This module tests the binary encoding/decoding functionality for BRC-100 wallet interface methods.

Reference: BRC-100 specification and Universal Test Vectors
"""

import pytest

from bsv_wallet_toolbox.abi.serializer import (
    _deserialize_dict,
    _deserialize_length,
    _deserialize_value,
    _deserialize_varint,
    _serialize_dict,
    _serialize_length,
    _serialize_value,
    _serialize_varint,
    deserialize_request,
    deserialize_response,
    serialize_request,
    serialize_response,
)


class TestSerializeRequest:
    """Test suite for serialize_request function."""

    def test_serialize_known_method(self) -> None:
        """Given: Known method name
        When: Call serialize_request
        Then: Returns correct method ID with empty args
        """
        # Given
        method = "getNetwork"
        args = {}

        # When
        result = serialize_request(method, args)

        # Then
        assert result == bytes([0x1B, 0x00])  # 0x1B is getNetwork ID

    def test_serialize_unknown_method(self) -> None:
        """Given: Unknown method name
        When: Call serialize_request
        Then: Returns unknown method ID (0xFF) with empty args
        """
        # Given
        method = "unknownMethod"
        args = {}

        # When
        result = serialize_request(method, args)

        # Then
        assert result == bytes([0xFF, 0x00])

    def test_serialize_method_with_args_ignored(self) -> None:
        """Given: Method with args (currently ignored in simplified impl)
        When: Call serialize_request
        Then: Returns method ID with empty args (simplified)
        """
        # Given
        method = "createAction"
        args = {"some": "data"}

        # When
        result = serialize_request(method, args)

        # Then
        assert result == bytes([0x1D, 0x00])  # 0x1D is createAction ID


class TestDeserializeRequest:
    """Test suite for deserialize_request function."""

    def test_deserialize_known_method(self) -> None:
        """Given: Wire data with known method ID
        When: Call deserialize_request
        Then: Returns correct method name and empty args
        """
        # Given
        data = bytes([0x1B, 0x00])  # getNetwork ID

        # When
        method, args = deserialize_request(data)

        # Then
        assert method == "getNetwork"
        assert args == {}

    def test_deserialize_unknown_method(self) -> None:
        """Given: Wire data with unknown method ID
        When: Call deserialize_request
        Then: Returns unknown method name and empty args
        """
        # Given
        data = bytes([0xFE, 0x00])  # Unknown method ID

        # When
        method, args = deserialize_request(data)

        # Then
        assert method == "unknown_254"
        assert args == {}

    def test_deserialize_empty_data_raises_error(self) -> None:
        """Given: Empty wire data
        When: Call deserialize_request
        Then: Raises ValueError
        """
        # Given
        data = b""

        # When/Then
        with pytest.raises(ValueError, match="Wire data too short"):
            deserialize_request(data)

    def test_deserialize_single_byte_data(self) -> None:
        """Given: Single byte wire data
        When: Call deserialize_request
        Then: Returns unknown method name
        """
        # Given
        data = bytes([0x42])

        # When
        method, args = deserialize_request(data)

        # Then
        assert method == "unknown_66"
        assert args == {}


class TestSerializeResponse:
    """Test suite for serialize_response function."""

    def test_serialize_version_response(self) -> None:
        """Given: Response with version
        When: Call serialize_response
        Then: Returns wire format with version string
        """
        # Given
        result = {"version": "1.0.0"}

        # When
        data = serialize_response(result)

        # Then
        assert data == bytes([0x00]) + b"1.0.0"

    def test_serialize_network_response(self) -> None:
        """Given: Response with network
        When: Call serialize_response
        Then: Returns mock wire format
        """
        # Given
        result = {"network": "mainnet"}

        # When
        data = serialize_response(result)

        # Then
        assert data == bytes([0x00, 0x00])

    def test_serialize_signature_response(self) -> None:
        """Given: Response with signature
        When: Call serialize_response
        Then: Returns mock wire format with signature prefix
        """
        # Given
        signature = list(range(20))  # 20 bytes
        result = {"signature": signature}

        # When
        data = serialize_response(result)

        # Then
        assert data == bytes([0, *list(range(10))])  # First 10 bytes

    def test_serialize_unknown_response(self) -> None:
        """Given: Response with unknown structure
        When: Call serialize_response
        Then: Returns default mock wire format
        """
        # Given
        result = {"unknown": "data"}

        # When
        data = serialize_response(result)

        # Then
        assert data == bytes([0x00, 0x00])


class TestDeserializeResponse:
    """Test suite for deserialize_response function."""

    def test_deserialize_empty_data(self) -> None:
        """Given: Empty response data
        When: Call deserialize_response
        Then: Returns empty dict
        """
        # Given
        data = b""

        # When
        result = deserialize_response(data)

        # Then
        assert result == {}

    def test_deserialize_simple_dict(self) -> None:
        """Given: Simple dictionary data
        When: Call deserialize_response
        Then: Returns deserialized dict
        """
        # Given - Create test data using serialize_dict
        test_dict = {"key": "value"}
        data = _serialize_dict(test_dict)

        # When
        result = deserialize_response(data)

        # Then
        assert result == test_dict


class TestSerializeDict:
    """Test suite for _serialize_dict function."""

    def test_serialize_empty_dict(self) -> None:
        """Given: Empty dictionary
        When: Call _serialize_dict
        Then: Returns empty bytes
        """
        # Given
        data = {}

        # When
        result = _serialize_dict(data)

        # Then
        assert result == b""

    def test_serialize_simple_dict(self) -> None:
        """Given: Dictionary with string key/value
        When: Call _serialize_dict
        Then: Returns serialized bytes
        """
        # Given
        data = {"key": "value"}

        # When
        result = _serialize_dict(data)

        # Then
        # Should be able to deserialize back
        deserialized = _deserialize_dict(result)
        assert deserialized == data

    def test_serialize_multiple_entries(self) -> None:
        """Given: Dictionary with multiple entries
        When: Call _serialize_dict
        Then: Returns serialized bytes for all entries
        """
        # Given
        data = {"key1": "value1", "key2": "value2"}

        # When
        result = _serialize_dict(data)

        # Then
        deserialized = _deserialize_dict(result)
        assert deserialized == data


class TestDeserializeDict:
    """Test suite for _deserialize_dict function."""

    def test_deserialize_empty_data(self) -> None:
        """Given: Empty data
        When: Call _deserialize_dict
        Then: Returns empty dict
        """
        # Given
        data = b""

        # When
        result = _deserialize_dict(data)

        # Then
        assert result == {}

    def test_deserialize_truncated_key_length(self) -> None:
        """Given: Data with truncated key length
        When: Call _deserialize_dict
        Then: Raises ValueError
        """
        # Given - Manually create truncated data
        data = bytes([0xFF])  # Indicate long length but no more data

        # When/Then
        with pytest.raises(ValueError, match="Extended length data truncated"):
            _deserialize_dict(data)

    def test_deserialize_key_data_truncated(self) -> None:
        """Given: Valid key length but insufficient data for key content
        When: Call _deserialize_dict
        Then: Raises ValueError for key data truncated
        """
        # Given - Key length = 5, but only 3 bytes of data after length
        data = bytes([0x05, 0x00, 0x00, 0x00])  # Length=5, but only 3 bytes follow

        # When/Then
        with pytest.raises(ValueError, match="Key data truncated"):
            _deserialize_dict(data)


class TestSerializeValue:
    """Test suite for _serialize_value function."""

    def test_serialize_string(self) -> None:
        """Given: String value
        When: Call _serialize_value
        Then: Returns type byte + length + string bytes
        """
        # Given
        value = "hello"

        # When
        result = _serialize_value(value)

        # Then
        assert result[0] == 0x01  # String type
        # Should be able to deserialize back
        deserialized, _ = _deserialize_value(result, 0)
        assert deserialized == value

    def test_serialize_boolean_true(self) -> None:
        """Given: Boolean true value
        When: Call _serialize_value
        Then: Returns type byte + boolean byte
        """
        # Given
        value = True

        # When
        result = _serialize_value(value)

        # Then
        assert result == bytes([0x02, 0x01])
        deserialized, _ = _deserialize_value(result, 0)
        assert deserialized == value

    def test_serialize_boolean_false(self) -> None:
        """Given: Boolean false value
        When: Call _serialize_value
        Then: Returns type byte + boolean byte
        """
        # Given
        value = False

        # When
        result = _serialize_value(value)

        # Then
        assert result == bytes([0x02, 0x00])
        deserialized, _ = _deserialize_value(result, 0)
        assert deserialized == value

    def test_serialize_integer(self) -> None:
        """Given: Integer value
        When: Call _serialize_value
        Then: Returns type byte + varint bytes
        """
        # Given
        value = 42

        # When
        result = _serialize_value(value)

        # Then
        assert result[0] == 0x03  # Integer type
        deserialized, _ = _deserialize_value(result, 0)
        assert deserialized == value

    def test_serialize_byte_array(self) -> None:
        """Given: List of bytes (0-255)
        When: Call _serialize_value
        Then: Returns type byte + length + byte data
        """
        # Given
        value = [1, 2, 3, 4, 5]

        # When
        result = _serialize_value(value)

        # Then
        assert result[0] == 0x04  # Byte array type
        deserialized, _ = _deserialize_value(result, 0)
        assert deserialized == value

    def test_serialize_generic_list(self) -> None:
        """Given: List with mixed types
        When: Call _serialize_value
        Then: Returns type byte + length + serialized elements
        """
        # Given
        value = ["hello", 42]

        # When
        result = _serialize_value(value)

        # Then
        assert result[0] == 0x05  # List type
        deserialized, _ = _deserialize_value(result, 0)
        assert deserialized == value

    def test_serialize_dict(self) -> None:
        """Given: Dictionary value
        When: Call _serialize_value
        Then: Returns type byte + serialized dict
        """
        # Given
        value = {"key": "value"}

        # When
        result = _serialize_value(value)

        # Then
        assert result[0] == 0x06  # Dict type
        deserialized, _ = _deserialize_value(result, 0)
        assert deserialized == value

    def test_serialize_unsupported_type_raises_error(self) -> None:
        """Given: Unsupported value type
        When: Call _serialize_value
        Then: Raises ValueError
        """
        # Given
        value = object()  # Not supported

        # When/Then
        with pytest.raises(ValueError, match="Unsupported value type"):
            _serialize_value(value)


class TestDeserializeValue:
    """Test suite for _deserialize_value function."""

    def test_deserialize_string(self) -> None:
        """Given: Serialized string data
        When: Call _deserialize_value
        Then: Returns string and new offset
        """
        # Given
        data = bytes([0x01, 0x05]) + b"hello"  # Type + length + string

        # When
        value, offset = _deserialize_value(data, 0)

        # Then
        assert value == "hello"
        assert offset == len(data)

    def test_deserialize_boolean_true(self) -> None:
        """Given: Serialized boolean true
        When: Call _deserialize_value
        Then: Returns True and new offset
        """
        # Given
        data = bytes([0x02, 0x01])  # Type + boolean

        # When
        value, offset = _deserialize_value(data, 0)

        # Then
        assert value is True
        assert offset == 2

    def test_deserialize_integer(self) -> None:
        """Given: Serialized integer
        When: Call _deserialize_value
        Then: Returns integer and new offset
        """
        # Given
        data = bytes([0x03, 0x2A])  # Type + varint for 42

        # When
        value, offset = _deserialize_value(data, 0)

        # Then
        assert value == 42
        assert offset == 2

    def test_deserialize_byte_array(self) -> None:
        """Given: Serialized byte array
        When: Call _deserialize_value
        Then: Returns byte list and new offset
        """
        # Given
        data = bytes([0x04, 0x03, 0x01, 0x02, 0x03])  # Type + length + bytes

        # When
        value, offset = _deserialize_value(data, 0)

        # Then
        assert value == [1, 2, 3]
        assert offset == 5

    def test_deserialize_list(self) -> None:
        """Given: Serialized list
        When: Call _deserialize_value
        Then: Returns list and new offset
        """
        # Given
        data = bytes([0x05, 0x02, 0x03, 0x2A, 0x03, 0x2B])  # Type + length + 2 integers

        # When
        value, offset = _deserialize_value(data, 0)

        # Then
        assert value == [42, 43]
        assert offset == 6

    def test_deserialize_dict(self) -> None:
        """Given: Serialized dict
        When: Call _deserialize_value
        Then: Returns dict and new offset
        """
        # Given
        dict_data = _serialize_dict({"key": "value"})
        data = bytes([0x06]) + dict_data  # Type + dict data

        # When
        value, offset = _deserialize_value(data, 0)

        # Then
        assert value == {"key": "value"}
        assert offset == len(data)

    def test_deserialize_unknown_type_raises_error(self) -> None:
        """Given: Unknown type byte
        When: Call _deserialize_value
        Then: Raises ValueError
        """
        # Given
        data = bytes([0xFF, 0x00])  # Unknown type

        # When/Then
        with pytest.raises(ValueError, match="Unknown value type"):
            _deserialize_value(data, 0)

    def test_deserialize_truncated_data_raises_error(self) -> None:
        """Given: Truncated data
        When: Call _deserialize_value
        Then: Raises ValueError
        """
        # Given
        data = bytes([0x01])  # String type but no length

        # When/Then
        with pytest.raises(ValueError):
            _deserialize_value(data, 0)

    def test_deserialize_value_data_truncated(self) -> None:
        """Given: Empty data at start of value deserialization
        When: Call _deserialize_value
        Then: Raises ValueError for value data truncated
        """
        # Given
        data = b""  # Empty data

        # When/Then
        with pytest.raises(ValueError, match="Value data truncated"):
            _deserialize_value(data, 0)

    def test_deserialize_string_data_truncated(self) -> None:
        """Given: String type with valid length but insufficient string data
        When: Call _deserialize_value
        Then: Raises ValueError for string data truncated
        """
        # Given - String type (0x01), length=5, but only 3 bytes of string data
        data = bytes([0x01, 0x05, 0x00, 0x00, 0x00])  # Type=1, length=5, but only 3 bytes

        # When/Then
        with pytest.raises(ValueError, match="String data truncated"):
            _deserialize_value(data, 0)

    def test_deserialize_boolean_data_truncated(self) -> None:
        """Given: Boolean type but no data byte
        When: Call _deserialize_value
        Then: Raises ValueError for boolean data truncated
        """
        # Given - Boolean type (0x02) but no boolean byte
        data = bytes([0x02])

        # When/Then
        with pytest.raises(ValueError, match="Boolean data truncated"):
            _deserialize_value(data, 0)

    def test_deserialize_array_data_truncated(self) -> None:
        """Given: Byte array type with valid length but insufficient array data
        When: Call _deserialize_value
        Then: Raises ValueError for array data truncated
        """
        # Given - Array type (0x04), length=5, but only 3 bytes of array data
        data = bytes([0x04, 0x05, 0x00, 0x00, 0x00])  # Type=4, length=5, but only 3 bytes

        # When/Then
        with pytest.raises(ValueError, match="Array data truncated"):
            _deserialize_value(data, 0)


class TestSerializeLength:
    """Test suite for _serialize_length function."""

    def test_serialize_small_length(self) -> None:
        """Given: Small length (< 128)
        When: Call _serialize_length
        Then: Returns single byte
        """
        # Given
        length = 42

        # When
        result = _serialize_length(length)

        # Then
        assert result == bytes([42])
        deserialized, _ = _deserialize_length(result, 0)
        assert deserialized == length

    def test_serialize_medium_length(self) -> None:
        """Given: Medium length (128-16383)
        When: Call _serialize_length
        Then: Returns two bytes
        """
        # Given
        length = 500

        # When
        result = _serialize_length(length)

        # Then
        assert len(result) == 2
        assert result[0] & 0x80  # High bit set
        deserialized, _ = _deserialize_length(result, 0)
        assert deserialized == length

    def test_serialize_large_length(self) -> None:
        """Given: Large length (>= 16384)
        When: Call _serialize_length
        Then: Returns four bytes
        """
        # Given
        length = 20000

        # When
        result = _serialize_length(length)

        # Then
        assert len(result) == 4
        deserialized, _ = _deserialize_length(result, 0)
        assert deserialized == length


class TestDeserializeLength:
    """Test suite for _deserialize_length function."""

    def test_deserialize_small_length(self) -> None:
        """Given: Single byte length
        When: Call _deserialize_length
        Then: Returns length and new offset
        """
        # Given
        data = bytes([42])

        # When
        length, offset = _deserialize_length(data, 0)

        # Then
        assert length == 42
        assert offset == 1

    def test_deserialize_medium_length(self) -> None:
        """Given: Two byte length
        When: Call _deserialize_length
        Then: Returns length and new offset
        """
        # Given - 500 = 0x01F4, so 0x81 | (0x01) = 0x81, and 0xF4 = 244
        data = bytes([0x81, 0xF4])  # 500 in medium format

        # When
        length, offset = _deserialize_length(data, 0)

        # Then
        assert length == 500
        assert offset == 2

    def test_deserialize_large_length(self) -> None:
        """Given: Four byte length
        When: Call _deserialize_length
        Then: Returns length and new offset
        """
        # Given - 20000 = 0x4E20, so first byte 0xC0 | (0x00) = 0xC0, then 0x00, 0x4E, 0x20
        data = bytes([0xC0, 0x00, 0x4E, 0x20])  # 20000 in large format

        # When
        length, offset = _deserialize_length(data, 0)

        # Then
        assert length == 20000
        assert offset == 4

    def test_deserialize_truncated_data_raises_error(self) -> None:
        """Given: Truncated length data
        When: Call _deserialize_length
        Then: Raises ValueError
        """
        # Given
        data = bytes([0x81])  # Medium length but missing second byte

        # When/Then
        with pytest.raises(ValueError, match="Extended length data truncated"):
            _deserialize_length(data, 0)


class TestSerializeVarint:
    """Test suite for _serialize_varint function."""

    def test_serialize_small_int(self) -> None:
        """Given: Small integer (< 128)
        When: Call _serialize_varint
        Then: Returns single byte
        """
        # Given
        value = 42

        # When
        result = _serialize_varint(value)

        # Then
        assert result == bytes([42])
        deserialized, _ = _deserialize_varint(result, 0)
        assert deserialized == value

    def test_serialize_medium_int(self) -> None:
        """Given: Medium integer (128-16383)
        When: Call _serialize_varint
        Then: Returns multiple bytes
        """
        # Given
        value = 300

        # When
        result = _serialize_varint(value)

        # Then
        assert len(result) == 2
        deserialized, _ = _deserialize_varint(result, 0)
        assert deserialized == value

    def test_serialize_large_int(self) -> None:
        """Given: Large integer
        When: Call _serialize_varint
        Then: Returns multiple bytes
        """
        # Given
        value = 100000

        # When
        result = _serialize_varint(value)

        # Then
        assert len(result) == 3
        deserialized, _ = _deserialize_varint(result, 0)
        assert deserialized == value

    def test_serialize_zero(self) -> None:
        """Given: Zero
        When: Call _serialize_varint
        Then: Returns single zero byte
        """
        # Given
        value = 0

        # When
        result = _serialize_varint(value)

        # Then
        assert result == bytes([0])
        deserialized, _ = _deserialize_varint(result, 0)
        assert deserialized == value

    def test_serialize_negative_raises_error(self) -> None:
        """Given: Negative integer
        When: Call _serialize_varint
        Then: Raises ValueError
        """
        # Given
        value = -1

        # When/Then
        with pytest.raises(ValueError, match="Negative integers not supported"):
            _serialize_varint(value)


class TestDeserializeVarint:
    """Test suite for _deserialize_varint function."""

    def test_deserialize_small_int(self) -> None:
        """Given: Single byte varint
        When: Call _deserialize_varint
        Then: Returns value and new offset
        """
        # Given
        data = bytes([42])

        # When
        value, offset = _deserialize_varint(data, 0)

        # Then
        assert value == 42
        assert offset == 1

    def test_deserialize_medium_int(self) -> None:
        """Given: Multi-byte varint
        When: Call _deserialize_varint
        Then: Returns value and new offset
        """
        # Given
        data = bytes([0xAC, 0x02])  # 300

        # When
        value, offset = _deserialize_varint(data, 0)

        # Then
        assert value == 300
        assert offset == 2

    def test_deserialize_large_int(self) -> None:
        """Given: Large multi-byte varint
        When: Call _deserialize_varint
        Then: Returns value and new offset
        """
        # Given
        data = bytes([0xA0, 0x8D, 0x06])  # 100000

        # When
        value, offset = _deserialize_varint(data, 0)

        # Then
        assert value == 100000
        assert offset == 3

    def test_deserialize_zero(self) -> None:
        """Given: Zero varint
        When: Call _deserialize_varint
        Then: Returns zero and new offset
        """
        # Given
        data = bytes([0])

        # When
        value, offset = _deserialize_varint(data, 0)

        # Then
        assert value == 0
        assert offset == 1

    def test_deserialize_truncated_data(self) -> None:
        """Given: Varint with continuation bit but no more data
        When: Call _deserialize_varint
        Then: Raises ValueError
        """
        # Given
        data = bytes([0x80])  # Continuation bit set but no more bytes

        # When/Then
        with pytest.raises(ValueError, match="Varint data truncated"):
            _deserialize_varint(data, 0)

    def test_deserialize_max_length_varint(self) -> None:
        """Given: Varint at max safe length
        When: Call _deserialize_varint
        Then: Raises ValueError to prevent overflow
        """
        # Given - Create a varint with too many continuation bytes
        data = bytes([0x80] * 10) + bytes([0x00])  # 10 continuation bytes

        # When/Then
        with pytest.raises(ValueError, match="Varint too long"):
            _deserialize_varint(data, 0)
