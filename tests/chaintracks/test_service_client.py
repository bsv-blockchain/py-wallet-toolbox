"""Unit tests for ChaintracksServiceClient.

This module tests ChaintracksServiceClient functionality for mainnet and testnet.

Reference: wallet-toolbox/src/services/chaintracker/__tests/ChaintracksServiceClient.test.ts
"""

import pytest

try:
    from bsv_wallet_toolbox.services.chaintracker import ChaintracksServiceClient

    IMPORTS_AVAILABLE = True
except ImportError:
    IMPORTS_AVAILABLE = False


class TestChaintracksServiceClient:
    """Test suite for ChaintracksServiceClient.

    Reference: wallet-toolbox/src/services/chaintracker/__tests/ChaintracksServiceClient.test.ts
               describe('ChaintracksServiceClient tests')
    """

    @pytest.mark.integration
    def test_mainnet_findheaderforheight(self) -> None:
        """Given: ChaintracksServiceClient for mainnet
           When: Find header for height 877595 and invalid height 999999999
           Then: Returns correct header hash for valid height, undefined for invalid

        Reference: wallet-toolbox/src/services/chaintracker/__tests/ChaintracksServiceClient.test.ts
                   test('0 mainNet findHeaderForHeight')

        Note: Requires a running ChaintracksService instance to query
        """
        pytest.skip("ChaintracksServiceClient requires full abstract method implementations for integration testing")
        # Given
        client = self._make_client("main")

        # When
        r = client.find_header_for_height(877595)

        # Then
        assert r is not None
        assert r.hash == "00000000000000000b010edee7422c59ec9131742e35f3e0d5837d710b961406"

        # When - Invalid height
        r_invalid = client.find_header_for_height(999999999)

        # Then
        assert r_invalid is None

    @pytest.mark.integration
    def test_testnet_findheaderforheight(self) -> None:
        """Given: ChaintracksServiceClient for testnet
           When: Find header for height 1651723 and invalid height 999999999
           Then: Returns correct header hash for valid height, undefined for invalid

        Reference: wallet-toolbox/src/services/chaintracker/__tests/ChaintracksServiceClient.test.ts
                   test('1 testNet findHeaderForHeight')

        Note: Requires a running ChaintracksService instance to query
        """
        pytest.skip("ChaintracksServiceClient requires full abstract method implementations for integration testing")
        # Note: TypeScript has `if (!includeTestChaintracks) return` here, which always skips this test.
        #       We removed this constant to make the test actually run when the API is implemented.

        # Given
        client = self._make_client("test")

        # When
        r = client.find_header_for_height(1651723)

        # Then
        assert r is not None
        assert r.hash == "0000000049686fe721f70614c89df146e410240f838b8f3ef8e6471c6dfdd153"

        # When - Invalid height
        r_invalid = client.find_header_for_height(999999999)

        # Then
        assert r_invalid is None

    def _make_client(self, chain: str) -> "ChaintracksServiceClient":
        """Create ChaintracksServiceClient for given chain.

        Reference: wallet-toolbox/src/services/chaintracker/__tests/ChaintracksServiceClient.test.ts
                   function makeClient(chain: sdk.Chain)
        """
        chaintracks_url = f"https://{chain}net-chaintracks.babbage.systems"
        return ChaintracksServiceClient(chain, chaintracks_url)
