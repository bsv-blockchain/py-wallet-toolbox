"""Tests for validate_abort_action_args utility function.

Reference: go-wallet-toolbox/pkg/internal/validate/validate_abort_action_args_test.go
"""

import pytest

from bsv_wallet_toolbox.errors import InvalidParameterError
from bsv_wallet_toolbox.utils.validation import validate_abort_action_args


class TestValidateAbortActionArgs:
    """Test suite for validate_abort_action_args function.

    This validates AbortActionArgs according to BRC-100 specifications.
    AbortActionArgs must include:
    - reference: non-empty string, valid base64 format (length divisible by 4)
    """

    def test_validate_abort_action_args_valid(self) -> None:
        """Given: Valid AbortActionArgs
           When: Call validate_abort_action_args
           Then: No exception raised

        Reference: go-wallet-toolbox/pkg/internal/validate/validate_abort_action_args_test.go
                   TestValidAbortActionArgs - ValidArgs
        """
        # Given
        valid_args = {"reference": "ybQus1rq4M4gi/7L"}  # Valid base64 string (length 16, divisible by 4)

        # When / Then
        validate_abort_action_args(valid_args)  # Should not raise

    def test_validate_abort_action_args_nil_args(self) -> None:
        """Given: None as arguments
           When: Call validate_abort_action_args
           Then: Raises InvalidParameterError

        Reference: go-wallet-toolbox/pkg/internal/validate/validate_abort_action_args_test.go
                   TestValidAbortActionArgs - NilArgs
        """
        # Given / When / Then
        with pytest.raises(InvalidParameterError) as exc_info:
            validate_abort_action_args(None)
        assert "args" in str(exc_info.value).lower() or "required" in str(exc_info.value).lower()

    def test_validate_abort_action_args_blank_reference(self) -> None:
        """Given: AbortActionArgs with blank reference
           When: Call validate_abort_action_args
           Then: Raises InvalidParameterError

        Reference: go-wallet-toolbox/pkg/internal/validate/validate_abort_action_args_test.go
                   TestValidAbortActionArgs - BlankReference
        """
        # Given
        invalid_args = {"reference": ""}  # Empty reference

        # When / Then
        with pytest.raises(InvalidParameterError) as exc_info:
            validate_abort_action_args(invalid_args)
        assert "reference" in str(exc_info.value).lower()

    def test_validate_abort_action_args_invalid_base64(self) -> None:
        """Given: AbortActionArgs with invalid base64 reference (length not divisible by 4)
           When: Call validate_abort_action_args
           Then: Raises InvalidParameterError

        Reference: go-wallet-toolbox/pkg/internal/validate/validate_abort_action_args_test.go
                   TestValidAbortActionArgs - Base64StringNotDivisibleBy4
        """
        # Given
        invalid_args = {"reference": "ybQus1rq4M4gi/7LT"}  # Length 17 (not divisible by 4)

        # When / Then
        with pytest.raises(InvalidParameterError) as exc_info:
            validate_abort_action_args(invalid_args)
        assert "reference" in str(exc_info.value).lower() or "base64" in str(exc_info.value).lower()
