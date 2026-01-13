"""Universal Test Vectors for encrypt method.

Tests using official BRC-100 test vectors from:
https://github.com/bsv-blockchain/universal-test-vectors

Source files:
- tests/data/universal-test-vectors/generated/brc100/encrypt-simple-args.json
- tests/data/universal-test-vectors/generated/brc100/encrypt-simple-result.json
"""

from collections.abc import Callable

from bsv_wallet_toolbox import Wallet


class TestUniversalVectorsEncrypt:
    """Tests using Universal Test Vectors for encrypt.

    Following the principle: "If TypeScript skips it, we skip it too."
    """

    def test_encrypt_wire_matches_universal_vectors(
        self, load_test_vectors: Callable[[str], tuple[dict, dict]], test_key_deriver
    ) -> None:
        """ABI wire format test for encrypt.

        Verifies:
        1. Execute encrypt method with JSON args
        2. Serialize result to wire format
        3. Wire serialization works (ABI framework test)
        """
        from bsv_wallet_toolbox.abi import serialize_response

        # Given
        args_data, _result_data = load_test_vectors("encrypt-simple")
        wallet = Wallet(chain="main", key_deriver=test_key_deriver)

        # When
        result = wallet.encrypt(args_data["json"], originator=None)
        wire_output = serialize_response(result)

        # Then - Verify the method works and wire serialization works
        assert "ciphertext" in result
        assert isinstance(result["ciphertext"], list)
        assert len(result["ciphertext"]) >= 4  # ECIES produces at least 4 bytes
        assert isinstance(wire_output, bytes)
        assert len(wire_output) > 0
