"""Unit tests for Wallet.get_network method.

Ported from TypeScript implementation to ensure compatibility.

Reference: toolbox/ts-wallet-toolbox/test/Wallet/get/getNetwork.test.ts
"""

import pytest

from bsv_wallet_toolbox import Wallet
from bsv_wallet_toolbox.errors import InvalidParameterError


class TestGetNetworkBasic:
    """Basic functionality tests for getNetwork method.

    Reference: toolbox/ts-wallet-toolbox/test/Wallet/get/getNetwork.test.ts

    Note: TypeScript tests use chain='test' by default in test environment,
          so the primary test expects 'testnet'.
    """

    @pytest.mark.asyncio
    async def test_returns_testnet_for_test_chain(self) -> None:
        """Given: Wallet with chain='test' (matches TypeScript test setup)
           When: Call getNetwork
           Then: Returns 'testnet'

        Reference: TypeScript test creates wallet with chain='test' (line 805 in TestUtilsWalletStorage.ts)
        """
        # Given
        wallet = Wallet(chain="test")

        # When
        result = await wallet.get_network({})

        # Then
        assert result == {"network": "testnet"}

    @pytest.mark.asyncio
    async def test_returns_mainnet_for_main_chain(self) -> None:
        """Given: Wallet with chain='main'
        When: Call getNetwork
        Then: Returns 'mainnet'
        """
        # Given
        wallet = Wallet(chain="main")

        # When
        result = await wallet.get_network({})

        # Then
        assert result == {"network": "mainnet"}

    @pytest.mark.asyncio
    async def test_default_chain_is_mainnet(self) -> None:
        """Given: Wallet with no chain specified (default)
        When: Call getNetwork
        Then: Returns 'mainnet' (default)
        """
        # Given
        wallet = Wallet()  # No chain specified, defaults to 'main'

        # When
        result = await wallet.get_network({})

        # Then
        assert result == {"network": "mainnet"}


class TestGetNetworkOriginator:
    """Tests for originator parameter validation in getNetwork method."""

    @pytest.mark.asyncio
    async def test_with_valid_originator(self) -> None:
        """Given: Wallet and valid originator string
        When: Call getNetwork with originator
        Then: Returns network without error
        """
        # Given
        wallet = Wallet(chain="main")
        originator = "test.example.com"

        # When
        result = await wallet.get_network({}, originator=originator)

        # Then
        assert result == {"network": "mainnet"}
        # No exception raised

    @pytest.mark.asyncio
    async def test_with_invalid_originator_type(self) -> None:
        """Given: Wallet and non-string originator
        When: Call getNetwork with invalid originator type
        Then: Raises InvalidParameterError
        """
        # Given
        wallet = Wallet(chain="main")
        invalid_originator = 123  # Not a string

        # When/Then
        with pytest.raises(InvalidParameterError) as exc_info:
            await wallet.get_network({}, originator=invalid_originator)

        assert "originator" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_with_too_long_originator(self) -> None:
        """Given: Wallet and originator > 250 bytes
        When: Call getNetwork with too long originator
        Then: Raises InvalidParameterError
        """
        # Given
        wallet = Wallet(chain="main")
        too_long_originator = "a" * 251  # 251 bytes > 250

        # When/Then
        with pytest.raises(InvalidParameterError) as exc_info:
            await wallet.get_network({}, originator=too_long_originator)

        assert "originator" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_with_none_originator(self) -> None:
        """Given: Wallet and None originator
        When: Call getNetwork with originator=None
        Then: Returns network without error
        """
        # Given
        wallet = Wallet(chain="main")

        # When
        result = await wallet.get_network({}, originator=None)

        # Then
        assert result == {"network": "mainnet"}
        # No exception raised
