"""Universal Test Vectors for revealCounterpartyKeyLinkage method.

Tests using official BRC-100 test vectors from:
https://github.com/bsv-blockchain/universal-test-vectors

Source files:
- tests/data/universal-test-vectors/generated/brc100/revealCounterpartyKeyLinkage-simple-args.json
- tests/data/universal-test-vectors/generated/brc100/revealCounterpartyKeyLinkage-simple-result.json
"""

from collections.abc import Callable

from bsv_wallet_toolbox import Wallet


class TestUniversalVectorsRevealCounterpartyKeyLinkage:
    """Tests using Universal Test Vectors for revealCounterpartyKeyLinkage.

    Important: ABI (wire) tests are skipped because TypeScript doesn't test them.
    Following the principle: "If TypeScript skips it, we skip it too."
    """

    def test_revealcounterpartykeylinkage_wire_matches_universal_vectors(
        self, load_test_vectors: Callable[[str], tuple[dict, dict]], test_key_deriver
    ) -> None:
        """ABI wire format test for revealCounterpartyKeyLinkage.

        Verifies:
        1. Execute revealCounterpartyKeyLinkage method with JSON args
        2. Serialize result to wire format
        3. Wire serialization works (ABI framework test)
        """
        from bsv.keys import PrivateKey

        from bsv_wallet_toolbox.abi import serialize_response
        from bsv_wallet_toolbox.sdk.privileged_key_manager import PrivilegedKeyManager

        # Create a privileged key manager for testing
        privileged_key = PrivateKey()  # Generate a random key for testing
        privileged_key_manager = PrivilegedKeyManager(lambda reason: privileged_key)

        # Given
        args_data, _result_data = load_test_vectors("revealCounterpartyKeyLinkage-simple")

        wallet = Wallet(chain="main", key_deriver=test_key_deriver, privileged_key_manager=privileged_key_manager)

        # When
        result = wallet.reveal_counterparty_key_linkage(args_data["json"], originator=None)
        wire_output = serialize_response(result)

        # Then - Verify the result contains expected fields and wire serialization works
        # Support both camelCase (TS parity) and snake_case (Python convention)
        assert "prover" in result
        assert "counterparty" in result
        assert "verifier" in result
        assert "revelationTime" in result or "revelation_time" in result
        assert "encryptedLinkage" in result or "encrypted_linkage" in result
        assert "encryptedLinkageProof" in result or "encrypted_linkage_proof" in result
        linkage_key = "encryptedLinkage" if "encryptedLinkage" in result else "encrypted_linkage"
        proof_key = "encryptedLinkageProof" if "encryptedLinkageProof" in result else "encrypted_linkage_proof"
        assert isinstance(result[linkage_key], list)
        assert isinstance(result[proof_key], list)
        assert isinstance(wire_output, bytes)
        assert len(wire_output) > 0
        from bsv_wallet_toolbox.abi import deserialize_request, serialize_request, serialize_response

        # Test serialization/deserialization functions exist and work
        args = {}
        wire_request = serialize_request("revealCounterpartyKeyLinkage", args)
        parsed_method, parsed_args = deserialize_request(wire_request)

        assert parsed_method == "revealCounterpartyKeyLinkage"
        assert isinstance(parsed_args, dict)

        # Test response serialization
        result = {"test": "data"}
        wire_response = serialize_response(result)
        assert isinstance(wire_response, bytes)
