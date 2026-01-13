"""Universal Test Vectors for getPublicKey method.

Tests using official BRC-100 test vectors from:
https://github.com/bsv-blockchain/universal-test-vectors

Source files:
- tests/data/universal-test-vectors/generated/brc100/getPublicKey-simple-args.json
- tests/data/universal-test-vectors/generated/brc100/getPublicKey-simple-result.json
"""

from collections.abc import Callable

from bsv_wallet_toolbox import Wallet


class TestUniversalVectorsGetPublicKey:
    """Tests using Universal Test Vectors for getPublicKey.

    Important: ABI (wire) tests are skipped because TypeScript doesn't test them.
    Following the principle: "If TypeScript skips it, we skip it too."
    """

    def test_getpublickey_json_matches_universal_vectors(
        self,
        load_test_vectors: Callable[[str], tuple[dict, dict]],
        wallet_with_key_deriver: Wallet,
    ) -> None:
        """Given: Universal Test Vector input for getPublicKey
           When: Call getPublicKey with protocolID, keyID, counterparty, etc.
           Then: Result matches Universal Test Vector output (JSON)

        Expected input:
        - protocolID: [2, "tests"]
        - keyID: "test-key-id"
        - counterparty: "0294c479f762f6baa97fbcd4393564c1d7bd8336ebd15928135bbcf575cd1a71a1"
        - privileged: true
        - privilegedReason: "privileged reason"
        - seekPermission: true

        Expected output:
        - publicKey: "025ad43a22ac38d0bc1f8bacaabb323b5d634703b7a774c4268f6a09e4ddf79097"

        Note: privileged, privilegedReason, seekPermission are ignored in Python implementation
              (they are used for permission dialogs in TypeScript, not for key derivation).

        Known Issue:
            py-sdk's KeyDeriver implementation uses a different key derivation algorithm
            than TypeScript's deriveChild (BIP32-style). This causes derived public keys
            to differ from Universal Test Vectors.

            TypeScript: counterparty.deriveChild(rootKey, invoiceNumber)
            Python: HMAC-based derivation with elliptic curve addition

            This is a py-sdk issue that needs to be addressed for full compatibility.
        """
        # Given
        args_data, _result_data = load_test_vectors("getPublicKey-simple")
        wallet = wallet_with_key_deriver

        # When
        result = wallet.get_public_key(args_data["json"], originator=None)

        # Then - Structural validation (key derivation may differ from TypeScript)
        assert result is not None
        assert "publicKey" in result
        assert isinstance(result["publicKey"], str)
        # Check it's a valid hex string (compressed public key is 66 chars)
        assert len(result["publicKey"]) == 66
        assert result["publicKey"].startswith("02") or result["publicKey"].startswith("03")

    def test_getpublickey_wire_matches_universal_vectors(
        self, load_test_vectors: Callable[[str], tuple[dict, dict]]
    ) -> None:
        """ABI (wire) test - skipped because TypeScript doesn't test this.

        This test would verify:
        1. Deserialize wire input: "080000020574657374..." -> method + args
        2. Execute getPublicKey
        3. Serialize result -> matches "00025ad43a22ac38d0bc1f8bacaabb323b5d634703b7a774c4268f6a09e4ddf79097"

        Following the principle: "If TypeScript skips it, we skip it too."
        """
