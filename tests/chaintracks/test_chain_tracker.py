"""Unit tests for ChainTracker.

This module tests ChainTracker functionality for mainnet and testnet.

Reference: wallet-toolbox/src/services/chaintracker/__tests/ChaintracksChainTracker.test.ts
"""

import pytest

try:
    from bsv_wallet_toolbox.services.chaintracker import ChaintracksChainTracker

    IMPORTS_AVAILABLE = True
except ImportError:
    IMPORTS_AVAILABLE = False


@pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="ChaintracksChainTracker not available")
class TestChaintracksChainTracker:
    """Test suite for ChainTracker.

    Reference: wallet-toolbox/src/services/chaintracker/__tests/ChaintracksChainTracker.test.ts
               describe('ChaintracksChaintracker tests')
    """

    async def test_test(self) -> None:
        """Given: ChainTracker for testnet
           When: Get current height and verify merkle roots
           Then: Height > 877598, and validates testnet root correctly

        Reference: wallet-toolbox/src/services/chaintracker/__tests/ChaintracksChainTracker.test.ts
                   test('0 test')
        """
        # Note: TypeScript has `if (!includeTestChaintracks) return` here, which always skips this test.
        #       We removed this constant to make the test actually run when the API is implemented.

        # Note: This test just calls a helper function with no assertions in the test body itself.
        #       This matches TypeScript's structure: `await testChaintracksChaintracker('test')`
        #       All assertions are in the helper function _test_chaintracks_chaintracker().

        # Given/When/Then
        await self._test_chaintracks_chaintracker("test")

    async def test_main(self) -> None:
        """Given: ChainTracker for mainnet
           When: Get current height and verify merkle roots
           Then: Height > 877598, and validates mainnet root correctly

        Reference: wallet-toolbox/src/services/chaintracker/__tests/ChaintracksChainTracker.test.ts
                   test('1 main')
        """
        # Note: This test just calls a helper function with no assertions in the test body itself.
        #       This matches TypeScript's structure: `await testChaintracksChaintracker('main')`
        #       All assertions are in the helper function _test_chaintracks_chaintracker().

        # Given/When/Then
        await self._test_chaintracks_chaintracker("main")

    async def _test_chaintracks_chaintracker(self, chain: str) -> None:
        """Test ChainTracker for given chain.

        Reference: wallet-toolbox/src/services/chaintracker/__tests/ChaintracksChainTracker.test.ts
                   async function testChaintracksChaintracker(chain: sdk.Chain)
        """
        # Given
        tracker = ChaintracksChainTracker(chain)

        # When
        height = tracker.current_height()

        # Then
        assert height > 877598

        # When - Check mainnet root
        ok_main = tracker.is_valid_root_for_height(
            "2bf2edb5fa42aa773c6c13bc90e097b4e7de7ca1df2227f433be75ceace339e9", 877599
        )

        # Then
        assert ok_main == (chain == "main")

        # When - Check testnet root
        ok_test = tracker.is_valid_root_for_height(
            "5513f13554442588dd9acf395072bf1d2e7d5d360fbc42d3ab1fa2026b17c200", 1654265
        )

        # Then
        assert ok_test == (chain == "test")
