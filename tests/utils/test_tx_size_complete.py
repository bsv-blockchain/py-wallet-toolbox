"""Complete coverage tests for tx_size utilities.

This file provides comprehensive tests to achieve 100% coverage of tx_size.py.
"""

import pytest

from bsv_wallet_toolbox.errors import TransactionSizeError
from bsv_wallet_toolbox.utils.tx_size import (
    inputs_outputs_sizes,
    transaction_input_size,
    transaction_output_size,
    transaction_size,
)


class TestVarintLen:
    """Test varint length calculations (indirectly through functions)."""

    def test_varint_len_through_input_size(self) -> None:
        """Test varint length calculation through input size."""
        # Script size <= 252: varint is 1 byte
        assert transaction_input_size(100) == 40 + 100 + 1  # 141
        assert transaction_input_size(252) == 40 + 252 + 1  # 293

        # Script size <= 0xFFFF: varint is 3 bytes
        assert transaction_input_size(253) == 40 + 253 + 3  # 296
        assert transaction_input_size(1000) == 40 + 1000 + 3  # 1043
        assert transaction_input_size(0xFFFF) == 40 + 0xFFFF + 3  # 65578

        # Script size <= 0xFFFFFFFF: varint is 5 bytes
        assert transaction_input_size(0x10000) == 40 + 0x10000 + 5  # 65581
        assert transaction_input_size(0xFFFFFFFF) == 40 + 0xFFFFFFFF + 5  # 4294967340

    def test_varint_negative_size_raises(self) -> None:
        """Test that negative script size raises error."""
        with pytest.raises(TransactionSizeError, match="negative size"):
            transaction_input_size(-1)


class TestTransactionInputSize:
    """Test transaction_input_size function."""

    def test_input_size_small_script(self) -> None:
        """Test input size with small script."""
        # 40 bytes base + script + varint(1)
        size = transaction_input_size(100)
        assert size == 141

    def test_input_size_zero_script(self) -> None:
        """Test input size with zero-length script."""
        size = transaction_input_size(0)
        assert size == 41  # 40 + 0 + 1

    def test_input_size_large_script(self) -> None:
        """Test input size with large script."""
        size = transaction_input_size(1000)
        assert size == 1043  # 40 + 1000 + 3

    def test_input_size_converts_to_int(self) -> None:
        """Test that input size converts float to int."""
        size = transaction_input_size(100.7)
        assert size == 141  # Same as 100


class TestTransactionOutputSize:
    """Test transaction_output_size function."""

    def test_output_size_small_script(self) -> None:
        """Test output size with small script."""
        # 8 bytes base + script + varint(1)
        size = transaction_output_size(100)
        assert size == 109

    def test_output_size_zero_script(self) -> None:
        """Test output size with zero-length script."""
        size = transaction_output_size(0)
        assert size == 9  # 8 + 0 + 1

    def test_output_size_large_script(self) -> None:
        """Test output size with large script."""
        size = transaction_output_size(1000)
        assert size == 1011  # 8 + 1000 + 3

    def test_output_size_converts_to_int(self) -> None:
        """Test that output size converts float to int."""
        size = transaction_output_size(100.7)
        assert size == 109  # Same as 100


class TestTransactionSize:
    """Test transaction_size function."""

    def test_transaction_size_single_input_output(self) -> None:
        """Test transaction size with single input and output."""
        # 8 (envelope) + 1 (input count) + input + 1 (output count) + output
        size = transaction_size([100], [25])
        expected = 8 + 1 + 141 + 1 + 34  # 185
        assert size == expected

    def test_transaction_size_multiple_inputs(self) -> None:
        """Test transaction size with multiple inputs."""
        size = transaction_size([100, 150], [25])
        # 8 + 1 (2 inputs) + (40+100+1) + (40+150+1) + 1 + (8+25+1)
        expected = 8 + 1 + 141 + 191 + 1 + 34  # 376
        assert size == expected

    def test_transaction_size_multiple_outputs(self) -> None:
        """Test transaction size with multiple outputs."""
        size = transaction_size([100], [25, 25])
        # 8 + 1 + (40+100+1) + 1 (2 outputs) + (8+25+1) + (8+25+1)
        expected = 8 + 1 + 141 + 1 + 34 + 34  # 219
        assert size == expected

    def test_transaction_size_no_inputs_no_outputs(self) -> None:
        """Test transaction size with no inputs or outputs."""
        size = transaction_size([], [])
        # 8 (envelope) + 1 (0 inputs) + 1 (0 outputs)
        assert size == 10

    def test_transaction_size_many_inputs_outputs(self) -> None:
        """Test transaction size with many inputs and outputs."""
        inputs = [100] * 300  # 300 inputs
        outputs = [25] * 300  # 300 outputs
        size = transaction_size(inputs, outputs)

        # 8 (envelope)
        # + 3 (varint for 300 inputs, since 300 > 252)
        # + 300 * (40 + 100 + 1)
        # + 3 (varint for 300 outputs)
        # + 300 * (8 + 25 + 1)
        expected = 8 + 3 + (300 * 141) + 3 + (300 * 34)
        assert size == expected

    def test_transaction_size_with_error_in_input(self) -> None:
        """Test transaction size with error in input calculation."""
        # Using negative size should raise error
        with pytest.raises(TransactionSizeError):
            transaction_size([-1], [25])

    def test_transaction_size_with_error_in_output(self) -> None:
        """Test transaction size with error in output calculation."""
        # Using negative size should raise error
        with pytest.raises(TransactionSizeError):
            transaction_size([100], [-1])


class TestInputsOutputsSizes:
    """Test inputs_outputs_sizes function."""

    def test_inputs_outputs_sizes_basic(self) -> None:
        """Test basic inputs and outputs sizes."""
        unlocking = [100, 150]
        locking = [25, 30]

        input_sizes, output_sizes = inputs_outputs_sizes(unlocking, locking)

        assert input_sizes == [141, 191]  # 40+100+1, 40+150+1
        assert output_sizes == [34, 39]  # 8+25+1, 8+30+1

    def test_inputs_outputs_sizes_empty(self) -> None:
        """Test inputs_outputs_sizes with empty lists."""
        input_sizes, output_sizes = inputs_outputs_sizes([], [])

        assert input_sizes == []
        assert output_sizes == []

    def test_inputs_outputs_sizes_single(self) -> None:
        """Test inputs_outputs_sizes with single values."""
        input_sizes, output_sizes = inputs_outputs_sizes([100], [25])

        assert input_sizes == [141]
        assert output_sizes == [34]

    def test_inputs_outputs_sizes_large_scripts(self) -> None:
        """Test inputs_outputs_sizes with large script sizes."""
        unlocking = [1000, 2000]
        locking = [500, 1000]

        input_sizes, output_sizes = inputs_outputs_sizes(unlocking, locking)

        # varint for 1000 is 3 bytes, varint for 2000 is 3 bytes
        assert input_sizes == [1043, 2043]  # 40+1000+3, 40+2000+3
        # varint for 500 is 3 bytes, varint for 1000 is 3 bytes
        assert output_sizes == [511, 1011]  # 8+500+3, 8+1000+3

    def test_inputs_outputs_sizes_converts_to_int(self) -> None:
        """Test that inputs_outputs_sizes converts floats to int."""
        input_sizes, output_sizes = inputs_outputs_sizes([100.7], [25.3])

        assert input_sizes == [141]  # Same as [100]
        assert output_sizes == [34]  # Same as [25]


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_varint_boundaries(self) -> None:
        """Test varint length at boundaries."""
        # At 252: varint is 1 byte
        assert transaction_input_size(252) == 40 + 252 + 1

        # At 253: varint is 3 bytes
        assert transaction_input_size(253) == 40 + 253 + 3

        # At 0xFFFF: varint is still 3 bytes
        assert transaction_input_size(0xFFFF) == 40 + 0xFFFF + 3

        # At 0x10000: varint is 5 bytes
        assert transaction_input_size(0x10000) == 40 + 0x10000 + 5

    def test_typical_p2pkh_transaction(self) -> None:
        """Test size of typical P2PKH transaction."""
        # 1 input with ~107-byte unlocking script
        # 2 outputs with 25-byte locking scripts (P2PKH)
        size = transaction_size([107], [25, 25])

        # 8 + 1 + (40+107+1) + 1 + (8+25+1) + (8+25+1)
        expected = 8 + 1 + 148 + 1 + 34 + 34  # 226 bytes
        assert size == expected

    def test_large_transaction(self) -> None:
        """Test size of large transaction with many inputs/outputs."""
        # 1000 inputs, 1000 outputs
        inputs = [100] * 1000
        outputs = [25] * 1000

        size = transaction_size(inputs, outputs)

        # With 1000 items, varint is 3 bytes
        # 8 + 3 + 1000*(40+100+1) + 3 + 1000*(8+25+1)
        expected = 8 + 3 + (1000 * 141) + 3 + (1000 * 34)  # 175014
        assert size == expected

    def test_zero_script_sizes(self) -> None:
        """Test transaction with zero-length scripts."""
        size = transaction_size([0], [0])

        # 8 + 1 + (40+0+1) + 1 + (8+0+1)
        expected = 8 + 1 + 41 + 1 + 9  # 60
        assert size == expected
