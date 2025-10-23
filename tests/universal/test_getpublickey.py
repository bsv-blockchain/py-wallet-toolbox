"""Universal Test Vectors for getPublicKey method.

Tests using official BRC-100 test vectors from:
https://github.com/bsv-blockchain/universal-test-vectors

Source files:
- tests/data/universal-test-vectors/generated/brc100/getPublicKey-simple-args.json
- tests/data/universal-test-vectors/generated/brc100/getPublicKey-simple-result.json
"""

from collections.abc import Callable

import pytest

from bsv_wallet_toolbox import Wallet


class TestUniversalVectorsGetPublicKey:
    """Tests using Universal Test Vectors for getPublicKey.

    Important: ABI (wire) tests are skipped because TypeScript doesn't test them.
    Following the principle: "If TypeScript skips it, we skip it too."
    """

    @pytest.mark.skip(reason="Waiting for get_public_key implementation")
    @pytest.mark.asyncio
    async def test_getpublickey_json_matches_universal_vectors(
        self, load_test_vectors: Callable[[str], tuple[dict, dict]]
    ) -> None:
        """Given: Universal Test Vector input for getPublicKey
           When: Call getPublicKey with protocolID, keyID, counterparty, etc.
           Then: Result matches Universal Test Vector output (JSON)

        Note: This test is currently skipped because get_public_key is not yet implemented.
              Expected input:
              - protocolID: [2, "tests"]
              - keyID: "test-key-id"
              - counterparty: "0294c479f762f6baa97fbcd4393564c1d7bd8336ebd15928135bbcf575cd1a71a1"
              - privileged: true
              - privilegedReason: "privileged reason"
              - seekPermission: true

              Expected output:
              - publicKey: "025ad43a22ac38d0bc1f8bacaabb323b5d634703b7a774c4268f6a09e4ddf79097"
        """
        # Given
        args_data, result_data = load_test_vectors("getPublicKey-simple")
        wallet = Wallet(chain="main")

        # When
        result = await wallet.get_public_key(args_data["json"], originator=None)

        # Then
        assert result == result_data["json"]
        assert "publicKey" in result
        assert result["publicKey"] == "025ad43a22ac38d0bc1f8bacaabb323b5d634703b7a774c4268f6a09e4ddf79097"

    @pytest.mark.skip(reason="ABI tests skipped - TypeScript doesn't test ABI wire format")
    @pytest.mark.asyncio
    async def test_getpublickey_wire_matches_universal_vectors(
        self, load_test_vectors: Callable[[str], tuple[dict, dict]]
    ) -> None:
        """ABI (wire) test - skipped because TypeScript doesn't test this.

        This test would verify:
        1. Deserialize wire input: "080000020574657374..." -> method + args
        2. Execute getPublicKey
        3. Serialize result -> matches "00025ad43a22ac38d0bc1f8bacaabb323b5d634703b7a774c4268f6a09e4ddf79097"

        Following the principle: "If TypeScript skips it, we skip it too."
        """

