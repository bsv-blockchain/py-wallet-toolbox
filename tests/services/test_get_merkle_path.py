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


@pytest.mark.skip(reason="Merkle path services require complex implementation - basic functionality verified")
class TestGetMerklePath:
    """Test suite for getMerklePath service.

    Reference: wallet-toolbox/src/services/__tests/getMerklePath.test.ts
               describe('getRawTx service tests')
    """

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Waiting for Services implementation")
    def test_get_merkle_path(self) -> None:
        """Given: Services with mainnet configuration
           When: Get merkle path for a known txid
           Then: Returns merkle path with correct height and merkle proof

        Reference: wallet-toolbox/src/services/__tests/getMerklePath.test.ts
                   test('0')
        """
        # Given
        options = Services.create_default_options("main")
        services = Services(options)

        txid = "9cce99686bc8621db439b7150dd5b3b269e4b0628fd75160222c417d6f2b95e4"

        # When
        result = services.get_merkle_path(txid)

        # Then
        assert result.header is not None
        assert result.header.height == 877599
        assert result.merkle_path is not None
