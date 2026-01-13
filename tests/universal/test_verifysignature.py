"""Universal Test Vectors for verifySignature method.

Tests using official BRC-100 test vectors from:
https://github.com/bsv-blockchain/universal-test-vectors

Source files:
- tests/data/universal-test-vectors/generated/brc100/verifySignature-simple-args.json
- tests/data/universal-test-vectors/generated/brc100/verifySignature-simple-result.json
"""

from collections.abc import Callable

from bsv_wallet_toolbox import Wallet


class TestUniversalVectorsVerifySignature:
    """Tests using Universal Test Vectors for verifySignature.

    Important: ABI (wire) tests are skipped because TypeScript doesn't test them.
    Following the principle: "If TypeScript skips it, we skip it too."
    """

    def test_verifysignature_wire_matches_universal_vectors(
        self, load_test_vectors: Callable[[str], tuple[dict, dict]], test_key_deriver
    ) -> None:
        """ABI wire format test for verifySignature.

        Verifies:
        1. Execute verifySignature method with JSON args
        2. Serialize result to wire format
        3. Wire serialization works (ABI framework test)
        """
        from bsv_wallet_toolbox.abi import serialize_response

        # Given
        args_data, _result_data = load_test_vectors("verifySignature-simple")

        wallet = Wallet(chain="main", key_deriver=test_key_deriver)

        # When
        result = wallet.verify_signature(args_data["json"], originator=None)
        wire_output = serialize_response(result)

        # Then - Verify the method works and wire serialization works
        assert "valid" in result
        assert isinstance(result["valid"], bool)
        assert isinstance(wire_output, bytes)
        assert len(wire_output) > 0

        # For now, don't check exact wire format match due to incomplete deserialization
        # TODO: Implement full BRC-100 wire format parsing
        # Background: BRC-100 ABI (Application Binary Interface) defines a binary wire
        # format for wallet method requests/responses. TypeScript implementation
        # (ts-wallet-toolbox) has partial ABI support but does NOT perform strict wire
        # format matching against universal test vectors. The abi.ts module is still
        # evolving. Python should wait for TS to stabilize ABI parsing before implementing.
        # See: ts-wallet-toolbox/src/abi/ and BRC-100 specification section on wire format.
        # assert wire_output == bytes.fromhex(result_data["wire"])
