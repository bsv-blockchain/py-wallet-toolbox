"""Coverage tests for extract_raw_txs utility.

This module tests the extraction of raw transaction hex strings from various input formats.
"""

import pytest

from bsv_wallet_toolbox.utils.extract_raw_txs import extract_raw_txs


class TestExtractRawTxs:
    """Test extract_raw_txs function."""

    def test_extract_from_hex_strings(self) -> None:
        """Test extracting raw txs from hex string inputs."""
        tx_hex = "0100000001abcd"  # Simplified tx hex
        items = [tx_hex, tx_hex.upper()]

        result = extract_raw_txs(items)

        assert len(result) == 2
        assert all(tx == tx_hex for tx in result)

    def test_extract_from_bytes(self) -> None:
        """Test extracting raw txs from bytes inputs."""
        tx_hex = "0100000001abcd"
        tx_bytes = bytes.fromhex(tx_hex)

        result = extract_raw_txs([tx_bytes])

        assert len(result) == 1
        assert result[0] == tx_hex

    def test_extract_from_bytearray(self) -> None:
        """Test extracting raw txs from bytearray inputs."""
        tx_hex = "0100000001abcd"
        tx_bytearray = bytearray.fromhex(tx_hex)

        result = extract_raw_txs([tx_bytearray])

        assert len(result) == 1
        assert result[0] == tx_hex

    def test_extract_from_dict_with_raw(self) -> None:
        """Test extracting raw txs from dicts with 'raw' key."""
        tx_hex = "0100000001abcd"
        item = {"raw": tx_hex, "other": "data"}

        result = extract_raw_txs([item])

        assert len(result) == 1
        assert result[0] == tx_hex

    def test_extract_from_dict_with_rawTx(self) -> None:
        """Test extracting raw txs from dicts with 'rawTx' key."""
        tx_hex = "0100000001abcd"
        item = {"rawTx": tx_hex, "other": "data"}

        result = extract_raw_txs([item])

        assert len(result) == 1
        assert result[0] == tx_hex

    def test_extract_from_dict_with_hex(self) -> None:
        """Test extracting raw txs from dicts with 'hex' key."""
        tx_hex = "0100000001abcd"
        item = {"hex": tx_hex, "other": "data"}

        result = extract_raw_txs([item])

        assert len(result) == 1
        assert result[0] == tx_hex

    def test_extract_dict_priority_raw_over_others(self) -> None:
        """Test that 'raw' key takes priority in dict extraction."""
        tx_hex1 = "0100000001abcd"
        tx_hex2 = "0200000001beef"
        item = {"raw": tx_hex1, "rawTx": tx_hex2, "hex": "other"}

        result = extract_raw_txs([item])

        assert len(result) == 1
        assert result[0] == tx_hex1

    def test_extract_dict_priority_rawTx_over_hex(self) -> None:
        """Test that 'rawTx' key takes priority over 'hex'."""
        tx_hex1 = "0100000001abcd"
        tx_hex2 = "0200000001beef"
        item = {"rawTx": tx_hex1, "hex": tx_hex2}

        result = extract_raw_txs([item])

        assert len(result) == 1
        assert result[0] == tx_hex1

    def test_extract_mixed_types(self) -> None:
        """Test extracting from mixed input types."""
        tx_hex1 = "0100000001abcd"
        tx_hex2 = "0200000001beef"
        tx_hex3 = "0300000001cafe"

        items = [
            tx_hex1,
            bytes.fromhex(tx_hex2),
            {"raw": tx_hex3},
        ]

        result = extract_raw_txs(items)

        assert len(result) == 3
        assert result[0] == tx_hex1
        assert result[1] == tx_hex2
        assert result[2] == tx_hex3

    def test_extract_empty_list(self) -> None:
        """Test extracting from empty iterable."""
        result = extract_raw_txs([])

        assert result == []

    def test_extract_invalid_hex_string_raises(self) -> None:
        """Test that invalid hex string raises ValueError."""
        invalid_hex = "not_hex_123"

        with pytest.raises(ValueError, match="non-hexadecimal"):
            extract_raw_txs([invalid_hex])

    def test_extract_odd_length_hex_raises(self) -> None:
        """Test that odd-length hex string raises ValueError."""
        odd_hex = "abc"  # Odd number of characters

        with pytest.raises(ValueError, match="non-hexadecimal"):
            extract_raw_txs([odd_hex])

    def test_extract_dict_missing_raw_raises(self) -> None:
        """Test that dict without raw tx fields raises ValueError."""
        item = {"other": "data", "no": "raw"}

        with pytest.raises(ValueError, match="missing raw tx hex"):
            extract_raw_txs([item])

    def test_extract_dict_non_string_raw_raises(self) -> None:
        """Test that dict with non-string raw value raises ValueError."""
        item = {"raw": 12345}  # int instead of string

        with pytest.raises(ValueError, match="missing raw tx hex"):
            extract_raw_txs([item])

    def test_extract_dict_invalid_hex_raises(self) -> None:
        """Test that dict with invalid hex raises ValueError."""
        item = {"raw": "invalid_hex"}

        with pytest.raises(ValueError, match="non-hexadecimal"):
            extract_raw_txs([item])

    def test_extract_unsupported_type_raises(self) -> None:
        """Test that unsupported input type raises TypeError."""
        with pytest.raises(TypeError, match="unsupported item type"):
            extract_raw_txs([123])  # int is not supported

        with pytest.raises(TypeError, match="unsupported item type"):
            extract_raw_txs([None])  # None is not supported

        with pytest.raises(TypeError, match="unsupported item type"):
            extract_raw_txs([[]])  # list is not supported

    def test_extract_uppercase_hex_normalized_to_lowercase(self) -> None:
        """Test that uppercase hex is normalized to lowercase."""
        tx_hex_upper = "ABCDEF012345"
        tx_hex_lower = tx_hex_upper.lower()

        result = extract_raw_txs([tx_hex_upper])

        assert result[0] == tx_hex_lower

    def test_extract_preserves_order(self) -> None:
        """Test that output preserves input order."""
        tx1 = "0100000001abcd"
        tx2 = "0200000001beef"
        tx3 = "0300000001cafe"

        items = [tx1, tx2, tx3]
        result = extract_raw_txs(items)

        assert result == [tx1, tx2, tx3]

    def test_extract_generator_input(self) -> None:
        """Test extracting from generator/iterator input."""
        tx1 = "0100000001abcd"
        tx2 = "0200000001beef"

        def gen():
            yield tx1
            yield tx2

        result = extract_raw_txs(gen())

        assert len(result) == 2
        assert result[0] == tx1
        assert result[1] == tx2
