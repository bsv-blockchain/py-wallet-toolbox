"""Tests for validate_internalize_action_args utility function.

Reference: go-wallet-toolbox/pkg/internal/validate/validate_internize_action_args_test.go
"""

import pytest

from bsv_wallet_toolbox.errors import InvalidParameterError
from bsv_wallet_toolbox.utils.validation import validate_internalize_action_args


class TestValidateInternalizeActionArgs:
    """Test suite for validate_internalize_action_args function.

    This validates InternalizeActionArgs according to BRC-100 specifications.
    InternalizeActionArgs must include:
    - tx: non-empty byte array (raw transaction)
    - outputs: non-empty list of InternalizeOutput objects
    - description: string at least 3 characters
    - labels: list of strings (each under 300 characters)
    - each output must have a protocol and appropriate remittance data
    """

    def test_validate_internalize_action_args_valid(self) -> None:
        """Given: Valid InternalizeActionArgs
           When: Call validate_internalize_action_args
           Then: No exception raised

        Reference: go-wallet-toolbox/pkg/internal/validate/validate_internize_action_args_test.go
                   TestForDefaultValidCreateActionArgs
        """
        # Given

        valid_args = {
            "tx": b"\x01\x00\x00\x00",  # Non-empty tx bytes
            "outputs": [
                {
                    "outputIndex": 0,
                    "protocol": "wallet payment",
                    "paymentRemittance": {"derivationPrefix": "AAAA", "derivationSuffix": "BBBB"},  # Valid base64
                }
            ],
            "description": "Internalize test transaction",
            "labels": ["label1", "label2"],
        }

        # When / Then
        validate_internalize_action_args(valid_args)  # Should not raise

    def test_validate_internalize_action_args_empty_tx(self) -> None:
        """Given: InternalizeActionArgs with empty tx
           When: Call validate_internalize_action_args
           Then: Raises InvalidParameterError

        Reference: go-wallet-toolbox/pkg/internal/validate/validate_internize_action_args_test.go
                   TestWrongInternalizeActionArgs - Tx empty
        """
        # Given

        invalid_args = {
            "tx": b"",  # Empty tx
            "outputs": [{"outputIndex": 0, "protocol": "wallet payment"}],
            "description": "Test",
        }

        # When / Then
        with pytest.raises(InvalidParameterError) as exc_info:
            validate_internalize_action_args(invalid_args)
        assert "tx" in str(exc_info.value).lower()

    def test_validate_internalize_action_args_empty_outputs(self) -> None:
        """Given: InternalizeActionArgs with empty outputs
           When: Call validate_internalize_action_args
           Then: Raises InvalidParameterError

        Reference: go-wallet-toolbox/pkg/internal/validate/validate_internize_action_args_test.go
                   TestWrongInternalizeActionArgs - Outputs empty
        """
        # Given

        invalid_args = {"tx": b"\x01\x00\x00\x00", "outputs": [], "description": "Test"}  # Empty outputs

        # When / Then
        with pytest.raises(InvalidParameterError) as exc_info:
            validate_internalize_action_args(invalid_args)
        assert "output" in str(exc_info.value).lower()

    def test_validate_internalize_action_args_description_too_short(self) -> None:
        """Given: InternalizeActionArgs with description too short
           When: Call validate_internalize_action_args
           Then: Raises InvalidParameterError

        Reference: go-wallet-toolbox/pkg/internal/validate/validate_internize_action_args_test.go
                   TestWrongInternalizeActionArgs - Description too short
        """
        # Given

        invalid_args = {
            "tx": b"\x01\x00\x00\x00",
            "outputs": [{"outputIndex": 0, "protocol": "wallet payment"}],
            "description": "sh",  # Too short (less than 3 characters)
        }

        # When / Then
        with pytest.raises(InvalidParameterError) as exc_info:
            validate_internalize_action_args(invalid_args)
        assert "description" in str(exc_info.value).lower()

    def test_validate_internalize_action_args_label_too_long(self) -> None:
        """Given: InternalizeActionArgs with label exceeding 300 characters
           When: Call validate_internalize_action_args
           Then: Raises InvalidParameterError

        Reference: go-wallet-toolbox/pkg/internal/validate/validate_internize_action_args_test.go
                   TestWrongInternalizeActionArgs - Label too long
        """
        # Given

        invalid_args = {
            "tx": b"\x01\x00\x00\x00",
            "outputs": [{"outputIndex": 0, "protocol": "wallet payment"}],
            "description": "Valid description",
            "labels": ["a" * 301],  # 301 characters (exceeds 300 limit)
        }

        # When / Then
        with pytest.raises(InvalidParameterError) as exc_info:
            validate_internalize_action_args(invalid_args)
        assert "label" in str(exc_info.value).lower()

    def test_validate_internalize_action_args_output_empty_protocol(self) -> None:
        """Given: InternalizeActionArgs with output having empty protocol
           When: Call validate_internalize_action_args
           Then: Raises InvalidParameterError

        Reference: go-wallet-toolbox/pkg/internal/validate/validate_internize_action_args_test.go
                   TestWrongInternalizeActionArgs - Output empty protocol
        """
        # Given

        invalid_args = {
            "tx": b"\x01\x00\x00\x00",
            "outputs": [{"outputIndex": 0, "protocol": ""}],  # Empty protocol
            "description": "Valid description",
        }

        # When / Then
        with pytest.raises(InvalidParameterError) as exc_info:
            validate_internalize_action_args(invalid_args)
        assert "protocol" in str(exc_info.value).lower()

    def test_validate_internalize_action_args_wallet_payment_missing_remittance(self) -> None:
        """Given: InternalizeActionArgs with wallet payment protocol but missing paymentRemittance
           When: Call validate_internalize_action_args
           Then: Raises InvalidParameterError

        Reference: go-wallet-toolbox/pkg/internal/validate/validate_internize_action_args_test.go
                   TestWrongInternalizeActionArgs - Output WalletPayment missing PaymentRemittance
        """
        # Given

        invalid_args = {
            "tx": b"\x01\x00\x00\x00",
            "outputs": [
                {"outputIndex": 0, "protocol": "wallet payment", "paymentRemittance": None}  # Missing remittance
            ],
            "description": "Valid description",
        }

        # When / Then
        with pytest.raises(InvalidParameterError) as exc_info:
            validate_internalize_action_args(invalid_args)
        assert "remittance" in str(exc_info.value).lower() or "payment" in str(exc_info.value).lower()
