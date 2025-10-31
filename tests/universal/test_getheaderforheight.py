"""Universal Test Vectors for getHeaderForHeight.

Reference: https://github.com/bsv-blockchain/universal-test-vectors
"""

from collections.abc import Callable

import pytest

from bsv_wallet_toolbox import Wallet
from tests.conftest import MockWalletServices

# Block header is 80 bytes = 160 hex characters
BLOCK_HEADER_HEX_LENGTH = 160


class TestUniversalVectorsGetHeaderForHeight:
    """Test getHeaderForHeight using Universal Test Vectors."""

    def test_getheaderforheight_json_matches_universal_vectors(
        self, load_test_vectors: Callable[[str], tuple[dict, dict]]
    ) -> None:
        """Given: Universal Test Vector input for getHeaderForHeight
        When: Call getHeaderForHeight with height from args
        Then: Result matches Universal Test Vector output (JSON)"""
        # Given
        args_data, result_data = load_test_vectors("getHeaderForHeight-simple")
        # Mock services returning the expected header from Universal Test Vectors
        expected_header_hex = result_data["json"]["header"]
        header_bytes = bytes.fromhex(expected_header_hex)
        services = MockWalletServices(height=850000, header=header_bytes)
        wallet = Wallet(chain="main", services=services)

        # When
        result = wallet.get_header_for_height(args_data["json"], originator=None)

        # Then
        assert result == result_data["json"]
        assert result["header"] == expected_header_hex
        # Verify it's a valid 80-byte header (160 hex chars)
        assert len(result["header"]) == BLOCK_HEADER_HEX_LENGTH

    @pytest.mark.skip(reason="ABI tests skipped - TypeScript doesn't test ABI wire format")
    def test_getheaderforheight_wire_matches_universal_vectors(
        self, load_test_vectors: Callable[[str], tuple[dict, dict]]
    ) -> None:
        """ABI wire format test (skipped for now)."""
