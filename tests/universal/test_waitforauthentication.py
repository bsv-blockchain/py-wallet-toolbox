"""Universal Test Vectors for waitForAuthentication method.

Tests using official BRC-100 test vectors from:
https://github.com/bsv-blockchain/universal-test-vectors

Source files:
- tests/data/universal-test-vectors/generated/brc100/waitForAuthentication-simple-args.json
- tests/data/universal-test-vectors/generated/brc100/waitForAuthentication-simple-result.json
"""

from collections.abc import Callable

import pytest

from bsv_wallet_toolbox import Wallet


class TestUniversalVectorsWaitForAuthentication:
    """Tests using Universal Test Vectors for waitForAuthentication.

    Important: ABI (wire) tests are skipped because TypeScript doesn't test them.
    Following the principle: "If TypeScript skips it, we skip it too."
    """

    @pytest.mark.asyncio
    async def test_waitforauthentication_json_matches_universal_vectors(
        self, load_test_vectors: Callable[[str], tuple[dict, dict]]
    ) -> None:
        """Given: Universal Test Vector input for waitForAuthentication
           When: Call waitForAuthentication with empty args
           Then: Result matches Universal Test Vector output (JSON)

        Note: Universal Test Vectors expect authenticated=true.
        """
        # Given
        args_data, result_data = load_test_vectors("waitForAuthentication-simple")
        wallet = Wallet(chain="main")

        # When
        result = await wallet.wait_for_authentication(args_data["json"], originator=None)

        # Then
        assert result == result_data["json"]
        assert result["authenticated"] is True

    @pytest.mark.skip(reason="ABI tests skipped - TypeScript doesn't test ABI wire format")
    @pytest.mark.asyncio
    async def test_waitforauthentication_wire_matches_universal_vectors(
        self, load_test_vectors: Callable[[str], tuple[dict, dict]]
    ) -> None:
        """ABI (wire) test - skipped because TypeScript doesn't test this.

        This test would verify:
        1. Deserialize wire input: "1800" -> method + args
        2. Execute waitForAuthentication
        3. Serialize result -> matches "00"

        Following the principle: "If TypeScript skips it, we skip it too."
        """
