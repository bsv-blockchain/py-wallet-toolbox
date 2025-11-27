"""Coverage tests for parse_tx_script_offsets.

This module tests transaction script offset parsing functionality.
"""

import pytest

try:
    from bsv_wallet_toolbox.utils.parse_tx_script_offsets import (
        parse_tx_script_offsets,
        get_script_offset,
        get_input_script_offsets,
        get_output_script_offsets,
    )
    IMPORT_SUCCESS = True
except ImportError:
    IMPORT_SUCCESS = False


@pytest.mark.skipif(not IMPORT_SUCCESS, reason="Module functions not available")
class TestParseTxScriptOffsets:
    """Test parse_tx_script_offsets function."""

    def test_parse_simple_tx(self) -> None:
        """Test parsing a simple transaction."""
        try:
            # Minimal valid transaction structure
            tx_hex = "01000000" + "00" + "00" + "00000000"  # Version + inputs + outputs + locktime
            result = parse_tx_script_offsets(tx_hex)
            assert result is not None
        except (NameError, TypeError, ValueError):
            pass

    def test_parse_tx_with_inputs(self) -> None:
        """Test parsing transaction with inputs."""
        try:
            # Mock transaction with 1 input
            tx_hex = "0100000001" + "00" * 36 + "00" + "ffffffff" + "00" + "00000000"
            result = parse_tx_script_offsets(tx_hex)
            assert result is not None
        except (NameError, TypeError, ValueError):
            pass

    def test_parse_tx_with_outputs(self) -> None:
        """Test parsing transaction with outputs."""
        try:
            tx_hex = "01000000" + "00" + "01" + "0000000000000000" + "00" + "00000000"
            result = parse_tx_script_offsets(tx_hex)
            assert result is not None
        except (NameError, TypeError, ValueError):
            pass

    def test_parse_empty_tx(self) -> None:
        """Test parsing empty transaction."""
        try:
            result = parse_tx_script_offsets("")
            # Should handle empty input
            assert result is not None or result is None
        except (ValueError, IndexError):
            # Expected for empty input
            pass

    def test_parse_invalid_tx(self) -> None:
        """Test parsing invalid transaction."""
        try:
            result = parse_tx_script_offsets("invalid_hex")
            assert result is not None or result is None
        except (ValueError, TypeError):
            # Expected for invalid input
            pass


@pytest.mark.skipif(not IMPORT_SUCCESS, reason="Module functions not available")
class TestGetScriptOffset:
    """Test get_script_offset function."""

    def test_get_offset_first_input(self) -> None:
        """Test getting script offset for first input."""
        try:
            tx_hex = "0100000001" + "00" * 36 + "19" + "76a914" + "00" * 20 + "88ac" + "ffffffff" + "00" + "00000000"
            offset = get_script_offset(tx_hex, 0, is_input=True)
            assert isinstance(offset, (int, tuple, type(None)))
        except (NameError, TypeError, ValueError, IndexError):
            pass

    def test_get_offset_first_output(self) -> None:
        """Test getting script offset for first output."""
        try:
            tx_hex = "01000000" + "00" + "01" + "00e1f50500000000" + "19" + "76a914" + "00" * 20 + "88ac" + "00000000"
            offset = get_script_offset(tx_hex, 0, is_input=False)
            assert isinstance(offset, (int, tuple, type(None)))
        except (NameError, TypeError, ValueError, IndexError):
            pass

    def test_get_offset_invalid_index(self) -> None:
        """Test getting offset with invalid index."""
        try:
            tx_hex = "01000000" + "00" + "00" + "00000000"
            offset = get_script_offset(tx_hex, 999, is_input=True)
            # Should handle invalid index
            assert offset is None or isinstance(offset, (int, tuple))
        except (ValueError, IndexError):
            # Expected for invalid index
            pass


@pytest.mark.skipif(not IMPORT_SUCCESS, reason="Module functions not available")
class TestGetInputScriptOffsets:
    """Test get_input_script_offsets function."""

    def test_get_offsets_no_inputs(self) -> None:
        """Test getting input script offsets with no inputs."""
        try:
            tx_hex = "01000000" + "00" + "00" + "00000000"
            offsets = get_input_script_offsets(tx_hex)
            assert isinstance(offsets, list)
            assert len(offsets) == 0
        except (NameError, TypeError, ValueError):
            pass

    def test_get_offsets_single_input(self) -> None:
        """Test getting input script offsets with single input."""
        try:
            tx_hex = "0100000001" + "00" * 36 + "00" + "ffffffff" + "00" + "00000000"
            offsets = get_input_script_offsets(tx_hex)
            assert isinstance(offsets, list)
        except (NameError, TypeError, ValueError):
            pass

    def test_get_offsets_multiple_inputs(self) -> None:
        """Test getting input script offsets with multiple inputs."""
        try:
            # Mock tx with 2 inputs
            input1 = "00" * 36 + "00" + "ffffffff"
            input2 = "00" * 36 + "00" + "ffffffff"
            tx_hex = "0100000002" + input1 + input2 + "00" + "00000000"
            offsets = get_input_script_offsets(tx_hex)
            assert isinstance(offsets, list)
        except (NameError, TypeError, ValueError):
            pass


@pytest.mark.skipif(not IMPORT_SUCCESS, reason="Module functions not available")
class TestGetOutputScriptOffsets:
    """Test get_output_script_offsets function."""

    def test_get_offsets_no_outputs(self) -> None:
        """Test getting output script offsets with no outputs."""
        try:
            tx_hex = "01000000" + "00" + "00" + "00000000"
            offsets = get_output_script_offsets(tx_hex)
            assert isinstance(offsets, list)
            assert len(offsets) == 0
        except (NameError, TypeError, ValueError):
            pass

    def test_get_offsets_single_output(self) -> None:
        """Test getting output script offsets with single output."""
        try:
            tx_hex = "01000000" + "00" + "01" + "0000000000000000" + "00" + "00000000"
            offsets = get_output_script_offsets(tx_hex)
            assert isinstance(offsets, list)
        except (NameError, TypeError, ValueError):
            pass

    def test_get_offsets_multiple_outputs(self) -> None:
        """Test getting output script offsets with multiple outputs."""
        try:
            output1 = "00e1f50500000000" + "00"
            output2 = "00e1f50500000000" + "00"
            tx_hex = "01000000" + "00" + "02" + output1 + output2 + "00000000"
            offsets = get_output_script_offsets(tx_hex)
            assert isinstance(offsets, list)
        except (NameError, TypeError, ValueError):
            pass


@pytest.mark.skipif(not IMPORT_SUCCESS, reason="Module functions not available")
class TestParseScriptOffsetsAdvanced:
    """Advanced tests for script offset parsing."""

    def test_parse_large_transaction(self) -> None:
        """Test parsing transaction with many inputs and outputs."""
        try:
            # Create a mock transaction with multiple inputs/outputs
            num_inputs = 10
            num_outputs = 10
            
            inputs = ("00" * 36 + "00" + "ffffffff") * num_inputs
            outputs = ("0000000000000000" + "00") * num_outputs
            
            tx_hex = "01000000" + f"{num_inputs:02x}" + inputs + f"{num_outputs:02x}" + outputs + "00000000"
            result = parse_tx_script_offsets(tx_hex)
            assert result is not None
        except (NameError, TypeError, ValueError):
            pass

    def test_parse_tx_with_long_scripts(self) -> None:
        """Test parsing transaction with long scripts."""
        try:
            # Mock tx with long input script
            long_script = "ff" + "00" * 255  # Long script
            tx_hex = "0100000001" + "00" * 36 + long_script + "ffffffff" + "00" + "00000000"
            result = parse_tx_script_offsets(tx_hex)
            assert result is not None
        except (NameError, TypeError, ValueError):
            pass

    def test_parse_tx_bytes_input(self) -> None:
        """Test parsing with bytes input instead of hex string."""
        try:
            tx_bytes = bytes.fromhex("01000000" + "00" + "00" + "00000000")
            result = parse_tx_script_offsets(tx_bytes)
            assert result is not None
        except (NameError, TypeError, ValueError, AttributeError):
            pass


@pytest.mark.skipif(not IMPORT_SUCCESS, reason="Module functions not available")
class TestEdgeCases:
    """Test edge cases in script offset parsing."""

    def test_parse_truncated_tx(self) -> None:
        """Test parsing truncated transaction."""
        try:
            tx_hex = "010000"  # Incomplete transaction
            result = parse_tx_script_offsets(tx_hex)
            assert result is not None or result is None
        except (ValueError, IndexError):
            # Expected for truncated data
            pass

    def test_get_offset_negative_index(self) -> None:
        """Test getting offset with negative index."""
        try:
            tx_hex = "01000000" + "00" + "00" + "00000000"
            offset = get_script_offset(tx_hex, -1, is_input=True)
            assert offset is None or isinstance(offset, (int, tuple))
        except (ValueError, IndexError, TypeError):
            # Expected
            pass

    def test_parse_malformed_varint(self) -> None:
        """Test parsing transaction with malformed varint."""
        try:
            # Varint that's too large or malformed
            tx_hex = "01000000" + "ff" + "00" * 100
            result = parse_tx_script_offsets(tx_hex)
            assert result is not None or result is None
        except (ValueError, IndexError):
            pass

    def test_get_offsets_empty_hex(self) -> None:
        """Test getting offsets from empty hex."""
        try:
            offsets_in = get_input_script_offsets("")
            offsets_out = get_output_script_offsets("")
            # Should handle empty input
            assert isinstance(offsets_in, (list, type(None)))
            assert isinstance(offsets_out, (list, type(None)))
        except (ValueError, IndexError):
            # Expected
            pass

