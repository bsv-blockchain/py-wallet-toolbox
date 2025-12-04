"""Unit tests for Wallet.get_network method.

Ported from TypeScript implementation to ensure compatibility.

Reference: wallet-toolbox/test/Wallet/get/getNetwork.test.ts
"""

from bsv_wallet_toolbox import Wallet


class TestWalletGetNetwork:
    """Test suite for Wallet.get_network method."""

    def test_returns_testnet_for_test_chain(self, test_key_deriver) -> None:
        """Given: Wallet with chain='test'
           When: Call getNetwork
           Then: Returns 'testnet'

        Reference: wallet-toolbox/test/Wallet/get/getNetwork.test.ts
                   test('should return the correct network')

        Note: TypeScript tests use chain='test' by default in test environment.
        """
        # Given
        wallet = Wallet(chain="test", key_deriver=test_key_deriver)

        # When
        result = wallet.get_network({})

        # Then
        assert result == {"network": "testnet"}

    def test_returns_mainnet_for_main_chain(self, test_key_deriver) -> None:
        """Given: Wallet with chain='main'
           When: Call getNetwork
           Then: Returns 'mainnet'

        Note: Python-specific test (TypeScript does not have this test).
              TypeScript does not test mainnet case (test environment uses chain='test' only).
              This test verifies that chain='main' correctly maps to network='mainnet'.
              Both chain values ('main' and 'test') should be tested for completeness.
        """
        # Given
        wallet = Wallet(chain="main", key_deriver=test_key_deriver)

        # When
        result = wallet.get_network({})

        # Then
        assert result == {"network": "mainnet"}
