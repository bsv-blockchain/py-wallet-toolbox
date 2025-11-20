"""Unit tests for Chaintracks.

This module tests the main Chaintracks class with NoDb mode.

Reference: wallet-toolbox/src/services/chaintracker/chaintracks/__tests/Chaintracks.test.ts
"""

import pytest

try:
    from bsv_wallet_toolbox.services.chaintracker.chaintracks.options import create_default_no_db_chaintracks_options

    from bsv_wallet_toolbox.services.chaintracker.chaintracks import Chaintracks

    IMPORTS_AVAILABLE = True
except ImportError:
    IMPORTS_AVAILABLE = False


class TestChaintracks:
    """Test suite for Chaintracks.

    Reference: wallet-toolbox/src/services/chaintracker/chaintracks/__tests/Chaintracks.test.ts
               describe('Chaintracks tests')
    """

    def test_nodb_mainnet(self) -> None:
        """Given: Chaintracks with NoDb options for mainnet
           When: Make available and test basic operations
           Then: Successfully initializes without database

        Reference: wallet-toolbox/src/services/chaintracker/chaintracks/__tests/Chaintracks.test.ts
                   test('1 NoDb mainnet')
        """
        # Given
        chain = "main"
        o = create_default_no_db_chaintracks_options(chain)
        c = Chaintracks(o)

        # When
        c.make_available()

        # Test basic operations
        info = c.get_info()
        assert info.chain == chain

        present_height = c.get_present_height()
        assert present_height > 0

        # Then
        c.destroy()

    def test_nodb_testnet(self) -> None:
        """Given: Chaintracks with NoDb options for testnet
           When: Make available and test basic operations
           Then: Successfully initializes without database

        Reference: wallet-toolbox/src/services/chaintracker/chaintracks/__tests/Chaintracks.test.ts
                   test('2 NoDb testnet')
        """
        # Given
        chain = "test"
        o = create_default_no_db_chaintracks_options(chain)
        c = Chaintracks(o)

        # When
        c.make_available()

        # Test basic operations
        info = c.get_info()
        assert info.chain == chain

        present_height = c.get_present_height()
        assert present_height > 0

        # Then
        c.destroy()
