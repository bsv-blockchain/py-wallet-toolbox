"""Tests for validate_originator utility function.

Reference: go-wallet-toolbox/pkg/internal/validate/validate_originator_test.go
"""

import pytest

from bsv_wallet_toolbox.errors import InvalidParameterError
from bsv_wallet_toolbox.utils.validation import validate_originator


class TestValidateOriginator:
    """Test suite for validate_originator function.

    This validates the originator parameter according to BRC-100 specifications.
    Originator must be:
    - A string
    - At most 250 bytes in length
    - Can be None (optional parameter)
    """

    def test_validate_originator_valid(self) -> None:
        """Given: Valid originator values
           When: Call validate_originator
           Then: No exception raised

        Reference: go-wallet-toolbox/pkg/internal/validate/validate_originator_test.go
                   TestValidateOriginator
        """
        # Given

        valid_cases = [
            None,  # Optional parameter
            "example.com",  # Valid domain
            "subdomain.example.com",  # Valid subdomain
            "app.example.co.uk",  # Valid multi-level domain
            "a" * 250,  # Max length (250 bytes)
            "localhost",  # Valid single word
            "192.168.1.1",  # IP address
        ]

        # When / Then
        for originator in valid_cases:
            validate_originator(originator)  # Should not raise

    def test_validate_originator_invalid_type(self) -> None:
        """Given: Originator with invalid type
           When: Call validate_originator
           Then: Raises InvalidParameterError

        Reference: go-wallet-toolbox/pkg/internal/validate/validate_originator_test.go
                   TestValidateOriginator
        """
        # Given

        invalid_cases = [
            123,  # Integer
            12.34,  # Float
            True,  # Boolean
            [],  # List
            {},  # Dict
        ]

        # When / Then
        for originator in invalid_cases:
            with pytest.raises(InvalidParameterError) as exc_info:
                validate_originator(originator)
            assert "originator" in str(exc_info.value).lower()

    def test_validate_originator_too_long(self) -> None:
        """Given: Originator exceeding 250 bytes
           When: Call validate_originator
           Then: Raises InvalidParameterError

        Reference: go-wallet-toolbox/pkg/internal/validate/validate_originator_test.go
                   TestValidateOriginator
        """
        # Given

        too_long_originator = "a" * 251  # 251 bytes (exceeds limit)

        # When / Then
        with pytest.raises(InvalidParameterError) as exc_info:
            validate_originator(too_long_originator)
        assert "originator" in str(exc_info.value).lower()
        assert "250" in str(exc_info.value)
