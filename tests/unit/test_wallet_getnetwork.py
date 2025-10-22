"""Unit tests for Wallet.get_network method.

Ported from TypeScript implementation to ensure compatibility.

Reference: toolbox/ts-wallet-toolbox/test/Wallet/get/getNetwork.test.ts
"""

import pytest

from bsv_wallet_toolbox import Wallet


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

        Reference: toolbox/ts-wallet-toolbox/test/Wallet/get/getNetwork.test.ts
                   test('should return the correct network')
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

        Note: TypeScript only tests chain='test' (testnet).
              This test verifies mainnet behavior for completeness.
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

        Note: TypeScript does not test default chain behavior.
              This test verifies Python's default chain='main' parameter works correctly.
        """
        # Given
        wallet = Wallet()  # No chain specified, defaults to 'main'

        # When
        result = await wallet.get_network({})

        # Then
        assert result == {"network": "mainnet"}
