"""Tests for validate_process_action_args utility function.

Reference: go-wallet-toolbox/pkg/internal/validate/validate_process_action_args_test.go
"""

import pytest

from bsv_wallet_toolbox.errors import InvalidParameterError
from bsv_wallet_toolbox.utils.validation import validate_process_action_args


class TestValidateProcessActionArgs:
    """Test suite for validate_process_action_args function.

    This validates ProcessActionArgs according to BRC-100 specifications.
    ProcessActionArgs must include:
    - txid: valid hexadecimal transaction ID (if provided)
    - reference: required if isNewTx is True
    - rawTx: required if isNewTx is True
    - sendWith: required if isSendWith is True
    """

    def test_validate_process_action_args_valid(self) -> None:
        """Given: Valid ProcessActionArgs
           When: Call validate_process_action_args
           Then: No exception raised

        Reference: go-wallet-toolbox/pkg/internal/validate/validate_process_action_args_test.go
                   TestForDefaultProcessActionArgs
        """
        # Given

        valid_args = {"txid": "a" * 64, "isNewTx": False, "isSendWith": False}  # Valid 64-character hex txid

        # When / Then
        validate_process_action_args(valid_args)  # Should not raise

    def test_validate_process_action_args_invalid_txid(self) -> None:
        """Given: ProcessActionArgs with invalid txid
           When: Call validate_process_action_args
           Then: Raises InvalidParameterError

        Reference: go-wallet-toolbox/pkg/internal/validate/validate_process_action_args_test.go
                   TestWrongProcessActionArgs - TxID invalid
        """
        # Given

        invalid_args = {"txid": "invalid", "isNewTx": False}  # Not a valid hex txid

        # When / Then
        with pytest.raises(InvalidParameterError) as exc_info:
            validate_process_action_args(invalid_args)
        assert "txid" in str(exc_info.value).lower()

    def test_validate_process_action_args_new_tx_missing_reference(self) -> None:
        """Given: ProcessActionArgs with isNewTx=True but missing reference
           When: Call validate_process_action_args
           Then: Raises InvalidParameterError

        Reference: go-wallet-toolbox/pkg/internal/validate/validate_process_action_args_test.go
                   TestWrongProcessActionArgs - NewTx missing reference
        """
        # Given

        invalid_args = {
            "isNewTx": True,
            "reference": None,  # Missing reference
            "rawTx": b"\x01\x00\x00\x00",
            "txid": "a" * 64,
        }

        # When / Then
        with pytest.raises(InvalidParameterError) as exc_info:
            validate_process_action_args(invalid_args)
        assert "reference" in str(exc_info.value).lower()

    def test_validate_process_action_args_new_tx_missing_raw_tx(self) -> None:
        """Given: ProcessActionArgs with isNewTx=True but missing rawTx
           When: Call validate_process_action_args
           Then: Raises InvalidParameterError

        Reference: go-wallet-toolbox/pkg/internal/validate/validate_process_action_args_test.go
                   TestWrongProcessActionArgs - NewTx missing rawTx
        """
        # Given

        invalid_args = {"isNewTx": True, "reference": "ref123", "rawTx": None, "txid": "a" * 64}  # Missing rawTx

        # When / Then
        with pytest.raises(InvalidParameterError) as exc_info:
            validate_process_action_args(invalid_args)
        assert "rawtx" in str(exc_info.value).lower() or "raw" in str(exc_info.value).lower()

    def test_validate_process_action_args_new_tx_missing_txid(self) -> None:
        """Given: ProcessActionArgs with isNewTx=True but missing txid
           When: Call validate_process_action_args
           Then: Raises InvalidParameterError

        Reference: go-wallet-toolbox/pkg/internal/validate/validate_process_action_args_test.go
                   TestWrongProcessActionArgs - NewTx missing txID
        """
        # Given

        invalid_args = {
            "isNewTx": True,
            "reference": "ref123",
            "rawTx": b"\x01\x00\x00\x00",
            "txid": None,  # Missing txid
        }

        # When / Then
        with pytest.raises(InvalidParameterError) as exc_info:
            validate_process_action_args(invalid_args)
        assert "txid" in str(exc_info.value).lower()

    def test_validate_process_action_args_send_with_missing_arguments(self) -> None:
        """Given: ProcessActionArgs with isSendWith=True but missing sendWith
           When: Call validate_process_action_args
           Then: Raises InvalidParameterError

        Reference: go-wallet-toolbox/pkg/internal/validate/validate_process_action_args_test.go
                   TestWrongProcessActionArgs - IsSendWith true but no sendWith arguments
        """
        # Given

        invalid_args = {"isSendWith": True, "sendWith": None}  # Missing sendWith

        # When / Then
        with pytest.raises(InvalidParameterError) as exc_info:
            validate_process_action_args(invalid_args)
        assert "sendwith" in str(exc_info.value).lower()
