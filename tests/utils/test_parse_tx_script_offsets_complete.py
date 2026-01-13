"""Complete coverage tests for parse_tx_script_offsets.

This module provides comprehensive tests for transaction script offset parsing.
"""

try:
    from bsv_wallet_toolbox.utils.parse_tx_script_offsets import (
        _read_varint,
        parse_tx_script_offsets,
    )

    IMPORT_SUCCESS = True
except ImportError:
    IMPORT_SUCCESS = False


class TestReadVarint:
    """Test _read_varint internal function."""

    def test_read_varint_single_byte(self) -> None:
        """Test reading single-byte varint (< 0xFD)."""
        data = [0x42, 0x00, 0x00]  # 66 in decimal
        value, bytes_read = _read_varint(data, 0)
        assert value == 0x42
        assert bytes_read == 1

    def test_read_varint_zero(self) -> None:
        """Test reading zero varint."""
        data = [0x00, 0x00, 0x00]
        value, bytes_read = _read_varint(data, 0)
        assert value == 0
        assert bytes_read == 1

    def test_read_varint_max_single_byte(self) -> None:
        """Test reading maximum single-byte varint (0xFC)."""
        data = [0xFC, 0x00, 0x00]
        value, bytes_read = _read_varint(data, 0)
        assert value == 0xFC
        assert bytes_read == 1

    def test_read_varint_uint16(self) -> None:
        """Test reading 2-byte varint (0xFD marker)."""
        data = [0xFD, 0x34, 0x12]  # Little-endian 0x1234
        value, bytes_read = _read_varint(data, 0)
        assert value == 0x1234
        assert bytes_read == 3

    def test_read_varint_uint16_small(self) -> None:
        """Test reading small 2-byte varint."""
        data = [0xFD, 0x01, 0x00]  # 1 in 2-byte format
        value, bytes_read = _read_varint(data, 0)
        assert value == 1
        assert bytes_read == 3

    def test_read_varint_uint32(self) -> None:
        """Test reading 4-byte varint (0xFE marker)."""
        data = [0xFE, 0x78, 0x56, 0x34, 0x12]  # Little-endian 0x12345678
        value, bytes_read = _read_varint(data, 0)
        assert value == 0x12345678
        assert bytes_read == 5

    def test_read_varint_uint64(self) -> None:
        """Test reading 8-byte varint (0xFF marker)."""
        data = [0xFF, 0x08, 0x07, 0x06, 0x05, 0x04, 0x03, 0x02, 0x01]
        value, bytes_read = _read_varint(data, 0)
        assert value == 0x0102030405060708
        assert bytes_read == 9

    def test_read_varint_offset_beyond_end(self) -> None:
        """Test reading varint when offset is beyond data."""
        data = [0x01, 0x02, 0x03]
        value, bytes_read = _read_varint(data, 10)
        assert value == 0
        assert bytes_read == 0

    def test_read_varint_uint16_truncated(self) -> None:
        """Test reading uint16 varint with truncated data."""
        data = [0xFD, 0x01]  # Missing second byte
        value, bytes_read = _read_varint(data, 0)
        assert value == 0
        assert bytes_read == 1

    def test_read_varint_uint32_truncated(self) -> None:
        """Test reading uint32 varint with truncated data."""
        data = [0xFE, 0x01, 0x02]  # Missing bytes
        value, bytes_read = _read_varint(data, 0)
        assert value == 0
        assert bytes_read == 1

    def test_read_varint_uint64_truncated(self) -> None:
        """Test reading uint64 varint with truncated data."""
        data = [0xFF, 0x01, 0x02, 0x03]  # Missing bytes
        value, bytes_read = _read_varint(data, 0)
        assert value == 0
        assert bytes_read == 1

    def test_read_varint_at_different_offsets(self) -> None:
        """Test reading varint at various offsets."""
        data = [0x00, 0x00, 0x42, 0x00, 0x00]

        value1, _bytes_read1 = _read_varint(data, 0)
        assert value1 == 0

        value2, _bytes_read2 = _read_varint(data, 2)
        assert value2 == 0x42

        value3, _bytes_read3 = _read_varint(data, 4)
        assert value3 == 0

    def test_read_varint_all_byte_values_covered(self) -> None:
        """Test that all possible byte values are handled by _read_varint conditions.

        This ensures the fallback return at line 138 is unreachable.
        """
        # Test all possible byte values (0x00 to 0xFF)
        for byte_val in range(256):
            data = [byte_val, 0, 0, 0, 0, 0, 0, 0, 0, 0]  # Sufficient data for all cases

            # This should never raise and should always return valid results
            value, bytes_read = _read_varint(data, 0)

            # Verify bytes_read is always 1, 3, 5, or 9 (valid varint lengths)
            assert bytes_read in [1, 3, 5, 9], f"Invalid bytes_read {bytes_read} for byte 0x{byte_val:02x}"
            assert isinstance(value, int)


class TestParseTxScriptOffsetsEmpty:
    """Test parse_tx_script_offsets with empty/invalid data."""

    def test_parse_empty_tx(self) -> None:
        """Test parsing empty transaction."""
        result = parse_tx_script_offsets([])
        assert isinstance(result, dict)
        assert "inputs" in result
        assert "outputs" in result
        assert len(result["inputs"]) == 0
        assert len(result["outputs"]) == 0

    def test_parse_too_short_tx(self) -> None:
        """Test parsing transaction that's too short."""
        result = parse_tx_script_offsets([0x01, 0x00, 0x00])
        assert isinstance(result, dict)
        assert len(result["inputs"]) == 0
        assert len(result["outputs"]) == 0

    def test_parse_exactly_min_length(self) -> None:
        """Test parsing transaction at minimum length boundary."""
        # 10 bytes is minimum
        tx = [0x01] * 10
        result = parse_tx_script_offsets(tx)
        assert isinstance(result, dict)


class TestParseTxScriptOffsetsSimple:
    """Test parse_tx_script_offsets with simple transactions."""

    def test_parse_no_inputs_no_outputs(self) -> None:
        """Test parsing transaction with no inputs or outputs."""
        # Version (4 bytes) + input count (1) + output count (1) + locktime (4)
        tx = [
            0x01,
            0x00,
            0x00,
            0x00,  # Version
            0x00,  # Input count = 0
            0x00,  # Output count = 0
            0x00,
            0x00,
            0x00,
            0x00,  # Locktime
        ]
        result = parse_tx_script_offsets(tx)
        assert len(result["inputs"]) == 0
        assert len(result["outputs"]) == 0

    def test_parse_one_input_no_script(self) -> None:
        """Test parsing transaction with one input (empty script)."""
        tx = [
            0x01,
            0x00,
            0x00,
            0x00,  # Version
            0x01,  # Input count = 1
            # Input:
            *([0x00] * 32),  # Previous tx hash
            0x00,
            0x00,
            0x00,
            0x00,  # Previous tx output index
            0x00,  # Script length = 0
            # (no script bytes)
            0xFF,
            0xFF,
            0xFF,
            0xFF,  # Sequence
            # Outputs:
            0x00,  # Output count = 0
            0x00,
            0x00,
            0x00,
            0x00,  # Locktime
        ]
        result = parse_tx_script_offsets(tx)
        assert len(result["inputs"]) == 1
        # Script offset should be at position 4 + 1 + 32 + 4 + 1 = 42
        assert result["inputs"][0] == 42
        assert len(result["outputs"]) == 0

    def test_parse_one_input_with_script(self) -> None:
        """Test parsing transaction with one input and a script."""
        script_bytes = [0x48, 0x30, 0x45]  # Example script
        tx = [
            0x01,
            0x00,
            0x00,
            0x00,  # Version
            0x01,  # Input count = 1
            *([0x00] * 32),  # Previous tx hash
            0x00,
            0x00,
            0x00,
            0x00,  # Previous tx output index
            len(script_bytes),  # Script length
            *script_bytes,  # Script
            0xFF,
            0xFF,
            0xFF,
            0xFF,  # Sequence
            0x00,  # Output count = 0
            0x00,
            0x00,
            0x00,
            0x00,  # Locktime
        ]
        result = parse_tx_script_offsets(tx)
        assert len(result["inputs"]) == 1
        # Script offset at position 42
        assert result["inputs"][0] == 42

    def test_parse_one_output_no_script(self) -> None:
        """Test parsing transaction with one output (empty script)."""
        tx = [
            0x01,
            0x00,
            0x00,
            0x00,  # Version
            0x00,  # Input count = 0
            0x01,  # Output count = 1
            0x00,
            0x00,
            0x00,
            0x00,
            0x00,
            0x00,
            0x00,
            0x00,  # Satoshis
            0x00,  # Script length = 0
            0x00,
            0x00,
            0x00,
            0x00,  # Locktime
        ]
        result = parse_tx_script_offsets(tx)
        assert len(result["inputs"]) == 0
        assert len(result["outputs"]) == 1
        # Script offset at position 4 + 1 + 1 + 8 + 1 = 15
        assert result["outputs"][0] == 15

    def test_parse_one_output_with_script(self) -> None:
        """Test parsing transaction with one output and a script."""
        script_bytes = [0x76, 0xA9, 0x14, *([0xAB] * 20), 0x88, 0xAC]  # P2PKH script
        tx = [
            0x01,
            0x00,
            0x00,
            0x00,  # Version
            0x00,  # Input count = 0
            0x01,  # Output count = 1
            0x00,
            0x00,
            0x00,
            0x00,
            0x00,
            0x00,
            0x00,
            0x00,  # Satoshis
            len(script_bytes),  # Script length
            *script_bytes,  # Script
            0x00,
            0x00,
            0x00,
            0x00,  # Locktime
        ]
        result = parse_tx_script_offsets(tx)
        assert len(result["outputs"]) == 1
        assert result["outputs"][0] == 15


class TestParseTxScriptOffsetsMultiple:
    """Test parse_tx_script_offsets with multiple inputs/outputs."""

    def test_parse_two_inputs(self) -> None:
        """Test parsing transaction with two inputs."""
        tx = [
            0x01,
            0x00,
            0x00,
            0x00,  # Version
            0x02,  # Input count = 2
            # Input 1:
            *([0x00] * 32),  # Previous tx hash
            0x00,
            0x00,
            0x00,
            0x00,  # Previous tx output index
            0x00,  # Script length = 0
            0xFF,
            0xFF,
            0xFF,
            0xFF,  # Sequence
            # Input 2:
            *([0x01] * 32),  # Previous tx hash
            0x01,
            0x00,
            0x00,
            0x00,  # Previous tx output index
            0x00,  # Script length = 0
            0xFF,
            0xFF,
            0xFF,
            0xFF,  # Sequence
            0x00,  # Output count = 0
            0x00,
            0x00,
            0x00,
            0x00,  # Locktime
        ]
        result = parse_tx_script_offsets(tx)
        assert len(result["inputs"]) == 2
        # First input script offset
        assert result["inputs"][0] == 42
        # Second input script offset (42 + 0 + 4 + 32 + 4 + 1)
        assert result["inputs"][1] == 83

    def test_parse_two_outputs(self) -> None:
        """Test parsing transaction with two outputs."""
        tx = [
            0x01,
            0x00,
            0x00,
            0x00,  # Version
            0x00,  # Input count = 0
            0x02,  # Output count = 2
            # Output 1:
            0x00,
            0x00,
            0x00,
            0x00,
            0x00,
            0x00,
            0x00,
            0x00,  # Satoshis
            0x00,  # Script length = 0
            # Output 2:
            0x01,
            0x00,
            0x00,
            0x00,
            0x00,
            0x00,
            0x00,
            0x00,  # Satoshis
            0x00,  # Script length = 0
            0x00,
            0x00,
            0x00,
            0x00,  # Locktime
        ]
        result = parse_tx_script_offsets(tx)
        assert len(result["outputs"]) == 2
        # First output script offset
        assert result["outputs"][0] == 15
        # Second output script offset (15 + 0 + 8 + 1)
        assert result["outputs"][1] == 24

    def test_parse_mixed_inputs_outputs(self) -> None:
        """Test parsing transaction with both inputs and outputs."""
        input_script = [0xAA, 0xBB]
        output_script = [0xCC, 0xDD]

        tx = [
            0x01,
            0x00,
            0x00,
            0x00,  # Version
            0x01,  # Input count = 1
            *([0x00] * 32),  # Previous tx hash
            0x00,
            0x00,
            0x00,
            0x00,  # Previous tx output index
            len(input_script),  # Script length
            *input_script,  # Script
            0xFF,
            0xFF,
            0xFF,
            0xFF,  # Sequence
            0x01,  # Output count = 1
            0x10,
            0x27,
            0x00,
            0x00,
            0x00,
            0x00,
            0x00,
            0x00,  # Satoshis (10000)
            len(output_script),  # Script length
            *output_script,  # Script
            0x00,
            0x00,
            0x00,
            0x00,  # Locktime
        ]
        result = parse_tx_script_offsets(tx)
        assert len(result["inputs"]) == 1
        assert len(result["outputs"]) == 1
        assert result["inputs"][0] == 42  # After version + input_count + 32 + 4 + 1
        # Output script offset: 4 + 1 + 32 + 4 + 2 + 2 + 4 + 1 + 8 + 1 = 59
        # Actually: 4 (version) + 1 (input count) + 32 + 4 + 2 + 2 + 4 (input) + 1 (output count) + 8 + 1 = 59
        # Real calculation: 42 + 2 + 4 + 1 + 8 + 1 = 58
        assert result["outputs"][0] == 58


class TestParseTxScriptOffsetsVarint:
    """Test parse_tx_script_offsets with large varint values."""

    def test_parse_input_count_varint_uint16(self) -> None:
        """Test parsing transaction with large input count (0xFD format)."""
        # This creates a tx with 253+ inputs (using 0xFD marker)
        # For simplicity, we'll just test the parsing starts correctly
        tx = [
            0x01,
            0x00,
            0x00,
            0x00,  # Version
            0xFD,
            0x01,
            0x00,  # Input count = 1 (in 2-byte format)
            *([0x00] * 32),  # Previous tx hash
            0x00,
            0x00,
            0x00,
            0x00,  # Previous tx output index
            0x00,  # Script length = 0
            0xFF,
            0xFF,
            0xFF,
            0xFF,  # Sequence
            0x00,  # Output count = 0
            0x00,
            0x00,
            0x00,
            0x00,  # Locktime
        ]
        result = parse_tx_script_offsets(tx)
        assert len(result["inputs"]) == 1
        # Script offset: 4 + 3 + 32 + 4 + 1 = 44
        assert result["inputs"][0] == 44

    def test_parse_output_count_varint_uint16(self) -> None:
        """Test parsing transaction with large output count (0xFD format)."""
        tx = [
            0x01,
            0x00,
            0x00,
            0x00,  # Version
            0x00,  # Input count = 0
            0xFD,
            0x01,
            0x00,  # Output count = 1 (in 2-byte format)
            0x00,
            0x00,
            0x00,
            0x00,
            0x00,
            0x00,
            0x00,
            0x00,  # Satoshis
            0x00,  # Script length = 0
            0x00,
            0x00,
            0x00,
            0x00,  # Locktime
        ]
        result = parse_tx_script_offsets(tx)
        assert len(result["outputs"]) == 1
        # Script offset: 4 + 1 + 3 + 8 + 1 = 17
        assert result["outputs"][0] == 17

    def test_parse_script_length_varint_uint16(self) -> None:
        """Test parsing with large script length (0xFD format)."""
        large_script_size = 253
        script_bytes = [0xAA] * large_script_size

        tx = [
            0x01,
            0x00,
            0x00,
            0x00,  # Version
            0x01,  # Input count = 1
            *([0x00] * 32),  # Previous tx hash
            0x00,
            0x00,
            0x00,
            0x00,  # Previous tx output index
            0xFD,
            0xFD,
            0x00,  # Script length = 253 (in 2-byte format)
            *script_bytes,  # Script
            0xFF,
            0xFF,
            0xFF,
            0xFF,  # Sequence
            0x00,  # Output count = 0
            0x00,
            0x00,
            0x00,
            0x00,  # Locktime
        ]
        result = parse_tx_script_offsets(tx)
        assert len(result["inputs"]) == 1
        # Script offset: 4 + 1 + 32 + 4 + 3 = 44
        assert result["inputs"][0] == 44


class TestParseTxScriptOffsetsEdgeCases:
    """Test parse_tx_script_offsets edge cases."""

    def test_parse_max_single_byte_counts(self) -> None:
        """Test with maximum single-byte input/output counts (252)."""
        # Create transaction with many empty inputs
        tx = [0x01, 0x00, 0x00, 0x00, 0xFC]  # Version + input count (252)

        # Add 252 minimal inputs
        for _ in range(252):
            tx.extend([0x00] * 32)  # Previous tx hash
            tx.extend([0x00, 0x00, 0x00, 0x00])  # Previous tx output index
            tx.append(0x00)  # Script length = 0
            tx.extend([0xFF, 0xFF, 0xFF, 0xFF])  # Sequence

        tx.append(0x00)  # Output count = 0
        tx.extend([0x00, 0x00, 0x00, 0x00])  # Locktime

        result = parse_tx_script_offsets(tx)
        assert len(result["inputs"]) == 252
        assert len(result["outputs"]) == 0

    def test_parse_all_zeros_transaction(self) -> None:
        """Test parsing transaction with all zero bytes."""
        tx = [0x00] * 50
        result = parse_tx_script_offsets(tx)
        # Should handle gracefully
        assert isinstance(result, dict)
        assert "inputs" in result
        assert "outputs" in result

    def test_parse_real_like_transaction_structure(self) -> None:
        """Test with realistic transaction structure."""
        # Simulating a real P2PKH transaction
        tx = [
            # Version
            0x01,
            0x00,
            0x00,
            0x00,
            # Input count
            0x01,
            # Input:
            *([0xAB] * 32),  # Previous txid
            0x00,
            0x00,
            0x00,
            0x00,  # Vout
            0x6A,  # Script length (106 bytes - typical scriptSig)
            *([0x30] * 106),  # Script (mock signature + pubkey)
            0xFF,
            0xFF,
            0xFF,
            0xFF,  # Sequence
            # Output count
            0x02,
            # Output 1:
            0x40,
            0x42,
            0x0F,
            0x00,
            0x00,
            0x00,
            0x00,
            0x00,  # Satoshis (1000000)
            0x19,  # Script length (25 bytes - P2PKH)
            0x76,
            0xA9,
            0x14,
            *([0xCD] * 20),
            0x88,
            0xAC,  # P2PKH script
            # Output 2 (change):
            0x20,
            0xA1,
            0x07,
            0x00,
            0x00,
            0x00,
            0x00,
            0x00,  # Satoshis (500000)
            0x19,  # Script length (25 bytes - P2PKH)
            0x76,
            0xA9,
            0x14,
            *([0xEF] * 20),
            0x88,
            0xAC,  # P2PKH script
            # Locktime
            0x00,
            0x00,
            0x00,
            0x00,
        ]

        result = parse_tx_script_offsets(tx)
        assert len(result["inputs"]) == 1
        assert len(result["outputs"]) == 2

        # Verify offsets are sensible
        assert result["inputs"][0] == 42  # After version + count + prevtx + vout + script_len
        assert result["outputs"][0] > 100  # After inputs
        assert result["outputs"][1] > result["outputs"][0]  # Second output after first


class TestParseTxScriptOffsetsStress:
    """Stress tests for parse_tx_script_offsets."""

    def test_parse_many_small_inputs(self) -> None:
        """Test parsing transaction with many small inputs."""
        input_count = 100
        tx = [0x01, 0x00, 0x00, 0x00, input_count]  # Version + input count

        for _ in range(input_count):
            tx.extend([0x00] * 32)  # Previous tx hash
            tx.extend([0x00, 0x00, 0x00, 0x00])  # Previous tx output index
            tx.append(0x00)  # Script length = 0
            tx.extend([0xFF, 0xFF, 0xFF, 0xFF])  # Sequence

        tx.append(0x00)  # Output count = 0
        tx.extend([0x00, 0x00, 0x00, 0x00])  # Locktime

        result = parse_tx_script_offsets(tx)
        assert len(result["inputs"]) == input_count
        # Verify offsets are sequential
        for i in range(1, input_count):
            # Each input adds 41 bytes (32 + 4 + 1 + 0 + 4)
            assert result["inputs"][i] == result["inputs"][i - 1] + 41

    def test_parse_many_small_outputs(self) -> None:
        """Test parsing transaction with many small outputs."""
        output_count = 100
        tx = [
            0x01,
            0x00,
            0x00,
            0x00,  # Version
            0x00,  # Input count = 0
            output_count,  # Output count
        ]

        for _ in range(output_count):
            tx.extend([0x10, 0x27, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])  # Satoshis
            tx.append(0x00)  # Script length = 0

        tx.extend([0x00, 0x00, 0x00, 0x00])  # Locktime

        result = parse_tx_script_offsets(tx)
        assert len(result["outputs"]) == output_count
        # Verify offsets are sequential
        for i in range(1, output_count):
            # Each output adds 9 bytes (8 + 1 + 0)
            assert result["outputs"][i] == result["outputs"][i - 1] + 9
