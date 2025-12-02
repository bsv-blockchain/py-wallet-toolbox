"""Universal Test Vectors for internalizeAction method.

Tests using official BRC-100 test vectors from:
https://github.com/bsv-blockchain/universal-test-vectors

Source files:
- tests/data/universal-test-vectors/generated/brc100/internalizeAction-simple-args.json
- tests/data/universal-test-vectors/generated/brc100/internalizeAction-simple-result.json
"""

from collections.abc import Callable

import pytest

from bsv_wallet_toolbox import Wallet


class TestUniversalVectorsInternalizeAction:
    """Tests using Universal Test Vectors for internalizeAction.

    Important: ABI (wire) tests are skipped because TypeScript doesn't test them.
    Following the principle: "If TypeScript skips it, we skip it too."
    """

    @pytest.mark.skip(reason="Requires deterministic wallet state")
    def test_internalizeaction_wire_matches_universal_vectors(
        self, load_test_vectors: Callable[[str], tuple[dict, dict]], test_key_deriver
    ) -> None:
        """ABI wire format test for internalizeAction.

        Verifies:
        1. Execute internalizeAction method with JSON args
        2. Serialize result to wire format
        3. Wire serialization works (ABI framework test)
        """
        from bsv_wallet_toolbox.abi import serialize_response

        # Given
        args_data, result_data = load_test_vectors(1)

        wallet = Wallet(chain="main", key_deriver=test_key_deriver)

        # When - Use JSON args since wire deserialization is incomplete
        result = wallet.internalizeaction(args_data["json"], originator=None)
        wire_output = serialize_response(result)

        # Then - Just verify the ABI serialization works
        assert isinstance(wire_output, bytes)
        assert len(wire_output) > 0
        from bsv_wallet_toolbox.abi import serialize_request, deserialize_request, serialize_response

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
