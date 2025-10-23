"""Unit tests for exchangeRates service.

This module tests exchange rate update functionality.

Reference: wallet-toolbox/src/services/providers/__tests/exchangeRates.test.ts
"""

import pytest

try:
    from bsv_wallet_toolbox.services import create_default_wallet_services_options
    from bsv_wallet_toolbox.services.providers import update_exchangeratesapi
    from bsv_wallet_toolbox.utils import TestUtils

    IMPORTS_AVAILABLE = True
except ImportError:
    IMPORTS_AVAILABLE = False


class TestExchangeRates:
    """Test suite for exchangeRates service.

    Reference: wallet-toolbox/src/services/providers/__tests/exchangeRates.test.ts
               describe('exchangeRates tests')
    """

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Waiting for exchangeRates implementation")
    @pytest.mark.asyncio
    async def test_update_exchange_rates_for_multiple_currencies(self) -> None:
        """Given: Default wallet services options for mainnet
           When: Call updateExchangeratesapi with ['EUR', 'GBP', 'USD']
           Then: Returns defined result

        Reference: wallet-toolbox/src/services/providers/__tests/exchangeRates.test.ts
                   test('0')

        Note: The default API key for this service is severely use limited.
              Do not run this test aggressively without substituting your own key.
        """
        # Given
        if TestUtils.no_env("main"):
            pytest.skip("No 'main' environment configured")

        options = create_default_wallet_services_options("main")
        # To use your own API key, uncomment:
        # options.exchangeratesapi_key = 'YOUR_API_KEY'

        # When
        r = await update_exchangeratesapi(["EUR", "GBP", "USD"], options)

        # Then
        assert r is not None
