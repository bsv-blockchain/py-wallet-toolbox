"""Universal Test Vectors for discoverByIdentityKey method.

Tests using official BRC-100 test vectors from:
https://github.com/bsv-blockchain/universal-test-vectors

Source files:
- tests/data/universal-test-vectors/generated/brc100/discoverByIdentityKey-simple-args.json
- tests/data/universal-test-vectors/generated/brc100/discoverByIdentityKey-simple-result.json
"""

from collections.abc import Callable

import pytest

from bsv_wallet_toolbox import Wallet


class TestUniversalVectorsDiscoverByIdentityKey:
    """Tests using Universal Test Vectors for discoverByIdentityKey.

    Important: ABI (wire) tests are skipped because TypeScript doesn't test them.
    Following the principle: "If TypeScript skips it, we skip it too."
    """

    @pytest.mark.skip(reason="Waiting for discover_by_identity_key implementation")
    @pytest.mark.asyncio
    async def test_discoverbyidentitykey_json_matches_universal_vectors(
        self, load_test_vectors: Callable[[str], tuple[dict, dict]]
    ) -> None:
        """Given: Universal Test Vector input for discoverByIdentityKey
        When: Call discoverByIdentityKey
        Then: Result matches Universal Test Vector output (JSON)
        """
        # Given
        args_data, result_data = load_test_vectors("discoverByIdentityKey-simple")
        wallet = Wallet(chain="main")

        # When
        result = await wallet.discover_by_identity_key(args_data["json"], originator=None)

        # Then
        assert result == result_data["json"]

    @pytest.mark.skip(reason="ABI tests skipped - TypeScript doesn't test ABI wire format")
    @pytest.mark.asyncio
    async def test_discoverbyidentitykey_wire_matches_universal_vectors(
        self, load_test_vectors: Callable[[str], tuple[dict, dict]]
    ) -> None:
        """ABI (wire) test - skipped because TypeScript doesn't test this."""
