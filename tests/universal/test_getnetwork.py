"""Universal Test Vectors for getNetwork method.

Tests using official BRC-100 test vectors from:
https://github.com/bsv-blockchain/universal-test-vectors

Source files:
- tests/data/universal-test-vectors/generated/brc100/getNetwork-simple-args.json
- tests/data/universal-test-vectors/generated/brc100/getNetwork-simple-result.json
"""

from collections.abc import Callable

from bsv_wallet_toolbox import Wallet


class TestUniversalVectorsGetNetwork:
    """Tests using Universal Test Vectors for getNetwork.

    Important: ABI (wire) tests are skipped because TypeScript doesn't test them.
    Following the principle: "If TypeScript skips it, we skip it too."
    """

    def test_getnetwork_json_matches_universal_vectors(
        self, load_test_vectors: Callable[[str], tuple[dict, dict]], test_key_deriver
    ) -> None:
        """Given: Universal Test Vector input for getNetwork
           When: Call getNetwork with empty args on mainnet wallet
           Then: Result matches Universal Test Vector output (JSON)

        Note: Universal Test Vectors expect "mainnet" as the result.
        """
        # Given
        args_data, result_data = load_test_vectors("getNetwork-simple")
        wallet = Wallet(chain="main", key_deriver=test_key_deriver)  # Mainnet wallet

        # When
        result = wallet.get_network(args_data["json"], originator=None)

        # Then
        assert result == result_data["json"]
        assert result["network"] == "mainnet"

    def test_getnetwork_wire_matches_universal_vectors(
        self, load_test_vectors: Callable[[str], tuple[dict, dict]], test_key_deriver
    ) -> None:
        """ABI wire format test for getNetwork.

        Verifies:
        1. Deserialize wire input to method call
        2. Execute getNetwork method
        3. Serialize result matches expected wire output
        """
        from bsv_wallet_toolbox.abi import deserialize_request, serialize_response

        # Given
        args_data, result_data = load_test_vectors("getNetwork-simple")
        wire_input = bytes.fromhex(args_data["wire"])
        expected_wire_output = bytes.fromhex(result_data["wire"])

        wallet = Wallet(chain="main", key_deriver=test_key_deriver)

        # When
        method_name, args = deserialize_request(wire_input)
        assert method_name == "getNetwork"

        result = wallet.get_network(args, originator=None)
        wire_output = serialize_response(result)

        # Then
        assert wire_output == expected_wire_output
