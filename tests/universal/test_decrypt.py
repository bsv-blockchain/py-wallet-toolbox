"""Universal Test Vectors for decrypt method.

Tests using official BRC-100 test vectors from:
https://github.com/bsv-blockchain/universal-test-vectors

Source files:
- tests/data/universal-test-vectors/generated/brc100/decrypt-simple-args.json
- tests/data/universal-test-vectors/generated/brc100/decrypt-simple-result.json
"""

from collections.abc import Callable

import pytest

from bsv_wallet_toolbox import Wallet


class TestUniversalVectorsDecrypt:
    """Tests using Universal Test Vectors for decrypt.

    Important: ABI (wire) tests are skipped because TypeScript doesn't test them.
    Following the principle: "If TypeScript skips it, we skip it too."
    """

    def test_decrypt_json_matches_universal_vectors(
        self, load_test_vectors: Callable[[str], tuple[dict, dict]], test_key_deriver
    ) -> None:
        """Given: Universal Test Vector input for decrypt
        When: Call decrypt
        Then: Result matches Universal Test Vector output (JSON)
        """
        # Given
        args_data, result_data = load_test_vectors("decrypt-simple")
        wallet = Wallet(chain="main", key_deriver=test_key_deriver)

        # When
        result = wallet.decrypt(args_data["json"], originator=None)

        # Then
        assert result == result_data["json"]

    def test_decrypt_wire_matches_universal_vectors(
        self, load_test_vectors: Callable[[str], tuple[dict, dict]]
    ) -> None:
        """ABI (wire) test - skipped because TypeScript doesn't test this."""
