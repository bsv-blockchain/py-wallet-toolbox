"""Unit tests for getMerklePath service.

This module tests getMerklePath service functionality.

Reference: wallet-toolbox/src/services/__tests/getMerklePath.test.ts
"""

import pytest

try:
    from bsv_wallet_toolbox.services import Services

    # Check if Services has the required method
    if hasattr(Services, "create_default_options"):
        IMPORTS_AVAILABLE = True
    else:
        IMPORTS_AVAILABLE = False
except (ImportError, AttributeError):
    IMPORTS_AVAILABLE = False


class TestGetMerklePath:
    """Test suite for getMerklePath service.

    Reference: wallet-toolbox/src/services/__tests/getMerklePath.test.ts
               describe('getRawTx service tests')
    """

    @pytest.mark.skip(reason="Integration test requiring async service calls and network access")
    def test_get_merkle_path(self) -> None:
        """Given: Services with mainnet configuration
           When: Get merkle path for a known txid
           Then: Returns merkle path with correct height and merkle proof

        Reference: wallet-toolbox/src/services/__tests/getMerklePath.test.ts
                   test('0')
        
        Note: This test requires:
        - Async/await support for service calls  
        - Live network connection to fetch merkle paths
        - Services return dict format, test expects object notation
        """
        # Given
        options = Services.create_default_options("main")
        services = Services(options)

        txid = "9cce99686bc8621db439b7150dd5b3b269e4b0628fd75160222c417d6f2b95e4"

        # When
        result = services.get_merkle_path(txid)

        # Then - Result is dict, use dict notation
        assert result.get("header") is not None
        assert result["header"]["height"] == 877599
        assert result.get("merklePath") is not None
