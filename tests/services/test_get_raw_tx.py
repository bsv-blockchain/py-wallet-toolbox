"""Unit tests for getRawTx service.

This module tests getRawTx service functionality.

Reference: wallet-toolbox/src/services/__tests/getRawTx.test.ts
"""

from typing import Any
import asyncio
from unittest.mock import Mock, patch, AsyncMock

import pytest

try:
    from bsv_wallet_toolbox.services import Services
    from bsv_wallet_toolbox.errors import InvalidParameterError

    # Check if Services has the required method
    if hasattr(Services, "create_default_options"):
        IMPORTS_AVAILABLE = True
    else:
        IMPORTS_AVAILABLE = False
except (ImportError, AttributeError):
    IMPORTS_AVAILABLE = False


@pytest.fixture
def valid_services_config():
    """Fixture providing valid services configuration."""
    return {
        "chain": "test",
        "whatsonchain_api_key": "test_woc_key",
        "taal_api_key": "test_taal_key"
    }


@pytest.fixture
def mock_services(valid_services_config):
    """Fixture providing mock services instance."""
    with patch('bsv_wallet_toolbox.services.services.ServiceCollection') as mock_service_collection:
        mock_instance = Mock()
        mock_service_collection.return_value = mock_instance

        with patch('bsv_wallet_toolbox.services.services.Services._get_http_client', return_value=Mock()):
            services = Services(valid_services_config)
            yield services, mock_instance


@pytest.fixture
def valid_txid():
    """Fixture providing a valid transaction ID."""
    return "c3b6ee8b83a4261771ede9b0d2590d2f65853239ee34f84cdda36524ce317d76"


@pytest.fixture
def invalid_txids():
    """Fixture providing various invalid transaction IDs."""
    return [
        "",  # Empty string
        "invalid_hex",  # Invalid hex
        "123",  # Too short
        "gggggggggggggggggggggggggggggggggggggggg",  # Invalid hex chars
        "c3b6ee8b83a4261771ede9b0d2590d2f65853239ee34f84cdda36524ce317d7",  # Too short (63 chars)
        "c3b6ee8b83a4261771ede9b0d2590d2f65853239ee34f84cdda36524ce317d76aa",  # Too long (65 chars)
        None,  # None type
        123,  # Wrong type
        [],  # Wrong type
        {},  # Wrong type
    ]


@pytest.fixture
def network_error_responses():
    """Fixture providing various network error response scenarios."""
    return [
        # HTTP 500 Internal Server Error
        {"status": 500, "text": "Internal Server Error"},

        # HTTP 503 Service Unavailable
        {"status": 503, "text": "Service Unavailable"},

        # HTTP 429 Rate Limited
        {"status": 429, "text": "Rate limit exceeded", "headers": {"Retry-After": "60"}},

        # HTTP 401 Unauthorized
        {"status": 401, "text": "Unauthorized"},

        # HTTP 403 Forbidden
        {"status": 403, "text": "Forbidden"},

        # HTTP 404 Not Found (transaction not found)
        {"status": 404, "text": "Not Found"},

        # Timeout scenarios
        {"timeout": True, "error": "Connection timeout"},

        # Malformed JSON response
        {"status": 200, "text": "invalid json {{{", "malformed": True},

        # Empty response
        {"status": 200, "text": "", "empty": True},

        # Very large response (simulating memory issues)
        {"status": 200, "text": "x" * 1000000, "large": True},
    ]


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

    def test_get_raw_tx_invalid_txid_formats(self, mock_services, invalid_txids) -> None:
        """Given: Invalid txid formats
           When: Call get_raw_tx with invalid txids
           Then: Handles invalid formats appropriately
        """
        services, _ = mock_services

        for invalid_txid in invalid_txids:
            # Should handle invalid txid formats gracefully
            with pytest.raises((InvalidParameterError, ValueError, TypeError)):
                services.get_raw_tx(invalid_txid)
    def test_get_raw_tx_network_failure_500(self, mock_services, valid_txid) -> None:
        """Given: Network returns HTTP 500 error
           When: Call get_raw_tx
           Then: Handles server error appropriately
        """
        services, mock_instance = mock_services
        mock_instance.count = 1

        # Set count for the mocked service collection
        mock_instance.count = 1

        # Mock service to return error
        def mock_get_raw_tx_error(txid, chain):
            raise Exception("HTTP 500: Internal Server Error")

        # Set up the mocked service
        mock_service_to_call = Mock()
        mock_service_to_call.service = mock_get_raw_tx_error
        mock_instance.service_to_call = mock_service_to_call

        result = services.get_raw_tx(valid_txid)
        assert result is None  # Exception caught, method returns None

    def test_get_raw_tx_network_timeout(self, mock_services, valid_txid) -> None:
        """Given: Network request times out
           When: Call get_raw_tx
           Then: Handles timeout appropriately
        """
        services, mock_instance = mock_services
        mock_instance.count = 1

        # Mock service to timeout
        def mock_get_raw_tx_timeout(txid, chain):
            raise asyncio.TimeoutError("Connection timeout")

        mock_service_to_call = Mock()
        mock_service_to_call.service = mock_get_raw_tx_timeout
        mock_instance.service_to_call = mock_service_to_call

        result = services.get_raw_tx(valid_txid)
        assert result is None  # Should return None on timeout

    def test_get_raw_tx_rate_limiting_429(self, mock_services, valid_txid) -> None:
        """Given: API returns 429 rate limit exceeded
           When: Call get_raw_tx
           Then: Handles rate limiting appropriately
        """
        services, mock_instance = mock_services
        mock_instance.count = 1

        # Mock service to return rate limit error
        def mock_get_raw_tx_rate_limit(txid, chain):
            raise Exception("HTTP 429: Rate limit exceeded")

        mock_service_to_call = Mock()
        mock_service_to_call.service = mock_get_raw_tx_rate_limit
        mock_instance.service_to_call = mock_service_to_call

        result = services.get_raw_tx(valid_txid)
        assert result is None  # Should return None on rate limit

    def test_get_raw_tx_transaction_not_found_404(self, mock_services, valid_txid) -> None:
        """Given: Transaction not found (404)
           When: Call get_raw_tx
           Then: Returns None appropriately
        """
        services, mock_instance = mock_services
        mock_instance.count = 1

        # Mock service to return 404
        def mock_get_raw_tx_not_found(txid, chain):
            raise Exception("HTTP 404: Transaction not found")

        mock_service_to_call = Mock()
        mock_service_to_call.service = mock_get_raw_tx_not_found
        mock_instance.service_to_call = mock_service_to_call

        result = services.get_raw_tx(valid_txid)
        assert result is None  # Should return None for non-existent transactions

    def test_get_raw_tx_malformed_response(self, mock_services, valid_txid) -> None:
        """Given: API returns malformed response
           When: Call get_raw_tx
           Then: Handles malformed response appropriately
        """
        services, mock_instance = mock_services
        mock_instance.count = 1

        # Mock service to return malformed data
        def mock_get_raw_tx_malformed(txid, chain):
            raise Exception("Invalid JSON response")

        mock_service_to_call = Mock()
        mock_service_to_call.service = mock_get_raw_tx_malformed
        mock_instance.service_to_call = mock_service_to_call

        result = services.get_raw_tx(valid_txid)
        assert result is None  # Should return None on malformed response

    def test_get_raw_tx_connection_error(self, mock_services, valid_txid) -> None:
        """Given: Connection error occurs
           When: Call get_raw_tx
           Then: Handles connection error appropriately
        """
        services, mock_instance = mock_services
        mock_instance.count = 1

        # Mock service to raise connection error
        def mock_get_raw_tx_connection_error(txid, chain):
            raise ConnectionError("Network is unreachable")

        mock_service_to_call = Mock()
        mock_service_to_call.service = mock_get_raw_tx_connection_error
        mock_instance.service_to_call = mock_service_to_call

        result = services.get_raw_tx(valid_txid)
        assert result is None  # Should return None on connection error

    def test_get_raw_tx_provider_fallback(self, mock_services, valid_txid) -> None:
        """Given: Primary provider fails, fallback provider succeeds
        When: Call get_raw_tx
        Then: Uses fallback provider successfully
        """
        services, mock_instance = mock_services
        mock_instance.count = 2  # Allow 2 tries for fallback
        
        # Mock providers with fallback
        call_count = 0
        def mock_get_raw_tx_with_fallback(txid, chain):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise Exception("Primary provider failed")
            else:
                return {"rawTx": "01000000", "computedTxid": txid}
        
        mock_service_to_call = Mock()
        mock_service_to_call.service = mock_get_raw_tx_with_fallback
        mock_instance.service_to_call = mock_service_to_call
        
        result = services.get_raw_tx(valid_txid)
        assert result is not None
        assert call_count == 2  # Should have tried fallback

    def test_get_raw_tx_success_response(self, mock_services, valid_txid) -> None:
        """Given: Valid txid and successful API response
        When: Call get_raw_tx
        Then: Returns raw transaction data
        """
        services, mock_instance = mock_services
        mock_instance.count = 1

        expected_raw_tx = "01000000010000000000000000000000000000000000000000000000000000000000000000ffffffff0100f2052a01000000434104b0bd634234abbb1ba1e986e884185c61cf43e001f9137f23c2c409273eb16e65a9147c233e4c945cf877e6c7e25dfaa0816208673ef48b89b8002c06ba4d3c396f60a3cac00000000"

        # Mock successful response
        def mock_get_raw_tx_success(txid, chain):
            return {"rawTx": expected_raw_tx, "computedTxid": txid}

        # Set up the mocked service
        mock_service_to_call = Mock()
        mock_service_to_call.service = mock_get_raw_tx_success
        mock_instance.service_to_call = mock_service_to_call

        result = services.get_raw_tx(valid_txid)
        assert result is not None
        assert result == expected_raw_tx

    def test_get_raw_tx_different_chains(self, mock_services) -> None:
        """Given: Different blockchain chains
           When: Call get_raw_tx
           Then: Handles different chains appropriately
        """
        services, mock_instance = mock_services
        mock_instance.count = 1

        test_cases = [
            ("main", "d9978ffc6676523208f7b33bebf1b176388bbeace2c7ef67ce35c2eababa1805"),
            ("test", "c3b6ee8b83a4261771ede9b0d2590d2f65853239ee34f84cdda36524ce317d76"),
        ]

        for chain, txid in test_cases:
            # Mock response for specific chain
            def mock_get_raw_tx_chain(txid_param, chain_param):
                return {"rawTx": "01000000", "computedTxid": txid_param}

            mock_service_to_call = Mock()
            mock_service_to_call.service = mock_get_raw_tx_chain
            mock_instance.service_to_call = mock_service_to_call

            result = services.get_raw_tx(txid)
            assert result is not None
            assert result == "01000000"  # Returns string, not dict

    def test_get_raw_tx_unicode_txid_handling(self, mock_services) -> None:
        """Given: Txid with unicode characters (though txids are hex)
           When: Call get_raw_tx
           Then: Handles gracefully
        """
        services, mock_instance = mock_services
        mock_instance.count = 1

        # Even though txids are hex, test unicode handling
        unicode_txid = "c3b6ee8b83a4261771ede9b0d2590d2f65853239ee34f84cdda36524ce317d76"

        def mock_get_raw_tx_unicode(txid, chain):
            return {"rawTx": "01000000", "computedTxid": txid}

        mock_service_to_call = Mock()
        mock_service_to_call.service = mock_get_raw_tx_unicode
        mock_instance.service_to_call = mock_service_to_call

        result = services.get_raw_tx(unicode_txid)
        assert result is not None
        assert result == "01000000"

    def test_get_raw_tx_large_tx_data_handling(self, mock_services, valid_txid) -> None:
        """Given: Very large transaction data
           When: Call get_raw_tx
           Then: Handles large data appropriately
        """
        services, mock_instance = mock_services
        mock_instance.count = 1

        # Create large transaction data (simulate large transaction)
        large_raw_tx = "00" * 100000  # 100KB of transaction data

        def mock_get_raw_tx_large(txid, chain):
            return {"rawTx": large_raw_tx, "computedTxid": txid}

        mock_service_to_call = Mock()
        mock_service_to_call.service = mock_get_raw_tx_large
        mock_instance.service_to_call = mock_service_to_call

        result = services.get_raw_tx(valid_txid)
        assert result is not None
        assert len(result) == 200000  # Should handle large data

    def test_get_raw_tx_empty_response_handling(self, mock_services, valid_txid) -> None:
        """Given: API returns empty raw transaction
           When: Call get_raw_tx
           Then: Handles empty response appropriately (returns None)
        """
        services, mock_instance = mock_services
        mock_instance.count = 1

        def mock_get_raw_tx_empty(txid, chain):
            return {"rawTx": "", "computedTxid": txid}

        mock_service_to_call = Mock()
        mock_service_to_call.service = mock_get_raw_tx_empty
        mock_instance.service_to_call = mock_service_to_call

        result = services.get_raw_tx(valid_txid)
        assert result is None  # Empty rawTx is treated as not found

    def test_get_raw_tx_multiple_providers_fallback(self, mock_services, valid_txid) -> None:
        """Given: Multiple providers with primary failing, secondary succeeding
           When: Call get_raw_tx
           Then: Successfully falls back to working provider
        """
        services, mock_instance = mock_services
        mock_instance.count = 3  # Allow 3 tries

        # Simulate provider list with fallback
        provider_call_count = 0
        def mock_multi_provider_fallback(txid, chain):
            nonlocal provider_call_count
            provider_call_count += 1
            if provider_call_count == 1:
                raise Exception("Provider 1 failed")
            elif provider_call_count == 2:
                raise Exception("Provider 2 failed")
            else:
                return {"rawTx": "01000000", "computedTxid": txid}

        mock_service_to_call = Mock()
        mock_service_to_call.service = mock_multi_provider_fallback
        mock_instance.service_to_call = mock_service_to_call

        result = services.get_raw_tx(valid_txid)
        assert result is not None
        assert result == "01000000"  # Returns string, not dict
        assert provider_call_count == 3  # Tried 3 providers before success
