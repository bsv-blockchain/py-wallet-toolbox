"""Universal Test Vectors for isAuthenticated method.

Tests using official BRC-100 test vectors from:
https://github.com/bsv-blockchain/universal-test-vectors

Source files:
- tests/data/universal-test-vectors/generated/brc100/isAuthenticated-simple-args.json
- tests/data/universal-test-vectors/generated/brc100/isAuthenticated-simple-result.json
"""

from collections.abc import Callable

import pytest

from bsv_wallet_toolbox import Wallet


class TestUniversalVectorsIsAuthenticated:
    """Tests using Universal Test Vectors for isAuthenticated.

    Important: ABI (wire) tests are skipped because TypeScript doesn't test them.
    Following the principle: "If TypeScript skips it, we skip it too."
    """

    @pytest.mark.asyncio
    async def test_isauthenticated_json_matches_universal_vectors(
        self, load_test_vectors: Callable[[str], tuple[dict, dict]]
    ) -> None:
        """Given: Universal Test Vector input for isAuthenticated
           When: Call isAuthenticated with empty args
           Then: Result matches Universal Test Vector output (JSON)

        Note: Universal Test Vectors expect authenticated=true.
        """
        # Given
        args_data, result_data = load_test_vectors("isAuthenticated-simple")
        wallet = Wallet(chain="main")

        # When
        result = await wallet.is_authenticated(args_data["json"], originator=None)

        # Then
        assert result == result_data["json"]
        assert result["authenticated"] is True

    @pytest.mark.skip(reason="ABI tests skipped - TypeScript doesn't test ABI wire format")
    @pytest.mark.asyncio
    async def test_isauthenticated_wire_matches_universal_vectors(
        self, load_test_vectors: Callable[[str], tuple[dict, dict]]
    ) -> None:
        """ABI (wire) test - skipped because TypeScript doesn't test this.

        This test would verify:
        1. Deserialize wire input: "1700" -> method + args
        2. Execute isAuthenticated
        3. Serialize result -> matches "0001"

        Following the principle: "If TypeScript skips it, we skip it too."
        """
