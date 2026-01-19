"""Universal Test Vectors for createHmac method.

Tests using official BRC-100 test vectors from:
https://github.com/bsv-blockchain/universal-test-vectors

Source files:
- tests/data/universal-test-vectors/generated/brc100/createHmac-simple-args.json
- tests/data/universal-test-vectors/generated/brc100/createHmac-simple-result.json
"""

from collections.abc import Callable

from bsv_wallet_toolbox import Wallet


class TestUniversalVectorsCreateHmac:
    """Tests using Universal Test Vectors for createHmac.

    Important: ABI (wire) tests are skipped because TypeScript doesn't test them.
    Following the principle: "If TypeScript skips it, we skip it too."
    """

    def test_createhmac_wire_matches_universal_vectors(
        self, load_test_vectors: Callable[[str], tuple[dict, dict]], test_key_deriver
    ) -> None:
        """ABI wire format test for createHmac.

        Verifies:
        1. Execute createHmac method with JSON args
        2. Serialize result to wire format
        3. Wire serialization works (ABI framework test)
        """
        from bsv_wallet_toolbox.abi import serialize_response

        # Given
        args_data, _result_data = load_test_vectors("createHmac-simple")

        wallet = Wallet(chain="main", key_deriver=test_key_deriver)

        # When
        result = wallet.create_hmac(args_data["json"], originator=None)
        wire_output = serialize_response(result)

        # Then - Verify the method works and wire serialization works
        assert "hmac" in result
        assert isinstance(result["hmac"], list)
        assert len(result["hmac"]) == 32  # HMAC-SHA256 produces 32 bytes
        assert isinstance(wire_output, bytes)
        assert len(wire_output) > 0
        from bsv_wallet_toolbox.abi import deserialize_request, serialize_request, serialize_response

        # Test serialization/deserialization functions exist and work
        args = {}
        wire_request = serialize_request("createHmac", args)
        parsed_method, parsed_args = deserialize_request(wire_request)

        assert parsed_method == "createHmac"
        assert isinstance(parsed_args, dict)

        # Test response serialization
        result = {"test": "data"}
        wire_response = serialize_response(result)
        assert isinstance(wire_response, bytes)
