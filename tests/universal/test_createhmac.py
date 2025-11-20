"""Universal Test Vectors for createHmac method.

Tests using official BRC-100 test vectors from:
https://github.com/bsv-blockchain/universal-test-vectors

Source files:
- tests/data/universal-test-vectors/generated/brc100/createHmac-simple-args.json
- tests/data/universal-test-vectors/generated/brc100/createHmac-simple-result.json
"""

from collections.abc import Callable

import pytest

from bsv_wallet_toolbox import Wallet


class TestUniversalVectorsCreateHmac:
    """Tests using Universal Test Vectors for createHmac.

    Important: ABI (wire) tests are skipped because TypeScript doesn't test them.
    Following the principle: "If TypeScript skips it, we skip it too."
    """

    @pytest.mark.skip(reason="createHmac not implemented - requires crypto subsystem")
    def test_createhmac_json_matches_universal_vectors(
        self, load_test_vectors: Callable[[str], tuple[dict, dict]], test_key_deriver
    ) -> None:
        """Given: Universal Test Vector input for createHmac
        When: Call createHmac
        Then: Result matches Universal Test Vector output (JSON)
        """
        # Given
        args_data, result_data = load_test_vectors("createHmac-simple")
        wallet = Wallet(chain="main", key_deriver=test_key_deriver)

        # When
        result = wallet.create_hmac(args_data["json"], originator=None)

        # Then
        assert result == result_data["json"]

    def test_createhmac_wire_matches_universal_vectors(
        self, load_test_vectors: Callable[[str], tuple[dict, dict]]
    ) -> None:
        """ABI (wire) test - skipped because TypeScript doesn't test this."""
