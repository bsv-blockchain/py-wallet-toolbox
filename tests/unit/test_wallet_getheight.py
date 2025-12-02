"""Unit tests for Wallet.get_height method.

Reference: wallet-toolbox/test/Wallet/get/getHeight.test.ts

Note: TypeScript tests require full wallet setup with chaintracks.
      Python tests use MockWalletServices for interface verification.
"""

import pytest

from bsv_wallet_toolbox import Wallet
from tests.conftest import MockWalletServices

# Test constant matching Universal Test Vectors
EXPECTED_HEIGHT = 850000


class TestGetHeightBasic:
    """Basic functionality tests for getHeight method."""

    def test_returns_positive_height(self, test_key_deriver) -> None:
        """Given: Wallet with mock services
           When: Call getHeight
           Then: Returns positive height value

        Reference: wallet-toolbox/test/Wallet/get/getHeight.test.ts
                   test('0 valid height')
        """
        # Given
        services = MockWalletServices(height=EXPECTED_HEIGHT)
        wallet = Wallet(chain="test", services=services, key_deriver=test_key_deriver)

        # When
        result = wallet.get_height({})

        # Then
        assert "height" in result
        assert result["height"] > 0
        assert result["height"] == EXPECTED_HEIGHT

    def test_requires_services_configured(self, test_key_deriver) -> None:
        """Given: Wallet without services
        When: Call getHeight
        Then: Raises RuntimeError

        Note: TypeScript does not test this error case (services always configured in tests).
              This test verifies Python's error handling when services are not configured.
        """
        # Given
        wallet = Wallet(chain="test", key_deriver=test_key_deriver)  # No services

        # When/Then
        with pytest.raises(RuntimeError, match="Services must be configured"):
            wallet.get_height({})


class TestGetHeightWithOriginator:
    """Tests for getHeight with originator parameter."""

    def test_accepts_valid_originator(self, test_key_deriver) -> None:
        """Given: Wallet with services and valid originator
        When: Call getHeight with originator
        Then: Returns height without error

        Note: TypeScript does not test originator parameter with getHeight.
              This test verifies Python's originator validation works correctly.
        """
        # Given
        services = MockWalletServices(height=EXPECTED_HEIGHT)
        wallet = Wallet(chain="test", services=services, key_deriver=test_key_deriver)
        originator = "test.example.com"

        # When
        result = wallet.get_height({}, originator=originator)

        # Then
        assert result["height"] == EXPECTED_HEIGHT
