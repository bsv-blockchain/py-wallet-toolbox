"""Tests for validate_relinquish_certificate_args utility function.

Reference: go-wallet-toolbox/pkg/internal/validate/validate_relinquish_certificate_args_test.go
"""

import pytest

from bsv_wallet_toolbox.errors import InvalidParameterError
from bsv_wallet_toolbox.utils.validation import validate_relinquish_certificate_args


class TestValidateRelinquishCertificateArgs:
    """Test suite for validate_relinquish_certificate_args function.

    This validates RelinquishCertificateArgs according to BRC-100 specifications.
    RelinquishCertificateArgs must include:
    - type: valid base64 string
    - serialNumber: valid base64 string
    - certifier: non-empty hexadecimal string with even length
    """

    def test_validate_relinquish_certificate_args_valid(self) -> None:
        """Given: Valid RelinquishCertificateArgs
           When: Call validate_relinquish_certificate_args
           Then: No exception raised

        Reference: go-wallet-toolbox/pkg/internal/validate/validate_relinquish_certificate_args_test.go
                   TestForDefaultValidRelinquishCertificateArgs
        """
        # Given

        valid_args = {
            "type": "dGVzdA==",  # Valid base64
            "serialNumber": "c2VyaWFs",  # Valid base64
            "certifier": "02" + "0" * 64,  # Valid hex pubkey (66 chars)
        }

        # When / Then
        validate_relinquish_certificate_args(valid_args)  # Should not raise

    def test_validate_relinquish_certificate_args_invalid_type(self) -> None:
        """Given: RelinquishCertificateArgs with invalid type (non-base64)
           When: Call validate_relinquish_certificate_args
           Then: Raises InvalidParameterError

        Reference: go-wallet-toolbox/pkg/internal/validate/validate_relinquish_certificate_args_test.go
                   TestWrongRelinquishCertificateArgs - Invalid Type (non-base64 characters)
        """
        # Given

        invalid_args = {
            "type": "invalid!base64@",  # Invalid base64 characters
            "serialNumber": "c2VyaWFs",
            "certifier": "02" + "0" * 64,
        }

        # When / Then
        with pytest.raises(InvalidParameterError) as exc_info:
            validate_relinquish_certificate_args(invalid_args)
        assert "type" in str(exc_info.value).lower() or "base64" in str(exc_info.value).lower()

    def test_validate_relinquish_certificate_args_invalid_serial_number(self) -> None:
        """Given: RelinquishCertificateArgs with invalid serialNumber (non-base64)
           When: Call validate_relinquish_certificate_args
           Then: Raises InvalidParameterError

        Reference: go-wallet-toolbox/pkg/internal/validate/validate_relinquish_certificate_args_test.go
                   TestWrongRelinquishCertificateArgs - Invalid SerialNumber (non-base64)
        """
        # Given

        invalid_args = {
            "type": "dGVzdA==",
            "serialNumber": "serial@number!",  # Invalid base64
            "certifier": "02" + "0" * 64,
        }

        # When / Then
        with pytest.raises(InvalidParameterError) as exc_info:
            validate_relinquish_certificate_args(invalid_args)
        assert "serial" in str(exc_info.value).lower() or "base64" in str(exc_info.value).lower()

    def test_validate_relinquish_certificate_args_invalid_certifier_non_hex(self) -> None:
        """Given: RelinquishCertificateArgs with invalid certifier (non-hex)
           When: Call validate_relinquish_certificate_args
           Then: Raises InvalidParameterError

        Reference: go-wallet-toolbox/pkg/internal/validate/validate_relinquish_certificate_args_test.go
                   TestWrongRelinquishCertificateArgs - Invalid Certifier (non-hex characters)
        """
        # Given

        invalid_args = {"type": "dGVzdA==", "serialNumber": "c2VyaWFs", "certifier": "ghijk!"}  # Non-hex characters

        # When / Then
        with pytest.raises(InvalidParameterError) as exc_info:
            validate_relinquish_certificate_args(invalid_args)
        assert "certifier" in str(exc_info.value).lower() or "hex" in str(exc_info.value).lower()

    def test_validate_relinquish_certificate_args_certifier_odd_length(self) -> None:
        """Given: RelinquishCertificateArgs with odd-length certifier hex
           When: Call validate_relinquish_certificate_args
           Then: Raises InvalidParameterError

        Reference: go-wallet-toolbox/pkg/internal/validate/validate_relinquish_certificate_args_test.go
                   TestWrongRelinquishCertificateArgs - Certifier with odd length
        """
        # Given

        invalid_args = {"type": "dGVzdA==", "serialNumber": "c2VyaWFs", "certifier": "abc"}  # Odd length hex

        # When / Then
        with pytest.raises(InvalidParameterError) as exc_info:
            validate_relinquish_certificate_args(invalid_args)
        assert "certifier" in str(exc_info.value).lower() or "even" in str(exc_info.value).lower()

    def test_validate_relinquish_certificate_args_empty_certifier(self) -> None:
        """Given: RelinquishCertificateArgs with empty certifier
           When: Call validate_relinquish_certificate_args
           Then: Raises InvalidParameterError

        Reference: go-wallet-toolbox/pkg/internal/validate/validate_relinquish_certificate_args_test.go
                   TestWrongRelinquishCertificateArgs - Empty Certifier
        """
        # Given

        invalid_args = {"type": "dGVzdA==", "serialNumber": "c2VyaWFs", "certifier": ""}  # Empty certifier

        # When / Then
        with pytest.raises(InvalidParameterError) as exc_info:
            validate_relinquish_certificate_args(invalid_args)
        assert "certifier" in str(exc_info.value).lower() or "required" in str(exc_info.value).lower()
