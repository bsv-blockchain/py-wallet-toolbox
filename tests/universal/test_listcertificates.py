"""Universal Test Vectors for listCertificates method.

Tests using official BRC-100 test vectors from:
https://github.com/bsv-blockchain/universal-test-vectors

Source files:
- tests/data/universal-test-vectors/generated/brc100/listCertificates-simple-args.json
- tests/data/universal-test-vectors/generated/brc100/listCertificates-simple-result.json
- tests/data/universal-test-vectors/generated/brc100/listCertificates-full-args.json
- tests/data/universal-test-vectors/generated/brc100/listCertificates-full-result.json
"""

from collections.abc import Callable

import pytest

from bsv_wallet_toolbox import Wallet


class TestUniversalVectorsListCertificates:
    """Tests using Universal Test Vectors for listCertificates.

    Important: ABI (wire) tests are skipped because TypeScript doesn't test them.
    Following the principle: "If TypeScript skips it, we skip it too."
    """

    @pytest.mark.skip(reason="Waiting for list_certificates implementation")
    @pytest.mark.asyncio
    async def test_listcertificates_simple_json_matches_universal_vectors(
        self, load_test_vectors: Callable[[str], tuple[dict, dict]]
    ) -> None:
        """Given: Universal Test Vector input for listCertificates (simple)
        When: Call listCertificates
        Then: Result matches Universal Test Vector output (JSON)
        """
        # Given
        args_data, result_data = load_test_vectors("listCertificates-simple")
        wallet = Wallet(chain="main")

        # When
        result = await wallet.list_certificates(args_data["json"], originator=None)

        # Then
        assert result == result_data["json"]

    @pytest.mark.skip(reason="ABI tests skipped - TypeScript doesn't test ABI wire format")
    @pytest.mark.asyncio
    async def test_listcertificates_simple_wire_matches_universal_vectors(
        self, load_test_vectors: Callable[[str], tuple[dict, dict]]
    ) -> None:
        """ABI (wire) test - skipped because TypeScript doesn't test this."""

    @pytest.mark.skip(reason="Waiting for list_certificates implementation")
    @pytest.mark.asyncio
    async def test_listcertificates_full_json_matches_universal_vectors(
        self, load_test_vectors: Callable[[str], tuple[dict, dict]]
    ) -> None:
        """Given: Universal Test Vector input for listCertificates (full)
        When: Call listCertificates with all parameters
        Then: Result matches Universal Test Vector output (JSON)
        """
        # Given
        args_data, result_data = load_test_vectors("listCertificates-full")
        wallet = Wallet(chain="main")

        # When
        result = await wallet.list_certificates(args_data["json"], originator=None)

        # Then
        assert result == result_data["json"]

    @pytest.mark.skip(reason="ABI tests skipped - TypeScript doesn't test ABI wire format")
    @pytest.mark.asyncio
    async def test_listcertificates_full_wire_matches_universal_vectors(
        self, load_test_vectors: Callable[[str], tuple[dict, dict]]
    ) -> None:
        """ABI (wire) test - skipped because TypeScript doesn't test this."""
