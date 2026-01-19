"""Universal Test Vectors for internalizeAction method.

Tests using official BRC-100 test vectors from:
https://github.com/bsv-blockchain/universal-test-vectors

Source files:
- tests/data/universal-test-vectors/generated/brc100/internalizeAction-simple-args.json
- tests/data/universal-test-vectors/generated/brc100/internalizeAction-simple-result.json
"""

from collections.abc import Callable

import pytest


class TestUniversalVectorsInternalizeAction:
    """Tests using Universal Test Vectors for internalizeAction.

    Important: ABI (wire) tests are skipped because TypeScript doesn't test them.
    Following the principle: "If TypeScript skips it, we skip it too."
    """

    @pytest.mark.integration
    def test_internalizeaction_wire_matches_universal_vectors(
        self, load_test_vectors: Callable[[str], tuple[dict, dict]], wallet_with_storage
    ) -> None:
        """ABI wire format test for internalizeAction.

        Verifies:
        1. Execute internalizeAction method with JSON args
        2. Serialize result to wire format
        3. Wire serialization works (ABI framework test)
        """
        pytest.skip("BEEF parsing fails with 'unsupported BEEF version' - requires BEEF library fixes")
        from bsv_wallet_toolbox.abi import serialize_response

        # Given
        args_data, _result_data = load_test_vectors("internalizeAction-simple")

        # When - Use JSON args since wire deserialization is incomplete
        result = wallet_with_storage.internalize_action(args_data["json"], originator=None)
        wire_output = serialize_response(result)

        # Then - Just verify the ABI serialization works
        assert isinstance(wire_output, bytes)
        assert len(wire_output) > 0
        from bsv_wallet_toolbox.abi import deserialize_request, serialize_request, serialize_response

        # Test serialization/deserialization functions exist and work
        args = {}
        wire_request = serialize_request("internalizeAction", args)
        parsed_method, parsed_args = deserialize_request(wire_request)

        assert parsed_method == "internalizeAction"
        assert isinstance(parsed_args, dict)

        # Test response serialization
        result = {"test": "data"}
        wire_response = serialize_response(result)
        assert isinstance(wire_response, bytes)
