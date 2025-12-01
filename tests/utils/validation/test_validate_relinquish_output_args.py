"""Tests for validate_relinquish_output_args utility function.

Reference: go-wallet-toolbox/pkg/internal/validate/validate_relinquish_output_args_test.go
"""

import pytest

from bsv_wallet_toolbox.errors import InvalidParameterError
from bsv_wallet_toolbox.utils.validation import validate_relinquish_output_args


class TestValidateRelinquishOutputArgs:
    """Test suite for validate_relinquish_output_args function.

    This validates RelinquishOutputArgs according to BRC-100 specifications.
    RelinquishOutputArgs must include:
    - output: valid outpoint string in format "txid.index"
    - basket: string (can be empty or up to 300 characters)
    """

    def test_validate_relinquish_output_args_valid(self) -> None:
        """Given: Valid RelinquishOutputArgs
           When: Call validate_relinquish_output_args
           Then: No exception raised

        Reference: go-wallet-toolbox/pkg/internal/validate/validate_relinquish_output_args_test.go
                   TestValidRelinquishOutputArgs_Success - valid args
        """
        # Given

        valid_args = {
            "output": "deadbeefcafebabe" + "0" * 48 + ".0",  # Valid outpoint (64-char hex txid + .index)
            "basket": "validbasket",
        }

        # When / Then
        validate_relinquish_output_args(valid_args)  # Should not raise

    def test_validate_relinquish_output_args_basket_min_length(self) -> None:
        """Given: Valid RelinquishOutputArgs with basket at minimum length (1 char)
           When: Call validate_relinquish_output_args
           Then: No exception raised

        Reference: go-wallet-toolbox/pkg/internal/validate/validate_relinquish_output_args_test.go
                   TestValidRelinquishOutputArgs_Success - valid: basket at min length
        """
        # Given

        valid_args = {"output": "deadbeefcafebabe" + "0" * 48 + ".0", "basket": "a"}  # Min length (1 char)

        # When / Then
        validate_relinquish_output_args(valid_args)  # Should not raise

    def test_validate_relinquish_output_args_basket_max_length(self) -> None:
        """Given: Valid RelinquishOutputArgs with basket at maximum length (300 chars)
           When: Call validate_relinquish_output_args
           Then: No exception raised

        Reference: go-wallet-toolbox/pkg/internal/validate/validate_relinquish_output_args_test.go
                   TestValidRelinquishOutputArgs_Success - valid: basket at max length
        """
        # Given

        valid_args = {"output": "deadbeefcafebabe" + "0" * 48 + ".0", "basket": "a" * 300}  # Max length (300 chars)

        # When / Then
        validate_relinquish_output_args(valid_args)  # Should not raise

    def test_validate_relinquish_output_args_empty_basket(self) -> None:
        """Given: Valid RelinquishOutputArgs with empty basket
           When: Call validate_relinquish_output_args
           Then: No exception raised

        Reference: go-wallet-toolbox/pkg/internal/validate/validate_relinquish_output_args_test.go
                   TestValidRelinquishOutputArgs_Success - valid: empty basket
        """
        # Given

        valid_args = {"output": "deadbeefcafebabe" + "0" * 48 + ".0", "basket": ""}  # Empty basket is allowed

        # When / Then
        validate_relinquish_output_args(valid_args)  # Should not raise

    def test_validate_relinquish_output_args_missing_dot(self) -> None:
        """Given: RelinquishOutputArgs with outpoint missing dot separator
           When: Call validate_relinquish_output_args
           Then: Raises InvalidParameterError

        Reference: go-wallet-toolbox/pkg/internal/validate/validate_relinquish_output_args_test.go
                   TestValidRelinquishOutputArgs_Error_InvalidOutpoint - missing dot
        """
        # Given

        invalid_args = {"output": "deadbeefcafebabe0", "basket": "validbasket"}  # Missing dot separator

        # When / Then
        with pytest.raises((InvalidParameterError, ValueError)) as exc_info:
            validate_relinquish_output_args(invalid_args)
        assert "outpoint" in str(exc_info.value).lower() or "output" in str(exc_info.value).lower()

    def test_validate_relinquish_output_args_index_not_numeric(self) -> None:
        """Given: RelinquishOutputArgs with non-numeric outpoint index
           When: Call validate_relinquish_output_args
           Then: Raises InvalidParameterError

        Reference: go-wallet-toolbox/pkg/internal/validate/validate_relinquish_output_args_test.go
                   TestValidRelinquishOutputArgs_Error_InvalidOutpoint - index not numeric
        """
        # Given

        invalid_args = {"output": "deadbeefcafebabe.notanumber", "basket": "validbasket"}  # Index not numeric

        # When / Then
        with pytest.raises((InvalidParameterError, ValueError)) as exc_info:
            validate_relinquish_output_args(invalid_args)
        assert "outpoint" in str(exc_info.value).lower() or "index" in str(exc_info.value).lower()

    def test_validate_relinquish_output_args_empty_output(self) -> None:
        """Given: RelinquishOutputArgs with empty output
           When: Call validate_relinquish_output_args
           Then: Raises InvalidParameterError

        Reference: go-wallet-toolbox/pkg/internal/validate/validate_relinquish_output_args_test.go
                   TestValidRelinquishOutputArgs_Error_InvalidOutpoint - empty output
        """
        # Given

        invalid_args = {"output": "", "basket": "validbasket"}  # Empty output

        # When / Then
        with pytest.raises((InvalidParameterError, ValueError)) as exc_info:
            validate_relinquish_output_args(invalid_args)
        assert "output" in str(exc_info.value).lower() or "required" in str(exc_info.value).lower()

    def test_validate_relinquish_output_args_basket_too_long(self) -> None:
        """Given: RelinquishOutputArgs with basket exceeding 300 characters
           When: Call validate_relinquish_output_args
           Then: Raises InvalidParameterError

        Reference: go-wallet-toolbox/pkg/internal/validate/validate_relinquish_output_args_test.go
                   TestValidRelinquishOutputArgs_Error_InvalidBasket
        """
        # Given

        invalid_args = {
            "output": "deadbeefcafebabe" + "0" * 48 + ".0",
            "basket": "a" * 301,  # 301 chars (exceeds 300 limit)
        }

        # When / Then
        with pytest.raises((InvalidParameterError, ValueError)) as exc_info:
            validate_relinquish_output_args(invalid_args)
        assert "basket" in str(exc_info.value).lower()
