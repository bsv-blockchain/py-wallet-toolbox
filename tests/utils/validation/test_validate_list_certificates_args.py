"""Tests for validate_list_certificates_args utility function.

Reference: go-wallet-toolbox/pkg/internal/validate/validate_list_certificates_args_test.go
"""

import pytest

from bsv_wallet_toolbox.errors import InvalidParameterError
from bsv_wallet_toolbox.utils.validation import validate_list_certificates_args


class TestValidateListCertificatesArgs:
    """Test suite for validate_list_certificates_args function.

    This validates ListCertificatesArgs according to BRC-100 specifications.
    ListCertificatesArgs must include:
    - certifiers: list of valid public key hex strings (even length)
    - types: list of valid base64 strings
    - limit: must not exceed 10000
    - partial: optional filter with valid certifier, type, serialNumber, revocationOutpoint, signature, subject
    """

    def test_validate_list_certificates_args_valid(self) -> None:
        """Given: Valid ListCertificatesArgs
           When: Call validate_list_certificates_args
           Then: No exception raised

        Reference: go-wallet-toolbox/pkg/internal/validate/validate_list_certificates_args_test.go
                   TestForDefaultValidListCertificatesArgs
        """
        # Given

        valid_args = {
            "certifiers": ["0" * 66],  # Valid 66-char hex pubkey
            "types": ["dGVzdA=="],  # Valid base64
            "limit": 100,
        }

        # When / Then
        validate_list_certificates_args(valid_args)  # Should not raise

    def test_validate_list_certificates_args_invalid_certifier_non_hex(self) -> None:
        """Given: ListCertificatesArgs with invalid (non-hex) certifier
           When: Call validate_list_certificates_args
           Then: Raises InvalidParameterError

        Reference: go-wallet-toolbox/pkg/internal/validate/validate_list_certificates_args_test.go
                   TestWrongListCertificatesArgs - Invalid Certifier in Certifiers list
        """
        # Given

        invalid_args = {"certifiers": ["invalid!"]}  # Non-hex characters

        # When / Then
        with pytest.raises(InvalidParameterError) as exc_info:
            validate_list_certificates_args(invalid_args)
        assert "certifier" in str(exc_info.value).lower() or "hex" in str(exc_info.value).lower()

    def test_validate_list_certificates_args_certifier_odd_length(self) -> None:
        """Given: ListCertificatesArgs with odd-length hex certifier
           When: Call validate_list_certificates_args
           Then: Raises InvalidParameterError

        Reference: go-wallet-toolbox/pkg/internal/validate/validate_list_certificates_args_test.go
                   TestWrongListCertificatesArgs - Certifier with odd length hex
        """
        # Given

        invalid_args = {"certifiers": ["abc"]}  # Odd length

        # When / Then
        with pytest.raises(InvalidParameterError) as exc_info:
            validate_list_certificates_args(invalid_args)
        assert "certifier" in str(exc_info.value).lower() or "even" in str(exc_info.value).lower()

    def test_validate_list_certificates_args_invalid_type_not_base64(self) -> None:
        """Given: ListCertificatesArgs with invalid (non-base64) type
           When: Call validate_list_certificates_args
           Then: Raises InvalidParameterError

        Reference: go-wallet-toolbox/pkg/internal/validate/validate_list_certificates_args_test.go
                   TestWrongListCertificatesArgs - Invalid Type in Types list (non-base64)
        """
        # Given

        invalid_args = {"types": ["not@base64!"]}  # Invalid base64 characters

        # When / Then
        with pytest.raises(InvalidParameterError) as exc_info:
            validate_list_certificates_args(invalid_args)
        assert "type" in str(exc_info.value).lower() or "base64" in str(exc_info.value).lower()

    def test_validate_list_certificates_args_limit_above_maximum(self) -> None:
        """Given: ListCertificatesArgs with limit exceeding 10000
           When: Call validate_list_certificates_args
           Then: Raises InvalidParameterError

        Reference: go-wallet-toolbox/pkg/internal/validate/validate_list_certificates_args_test.go
                   TestWrongListCertificatesArgs - Limit above maximum (10001)
        """
        # Given

        invalid_args = {"limit": 10001}  # Exceeds maximum of 10000

        # When / Then
        with pytest.raises(InvalidParameterError) as exc_info:
            validate_list_certificates_args(invalid_args)
        assert "limit" in str(exc_info.value).lower()

    def test_validate_list_certificates_args_partial_invalid_certifier(self) -> None:
        """Given: ListCertificatesArgs with partial filter containing invalid certifier hex
           When: Call validate_list_certificates_args
           Then: Raises InvalidParameterError

        Reference: go-wallet-toolbox/pkg/internal/validate/validate_list_certificates_args_test.go
                   TestWrongListCertificatesArgs - Partial with invalid Certifier hex
        """
        # Given

        invalid_args = {"partial": {"certifier": "zzzz"}}  # Non-hex characters

        # When / Then
        with pytest.raises(InvalidParameterError) as exc_info:
            validate_list_certificates_args(invalid_args)
        assert "certifier" in str(exc_info.value).lower() or "hex" in str(exc_info.value).lower()

    def test_validate_list_certificates_args_partial_malformed_outpoint(self) -> None:
        """Given: ListCertificatesArgs with partial filter containing malformed revocationOutpoint
           When: Call validate_list_certificates_args
           Then: Raises InvalidParameterError

        Reference: go-wallet-toolbox/pkg/internal/validate/validate_list_certificates_args_test.go
                   TestWrongListCertificatesArgs - Partial with malformed RevocationOutpoint
        """
        # Given

        invalid_args = {"partial": {"revocationOutpoint": "missing.index"}}  # Malformed outpoint

        # When / Then
        with pytest.raises(InvalidParameterError) as exc_info:
            validate_list_certificates_args(invalid_args)
        assert "outpoint" in str(exc_info.value).lower()
