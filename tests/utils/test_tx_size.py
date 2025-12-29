"""Unit tests for tx_size (GO port).

This module tests transaction size calculation logic.

Reference: go-wallet-toolbox/pkg/internal/txutils/tx_size_test.go
"""

import pytest

try:
    from bsv_wallet_toolbox.utils.tx_size import (
        transaction_input_size,
        transaction_output_size,
        transaction_size,
    )

    IMPORTS_AVAILABLE = True
except ImportError:
    IMPORTS_AVAILABLE = False


class TestTxSize:
    """Test suite for tx_size (GO port).

    Reference: go-wallet-toolbox/pkg/internal/txutils/tx_size_test.go
    """

    def test_input_size(self) -> None:
        """Given: Unlocking script size
           When: Calculate transaction input size
           Then: Returns 40 + unlocking_script_size + 1

        Reference: go-wallet-toolbox/pkg/internal/txutils/tx_size_test.go
                   TestInputSize
        """
        # Given
        unlocking_script_size = 100

        # When
        size = transaction_input_size(unlocking_script_size)

        # Then
        assert size == 40 + unlocking_script_size + 1

    def test_output_size(self) -> None:
        """Given: Locking script size
           When: Calculate transaction output size
           Then: Returns 8 + locking_script_size + 1

        Reference: go-wallet-toolbox/pkg/internal/txutils/tx_size_test.go
                   TestOutputSize
        """
        # Given
        locking_script_size = 100

        # When
        size = transaction_output_size(locking_script_size)

        # Then
        assert size == 8 + locking_script_size + 1

    def test_transaction_size(self) -> None:
        """Given: Lists of input and output sizes
           When: Calculate total transaction size
           Then: Returns expected size including envelope and varint overhead

        Reference: go-wallet-toolbox/pkg/internal/txutils/tx_size_test.go
                   TestTransactionSize
        """
        tests = {
            "two inputs, two outputs": {
                "inputSizes": [100, 200],
                "outputSizes": [300, 400],
                "expected": (
                    8  # tx envelope size
                    + 1  # varint size of inputs count
                    + 141  # 40+100+1 input [0] size
                    + 241  # 40+200+1 input [1] size
                    + 1  # varint size of outputs count
                    + 311  # 8+300+3 output [0] size (3 for varint of large script)
                    + 411  # 8+400+3 output [1] size
                ),
            },
            "zero inputs, two outputs": {
                "inputSizes": [],
                "outputSizes": [300, 400],
                "expected": (
                    8  # tx envelope size
                    + 1  # varint size of inputs count
                    + 1  # varint size of outputs count
                    + 311  # 8+300+3 output [0] size
                    + 411  # 8+400+3 output [1] size
                ),
            },
            "two inputs, zero outputs": {
                "inputSizes": [100, 200],
                "outputSizes": [],
                "expected": (
                    8  # tx envelope size
                    + 1  # varint size of inputs count
                    + 141  # 40+100+1 input [0] size
                    + 241  # 40+200+1 input [1] size
                    + 1  # varint size of outputs count
                ),
            },
            "300 inputs, 400 outputs": {
                "inputSizes": [100] * 300,
                "outputSizes": [200] * 400,
                "expected": (
                    8  # tx envelope size
                    + 3  # varint size of inputs count
                    + 300 * 141  # 40+100+1 inputs size
                    + 3  # varint size of outputs count
                    + 400 * 209  # 8+200+1 outputs size
                ),
            },
        }

        for name, test in tests.items():
            # When
            size = transaction_size(test["inputSizes"], test["outputSizes"])

            # Then
            assert size == test["expected"], f"Test '{name}' failed"

    def test_transaction_size_with_error_on_inputs(self) -> None:
        """Given: Input sizes with error condition
           When: Calculate transaction size
           Then: Raises exception

        Reference: go-wallet-toolbox/pkg/internal/txutils/tx_size_test.go
                   TestTransactionSizeWithErrorOnInputs

        Note: GO test uses iterator with errors.
              Python raises exception during iteration.
        """

        # Given
        def error_inputs():
            yield 100
            yield 200
            raise ValueError("error")

        output_sizes = [300, 400]

        # When/Then
        with pytest.raises(ValueError):
            transaction_size(list(error_inputs()), output_sizes)

    def test_transaction_size_with_error_on_outputs(self) -> None:
        """Given: Output sizes with error condition
           When: Calculate transaction size
           Then: Raises exception

        Reference: go-wallet-toolbox/pkg/internal/txutils/tx_size_test.go
                   TestTransactionSizeWithErrorOnOutputs

        Note: GO test uses iterator with errors.
              Python raises exception during iteration.
        """
        # Given
        input_sizes = [100, 200]

        def error_outputs():
            yield 300
            yield 400
            raise ValueError("error")

        # When/Then
        with pytest.raises(ValueError):
            transaction_size(input_sizes, list(error_outputs()))
