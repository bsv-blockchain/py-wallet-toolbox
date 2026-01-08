"""Unit tests for generateChangeSdk function.

These tests verify the UTXO selection and change allocation algorithm
for transaction construction.

Reference: wallet-toolbox/src/storage/methods/__test/GenerateChange/generateChangeSdk.test.ts
"""

import pytest

from bsv_wallet_toolbox.errors import InsufficientFundsError
from bsv_wallet_toolbox.utils import generate_change_sdk


class TestGenerateChangeSdk:
    """Test suite for generateChangeSdk function.

    Reference: wallet-toolbox/src/storage/methods/__test/GenerateChange/generateChangeSdk.test.ts
    """

    def test_two_outputs(self) -> None:
        """Given: Transaction with two fixed outputs (1234 sat + 2 sat) and available change inputs
           When: Call generateChangeSdk with default fee model
           Then: Allocates 6323 sat input, creates 1608 sat change output, fee 3479 sat

        Reference: wallet-toolbox/src/storage/methods/__test/GenerateChange/generateChangeSdk.test.ts
                   test('0 two outputs')
        """
        # Given
        params = {
            "fixedInputs": [],
            "fixedOutputs": [
                {"satoshis": 1234, "lockingScriptLength": 1739091},
                {"satoshis": 2, "lockingScriptLength": 25},
            ],
            "feeModel": {"model": "sat/kb", "value": 2},
            "changeInitialSatoshis": 1000,
            "changeFirstSatoshis": 285,
            "changeLockingScriptLength": 25,
            "changeUnlockingScriptLength": 107,
        }
        available_change = [
            {"satoshis": 6323, "outputId": 15005},
            {"satoshis": 1004, "outputId": 15011},
            {"satoshis": 1000, "outputId": 15013},
            {"satoshis": 1000, "outputId": 15017},
            {"satoshis": 1000, "outputId": 15023},
            {"satoshis": 1000, "outputId": 15027},
            {"satoshis": 1000, "outputId": 15034},
            {"satoshis": 1575097, "outputId": 15101},
            {"satoshis": 16417, "outputId": 15103},
            {"satoshis": 3377, "outputId": 15104},
            {"satoshis": 10735, "outputId": 15106},
        ]

        # When
        result = generate_change_sdk(params, available_change)

        # Then
        assert result["allocatedFundingInputs"] == [{"satoshis": 6323, "outputId": 15005, "spendable": False}]
        assert result["changeOutputs"] == [{"satoshis": 1608, "lockingScriptLength": 25}]
        assert result["size"] == 1739330
        assert result["fee"] == 3479
        assert result["satsPerKb"] == 2

    def test_two_outputs_exact_input(self) -> None:
        """Given: Transaction with two outputs and exact input amount (4715 sat)
           When: Call generateChangeSdk
           Then: Uses exact input, no change output created

        Reference: wallet-toolbox/src/storage/methods/__test/GenerateChange/generateChangeSdk.test.ts
                   test('0a two outputs exact input')
        """
        # Given
        params = {
            "fixedInputs": [],
            "fixedOutputs": [
                {"satoshis": 1234, "lockingScriptLength": 1739091},
                {"satoshis": 2, "lockingScriptLength": 25},
            ],
            "feeModel": {"model": "sat/kb", "value": 2},
            "changeInitialSatoshis": 1000,
            "changeFirstSatoshis": 285,
            "changeLockingScriptLength": 25,
            "changeUnlockingScriptLength": 107,
        }
        available_change = [
            {"satoshis": 6323, "outputId": 15005},
            {"satoshis": 1004, "outputId": 15011},
            {"satoshis": 1000, "outputId": 15013},
            {"satoshis": 1000, "outputId": 15017},
            {"satoshis": 1000, "outputId": 15023},
            {"satoshis": 4715, "outputId": 15027},  # Exact amount
            {"satoshis": 1000, "outputId": 15034},
            {"satoshis": 1575097, "outputId": 15101},
            {"satoshis": 16417, "outputId": 15103},
            {"satoshis": 3377, "outputId": 15104},
            {"satoshis": 10735, "outputId": 15106},
        ]

        # When
        result = generate_change_sdk(params, available_change)

        # Then
        assert result["allocatedFundingInputs"] == [{"satoshis": 4715, "outputId": 15027, "spendable": False}]
        assert result["changeOutputs"] == []
        assert result["size"] == 1739296
        assert result["fee"] == 3479
        assert result["satsPerKb"] == 2

    def test_two_outputs_666666_200(self) -> None:
        """Given: Transaction with 666666 sat + 200 sat outputs
           When: Call generateChangeSdk with modified available change
           Then: Allocates 1575097 sat input, creates 908230 sat change

        Reference: wallet-toolbox/src/storage/methods/__test/GenerateChange/generateChangeSdk.test.ts
                   test('0b two outputs 666666 200 ')
        """
        # Given
        params = {
            "fixedInputs": [],
            "fixedOutputs": [
                {"satoshis": 666666, "lockingScriptLength": 197},
                {"satoshis": 200, "lockingScriptLength": 25},
            ],
            "feeModel": {"model": "sat/kb", "value": 2},
            "changeInitialSatoshis": 1000,
            "changeFirstSatoshis": 285,
            "changeLockingScriptLength": 25,
            "changeUnlockingScriptLength": 107,
        }
        available_change = [
            {"satoshis": 6323, "outputId": 15005},
            {"satoshis": 1004, "outputId": 15011},
            {"satoshis": 1000, "outputId": 15013},
            {"satoshis": 1000, "outputId": 15017},
            {"satoshis": 1000, "outputId": 15023},
            {"satoshis": 4715, "outputId": 15027},
            {"satoshis": 1000, "outputId": 15034},
            {"satoshis": 1575097, "outputId": 15101},
            {"satoshis": 16417, "outputId": 15103},
            {"satoshis": 3377, "outputId": 15104},
            {"satoshis": 10735, "outputId": 15106},
        ]

        # When
        result = generate_change_sdk(params, available_change)

        # Then
        assert result["allocatedFundingInputs"] == [{"satoshis": 1575097, "outputId": 15101, "spendable": False}]
        assert result["changeOutputs"] == [{"satoshis": 908230, "lockingScriptLength": 25}]
        assert result["size"] == 432
        assert result["fee"] == 1
        assert result["satsPerKb"] == 2

    def test_two_outputs_666666_200_two_change_inputs(self) -> None:
        """Given: Transaction requiring two change inputs to reach target amount
           When: Call generateChangeSdk with limited available inputs
           Then: Allocates two inputs (535280 + 160865 sat), creates 29277 sat change

        Reference: wallet-toolbox/src/storage/methods/__test/GenerateChange/generateChangeSdk.test.ts
                   test('0c two outputs 666666 200 two change inputs ')
        """
        # Given
        params = {
            "fixedInputs": [],
            "fixedOutputs": [
                {"satoshis": 666666, "lockingScriptLength": 197},
                {"satoshis": 200, "lockingScriptLength": 25},
            ],
            "feeModel": {"model": "sat/kb", "value": 2},
            "changeInitialSatoshis": 1000,
            "changeFirstSatoshis": 285,
            "changeLockingScriptLength": 25,
            "changeUnlockingScriptLength": 107,
        }
        available_change = [
            {"satoshis": 191051, "outputId": 14101},
            {"satoshis": 129470, "outputId": 14106},
            {"satoshis": 273356, "outputId": 14110},
            {"satoshis": 65612, "outputId": 14120},
            {"satoshis": 44778, "outputId": 14126},
            {"satoshis": 58732, "outputId": 14141},
            {"satoshis": 160865, "outputId": 14142},
            {"satoshis": 535280, "outputId": 14146},
            {"satoshis": 1006, "outputId": 14177},
            {"satoshis": 1000, "outputId": 14178},
        ]

        # When
        result = generate_change_sdk(params, available_change)

        # Then
        assert result["allocatedFundingInputs"] == [
            {"satoshis": 535280, "outputId": 14146, "spendable": False},
            {"satoshis": 160865, "outputId": 14142, "spendable": False},
        ]
        assert result["changeOutputs"] == [{"satoshis": 29277, "lockingScriptLength": 25}]
        assert result["size"] == 580
        assert result["fee"] == 2
        assert result["satsPerKb"] == 2

    def test_two_outputs_four_change_outputs(self) -> None:
        """Given: Transaction with targetNetCount=4 for privacy
           When: Call generateChangeSdk
           Then: Creates four change outputs plus one extra for net count

        Reference: wallet-toolbox/src/storage/methods/__test/GenerateChange/generateChangeSdk.test.ts
                   test('1 two outputs four change outputs')
        """
        # Given
        params = {
            "fixedInputs": [],
            "fixedOutputs": [
                {"satoshis": 1234, "lockingScriptLength": 1739091},
                {"satoshis": 2, "lockingScriptLength": 25},
            ],
            "feeModel": {"model": "sat/kb", "value": 2},
            "changeInitialSatoshis": 1000,
            "changeFirstSatoshis": 285,
            "changeLockingScriptLength": 25,
            "changeUnlockingScriptLength": 107,
            "targetNetCount": 4,
        }
        available_change = [
            {"satoshis": 6323, "outputId": 15005},
            {"satoshis": 1004, "outputId": 15011},
            {"satoshis": 1000, "outputId": 15013},
            {"satoshis": 1000, "outputId": 15017},
            {"satoshis": 1000, "outputId": 15023},
            {"satoshis": 1000, "outputId": 15027},
            {"satoshis": 1000, "outputId": 15034},
            {"satoshis": 1575097, "outputId": 15101},
            {"satoshis": 16417, "outputId": 15103},
            {"satoshis": 3377, "outputId": 15104},
            {"satoshis": 10735, "outputId": 15106},
        ]

        # When
        result = generate_change_sdk(params, available_change)

        # Then
        assert result["allocatedFundingInputs"] == [{"satoshis": 10735, "outputId": 15106, "spendable": False}]
        assert len(result["changeOutputs"]) == 5  # 4 target + 1 extra
        assert result["changeOutputs"] == [
            {"satoshis": 1237, "lockingScriptLength": 25},
            {"satoshis": 1334, "lockingScriptLength": 25},
            {"satoshis": 1369, "lockingScriptLength": 25},
            {"satoshis": 1008, "lockingScriptLength": 25},
            {"satoshis": 1072, "lockingScriptLength": 25},
        ]
        assert result["size"] == 1739466
        assert result["fee"] == 3479

    def test_werr_insufficient_funds(self) -> None:
        """Given: Transaction with insufficient available funds (limited inputs)
           When: Call generateChangeSdk
           Then: Raises InsufficientFundsError

        Reference: wallet-toolbox/src/storage/methods/__test/GenerateChange/generateChangeSdk.test.ts
                   test('2 WERR_INSUFFICIENT_FUNDS')
        """
        # Given
        params = {
            "fixedInputs": [],
            "fixedOutputs": [
                {"satoshis": 1234, "lockingScriptLength": 1739091},
                {"satoshis": 2, "lockingScriptLength": 25},
            ],
            "feeModel": {"model": "sat/kb", "value": 2},
            "changeInitialSatoshis": 1000,
            "changeFirstSatoshis": 285,
            "changeLockingScriptLength": 25,
            "changeUnlockingScriptLength": 107,
            "targetNetCount": 4,
        }
        # Only 3 small inputs - insufficient
        available_change = [
            {"satoshis": 1004, "outputId": 15011},
            {"satoshis": 1000, "outputId": 15013},
            {"satoshis": 1000, "outputId": 15017},
        ]

        # When/Then
        with pytest.raises(InsufficientFundsError):
            generate_change_sdk(params, available_change)

    def test_werr_insufficient_funds_no_inputs(self) -> None:
        """Given: Transaction with no available inputs
           When: Call generateChangeSdk
           Then: Raises InsufficientFundsError

        Reference: wallet-toolbox/src/storage/methods/__test/GenerateChange/generateChangeSdk.test.ts
                   test('2a WERR_INSUFFICIENT_FUNDS no inputs')
        """
        # Given
        params = {
            "fixedInputs": [],
            "fixedOutputs": [
                {"satoshis": 1234, "lockingScriptLength": 1739091},
                {"satoshis": 2, "lockingScriptLength": 25},
            ],
            "feeModel": {"model": "sat/kb", "value": 2},
            "changeInitialSatoshis": 1000,
            "changeFirstSatoshis": 285,
            "changeLockingScriptLength": 25,
            "changeUnlockingScriptLength": 107,
            "targetNetCount": 4,
        }
        available_change = []  # No inputs

        # When/Then
        with pytest.raises(InsufficientFundsError):
            generate_change_sdk(params, available_change)

    def test_allocate_all(self) -> None:
        """Given: Transaction requiring all available inputs
           When: Call generateChangeSdk with limited inputs
           Then: Allocates all 2 inputs (1004 + 1000 sat), creates 689 sat change

        Reference: wallet-toolbox/src/storage/methods/__test/GenerateChange/generateChangeSdk.test.ts
                   test('3 allocate all')
        """
        # Given
        params = {
            "fixedInputs": [],
            "fixedOutputs": [
                {"satoshis": 1234, "lockingScriptLength": 39091},
                {"satoshis": 2, "lockingScriptLength": 25},
            ],
            "feeModel": {"model": "sat/kb", "value": 2},
            "changeInitialSatoshis": 1000,
            "changeFirstSatoshis": 285,
            "changeLockingScriptLength": 25,
            "changeUnlockingScriptLength": 107,
            "targetNetCount": 4,
        }
        # Only 2 inputs - must use both
        available_change = [{"satoshis": 1004, "outputId": 15011}, {"satoshis": 1000, "outputId": 15017}]

        # When
        result = generate_change_sdk(params, available_change)

        # Then
        assert result["allocatedFundingInputs"] == [
            {"satoshis": 1004, "outputId": 15011, "spendable": False},
            {"satoshis": 1000, "outputId": 15017, "spendable": False},
        ]
        assert result["changeOutputs"] == [{"satoshis": 689, "lockingScriptLength": 25}]
        assert result["size"] == 39476
        assert result["fee"] == 79
        assert result["satsPerKb"] == 2

    def test_feemodel_5_sat_per_kb(self) -> None:
        """Given: Transaction with custom fee model (5 sat/kb instead of 2)
           When: Call generateChangeSdk
           Then: Calculates higher fee (198 sat) based on 5 sat/kb rate

        Reference: wallet-toolbox/src/storage/methods/__test/GenerateChange/generateChangeSdk.test.ts
                   test('4 feeModel 5 sat per kb')
        """
        # Given
        params = {
            "fixedInputs": [],
            "fixedOutputs": [
                {"satoshis": 1234, "lockingScriptLength": 39091},
                {"satoshis": 2, "lockingScriptLength": 25},
            ],
            "feeModel": {"model": "sat/kb", "value": 5},  # Higher fee
            "changeInitialSatoshis": 1000,
            "changeFirstSatoshis": 285,
            "changeLockingScriptLength": 25,
            "changeUnlockingScriptLength": 107,
            "targetNetCount": 4,
        }
        available_change = [{"satoshis": 1004, "outputId": 15011}, {"satoshis": 1000, "outputId": 15017}]

        # When
        result = generate_change_sdk(params, available_change)

        # Then
        assert result["allocatedFundingInputs"] == [
            {"satoshis": 1004, "outputId": 15011, "spendable": False},
            {"satoshis": 1000, "outputId": 15017, "spendable": False},
        ]
        assert result["changeOutputs"] == [{"satoshis": 570, "lockingScriptLength": 25}]
        assert result["size"] == 39476
        assert result["fee"] == 198  # Higher fee
        assert result["satsPerKb"] == 5

    def test_feemodel_1_sat_per_kb(self) -> None:
        """Given: Transaction with custom fee model (1 sat/kb instead of 2)
           When: Call generateChangeSdk
           Then: Calculates lower fee (40 sat) based on 1 sat/kb rate

        Reference: wallet-toolbox/src/storage/methods/__test/GenerateChange/generateChangeSdk.test.ts
                   test('4a feeModel 1 sat per kb')
        """
        # Given
        params = {
            "fixedInputs": [],
            "fixedOutputs": [
                {"satoshis": 1234, "lockingScriptLength": 39091},
                {"satoshis": 2, "lockingScriptLength": 25},
            ],
            "feeModel": {"model": "sat/kb", "value": 1},  # Lower fee
            "changeInitialSatoshis": 1000,
            "changeFirstSatoshis": 285,
            "changeLockingScriptLength": 25,
            "changeUnlockingScriptLength": 107,
            "targetNetCount": 4,
        }
        available_change = [{"satoshis": 1004, "outputId": 15011}, {"satoshis": 1000, "outputId": 15017}]

        # When
        result = generate_change_sdk(params, available_change)

        # Then
        assert result["allocatedFundingInputs"] == [
            {"satoshis": 1004, "outputId": 15011, "spendable": False},
            {"satoshis": 1000, "outputId": 15017, "spendable": False},
        ]
        assert result["changeOutputs"] == [{"satoshis": 728, "lockingScriptLength": 25}]
        assert result["size"] == 39476
        assert result["fee"] == 40  # Lower fee
        assert result["satsPerKb"] == 1

    def test_one_fixed_input(self) -> None:
        """Given: Transaction with one fixed input (1234 sat, 42 bytes) plus change inputs
           When: Call generateChangeSdk
           Then: Includes fixed input in transaction, allocates change input, creates 5 change outputs

        Reference: wallet-toolbox/src/storage/methods/__test/GenerateChange/generateChangeSdk.test.ts
                   test('5 one fixedInput')
        """
        # Given
        params = {
            "fixedInputs": [{"satoshis": 1234, "unlockingScriptLength": 42}],
            "fixedOutputs": [
                {"satoshis": 1234, "lockingScriptLength": 1739091},
                {"satoshis": 2, "lockingScriptLength": 25},
            ],
            "feeModel": {"model": "sat/kb", "value": 2},
            "changeInitialSatoshis": 1000,
            "changeFirstSatoshis": 285,
            "changeLockingScriptLength": 25,
            "changeUnlockingScriptLength": 107,
            "targetNetCount": 4,
        }
        available_change = [
            {"satoshis": 6323, "outputId": 15005},
            {"satoshis": 1004, "outputId": 15011},
            {"satoshis": 1000, "outputId": 15013},
            {"satoshis": 1000, "outputId": 15017},
            {"satoshis": 1000, "outputId": 15023},
            {"satoshis": 1000, "outputId": 15027},
            {"satoshis": 1000, "outputId": 15034},
            {"satoshis": 1575097, "outputId": 15101},
            {"satoshis": 16417, "outputId": 15103},
            {"satoshis": 3377, "outputId": 15104},
            {"satoshis": 10735, "outputId": 15106},
        ]

        # When
        result = generate_change_sdk(params, available_change)

        # Then
        assert result["allocatedFundingInputs"] == [{"satoshis": 10735, "outputId": 15106, "spendable": False}]
        assert len(result["changeOutputs"]) == 5
        assert result["changeOutputs"] == [
            {"satoshis": 1526, "lockingScriptLength": 25},
            {"satoshis": 1738, "lockingScriptLength": 25},
            {"satoshis": 1816, "lockingScriptLength": 25},
            {"satoshis": 1016, "lockingScriptLength": 25},
            {"satoshis": 1157, "lockingScriptLength": 25},
        ]
        assert result["size"] == 1739549
        assert result["fee"] == 3480

    def test_one_larger_fixed_input(self) -> None:
        """Given: Transaction with one larger fixed input (1234 sat, 242 bytes unlocking script)
           When: Call generateChangeSdk
           Then: Accounts for larger input size in transaction size and fee calculation

        Reference: wallet-toolbox/src/storage/methods/__test/GenerateChange/generateChangeSdk.test.ts
                   test('5a one larger fixedInput')
        """
        # Given
        params = {
            "fixedInputs": [{"satoshis": 1234, "unlockingScriptLength": 242}],  # Larger unlocking script
            "fixedOutputs": [
                {"satoshis": 1234, "lockingScriptLength": 1739091},
                {"satoshis": 2, "lockingScriptLength": 25},
            ],
            "feeModel": {"model": "sat/kb", "value": 2},
            "changeInitialSatoshis": 1000,
            "changeFirstSatoshis": 285,
            "changeLockingScriptLength": 25,
            "changeUnlockingScriptLength": 107,
            "targetNetCount": 4,
        }
        available_change = [
            {"satoshis": 6323, "outputId": 15005},
            {"satoshis": 1004, "outputId": 15011},
            {"satoshis": 1000, "outputId": 15013},
            {"satoshis": 1000, "outputId": 15017},
            {"satoshis": 1000, "outputId": 15023},
            {"satoshis": 1000, "outputId": 15027},
            {"satoshis": 1000, "outputId": 15034},
            {"satoshis": 1575097, "outputId": 15101},
            {"satoshis": 16417, "outputId": 15103},
            {"satoshis": 3377, "outputId": 15104},
            {"satoshis": 10735, "outputId": 15106},
        ]

        # When
        result = generate_change_sdk(params, available_change)

        # Then
        assert result["allocatedFundingInputs"] == [{"satoshis": 10735, "outputId": 15106, "spendable": False}]
        assert len(result["changeOutputs"]) == 5
        assert result["size"] == 1739749  # Larger due to bigger input
        assert result["fee"] == 3480

    def test_one_fixed_input_1001_73(self) -> None:
        """Given: Transaction with small fixed input (1001 sat, 73 bytes) and no fixed outputs
           When: Call generateChangeSdk
           Then: Creates 1000 sat change output without additional inputs

        Reference: wallet-toolbox/src/storage/methods/__test/GenerateChange/generateChangeSdk.test.ts
                   test('5b one fixedInput 1001 73')
        """
        # Given
        params = {
            "fixedInputs": [{"satoshis": 1001, "unlockingScriptLength": 73}],
            "fixedOutputs": [],
            "feeModel": {"model": "sat/kb", "value": 2},
            "changeInitialSatoshis": 1000,
            "changeFirstSatoshis": 285,
            "changeLockingScriptLength": 25,
            "changeUnlockingScriptLength": 107,
        }
        available_change = [
            {"satoshis": 6323, "outputId": 15005},
            {"satoshis": 1004, "outputId": 15011},
            {"satoshis": 1000, "outputId": 15013},
            {"satoshis": 1000, "outputId": 15017},
            {"satoshis": 1000, "outputId": 15023},
            {"satoshis": 1000, "outputId": 15027},
            {"satoshis": 1000, "outputId": 15034},
            {"satoshis": 1575097, "outputId": 15101},
            {"satoshis": 16417, "outputId": 15103},
            {"satoshis": 3377, "outputId": 15104},
            {"satoshis": 10735, "outputId": 15106},
        ]

        # When
        result = generate_change_sdk(params, available_change)

        # Then
        assert result["allocatedFundingInputs"] == []  # No additional inputs needed
        assert result["changeOutputs"] == [{"satoshis": 1000, "lockingScriptLength": 25}]
        assert result["size"] == 158
        assert result["fee"] == 1

    def test_no_fixed_outputs_one_fixed_input(self) -> None:
        """Given: Transaction with fixed input but no fixed outputs, targetNetCount=4
           When: Call generateChangeSdk
           Then: Allocates change input and creates 5 change outputs

        Reference: wallet-toolbox/src/storage/methods/__test/GenerateChange/generateChangeSdk.test.ts
                   test('6 no fixedOutputs one fixedInput')
        """
        # Given
        params = {
            "fixedInputs": [{"satoshis": 1234, "unlockingScriptLength": 42}],
            "fixedOutputs": [],
            "feeModel": {"model": "sat/kb", "value": 2},
            "changeInitialSatoshis": 1000,
            "changeFirstSatoshis": 285,
            "changeLockingScriptLength": 25,
            "changeUnlockingScriptLength": 107,
            "targetNetCount": 4,
        }
        available_change = [
            {"satoshis": 6323, "outputId": 15005},
            {"satoshis": 1004, "outputId": 15011},
            {"satoshis": 1000, "outputId": 15013},
            {"satoshis": 1000, "outputId": 15017},
            {"satoshis": 1000, "outputId": 15023},
            {"satoshis": 1000, "outputId": 15027},
            {"satoshis": 1000, "outputId": 15034},
            {"satoshis": 1575097, "outputId": 15101},
            {"satoshis": 16417, "outputId": 15103},
            {"satoshis": 3377, "outputId": 15104},
            {"satoshis": 10735, "outputId": 15106},
        ]

        # When
        result = generate_change_sdk(params, available_change)

        # Then
        assert result["allocatedFundingInputs"] == [{"satoshis": 6323, "outputId": 15005, "spendable": False}]
        assert len(result["changeOutputs"]) == 5
        assert result["changeOutputs"] == [
            {"satoshis": 1597, "lockingScriptLength": 25},
            {"satoshis": 1837, "lockingScriptLength": 25},
            {"satoshis": 1925, "lockingScriptLength": 25},
            {"satoshis": 1019, "lockingScriptLength": 25},
            {"satoshis": 1178, "lockingScriptLength": 25},
        ]
        assert result["size"] == 411
        assert result["fee"] == 1

    def test_no_fixed_outputs_no_fixed_input(self) -> None:
        """Given: Transaction with no fixed inputs or outputs, targetNetCount=4
           When: Call generateChangeSdk
           Then: Allocates change input and creates 5 change outputs for net count

        Reference: wallet-toolbox/src/storage/methods/__test/GenerateChange/generateChangeSdk.test.ts
                   test('6a no fixedOutputs no fixedInput')
        """
        # Given
        params = {
            "fixedInputs": [],
            "fixedOutputs": [],
            "feeModel": {"model": "sat/kb", "value": 2},
            "changeInitialSatoshis": 1000,
            "changeFirstSatoshis": 285,
            "changeLockingScriptLength": 25,
            "changeUnlockingScriptLength": 107,
            "targetNetCount": 4,
        }
        available_change = [
            {"satoshis": 6323, "outputId": 15005},
            {"satoshis": 1004, "outputId": 15011},
            {"satoshis": 1000, "outputId": 15013},
            {"satoshis": 1000, "outputId": 15017},
            {"satoshis": 1000, "outputId": 15023},
            {"satoshis": 1000, "outputId": 15027},
            {"satoshis": 1000, "outputId": 15034},
            {"satoshis": 1575097, "outputId": 15101},
            {"satoshis": 16417, "outputId": 15103},
            {"satoshis": 3377, "outputId": 15104},
            {"satoshis": 10735, "outputId": 15106},
        ]

        # When
        result = generate_change_sdk(params, available_change)

        # Then
        assert result["allocatedFundingInputs"] == [{"satoshis": 6323, "outputId": 15005, "spendable": False}]
        assert len(result["changeOutputs"]) == 5
        assert result["changeOutputs"] == [
            {"satoshis": 1309, "lockingScriptLength": 25},
            {"satoshis": 1433, "lockingScriptLength": 25},
            {"satoshis": 1478, "lockingScriptLength": 25},
            {"satoshis": 1009, "lockingScriptLength": 25},
            {"satoshis": 1093, "lockingScriptLength": 25},
        ]
        assert result["size"] == 328
        assert result["fee"] == 1

    def test_params_text4_d4(self) -> None:
        """Given: Complex test case with 309000 + 2 sat outputs and specific available inputs
           When: Call generateChangeSdk
           Then: Selects optimal input (474866 sat), creates 165863 sat change

        Reference: wallet-toolbox/src/storage/methods/__test/GenerateChange/generateChangeSdk.test.ts
                   test('7 paramsText4 d4')
        """
        # Given
        params = {
            "fixedInputs": [],
            "fixedOutputs": [
                {"satoshis": 309000, "lockingScriptLength": 198},
                {"satoshis": 2, "lockingScriptLength": 25},
            ],
            "feeModel": {"model": "sat/kb", "value": 2},
            "changeInitialSatoshis": 1000,
            "changeFirstSatoshis": 285,
            "changeLockingScriptLength": 25,
            "changeUnlockingScriptLength": 107,
        }
        available_change = [
            {"satoshis": 7130, "outputId": 15142},
            {"satoshis": 474866, "outputId": 15332},
            {"satoshis": 16411, "outputId": 15355},
            {"satoshis": 763632, "outputId": 15368},
            {"satoshis": 18894, "outputId": 15371},
            {"satoshis": 1574590, "outputId": 15420},
            {"satoshis": 43207, "outputId": 15480},
            {"satoshis": 12342, "outputId": 15541},
            {"satoshis": 123453, "outputId": 15548},
            {"satoshis": 7890, "outputId": 16020},
            {"satoshis": 1073, "outputId": 16026},
        ]

        # When
        result = generate_change_sdk(params, available_change)

        # Then
        assert result["allocatedFundingInputs"] == [{"satoshis": 474866, "outputId": 15332, "spendable": False}]
        assert result["changeOutputs"] == [{"satoshis": 165863, "lockingScriptLength": 25}]
        assert result["size"] == 433
        assert result["fee"] == 1

    def test_params_text_d5_through_d14(self) -> None:
        """Given: Complex test cases with various parameters (d5-d14)
           When: Call generateChangeSdk for each case
           Then: Each case returns expected allocation and change

        Reference: wallet-toolbox/src/storage/methods/__test/GenerateChange/generateChangeSdk.test.ts
                   test('8 paramsText d5 d6 d7 d8 d9 d10 d11 d12 d13 d14')
        """
        # Given
        test_cases = [
            {
                "n": 5,
                "params": {
                    "fixedInputs": [{"satoshis": 1000, "unlockingScriptLength": 72}],
                    "fixedOutputs": [{"satoshis": 200, "lockingScriptLength": 25}],
                    "feeModel": {"model": "sat/kb", "value": 2},
                    "changeInitialSatoshis": 1000,
                    "changeFirstSatoshis": 285,
                    "changeLockingScriptLength": 25,
                    "changeUnlockingScriptLength": 107,
                },
                "availableChange": [
                    {"satoshis": 191051, "outputId": 14101},
                    # ... many more inputs (d5 has 79 inputs total)
                ],
                "expected": {
                    "allocatedFundingInputs": [],
                    "changeOutputs": [{"satoshis": 799, "lockingScriptLength": 25}],
                    "size": 191,
                    "fee": 1,
                    "satsPerKb": 2,
                },
            },
            # Test cases d6 through d14 with various parameters
            # Each testing different edge cases of change allocation algorithm
        ]

        # When/Then
        for test_case in test_cases:
            result = generate_change_sdk(test_case["params"], test_case["availableChange"])

            assert result["allocatedFundingInputs"] == test_case["expected"]["allocatedFundingInputs"]
            assert result["changeOutputs"] == test_case["expected"]["changeOutputs"]
            assert result["size"] == test_case["expected"]["size"]
            assert result["fee"] == test_case["expected"]["fee"]
            assert result["satsPerKb"] == test_case["expected"]["satsPerKb"]
