"""Universal Test Vectors for acquireCertificate method.

Tests using official BRC-100 test vectors from:
https://github.com/bsv-blockchain/universal-test-vectors

Source files:
- tests/data/universal-test-vectors/generated/brc100/acquireCertificate-simple-args.json
- tests/data/universal-test-vectors/generated/brc100/acquireCertificate-simple-result.json
- tests/data/universal-test-vectors/generated/brc100/acquireCertificate-issuance-args.json
- tests/data/universal-test-vectors/generated/brc100/acquireCertificate-issuance-result.json
"""

from collections.abc import Callable

import pytest


class TestUniversalVectorsAcquireCertificate:
    """Tests using Universal Test Vectors for acquireCertificate.

    Important: ABI (wire) tests are skipped because TypeScript doesn't test them.
    Following the principle: "If TypeScript skips it, we skip it too."
    """

    @pytest.mark.xfail(reason="Test vector incomplete: missing required 'subject' field in simple variant")
    def test_acquirecertificate_simple_json_matches_universal_vectors(
        self, load_test_vectors: Callable[[str], tuple[dict, dict]], wallet_with_services
    ) -> None:
        """Given: Universal Test Vector input for acquireCertificate (simple)
        When: Call acquireCertificate
        Then: Result matches Universal Test Vector output (JSON)
        """
        # Given
        args_data, result_data = load_test_vectors("acquireCertificate-simple")
        wallet = wallet_with_services

        # When
        result = wallet.acquire_certificate(args_data["json"], originator=None)

        # Then
        assert result == result_data["json"]

    @pytest.mark.skip(reason="ABI tests skipped - TypeScript doesn't test ABI wire format")
    def test_acquirecertificate_simple_wire_matches_universal_vectors(
        self, load_test_vectors: Callable[[str], tuple[dict, dict]]
    ) -> None:
        """ABI (wire) test - skipped because TypeScript doesn't test this."""

    @pytest.mark.xfail(reason="Test vector incomplete: missing required 'serialNumber' field in issuance variant")
    def test_acquirecertificate_issuance_json_matches_universal_vectors(
        self, load_test_vectors: Callable[[str], tuple[dict, dict]], wallet_with_services
    ) -> None:
        """Given: Universal Test Vector input for acquireCertificate (issuance)
        When: Call acquireCertificate for issuance
        Then: Result matches Universal Test Vector output (JSON)
        """
        # Given
        args_data, result_data = load_test_vectors("acquireCertificate-issuance")
        wallet = wallet_with_services

        # When
        result = wallet.acquire_certificate(args_data["json"], originator=None)

        # Then
        assert result == result_data["json"]

    @pytest.mark.skip(reason="ABI tests skipped - TypeScript doesn't test ABI wire format")
    def test_acquirecertificate_issuance_wire_matches_universal_vectors(
        self, load_test_vectors: Callable[[str], tuple[dict, dict]]
    ) -> None:
        """ABI (wire) test - skipped because TypeScript doesn't test this."""
