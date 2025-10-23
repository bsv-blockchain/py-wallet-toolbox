"""Tests for validate_basket_config utility function.

Reference: go-wallet-toolbox/pkg/internal/validate/validate_basket_config_test.go
"""

import pytest

from bsv_wallet_toolbox.errors import InvalidParameterError
from bsv_wallet_toolbox.utils.validation import validate_basket_config


class TestValidateBasketConfig:
    """Test suite for validate_basket_config function.

    This validates BasketConfiguration according to BRC-100 specifications.
    BasketConfiguration must include:
    - name: non-empty string, at least 1 character and at most 300 characters
    """

    def test_validate_basket_config_valid_name(self) -> None:
        """Given: Valid BasketConfiguration with valid name
           When: Call validate_basket_config
           Then: No exception raised

        Reference: go-wallet-toolbox/pkg/internal/validate/validate_basket_config_test.go
                   TestValidBasketConfiguration_Success - valid name
        """
        # Given

        valid_config = {"name": "ValidName"}

        # When / Then
        validate_basket_config(valid_config)  # Should not raise

    def test_validate_basket_config_exact_300_bytes(self) -> None:
        """Given: Valid BasketConfiguration with name exactly 300 bytes
           When: Call validate_basket_config
           Then: No exception raised

        Reference: go-wallet-toolbox/pkg/internal/validate/validate_basket_config_test.go
                   TestValidBasketConfiguration_Success - exact 300 bytes
        """
        # Given

        valid_config = {"name": "a" * 300}  # Exactly 300 bytes

        # When / Then
        validate_basket_config(valid_config)  # Should not raise

    def test_validate_basket_config_empty_name(self) -> None:
        """Given: BasketConfiguration with empty name
           When: Call validate_basket_config
           Then: Raises InvalidParameterError with message about minimum length

        Reference: go-wallet-toolbox/pkg/internal/validate/validate_basket_config_test.go
                   TestValidBasketConfiguration_Error - empty name
        """
        # Given

        invalid_config = {"name": ""}  # Empty name

        # When / Then
        with pytest.raises(InvalidParameterError) as exc_info:
            validate_basket_config(invalid_config)
        assert "name" in str(exc_info.value).lower()
        assert "at least 1" in str(exc_info.value).lower() or "length" in str(exc_info.value).lower()

    def test_validate_basket_config_name_too_long(self) -> None:
        """Given: BasketConfiguration with name exceeding 300 bytes
           When: Call validate_basket_config
           Then: Raises InvalidParameterError with message about maximum length

        Reference: go-wallet-toolbox/pkg/internal/validate/validate_basket_config_test.go
                   TestValidBasketConfiguration_Error - name too long
        """
        # Given

        invalid_config = {"name": "a" * 301}  # 301 bytes (exceeds 300 limit)

        # When / Then
        with pytest.raises(InvalidParameterError) as exc_info:
            validate_basket_config(invalid_config)
        assert "name" in str(exc_info.value).lower()
        assert "no more than 300" in str(exc_info.value).lower() or "300" in str(exc_info.value)
