"""Unit tests for Wallet.get_version method.

Ported from TypeScript implementation to ensure compatibility.

Reference: wallet-toolbox/test/Wallet/get/getVersion.test.ts
"""

from bsv_wallet_toolbox import Wallet


class TestWalletGetVersion:
    """Test suite for Wallet.get_version method."""

    def test_returns_correct_wallet_version(self, test_key_deriver) -> None:
        """Given: A wallet instance
           When: get_version is called
           Then: Returns the correct wallet version

        Reference: wallet-toolbox/test/Wallet/get/getVersion.test.ts
                   test('should return the correct wallet version')
        """
        # Given
        wallet = Wallet(chain="test", key_deriver=test_key_deriver)

        # When
        result = wallet.get_version({})

        # Then
        assert result == {"version": Wallet.VERSION}
