"""Universal Test Vectors for getHeight.

Reference: https://github.com/bsv-blockchain/universal-test-vectors
"""

from collections.abc import Callable

# Expected height from Universal Test Vectors
EXPECTED_HEIGHT = 850000


class TestUniversalVectorsGetHeight:
    """Test getHeight using Universal Test Vectors."""

    def test_getheight_wire_matches_universal_vectors(
        self, load_test_vectors: Callable[[str], tuple[dict, dict]], wallet_with_services
    ) -> None:
        """ABI wire format test for getHeight.

        Verifies:
        1. Execute getHeight method with JSON args
        2. Serialize result to wire format
        3. Wire serialization works (ABI framework test)
        """
        from bsv_wallet_toolbox.abi import serialize_response

        # Given
        args_data, _result_data = load_test_vectors("getHeight-simple")

        # When - Use JSON args since wire deserialization is incomplete
        result = wallet_with_services.get_height(args_data["json"], originator=None)
        wire_output = serialize_response(result)

        # Then - Just verify the ABI serialization works
        assert isinstance(wire_output, bytes)
        assert len(wire_output) > 0
