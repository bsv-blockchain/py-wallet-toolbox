"""Unit tests for Wallet.get_header_for_height method.

Reference: wallet-toolbox/test/Wallet/get/getHeaderForHeight.test.ts

Note: TypeScript tests require full wallet setup with chaintracks.
      Python tests use MockWalletServices for interface verification.
"""

import pytest

from bsv_wallet_toolbox import InvalidParameterError, Wallet
from tests.conftest import MockWalletServices

# Test constant matching Universal Test Vectors
EXPECTED_HEIGHT = 850000
# Genesis block header (block 0) - 80 bytes = 160 hex characters
GENESIS_HEADER_HEX = (
    "0100000000000000000000000000000000000000000000000000000000000000"
    "000000003ba3edfd7a7b12b27ac72c3e67768f617fc81bc3888a51323a9fb8aa"
    "4b1e5e4a29ab5f49ffff001d1dac2b7c"
)
BLOCK_HEADER_HEX_LENGTH = 160  # 80 bytes * 2 hex chars per byte


class TestGetHeaderForHeightBasic:
    """Basic functionality tests for getHeaderForHeight method."""

    def test_returns_valid_header_string(self, test_key_deriver) -> None:
        """Given: Wallet with mock services
           When: Call getHeaderForHeight with valid height
           Then: Returns header as non-empty hex string

        Reference: wallet-toolbox/test/Wallet/get/getHeaderForHeight.test.ts
                   test('1 valid block height')
        """
        # Given
        header_bytes = bytes.fromhex(GENESIS_HEADER_HEX)
        services = MockWalletServices(height=EXPECTED_HEIGHT, header=header_bytes)
        wallet = Wallet(chain="test", services=services, key_deriver=test_key_deriver)

        # When
        result = wallet.get_header_for_height({"height": 1})

        # Then
        assert "header" in result
        assert isinstance(result["header"], str)
        assert len(result["header"]) > 0
        # Block header is 80 bytes = 160 hex characters
        assert len(result["header"]) == BLOCK_HEADER_HEX_LENGTH

    def test_requires_services_configured(self, test_key_deriver) -> None:
        """Given: Wallet without services
        When: Call getHeaderForHeight
        Then: Raises RuntimeError

        Note: TypeScript does not test this error case (services always configured in tests).
              This test verifies Python's error handling when services are not configured.
        """
        # Given
        wallet = Wallet(chain="test", key_deriver=test_key_deriver)

        # When / Then
        with pytest.raises(RuntimeError, match="Services must be configured"):
            wallet.get_header_for_height({"height": 1})


class TestGetHeaderForHeightValidation:
    """Parameter validation tests for getHeaderForHeight method."""

    def test_raises_error_for_negative_height(self, test_key_deriver) -> None:
        """Given: Wallet with services and negative height
           When: Call getHeaderForHeight with height: -1
           Then: Raises InvalidParameterError

        Reference: wallet-toolbox/test/Wallet/get/getHeaderForHeight.test.ts
                   test('0 invalid params')
        """
        # Given
        services = MockWalletServices(height=EXPECTED_HEIGHT)
        wallet = Wallet(chain="test", services=services, key_deriver=test_key_deriver)

        # When / Then
        with pytest.raises(InvalidParameterError, match="height"):
            wallet.get_header_for_height({"height": -1})

    def test_raises_error_for_missing_height(self, test_key_deriver) -> None:
        """Given: Wallet with services and missing height parameter
           When: Call getHeaderForHeight without height
           Then: Raises InvalidParameterError

        Note: TypeScript does not test missing height parameter.
              This test verifies Python's parameter validation for required fields.
        """
        # Given
        services = MockWalletServices(height=EXPECTED_HEIGHT)
        wallet = Wallet(chain="test", services=services, key_deriver=test_key_deriver)

        # When / Then
        with pytest.raises(InvalidParameterError, match="height"):
            wallet.get_header_for_height({})

    def test_raises_error_for_invalid_height_type(self, test_key_deriver) -> None:
        """Given: Wallet with services and non-integer height
           When: Call getHeaderForHeight with invalid height type
           Then: Raises InvalidParameterError

        Note: TypeScript does not test invalid height type.
              This test verifies Python's type validation for height parameter.
        """
        # Given
        services = MockWalletServices(height=EXPECTED_HEIGHT)
        wallet = Wallet(chain="test", services=services, key_deriver=test_key_deriver)
        invalid_height = "not_a_number"

        # When / Then
        with pytest.raises(InvalidParameterError, match="height"):
            wallet.get_header_for_height({"height": invalid_height})

    def test_accepts_zero_height(self, test_key_deriver) -> None:
        """Given: Wallet with services and height 0 (genesis block)
           When: Call getHeaderForHeight with height: 0
           Then: Returns valid header (genesis block)

        Note: TypeScript does not test height=0 (genesis block).
              This test verifies Python correctly handles the boundary case of height=0.
        """
        # Given
        header_bytes = bytes.fromhex(GENESIS_HEADER_HEX)
        services = MockWalletServices(height=EXPECTED_HEIGHT, header=header_bytes)
        wallet = Wallet(chain="test", services=services, key_deriver=test_key_deriver)

        # When
        result = wallet.get_header_for_height({"height": 0})

        # Then
        assert "header" in result
        assert result["header"] == GENESIS_HEADER_HEX


class TestGetHeaderForHeightIntegration:
    """Integration tests for getHeaderForHeight method."""

    def test_returns_correct_header_format(self, test_key_deriver) -> None:
        """Given: Wallet with mock services returning known header
           When: Call getHeaderForHeight
           Then: Returns header matching expected format

        Reference: wallet-toolbox/test/Wallet/get/getHeaderForHeight.test.ts
                   test('3 valid block height always returns a header')
        """
        # Given
        header_bytes = bytes.fromhex(GENESIS_HEADER_HEX)
        services = MockWalletServices(height=EXPECTED_HEIGHT, header=header_bytes)
        wallet = Wallet(chain="test", services=services, key_deriver=test_key_deriver)

        # When
        result = wallet.get_header_for_height({"height": 9999})

        # Then
        assert result["header"] == GENESIS_HEADER_HEX
