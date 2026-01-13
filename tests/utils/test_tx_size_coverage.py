"""Coverage tests for transaction size calculation utilities.

This module tests utilities for calculating transaction sizes.
"""

import pytest

from bsv_wallet_toolbox.errors import TransactionSizeError
from bsv_wallet_toolbox.utils.tx_size import (
    transaction_input_size,
    transaction_output_size,
    transaction_size,
)


class TestTransactionInputSize:
    """Test transaction input size calculation."""

    def test_small_script(self) -> None:
        """Test input with small unlocking script."""
        # 40 bytes (txid + vout + sequence) + script + varint
        size = transaction_input_size(100)
        assert size == 40 + 100 + 1  # varint for 100 is 1 byte

    def test_zero_script(self) -> None:
        """Test input with zero-length script."""
        size = transaction_input_size(0)
        assert size == 40 + 0 + 1

    def test_large_script(self) -> None:
        """Test input with large unlocking script."""
        size = transaction_input_size(300)
        assert size == 40 + 300 + 3  # varint for 300 is 3 bytes (0xfd...)


class TestTransactionOutputSize:
    """Test transaction output size calculation."""

    def test_p2pkh_output(self) -> None:
        """Test P2PKH output size."""
        # P2PKH script is 25 bytes
        size = transaction_output_size(25)
        assert size == 8 + 25 + 1  # 8 bytes value + script + varint

    def test_zero_script_output(self) -> None:
        """Test output with zero-length script."""
        size = transaction_output_size(0)
        assert size == 8 + 0 + 1

    def test_large_script_output(self) -> None:
        """Test output with large locking script."""
        size = transaction_output_size(500)
        assert size == 8 + 500 + 3  # varint for 500 is 3 bytes


class TestTransactionSize:
    """Test full transaction size calculation."""

    def test_simple_transaction(self) -> None:
        """Test simple 1-input, 2-output transaction."""
        input_sizes = [107]  # Typical P2PKH unlocking script
        output_sizes = [25, 25]  # Two P2PKH outputs

        size = transaction_size(input_sizes, output_sizes)
        # 8 (envelope) + 1 (input count) + input + 1 (output count) + outputs
        expected = 8 + 1 + transaction_input_size(107) + 1 + transaction_output_size(25) * 2
        assert size == expected

    def test_empty_transaction(self) -> None:
        """Test transaction with no inputs/outputs."""
        size = transaction_size([], [])
        # Just envelope (8) + varint for 0 inputs (1) + varint for 0 outputs (1)
        assert size == 8 + 1 + 1

    def test_multiple_inputs(self) -> None:
        """Test transaction with multiple inputs."""
        input_sizes = [107, 107, 107]
        output_sizes = [25]

        size = transaction_size(input_sizes, output_sizes)
        assert size > 400

    def test_large_input_count(self) -> None:
        """Test transaction with many inputs (varint changes)."""
        input_sizes = [107] * 300  # 300 inputs, varint becomes 3 bytes
        output_sizes = [25]

        size = transaction_size(input_sizes, output_sizes)
        # Should account for 3-byte varint for input count
        assert size > 40000


class TestVarintCalculation:
    """Test varint length calculation indirectly."""

    def test_varint_boundary_252(self) -> None:
        """Test varint at 252 boundary (still 1 byte)."""
        size = transaction_input_size(252)
        assert size == 40 + 252 + 1

    def test_varint_boundary_253(self) -> None:
        """Test varint at 253 boundary (becomes 3 bytes)."""
        size = transaction_input_size(253)
        assert size == 40 + 253 + 3

    def test_varint_boundary_65535(self) -> None:
        """Test varint at 65535 boundary."""
        size = transaction_input_size(65535)
        assert size == 40 + 65535 + 3

    def test_varint_boundary_65536(self) -> None:
        """Test varint at 65536 boundary (becomes 5 bytes)."""
        size = transaction_input_size(65536)
        assert size == 40 + 65536 + 5


class TestErrorHandling:
    """Test error handling in size calculations."""

    def test_negative_script_size_input(self) -> None:
        """Test negative script size for input."""
        with pytest.raises(TransactionSizeError):
            transaction_input_size(-1)

    def test_negative_script_size_output(self) -> None:
        """Test negative script size for output."""
        with pytest.raises(TransactionSizeError):
            transaction_output_size(-1)

    def test_invalid_input_size_type(self) -> None:
        """Test invalid type for input size."""
        with pytest.raises((TypeError, ValueError, TransactionSizeError)):
            transaction_input_size("invalid")  # type: ignore

    def test_transaction_with_negative_sizes(self) -> None:
        """Test transaction with negative sizes."""
        with pytest.raises(TransactionSizeError):
            transaction_size([-1], [25])


class TestRealWorldScenarios:
    """Test realistic transaction scenarios."""

    def test_typical_payment_tx(self) -> None:
        """Test typical payment transaction size."""
        # 1 input with P2PKH (107 byte script), 2 outputs (payment + change)
        input_sizes = [107]
        output_sizes = [25, 25]

        size = transaction_size(input_sizes, output_sizes)
        # Should be approximately 226 bytes
        assert 220 <= size <= 230

    def test_consolidation_tx(self) -> None:
        """Test consolidation transaction (many inputs, one output)."""
        input_sizes = [107] * 10
        output_sizes = [25]

        size = transaction_size(input_sizes, output_sizes)
        # Should be around 1524 bytes
        assert 1480 <= size <= 1530

    def test_distribution_tx(self) -> None:
        """Test distribution transaction (one input, many outputs)."""
        input_sizes = [107]
        output_sizes = [25] * 10

        size = transaction_size(input_sizes, output_sizes)
        # Should be around 500 bytes
        assert 490 <= size <= 510
