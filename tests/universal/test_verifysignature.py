"""Universal Test Vectors for verifySignature method.

Tests using official BRC-100 test vectors from:
https://github.com/bsv-blockchain/universal-test-vectors

Source files:
- tests/data/universal-test-vectors/generated/brc100/verifySignature-simple-args.json
- tests/data/universal-test-vectors/generated/brc100/verifySignature-simple-result.json
"""

from collections.abc import Callable

import pytest

from bsv_wallet_toolbox import Wallet


class TestUniversalVectorsVerifySignature:
    """Tests using Universal Test Vectors for verifySignature.

    Important: ABI (wire) tests are skipped because TypeScript doesn't test them.
    Following the principle: "If TypeScript skips it, we skip it too."
    """

    def test_verifysignature_json_matches_universal_vectors(
        self, load_test_vectors: Callable[[str], tuple[dict, dict]]
    ) -> None:
        """Given: Universal Test Vector input for verifySignature
        When: Call verifySignature
        Then: Result matches Universal Test Vector output (JSON)
        """
        # Given
        args_data, result_data = load_test_vectors("verifySignature-simple")
        wallet = Wallet(chain="main")

        # When
        result = wallet.verify_signature(args_data["json"], originator=None)

        # Then
        assert result == result_data["json"]

    def test_verifysignature_wire_matches_universal_vectors(
        self, load_test_vectors: Callable[[str], tuple[dict, dict]]
    ) -> None:
        """ABI (wire) test - skipped because TypeScript doesn't test this."""
