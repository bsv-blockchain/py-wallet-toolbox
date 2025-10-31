"""Universal Test Vectors for getNetwork method.

Tests using official BRC-100 test vectors from:
https://github.com/bsv-blockchain/universal-test-vectors

Source files:
- tests/data/universal-test-vectors/generated/brc100/getNetwork-simple-args.json
- tests/data/universal-test-vectors/generated/brc100/getNetwork-simple-result.json
"""

from collections.abc import Callable

import pytest

from bsv_wallet_toolbox import Wallet


class TestUniversalVectorsGetNetwork:
    """Tests using Universal Test Vectors for getNetwork.

    Important: ABI (wire) tests are skipped because TypeScript doesn't test them.
    Following the principle: "If TypeScript skips it, we skip it too."
    """

    def test_getnetwork_json_matches_universal_vectors(
        self, load_test_vectors: Callable[[str], tuple[dict, dict]]
    ) -> None:
        """Given: Universal Test Vector input for getNetwork
           When: Call getNetwork with empty args on mainnet wallet
           Then: Result matches Universal Test Vector output (JSON)

        Note: Universal Test Vectors expect "mainnet" as the result.
        """
        # Given
        args_data, result_data = load_test_vectors("getNetwork-simple")
        wallet = Wallet(chain="main")  # Mainnet wallet

        # When
        result = wallet.get_network(args_data["json"], originator=None)

        # Then
        assert result == result_data["json"]
        assert result["network"] == "mainnet"

    @pytest.mark.skip(reason="ABI tests skipped - TypeScript doesn't test ABI wire format")
    def test_getnetwork_wire_matches_universal_vectors(
        self, load_test_vectors: Callable[[str], tuple[dict, dict]]
    ) -> None:
        """ABI (wire) test - skipped because TypeScript doesn't test this.

        This test would verify:
        1. Deserialize wire input: "1b00" -> method + args
        2. Execute getNetwork
        3. Serialize result -> matches "0000"

        Following the principle: "If TypeScript skips it, we skip it too."
        """
