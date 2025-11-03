"""Tests for validate_insert_certificate_auth_args utility function.

Reference: go-wallet-toolbox/pkg/internal/validate/validate_insert_certificate_auth_args_test.go
"""

import pytest

from bsv_wallet_toolbox.errors import InvalidParameterError
from bsv_wallet_toolbox.utils.validation import validate_insert_certificate_auth_args


class TestValidateInsertCertificateAuthArgs:
    """Test suite for validate_insert_certificate_auth_args function.

    This validates TableCertificateX (insert certificate auth arguments) according to BRC-100 specifications.
    TableCertificateX must include:
    - type: hexadecimal string with even length
    - serialNumber: valid base64 string
    - certifier: valid public key hex (up to 300 characters)
    - subject: non-empty string
    - revocationOutpoint: valid outpoint string in format "txid.index"
    - signature: hexadecimal string with even length
    - fields: list of certificate fields with valid masterKey (hex)
    """

    def test_validate_insert_certificate_auth_args_valid(self) -> None:
        """Given: Valid TableCertificateX
           When: Call validate_insert_certificate_auth_args
           Then: No exception raised

        Reference: go-wallet-toolbox/pkg/internal/validate/validate_insert_certificate_auth_args_test.go
                   TestForDefaultValidInsertCertificateAuthArgs
        """
        # Given

        valid_args = {
            "type": "0102",  # Valid hex (even length)
            "serialNumber": "c2VyaWFs",  # Valid base64
            "certifier": "02" + "0" * 64,  # Valid hex pubkey
            "subject": "test_subject",
            "revocationOutpoint": "deadbeef" + "0" * 56 + ".0",  # Valid outpoint
            "signature": "3045022100" + "0" * 60,  # Valid hex signature
            "fields": [{"fieldName": "field1", "masterKey": "0102"}],  # Valid hex
        }

        # When / Then
        validate_insert_certificate_auth_args(valid_args)  # Should not raise

    def test_validate_insert_certificate_auth_args_invalid_type_non_hex(self) -> None:
        """Given: TableCertificateX with invalid type (non-hex)
           When: Call validate_insert_certificate_auth_args
           Then: Raises InvalidParameterError

        Reference: go-wallet-toolbox/pkg/internal/validate/validate_insert_certificate_auth_args_test.go
                   TestWrongInsertCertificateAuthArgs - Invalid Type (non-hex characters)
        """
        # Given

        invalid_args = {
            "type": "ghijk!",  # Non-hex characters
            "serialNumber": "c2VyaWFs",
            "certifier": "02" + "0" * 64,
            "subject": "test_subject",
        }

        # When / Then
        with pytest.raises(InvalidParameterError) as exc_info:
            validate_insert_certificate_auth_args(invalid_args)
        assert "type" in str(exc_info.value).lower() or "hex" in str(exc_info.value).lower()

    def test_validate_insert_certificate_auth_args_type_odd_length(self) -> None:
        """Given: TableCertificateX with odd-length type hex
           When: Call validate_insert_certificate_auth_args
           Then: Raises InvalidParameterError

        Reference: go-wallet-toolbox/pkg/internal/validate/validate_insert_certificate_auth_args_test.go
                   TestWrongInsertCertificateAuthArgs - Invalid Type (odd length)
        """
        # Given

        invalid_args = {
            "type": "abc",  # Odd length
            "serialNumber": "c2VyaWFs",
            "certifier": "02" + "0" * 64,
            "subject": "test_subject",
        }

        # When / Then
        with pytest.raises(InvalidParameterError) as exc_info:
            validate_insert_certificate_auth_args(invalid_args)
        assert "type" in str(exc_info.value).lower() or "even" in str(exc_info.value).lower()

    def test_validate_insert_certificate_auth_args_certifier_too_long(self) -> None:
        """Given: TableCertificateX with certifier exceeding 300 characters
           When: Call validate_insert_certificate_auth_args
           Then: Raises InvalidParameterError

        Reference: go-wallet-toolbox/pkg/internal/validate/validate_insert_certificate_auth_args_test.go
                   TestWrongInsertCertificateAuthArgs - Invalid Certifier (too long)
        """
        # Given

        invalid_args = {
            "type": "0102",
            "serialNumber": "c2VyaWFs",
            "certifier": "a" * 301,  # 301 characters (exceeds 300 limit)
            "subject": "test_subject",
        }

        # When / Then
        with pytest.raises(InvalidParameterError) as exc_info:
            validate_insert_certificate_auth_args(invalid_args)
        assert "certifier" in str(exc_info.value).lower()

    def test_validate_insert_certificate_auth_args_empty_subject(self) -> None:
        """Given: TableCertificateX with empty subject
           When: Call validate_insert_certificate_auth_args
           Then: Raises InvalidParameterError

        Reference: go-wallet-toolbox/pkg/internal/validate/validate_insert_certificate_auth_args_test.go
                   TestWrongInsertCertificateAuthArgs - Invalid Subject (empty)
        """
        # Given

        invalid_args = {
            "type": "0102",
            "serialNumber": "c2VyaWFs",
            "certifier": "02" + "0" * 64,
            "subject": "",  # Empty subject
        }

        # When / Then
        with pytest.raises(InvalidParameterError) as exc_info:
            validate_insert_certificate_auth_args(invalid_args)
        assert "subject" in str(exc_info.value).lower() or "required" in str(exc_info.value).lower()

    def test_validate_insert_certificate_auth_args_invalid_revocation_outpoint(self) -> None:
        """Given: TableCertificateX with invalid revocationOutpoint (missing index)
           When: Call validate_insert_certificate_auth_args
           Then: Raises InvalidParameterError

        Reference: go-wallet-toolbox/pkg/internal/validate/validate_insert_certificate_auth_args_test.go
                   TestWrongInsertCertificateAuthArgs - Invalid RevocationOutpoint (missing index)
        """
        # Given

        invalid_args = {
            "type": "0102",
            "serialNumber": "c2VyaWFs",
            "certifier": "02" + "0" * 64,
            "subject": "test_subject",
            "revocationOutpoint": "txidwithoutindex",  # Missing dot and index
            "signature": "3045022100" + "0" * 60,  # Add missing signature
        }

        # When / Then
        with pytest.raises(InvalidParameterError) as exc_info:
            validate_insert_certificate_auth_args(invalid_args)
        assert "outpoint" in str(exc_info.value).lower()

    def test_validate_insert_certificate_auth_args_signature_odd_length(self) -> None:
        """Given: TableCertificateX with odd-length signature hex
           When: Call validate_insert_certificate_auth_args
           Then: Raises InvalidParameterError

        Reference: go-wallet-toolbox/pkg/internal/validate/validate_insert_certificate_auth_args_test.go
                   TestWrongInsertCertificateAuthArgs - Invalid Signature (odd length)
        """
        # Given

        invalid_args = {
            "type": "0102",
            "serialNumber": "c2VyaWFs",
            "certifier": "02" + "0" * 64,
            "subject": "test_subject",
            "signature": "abc",  # Odd length
        }

        # When / Then
        with pytest.raises(InvalidParameterError) as exc_info:
            validate_insert_certificate_auth_args(invalid_args)
        assert "signature" in str(exc_info.value).lower() or "even" in str(exc_info.value).lower()

    def test_validate_insert_certificate_auth_args_field_invalid_master_key(self) -> None:
        """Given: TableCertificateX with field containing invalid masterKey (non-hex)
           When: Call validate_insert_certificate_auth_args
           Then: Raises InvalidParameterError

        Reference: go-wallet-toolbox/pkg/internal/validate/validate_insert_certificate_auth_args_test.go
                   TestWrongInsertCertificateAuthArgs - Field with invalid MasterKey (non-hex)
        """
        # Given

        invalid_args = {
            "type": "0102",
            "serialNumber": "c2VyaWFs",
            "certifier": "02" + "0" * 64,
            "subject": "test_subject",
            "fields": [{"fieldName": "field1", "masterKey": "invalidhex"}],  # Non-hex characters
        }

        # When / Then
        with pytest.raises(InvalidParameterError) as exc_info:
            validate_insert_certificate_auth_args(invalid_args)
        assert "masterkey" in str(exc_info.value).lower() or "hex" in str(exc_info.value).lower()
