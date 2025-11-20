"""Unit tests for getRawTx service.

This module tests getRawTx service functionality.

Reference: wallet-toolbox/src/services/__tests/getRawTx.test.ts
"""

from typing import Any

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


class TestGetRawTx:
    """Test suite for getRawTx service.

    Reference: wallet-toolbox/src/services/__tests/getRawTx.test.ts
               describe('getRawTx service tests')
    """

    def test_get_raw_tx(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Given: Services with testnet configuration
           When: Get raw transaction for a known txid
           Then: Returns raw transaction data

        Reference: wallet-toolbox/src/services/__tests/getRawTx.test.ts
                   test('0')
        """
        # Given
        options = Services.create_default_options("test")
        services = Services(options)

        # Mock: inject canned response in the service collection (proper dict structure)
        def fake_get_raw_tx(txid: str, chain: str = None) -> dict:
            return {
                "rawTx": "01000000",
                "computedTxid": txid,  # Return same txid to pass validation
            }

        # Replace the service in the collection (not just on the provider)
        services.get_raw_tx_services.services[0]["service"] = fake_get_raw_tx

        # When
        result = services.get_raw_tx("c3b6ee8b83a4261771ede9b0d2590d2f65853239ee34f84cdda36524ce317d76")

        # Then
        assert result is not None
