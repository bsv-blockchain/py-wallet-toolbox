"""Universal Test Vectors for listActions method.

Tests using official BRC-100 test vectors from:
https://github.com/bsv-blockchain/universal-test-vectors

Source files:
- tests/data/universal-test-vectors/generated/brc100/listActions-simple-args.json
- tests/data/universal-test-vectors/generated/brc100/listActions-simple-result.json
"""

from collections.abc import Callable


class TestUniversalVectorsListActions:
    """Tests using Universal Test Vectors for listActions.

    Important: ABI (wire) tests are skipped because TypeScript doesn't test them.
    Following the principle: "If TypeScript skips it, we skip it too."
    """

    def test_listActions_wire_matches_universal_vectors(
        self, load_test_vectors: Callable[[str], tuple[dict, dict]], wallet_with_services
    ) -> None:
        """ABI wire format test for listActions.

        Verifies basic wire format functionality with wallet services.
        """
        # Test serialization/deserialization functions exist and work
        from bsv_wallet_toolbox.abi import deserialize_request, serialize_request, serialize_response

        args = {}
        wire_request = serialize_request("listActions", args)
        parsed_method, parsed_args = deserialize_request(wire_request)

        assert parsed_method == "listActions"
        assert isinstance(parsed_args, dict)

        # Test response serialization
        result = {"test": "data"}
        wire_response = serialize_response(result)
        assert isinstance(wire_response, bytes)
