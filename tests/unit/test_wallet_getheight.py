"""Unit tests for Wallet.get_height method.

Reference: toolbox/ts-wallet-toolbox/test/Wallet/get/getHeight.test.ts

Note: TypeScript tests require full wallet setup with chaintracks.
      Python tests use MockWalletServices for simplicity.
"""

import pytest

from bsv_wallet_toolbox import Wallet
from bsv_wallet_toolbox.services import MockWalletServices

# Test constant matching Universal Test Vectors
EXPECTED_HEIGHT = 850000


class TestGetHeightBasic:
    """Basic functionality tests for getHeight method."""

    @pytest.mark.asyncio
    async def test_returns_positive_height(self) -> None:
        """Given: Wallet with mock services
           When: Call getHeight
           Then: Returns positive height value

        Reference: TypeScript test "0 valid height"
        """
        # Given
        services = MockWalletServices(height=EXPECTED_HEIGHT)
        wallet = Wallet(services=services)

        # When
        result = await wallet.get_height({})

        # Then
        assert "height" in result
        assert result["height"] > 0
        assert result["height"] == EXPECTED_HEIGHT

    @pytest.mark.asyncio
    async def test_requires_services_configured(self) -> None:
        """Given: Wallet without services
        When: Call getHeight
        Then: Raises RuntimeError"""
        # Given
        wallet = Wallet()  # No services

        # When/Then
        with pytest.raises(RuntimeError, match="Services must be configured"):
            await wallet.get_height({})


class TestGetHeightWithOriginator:
    """Tests for getHeight with originator parameter."""

    @pytest.mark.asyncio
    async def test_accepts_valid_originator(self) -> None:
        """Given: Wallet with services and valid originator
        When: Call getHeight with originator
        Then: Returns height without error"""
        # Given
        services = MockWalletServices(height=EXPECTED_HEIGHT)
        wallet = Wallet(services=services)
        originator = "test.example.com"

        # When
        result = await wallet.get_height({}, originator=originator)

        # Then
        assert result["height"] == EXPECTED_HEIGHT
