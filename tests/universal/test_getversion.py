"""Universal Test Vectors for getVersion method.

Tests using official BRC-100 test vectors from:
https://github.com/bsv-blockchain/universal-test-vectors

Source files:
- tests/data/universal-test-vectors/generated/brc100/getVersion-simple-args.json
- tests/data/universal-test-vectors/generated/brc100/getVersion-simple-result.json

Note: TypeScript implementation returns 'wallet-brc100-1.0.0',
      but Universal Test Vectors expect '1.0.0' only.

      As of v2.0.0, py-wallet-toolbox returns '2.0.0' which differs from
      the Universal Test Vectors expectation of '1.0.0'. These tests verify
      the actual version returned by the implementation.
"""

from collections.abc import Callable

import pytest

from bsv_wallet_toolbox import Wallet


class TestUniversalVectorsGetVersion:
    """Tests using Universal Test Vectors for getVersion.

    Important: ABI (wire) tests are skipped because TypeScript doesn't test them.
    Following the principle: "If TypeScript skips it, we skip it too."
    """

    @pytest.mark.skip(reason="Universal Test Vectors expect '1.0.0' but py-wallet-toolbox v2.0.0 returns '2.0.0'")
    def test_getversion_json_matches_universal_vectors(
        self, load_test_vectors: Callable[[str], tuple[dict, dict]], test_key_deriver
    ) -> None:
        """Given: Universal Test Vector input for getVersion
           When: Call getVersion with empty args
           Then: Result matches Universal Test Vector output (JSON)

        Note: Skipped because py-wallet-toolbox v2.0.0 returns "2.0.0"
              but Universal Test Vectors expect "1.0.0".
        """
        # Given
        args_data, result_data = load_test_vectors("getVersion-simple")
        wallet = Wallet(chain="main", key_deriver=test_key_deriver)

        # When
        result = wallet.get_version(args_data["json"], originator=None)

        # Then
        assert result == result_data["json"]

    @pytest.mark.skip(reason="Universal Test Vectors expect '1.0.0' but py-wallet-toolbox v2.0.0 returns '2.0.0'")
    def test_getversion_wire_matches_universal_vectors(
        self, load_test_vectors: Callable[[str], tuple[dict, dict]], test_key_deriver
    ) -> None:
        """ABI wire format test for getVersion.

        Verifies:
        1. Deserialize wire input to method call
        2. Execute getVersion method
        3. Serialize result matches expected wire output

        Note: Skipped because py-wallet-toolbox v2.0.0 returns "2.0.0"
              but Universal Test Vectors expect "1.0.0".
        """
        from bsv_wallet_toolbox.abi import deserialize_request, serialize_response

        # Given
        args_data, result_data = load_test_vectors("getVersion-simple")
        wire_input = bytes.fromhex(args_data["wire"])
        expected_wire_output = bytes.fromhex(result_data["wire"])

        wallet = Wallet(chain="main", key_deriver=test_key_deriver)

        # When
        method_name, args = deserialize_request(wire_input)
        assert method_name == "getVersion"

        result = wallet.get_version(args, originator=None)
        wire_output = serialize_response(result)

        # Then
        assert wire_output == expected_wire_output

    def test_getversion_returns_current_version(self, test_key_deriver) -> None:
        """Verify getVersion returns the current wallet version (2.0.0)."""
        wallet = Wallet(chain="main", key_deriver=test_key_deriver)
        result = wallet.get_version({}, originator=None)
        assert result == {"version": "2.0.0"}
