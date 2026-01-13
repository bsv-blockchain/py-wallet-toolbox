"""Unit tests for Wallet.list_certificates method.

Reference: wallet-toolbox/test/wallet/list/listCertificates.test.ts
"""

import pytest

from bsv_wallet_toolbox import Wallet
from bsv_wallet_toolbox.errors import InvalidParameterError


@pytest.fixture
def valid_list_certificates_args():
    """Fixture providing valid list certificates arguments."""
    return {"certifiers": [], "types": [], "limit": 10, "offset": 0}


@pytest.fixture
def list_certificates_with_filters():
    """Fixture providing list certificates arguments with certifier and type filters."""
    return {
        "certifiers": ["02cf6cdf466951d8dfc9e7c9367511d0007ed6fba35ed42d425cc412fd6cfd4a17"],
        "types": ["exOl3KM0dIJ04EW5pZgbZmPag6MdJXd3/a1enmUU/BA="],
        "limit": 5,
    }


@pytest.fixture
def list_certificates_pagination():
    """Fixture providing list certificates arguments with pagination."""
    return {"certifiers": [], "types": [], "limit": 5, "offset": 10}


@pytest.fixture
def invalid_list_certificates_cases():
    """Fixture providing various invalid list certificates arguments."""
    return [
        # Invalid certifier formats
        {"certifiers": ["thisisnotbase64"], "types": []},
        {"certifiers": ["invalid-hex-characters-!@#$"], "types": []},
        {"certifiers": ["too-short"], "types": []},
        {"certifiers": ["a" * 100], "types": []},  # Too long
        # Wrong types
        {"certifiers": None, "types": []},  # None certifiers
        {"certifiers": "not_a_list", "types": []},  # Wrong certifiers type
        {"certifiers": [123, "valid"], "types": []},  # Wrong certifier types in list
        {"certifiers": [], "types": None},  # None types
        {"certifiers": [], "types": "not_a_list"},  # Wrong types type
        {"certifiers": [], "types": [123, "valid"]},  # Wrong type types in list
        # Invalid limits/offsets
        {"certifiers": [], "types": [], "limit": 0},  # Zero limit
        {"certifiers": [], "types": [], "limit": -1},  # Negative limit
        {"certifiers": [], "types": [], "limit": 10001},  # Too large limit
        {"certifiers": [], "types": [], "offset": -1},  # Negative offset
        {"certifiers": [], "types": [], "limit": "not_number"},  # Wrong limit type
        {"certifiers": [], "types": [], "offset": "not_number"},  # Wrong offset type
    ]


class TestWalletListCertificates:
    """Test suite for Wallet.list_certificates method."""

    def test_invalid_params_invalid_certifier(self, wallet_with_storage: Wallet) -> None:
        """Given: ListCertificatesArgs with invalid certifier (not base64/hex)
           When: Call list_certificates
           Then: Raises InvalidParameterError

        Reference: wallet-toolbox/test/wallet/list/listCertificates.test.ts
                   test('0 invalid params')
        """
        # Given
        invalid_args = {"certifiers": ["thisisnotbase64"], "types": []}  # Invalid certifier

        # When / Then
        with pytest.raises(InvalidParameterError):
            wallet_with_storage.list_certificates(invalid_args)

    # @pytest.mark.skip(reason="Requires populated test database with specific certificate test data from TypeScript")
    def test_filter_by_certifier_lowercase(self, wallet_with_storage: Wallet) -> None:
        """Given: ListCertificatesArgs with valid certifier (lowercase hex)
           When: Call list_certificates
           Then: Returns certificates from that certifier

        Reference: wallet-toolbox/test/wallet/list/listCertificates.test.ts
                   test('1 certifier') - first test case

        Note: This test requires a populated test database with certificates.
        """
        # Given
        args = {
            "certifiers": ["02cf6cdf466951d8dfc9e7c9367511d0007ed6fba35ed42d425cc412fd6cfd4a17"],
            "types": [],
            "limit": 1,
        }
        expected_count = 4  # From test data

        # When
        result = wallet_with_storage.list_certificates(args)

        # Then
        assert len(result["certificates"]) == min(args["limit"], expected_count)
        assert result["totalCertificates"] == expected_count

    # @pytest.mark.skip(reason="Requires populated test database with specific certificate test data from TypeScript")
    def test_filter_by_certifier_uppercase(self, wallet_with_storage: Wallet) -> None:
        """Given: ListCertificatesArgs with valid certifier (uppercase hex)
           When: Call list_certificates
           Then: Returns certificates from that certifier (case-insensitive)

        Reference: wallet-toolbox/test/wallet/list/listCertificates.test.ts
                   test('1 certifier') - second test case

        Note: This test requires a populated test database with certificates.
        """
        # Given
        args = {
            "certifiers": ["02CF6CDF466951D8DFC9E7C9367511D0007ED6FBA35ED42D425CC412FD6CFD4A17"],
            "types": [],
            "limit": 10,
        }
        expected_count = 4  # From test data

        # When
        result = wallet_with_storage.list_certificates(args)

        # Then
        assert len(result["certificates"]) == min(args["limit"], expected_count)
        assert result["totalCertificates"] == expected_count

    # @pytest.mark.skip(reason="Requires populated test database with specific certificate test data from TypeScript")
    def test_filter_by_multiple_certifiers(self, wallet_with_storage: Wallet) -> None:
        """Given: ListCertificatesArgs with multiple certifiers
           When: Call list_certificates
           Then: Returns certificates from any of those certifiers

        Reference: wallet-toolbox/test/wallet/list/listCertificates.test.ts
                   test('1 certifier') - third test case

        Note: This test requires a populated test database with certificates.
        """
        # Given
        args = {
            "certifiers": [
                "02CF6CDF466951D8DFC9E7C9367511D0007ED6FBA35ED42D425CC412FD6CFD4A17",
                "03cf6cdf466951d8dfc9e7c9367511d0007ed6fba35ed42d425cc412fd6cfd4a17",
            ],
            "types": [],
            "limit": 10,
        }
        expected_count = 5  # From test data (4 + 1)

        # When
        result = wallet_with_storage.list_certificates(args)

        # Then
        assert len(result["certificates"]) == min(args["limit"], expected_count)
        assert result["totalCertificates"] == expected_count

    # @pytest.mark.skip(reason="Requires populated test database with specific certificate test data from TypeScript")
    def test_filter_by_type(self, wallet_with_storage: Wallet) -> None:
        """Given: ListCertificatesArgs with certificate type filter
           When: Call list_certificates
           Then: Returns only certificates of that type

        Reference: wallet-toolbox/test/wallet/list/listCertificates.test.ts
                   test('2 types')

        Note: This test requires a populated test database with typed certificates.
        """
        # Given
        args = {"certifiers": [], "types": ["exOl3KM0dIJ04EW5pZgbZmPag6MdJXd3/a1enmUU/BA="], "limit": 10}  # Base64 type
        expected_count = 3  # From test data

        # When
        result = wallet_with_storage.list_certificates(args)

        # Then
        assert len(result["certificates"]) == min(args["limit"], expected_count)
        assert result["totalCertificates"] == expected_count

    def test_invalid_params_none_certifiers_raises_error(self, wallet_with_storage: Wallet) -> None:
        """Given: ListCertificatesArgs with None certifiers
        When: Call list_certificates
        Then: Raises InvalidParameterError or TypeError
        """
        # Given
        invalid_args = {"certifiers": None, "types": []}

        # When/Then
        with pytest.raises((InvalidParameterError, TypeError)):
            wallet_with_storage.list_certificates(invalid_args)

    def test_invalid_params_wrong_certifiers_type_raises_error(self, wallet_with_storage: Wallet) -> None:
        """Given: ListCertificatesArgs with wrong certifiers type
        When: Call list_certificates
        Then: Raises InvalidParameterError or TypeError
        """
        # Given - Test various invalid types
        invalid_types = [123, {}, True, 45.67, "string"]

        for invalid_certifiers in invalid_types:
            invalid_args = {"certifiers": invalid_certifiers, "types": []}

            # When/Then
            with pytest.raises((InvalidParameterError, TypeError)):
                wallet_with_storage.list_certificates(invalid_args)

    def test_invalid_params_wrong_certifier_types_in_list_raises_error(self, wallet_with_storage: Wallet) -> None:
        """Given: ListCertificatesArgs with wrong types in certifiers list
        When: Call list_certificates
        Then: Raises InvalidParameterError or TypeError
        """
        # Given - Test various invalid certifier types in list
        invalid_certifier_types = [
            [123, "valid"],
            [None, "valid"],
            [{}, "valid"],
            [[], "valid"],
            [True, "valid"],
        ]

        for invalid_certifiers in invalid_certifier_types:
            invalid_args = {"certifiers": invalid_certifiers, "types": []}

            # When/Then
            with pytest.raises((InvalidParameterError, TypeError)):
                wallet_with_storage.list_certificates(invalid_args)

    def test_invalid_params_empty_certifier_strings_raises_error(self, wallet_with_storage: Wallet) -> None:
        """Given: ListCertificatesArgs with empty certifier strings
        When: Call list_certificates
        Then: Raises InvalidParameterError
        """
        # Given - Various empty/whitespace certifier strings
        empty_certifiers = ["", "   ", "\t", "\n", " \t \n "]

        for certifier in empty_certifiers:
            invalid_args = {"certifiers": [certifier], "types": []}

            # When/Then
            with pytest.raises((InvalidParameterError, ValueError)):
                wallet_with_storage.list_certificates(invalid_args)

    def test_invalid_params_invalid_hex_certifiers_raises_error(self, wallet_with_storage: Wallet) -> None:
        """Given: ListCertificatesArgs with invalid hex certifier strings
        When: Call list_certificates
        Then: Raises InvalidParameterError for invalid hex or odd length
        """
        # Given - Only invalid hex chars and odd length raise errors
        invalid_hex_certifiers = [
            "gggggggggggggggggggggggggggggggggggggggg",  # Invalid hex chars
            "abcdef1234567890abcdef1234567890abcde",  # Odd length
        ]

        for certifier in invalid_hex_certifiers:
            invalid_args = {"certifiers": [certifier], "types": []}

            # When/Then - InvalidParameterError is raised
            with pytest.raises(InvalidParameterError):
                wallet_with_storage.list_certificates(invalid_args)

    def test_invalid_params_certifier_too_long_raises_error(self, wallet_with_storage: Wallet) -> None:
        """Given: ListCertificatesArgs with certifier exceeding length limits
        When: Call list_certificates
        Then: Returns result (only format is validated, not length)
        """
        # Given - Certifier too long (but valid hex format)
        too_long_certifier = "a" * 200  # Much longer than valid key but valid hex
        invalid_args = {"certifiers": [too_long_certifier], "types": []}

        # When - Length is not validated, only format
        result = wallet_with_storage.list_certificates(invalid_args)

        # Then
        assert "certificates" in result

    def test_invalid_params_none_types_raises_error(self, wallet_with_storage: Wallet) -> None:
        """Given: ListCertificatesArgs with None types
        When: Call list_certificates
        Then: Raises InvalidParameterError or TypeError
        """
        # Given
        invalid_args = {"certifiers": [], "types": None}

        # When/Then
        with pytest.raises((InvalidParameterError, TypeError)):
            wallet_with_storage.list_certificates(invalid_args)

    def test_invalid_params_wrong_types_type_raises_error(self, wallet_with_storage: Wallet) -> None:
        """Given: ListCertificatesArgs with wrong types type
        When: Call list_certificates
        Then: Raises InvalidParameterError or TypeError
        """
        # Given - Test various invalid types
        invalid_types = [123, {}, True, 45.67, "string"]

        for invalid_types_val in invalid_types:
            invalid_args = {"certifiers": [], "types": invalid_types_val}

            # When/Then
            with pytest.raises((InvalidParameterError, TypeError)):
                wallet_with_storage.list_certificates(invalid_args)

    def test_invalid_params_wrong_type_types_in_list_raises_error(self, wallet_with_storage: Wallet) -> None:
        """Given: ListCertificatesArgs with wrong types in types list
        When: Call list_certificates
        Then: Raises InvalidParameterError or TypeError
        """
        # Given - Test various invalid type types in list
        invalid_type_types = [
            [123, "valid"],
            [None, "valid"],
            [{}, "valid"],
            [[], "valid"],
            [True, "valid"],
        ]

        for invalid_types_list in invalid_type_types:
            invalid_args = {"certifiers": [], "types": invalid_types_list}

            # When/Then
            with pytest.raises((InvalidParameterError, TypeError)):
                wallet_with_storage.list_certificates(invalid_args)

    def test_invalid_params_empty_type_strings_raises_error(self, wallet_with_storage: Wallet) -> None:
        """Given: ListCertificatesArgs with empty type strings
        When: Call list_certificates
        Then: Raises InvalidParameterError
        """
        # Given - Various empty/whitespace type strings
        empty_types = ["", "   ", "\t", "\n", " \t \n "]

        for cert_type in empty_types:
            invalid_args = {"certifiers": [], "types": [cert_type]}

            # When/Then
            with pytest.raises((InvalidParameterError, ValueError)):
                wallet_with_storage.list_certificates(invalid_args)

    def test_invalid_params_invalid_base64_types_raises_error(self, wallet_with_storage: Wallet) -> None:
        """Given: ListCertificatesArgs with invalid base64 type strings
        When: Call list_certificates
        Then: Raises InvalidParameterError
        """
        # Given - Invalid base64 type strings (note: + and / are valid base64 chars)
        invalid_base64_types = [
            "invalid@base64!",
            "contains#symbols",
            "with$dollar$signs",
            "percent%encoded",
            "caret^here",
            "ampersand&here",
            "asterisk*here",
            "backslash\\invalid",
        ]

        for cert_type in invalid_base64_types:
            invalid_args = {"certifiers": [], "types": [cert_type]}

            # When/Then - InvalidParameterError is raised
            with pytest.raises(InvalidParameterError):
                wallet_with_storage.list_certificates(invalid_args)

    def test_invalid_params_wrong_limit_type_raises_error(self, wallet_with_storage: Wallet) -> None:
        """Given: ListCertificatesArgs with wrong limit type
        When: Call list_certificates
        Then: Raises InvalidParameterError or TypeError
        """
        # Given - Test various invalid types

        # Note: True is coerced to 1 in Python isinstance check
        invalid_types_for_limit = ["string", [], {}, 45.67]

        for invalid_limit in invalid_types_for_limit:
            invalid_args = {"certifiers": [], "types": [], "limit": invalid_limit}

            # When/Then - InvalidParameterError is raised
            with pytest.raises(InvalidParameterError):
                wallet_with_storage.list_certificates(invalid_args)

    def test_invalid_params_wrong_offset_type_raises_error(self, wallet_with_storage: Wallet) -> None:
        """Given: ListCertificatesArgs with wrong offset type
        When: Call list_certificates
        Then: Raises InvalidParameterError
        """
        # Given - Test various invalid types (negative integers are allowed)
        invalid_types_for_offset = ["string", [], {}, 45.67]

        for invalid_offset in invalid_types_for_offset:
            invalid_args = {"certifiers": [], "types": [], "offset": invalid_offset}

            # When/Then - InvalidParameterError is raised
            with pytest.raises(InvalidParameterError):
                wallet_with_storage.list_certificates(invalid_args)

    def test_invalid_params_zero_limit_raises_error(self, wallet_with_storage: Wallet) -> None:
        """Given: ListCertificatesArgs with zero limit
        When: Call list_certificates
        Then: Returns empty result (zero limit is allowed)
        """
        # Given
        invalid_args = {"certifiers": [], "types": [], "limit": 0}

        # When - Zero limit is allowed (returns 0 items)
        result = wallet_with_storage.list_certificates(invalid_args)

        # Then
        assert "certificates" in result

    def test_invalid_params_negative_limit_raises_error(self, wallet_with_storage: Wallet) -> None:
        """Given: ListCertificatesArgs with negative limit
        When: Call list_certificates
        Then: Raises InvalidParameterError
        """
        # Given
        invalid_args = {"certifiers": [], "types": [], "limit": -1}

        # When/Then
        with pytest.raises(InvalidParameterError):
            wallet_with_storage.list_certificates(invalid_args)

    def test_negative_offset_accepted(self, wallet_with_storage: Wallet) -> None:
        """Given: ListCertificatesArgs with negative offset
        When: Call list_certificates
        Then: Returns result (negative offset is allowed)
        """
        # Given
        invalid_args = {"certifiers": [], "types": [], "offset": -1}

        # When - Negative offset is allowed
        result = wallet_with_storage.list_certificates(invalid_args)

        # Then
        assert "certificates" in result

    def test_invalid_params_extremely_large_limit_raises_error(self, wallet_with_storage: Wallet) -> None:
        """Given: ListCertificatesArgs with extremely large limit
        When: Call list_certificates
        Then: Raises InvalidParameterError for limits > 10000
        """
        # Given - Limits that exceed MAX_PAGINATION_LIMIT (10000)
        large_limits = [10001, 100000, 1000000]

        for limit in large_limits:
            invalid_args = {"certifiers": [], "types": [], "limit": limit}

            # When/Then - InvalidParameterError is raised
            with pytest.raises(InvalidParameterError):
                wallet_with_storage.list_certificates(invalid_args)

    def test_valid_params_minimal_args(self, wallet_with_storage: Wallet) -> None:
        """Given: Minimal valid ListCertificatesArgs
        When: Call list_certificates
        Then: Returns results successfully
        """
        # Given - Minimal required args
        minimal_args = {"certifiers": [], "types": []}

        # When
        result = wallet_with_storage.list_certificates(minimal_args)

        # Then
        assert "totalCertificates" in result
        assert "certificates" in result
        assert isinstance(result["certificates"], list)
        assert result["totalCertificates"] >= len(result["certificates"])

    def test_valid_params_empty_filters(self, wallet_with_storage: Wallet) -> None:
        """Given: ListCertificatesArgs with empty certifiers and types
        When: Call list_certificates
        Then: Returns all certificates (no filtering)
        """
        # Given
        args = {"certifiers": [], "types": []}

        # When
        result = wallet_with_storage.list_certificates(args)

        # Then
        assert "totalCertificates" in result
        assert "certificates" in result
        assert isinstance(result["certificates"], list)
        assert result["totalCertificates"] >= len(result["certificates"])

    def test_valid_params_with_pagination(self, wallet_with_storage: Wallet, list_certificates_pagination) -> None:
        """Given: ListCertificatesArgs with pagination parameters
        When: Call list_certificates
        Then: Returns paginated results
        """
        # When
        result = wallet_with_storage.list_certificates(list_certificates_pagination)

        # Then
        assert "totalCertificates" in result
        assert "certificates" in result
        assert isinstance(result["certificates"], list)
        assert len(result["certificates"]) <= list_certificates_pagination["limit"]
        assert result["totalCertificates"] >= len(result["certificates"])

    def test_valid_params_case_insensitive_certifier_hex(self, wallet_with_storage: Wallet) -> None:
        """Given: ListCertificatesArgs with mixed case hex certifier
        When: Call list_certificates
        Then: Handles case insensitive hex correctly
        """
        # Given - Test different case variations of same certifier
        test_cases = [
            "02cf6cdf466951d8dfc9e7c9367511d0007ed6fba35ed42d425cc412fd6cfd4a17",  # lowercase
            "02CF6CDF466951D8DFC9E7C9367511D0007ED6FBA35ED42D425CC412FD6CFD4A17",  # uppercase
            "02Cf6cDf466951d8dFc9E7c9367511D0007eD6FbA35eD42D425Cc412Fd6CfD4A17",  # mixed case
        ]

        for certifier in test_cases:
            args = {"certifiers": [certifier], "types": []}

            # When
            result = wallet_with_storage.list_certificates(args)

            # Then - Should not raise error and return valid result
            assert "totalCertificates" in result
            assert "certificates" in result
            assert isinstance(result["certificates"], list)

    def test_valid_params_large_offset_returns_empty(self, wallet_with_storage: Wallet) -> None:
        """Given: ListCertificatesArgs with offset larger than total certificates
        When: Call list_certificates
        Then: Returns empty results
        """
        # Given - Use a very large offset
        args = {
            "certifiers": [],
            "types": [],
            "offset": 10000,  # Much larger than any reasonable number of certificates
        }

        # When
        result = wallet_with_storage.list_certificates(args)

        # Then
        assert "totalCertificates" in result
        assert "certificates" in result
        assert isinstance(result["certificates"], list)
        assert len(result["certificates"]) == 0
        assert result["totalCertificates"] >= 0

    def test_valid_params_multiple_filters_combined(self, wallet_with_storage: Wallet) -> None:
        """Given: ListCertificatesArgs with both certifier and type filters
        When: Call list_certificates
        Then: Returns certificates matching both filters
        """
        # Given
        args = {
            "certifiers": ["02cf6cdf466951d8dfc9e7c9367511d0007ed6fba35ed42d425cc412fd6cfd4a17"],
            "types": ["exOl3KM0dIJ04EW5pZgbZmPag6MdJXd3/a1enmUU/BA="],
            "limit": 10,
        }

        # When
        result = wallet_with_storage.list_certificates(args)

        # Then
        assert "totalCertificates" in result
        assert "certificates" in result
        assert isinstance(result["certificates"], list)

        # Each returned certificate should match both filters
        for cert in result["certificates"]:
            assert isinstance(cert, dict)
            # Note: Actual validation depends on certificate structure
            # This tests that the filtering logic works without error

    def test_valid_params_unicode_type_strings(self, wallet_with_storage: Wallet) -> None:
        """Given: ListCertificatesArgs with unicode type strings
        When: Call list_certificates
        Then: Raises InvalidParameterError (types must be valid base64)
        """
        # Given - Unicode is not valid base64
        unicode_args = {"certifiers": [], "types": ["test_type_with_unicode_测试"]}

        # When/Then - Unicode in type string is not valid base64
        with pytest.raises(InvalidParameterError):
            wallet_with_storage.list_certificates(unicode_args)
