"""Tests for validate_create_action_args utility function.

References:
- wallet-toolbox/test/wallet/action/createAction.test.ts
- go-wallet-toolbox/pkg/internal/validate/validate_create_action_args_test.go
"""

import pytest

from bsv_wallet_toolbox.errors import InvalidParameterError
from bsv_wallet_toolbox.utils.validation import validate_create_action_args


class TestValidateCreateActionArgs:
    """Test suite for validate_create_action_args function.

    This validates CreateActionArgs according to BRC-100 specifications.
    CreateActionArgs must include:
    - description: non-empty string (at least 1 character)
    - outputs: list of output objects with valid satoshis and lockingScript
    - lockingScript: hexadecimal string with even length
    """

    def test_validate_create_action_args_valid(self) -> None:
        """Given: Valid CreateActionArgs
           When: Call validate_create_action_args
           Then: No exception raised

        Reference: wallet-toolbox/test/wallet/action/createAction.test.ts
                   test('1_repeatable txid')
        """
        # Given

        valid_args = {
            "description": "Test transaction",
            "outputs": [
                {
                    "satoshis": 1000,
                    "lockingScript": "76a914" + "00" * 20 + "88ac",  # Valid P2PKH hex
                    "outputDescription": "Payment to Alice",
                }
            ],
        }

        # When / Then
        validate_create_action_args(valid_args)  # Should not raise

    def test_validate_create_action_args_empty_description(self) -> None:
        """Given: CreateActionArgs with empty description
           When: Call validate_create_action_args
           Then: Raises InvalidParameterError

        Reference: wallet-toolbox/test/wallet/action/createAction.test.ts
                   test('0_invalid_params') - description is too short
        """
        # Given

        invalid_args = {
            "description": "",  # Empty description
            "outputs": [{"satoshis": 42, "lockingScript": "76a914" + "00" * 20 + "88ac"}],
        }

        # When / Then
        with pytest.raises(InvalidParameterError) as exc_info:
            validate_create_action_args(invalid_args)
        assert "description" in str(exc_info.value).lower()

    def test_validate_create_action_args_invalid_locking_script_not_hex(self) -> None:
        """Given: CreateActionArgs with non-hexadecimal lockingScript
           When: Call validate_create_action_args
           Then: Raises InvalidParameterError

        Reference: wallet-toolbox/test/wallet/action/createAction.test.ts
                   test('0_invalid_params') - lockingScript must be hexadecimal
        """
        # Given

        invalid_args = {
            "description": "12345",
            "outputs": [{"satoshis": 42, "lockingScript": "fred", "outputDescription": "pay fred"}],  # Not hex
        }

        # When / Then
        with pytest.raises(InvalidParameterError) as exc_info:
            validate_create_action_args(invalid_args)
        assert "lockingscript" in str(exc_info.value).lower() or "hex" in str(exc_info.value).lower()

    def test_validate_create_action_args_invalid_locking_script_odd_length(self) -> None:
        """Given: CreateActionArgs with odd-length lockingScript
           When: Call validate_create_action_args
           Then: Raises InvalidParameterError

        Reference: wallet-toolbox/test/wallet/action/createAction.test.ts
                   test('0_invalid_params') - lockingScript must be even length
        """
        # Given

        invalid_args = {
            "description": "12345",
            "outputs": [
                {"satoshis": 42, "lockingScript": "abc", "outputDescription": "pay fred"}  # Odd length (3 chars)
            ],
        }

        # When / Then
        with pytest.raises(InvalidParameterError) as exc_info:
            validate_create_action_args(invalid_args)
        assert "lockingscript" in str(exc_info.value).lower() or "even" in str(exc_info.value).lower()
