"""Unit tests for Wallet.get_version method.

Ported from TypeScript implementation to ensure compatibility.

Reference: toolbox/ts-wallet-toolbox/test/Wallet/get/getVersion.test.ts
"""

import pytest

from bsv_wallet_toolbox import Wallet


class TestWalletGetVersion:
    """Test suite for Wallet.get_version method."""

    @pytest.mark.asyncio
    async def test_returns_correct_wallet_version(self) -> None:
        """Given: A wallet instance
           When: get_version is called
           Then: Returns the correct wallet version

        Reference: toolbox/ts-wallet-toolbox/test/Wallet/get/getVersion.test.ts
                   test('should return the correct wallet version')
        """
        # Given
        wallet = Wallet(chain="test")

        # When
        result = await wallet.get_version({})

        # Then
        assert result == {"version": Wallet.VERSION}
