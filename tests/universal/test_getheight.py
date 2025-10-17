"""Universal Test Vectors for getHeight.

Reference: https://github.com/bsv-blockchain/universal-test-vectors
"""

from collections.abc import Callable

import pytest

from bsv_wallet_toolbox import Wallet
from bsv_wallet_toolbox.services import MockWalletServices

# Expected height from Universal Test Vectors
EXPECTED_HEIGHT = 850000


class TestUniversalVectorsGetHeight:
    """Test getHeight using Universal Test Vectors."""

    @pytest.mark.asyncio
    async def test_getheight_json_matches_universal_vectors(
        self, load_test_vectors: Callable[[str], tuple[dict, dict]]
    ) -> None:
        """Given: Universal Test Vector input for getHeight
        When: Call getHeight with empty args
        Then: Result matches Universal Test Vector output (JSON)"""
        # Given
        args_data, result_data = load_test_vectors("getHeight-simple")
        # Mock services returning the expected height from Universal Test Vectors
        services = MockWalletServices(height=result_data["json"]["height"])
        wallet = Wallet(services=services)

        # When
        result = await wallet.get_height(args_data["json"], originator=None)

        # Then
        assert result == result_data["json"]
        assert result["height"] == EXPECTED_HEIGHT

    @pytest.mark.skip(reason="ABI tests skipped - TypeScript doesn't test ABI wire format")
    async def test_getheight_wire_matches_universal_vectors(
        self, load_test_vectors: Callable[[str], tuple[dict, dict]]
    ) -> None:
        """Given: Universal Test Vector input for getHeight (wire format)
        When: Serialize and deserialize using wire protocol
        Then: Result matches Universal Test Vector output (wire)"""
