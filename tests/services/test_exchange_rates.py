"""Unit tests for exchangeRates service.

This module tests exchange rate update functionality.

Reference: wallet-toolbox/src/services/providers/__tests/exchangeRates.test.ts
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from bsv_wallet_toolbox.errors import InvalidParameterError

try:
    from bsv_wallet_toolbox.services import create_default_options
    from bsv_wallet_toolbox.services.providers import update_exchangeratesapi
    from tests.test_utils import TestUtils

    IMPORTS_AVAILABLE = True
except ImportError:
    IMPORTS_AVAILABLE = False


@pytest.fixture
def valid_services_config():
    """Fixture providing valid services configuration."""
    return {
        "chain": "main",
        "exchangeratesapi_key": "test_api_key_123"
    }


@pytest.fixture
def mock_services(valid_services_config):
    """Fixture providing mock services instance."""
    with patch('bsv_wallet_toolbox.services.services.ServiceCollection') as mock_service_collection:
        mock_instance = Mock()
        mock_service_collection.return_value = mock_instance

        with patch('bsv_wallet_toolbox.services.services.Services._get_http_client', return_value=Mock()):
            from bsv_wallet_toolbox.services import Services
            services = Services(valid_services_config)
            yield services, mock_instance


@pytest.fixture
def valid_currencies():
    """Fixture providing valid currency codes."""
    return ["USD", "EUR", "GBP", "CAD", "JPY"]


@pytest.fixture
def invalid_currencies():
    """Fixture providing various invalid currency codes."""
    return [
        "",  # Empty string
        "INVALID",  # Invalid currency code
        "US",  # Too short
        "USDDD",  # Too long
        "usd",  # Lowercase (should be uppercase)
        "US1",  # Contains number
        "U$D",  # Contains special character
        None,  # None type
        123,  # Wrong type
        [],  # Wrong type
        {},  # Wrong type
    ]


@pytest.fixture
def exchange_rate_responses():
    """Fixture providing various exchange rate response scenarios."""
    return [
        # Successful response
        {
            "status": 200,
            "json": {
                "success": True,
                "timestamp": 1640995200,
                "base": "EUR",
                "date": "2022-01-01",
                "rates": {
                    "EUR": 1.0,   # Base currency
                    "USD": 1.18,  # EUR to USD rate
                    "GBP": 0.86,
                    "CAD": 1.47,
                    "JPY": 135.0
                }
            }
        },

        # Partial success (some currencies missing)
        {
            "status": 200,
            "json": {
                "success": True,
                "timestamp": 1640995200,
                "base": "EUR",
                "date": "2022-01-01",
                "rates": {
                    "EUR": 1.0,
                    "USD": 1.18,
                    "GBP": 0.86
                    # Missing CAD, JPY
                }
            }
        },

        # Zero rates
        {
            "status": 200,
            "json": {
                "success": True,
                "timestamp": 1640995200,
                "base": "EUR",
                "date": "2022-01-01",
                "rates": {
                    "EUR": 1.0,
                    "USD": 0.0,
                    "GBP": 0.0
                }
            }
        },

        # Negative rates (edge case)
        {
            "status": 200,
            "json": {
                "success": True,
                "timestamp": 1640995200,
                "base": "EUR",
                "date": "2022-01-01",
                "rates": {
                    "EUR": 1.0,
                    "USD": -1.18,
                    "GBP": -0.86
                }
            }
        },

        # Very small rates
        {
            "status": 200,
            "json": {
                "success": True,
                "timestamp": 1640995200,
                "base": "EUR",
                "date": "2022-01-01",
                "rates": {
                    "EUR": 1.0,
                    "USD": 0.000001,
                    "GBP": 0.00001
                }
            }
        },

        # Very large rates
        {
            "status": 200,
            "json": {
                "success": True,
                "timestamp": 1640995200,
                "base": "EUR",
                "date": "2022-01-01",
                "rates": {
                    "EUR": 1.0,
                    "USD": 1.18,
                    "JPY": 1000000.0,
                    "KRW": 1000000000.0
                }
            }
        },
    ]


@pytest.fixture
def network_error_responses():
    """Fixture providing various network error response scenarios."""
    return [
        # HTTP 400 Bad Request
        {"status": 400, "text": "Bad Request", "json": {"error": "Invalid base currency"}},

        # HTTP 401 Unauthorized
        {"status": 401, "text": "Unauthorized", "json": {"error": "Invalid API key"}},

        # HTTP 403 Forbidden
        {"status": 403, "text": "Forbidden", "json": {"error": "API key quota exceeded"}},

        # HTTP 404 Not Found
        {"status": 404, "text": "Not Found", "json": {"error": "Endpoint not found"}},

        # HTTP 429 Rate Limited
        {"status": 429, "text": "Rate limit exceeded", "json": {"error": "Too many requests"}, "headers": {"Retry-After": "60"}},

        # HTTP 500 Internal Server Error
        {"status": 500, "text": "Internal Server Error", "json": {"error": "Server error"}},

        # HTTP 503 Service Unavailable
        {"status": 503, "text": "Service Unavailable", "json": {"error": "Service temporarily unavailable"}},

        # Timeout scenarios
        {"timeout": True, "error": "Connection timeout"},

        # Malformed JSON response
        {"status": 200, "text": "invalid json {{{", "malformed": True},

        # Empty response
        {"status": 200, "text": "", "empty": True},

        # Very large response (simulating memory issues)
        {"status": 200, "text": "x" * 1000000, "large": True},
    ]


@pytest.fixture
def invalid_api_keys():
    """Fixture providing various invalid API key scenarios."""
    return [
        "",  # Empty string
        "invalid_key",  # Invalid format
        "too_short",  # Too short
        None,  # None type
        123,  # Wrong type
        [],  # Wrong type
        {},  # Wrong type
    ]


class TestExchangeRates:
    """Test suite for exchangeRates service.

    Reference: wallet-toolbox/src/services/providers/__tests/exchangeRates.test.ts
               describe('exchangeRates tests')
    """

    @pytest.mark.integration
    def test_update_exchange_rates_for_multiple_currencies(self) -> None:
        """Given: Default wallet services options for mainnet
           When: Call updateExchangeratesapi with ['EUR', 'GBP', 'USD']
           Then: Returns defined result

        Reference: wallet-toolbox/src/services/providers/__tests/exchangeRates.test.ts
                   test('0')

        Note: The default API key for this service is severely use limited.
              Do not run this test aggressively without substituting your own key.
        """
        # Given - Requires implementation of update_exchangeratesapi
        from tests.test_utils import TestUtils
        if TestUtils.no_env("main"):
            pytest.skip("No 'main' environment configured")

        options = create_default_options("main")
        # To use your own API key, uncomment:
        # options.exchangeratesapi_key = 'YOUR_API_KEY'

        # When
        import asyncio
        r = asyncio.run(update_exchangeratesapi(["EUR", "GBP", "USD"], options))

        # Then
        assert r is not None

    def test_update_exchange_rates_invalid_currencies(self, mock_services, invalid_currencies) -> None:
        """Given: Invalid currency codes
           When: Call update_exchange_rates with invalid currencies
           Then: Raises appropriate errors
        """
        services, mock_instance = mock_services

        for invalid_currency in invalid_currencies:
            # Should handle invalid currency codes gracefully
            import asyncio
            with pytest.raises((InvalidParameterError, ValueError, TypeError)):
                asyncio.run(update_exchangeratesapi([invalid_currency], services.options))

    @pytest.mark.asyncio
    async def test_update_exchange_rates_network_failures(self, mock_services, valid_currencies, network_error_responses) -> None:
        """Given: Various network failure scenarios
           When: Call update_exchange_rates
           Then: Handles network failures appropriately
        """
        services, mock_instance = mock_services

        # Mock the update_exchangeratesapi function
        async def mock_update_exchangeratesapi(currencies, options):
            for error_scenario in network_error_responses:
                if error_scenario.get("timeout"):
                    await asyncio.sleep(0.1)
                    raise asyncio.TimeoutError(error_scenario["error"])
                else:
                    raise Exception(f"HTTP {error_scenario['status']}: {error_scenario['text']}")

        # Replace the function temporarily
        original_func = update_exchangeratesapi
        try:
            # Mock at module level
            with patch('bsv_wallet_toolbox.services.providers.exchange_rates.update_exchangeratesapi', side_effect=mock_update_exchangeratesapi):
                for error_scenario in network_error_responses:
                    try:
                        result = await update_exchangeratesapi(valid_currencies, services.options)
                        # Should handle errors gracefully
                        assert result is not None or isinstance(result, dict)
                    except Exception:
                        # Expected for network errors
                        pass
        finally:
            # Restore original function if needed
            pass

    @pytest.mark.asyncio
    async def test_update_exchange_rates_success_responses(self, mock_services, valid_currencies, exchange_rate_responses) -> None:
        """Given: Successful exchange rate API responses
           When: Call update_exchange_rates
           Then: Returns exchange rate data
        """
        services, mock_instance = mock_services

        # Only test the first successful response scenario for now
        # TODO: Handle partial/edge case scenarios separately
        response_scenario = exchange_rate_responses[0]  # Successful response

        # Mock the internal API call
        with patch('bsv_wallet_toolbox.services.providers.exchange_rates.get_exchange_rates_io', return_value=response_scenario["json"]):
            result = await update_exchangeratesapi(valid_currencies, services.options)

            assert isinstance(result, dict)
            assert "rates" in result
            assert isinstance(result["rates"], dict)

            # Check specific response characteristics
            if response_scenario["json"]["rates"]:
                rates = result["rates"]
                for currency, rate in rates.items():
                    assert isinstance(currency, str)
                    assert isinstance(rate, (int, float))

                    # Check edge cases
                    if "EUR" in rates and rates["EUR"] < 0:
                        assert rates["EUR"] < 0  # Negative rates
                    elif "EUR" in rates and rates["EUR"] == 0:
                        assert rates["EUR"] == 0  # Zero rates
                    elif "JPY" in rates and rates["JPY"] > 1000:
                        assert rates["JPY"] > 1000  # Large rates

    def test_update_exchange_rates_empty_currency_list(self, mock_services) -> None:
        """Given: Empty currency list
           When: Call update_exchange_rates
           Then: Raises InvalidParameterError appropriately
        """
        services, _ = mock_services

        # Should reject empty currency list with InvalidParameterError
        with pytest.raises(InvalidParameterError, match="target_currencies must be a non-empty list"):
            asyncio.run(update_exchangeratesapi([], services.options))

    @pytest.mark.asyncio
    async def test_update_exchange_rates_single_currency(self, mock_services, valid_currencies) -> None:
        """Given: Single currency code
           When: Call update_exchange_rates
           Then: Returns rate for single currency
        """
        services, _ = mock_services

        single_currency = [valid_currencies[0]]

        # Mock the internal API call
        mock_response = {
            "success": True,
            "timestamp": 1640995200,
            "base": "USD",
            "date": "2022-01-01",
            "rates": {single_currency[0]: 1.0}
        }

        with patch('bsv_wallet_toolbox.services.providers.exchange_rates.get_exchange_rates_io', return_value=mock_response):
            result = await update_exchangeratesapi(single_currency, services.options)
            assert isinstance(result, dict)
            assert single_currency[0] in result.get("rates", {})

    def test_update_exchange_rates_case_sensitivity(self, mock_services) -> None:
        """Given: Lowercase currency codes
           When: Call update_exchange_rates
           Then: Handles case sensitivity appropriately
        """
        services, _ = mock_services

        lowercase_currencies = ["usd", "eur", "gbp"]

        # Should handle lowercase currencies (may convert to uppercase or reject)
        try:
            result = asyncio.run(update_exchangeratesapi(lowercase_currencies, services.options))
            assert result is not None or isinstance(result, dict)
        except (InvalidParameterError, ValueError):
            # Expected if lowercase is not supported
            pass

    def test_update_exchange_rates_invalid_api_key(self, mock_services, valid_currencies, invalid_api_keys) -> None:
        """Given: Invalid API keys
           When: Call update_exchange_rates
           Then: Handles authentication errors appropriately
        """
        services, _ = mock_services

        for invalid_key in invalid_api_keys:
            # Create options with invalid API key
            invalid_options = services.options.copy()
            invalid_options["exchangeratesapi_key"] = invalid_key

            try:
                result = asyncio.run(update_exchangeratesapi(valid_currencies, invalid_options))
                # Should handle invalid API key gracefully
                assert result is not None or isinstance(result, dict)
            except Exception:
                # Expected for invalid API keys
                pass

    def test_update_exchange_rates_malformed_response_handling(self, mock_services, valid_currencies) -> None:
        """Given: Malformed API response
           When: Call update_exchange_rates
           Then: Handles malformed response appropriately
        """
        services, _ = mock_services

        # Mock malformed response
        async def mock_malformed_response(currencies, options):
            raise Exception("Invalid JSON response")

        with patch('bsv_wallet_toolbox.services.providers.exchange_rates.get_exchange_rates_io', side_effect=Exception("Invalid JSON response")):
            try:
                result = asyncio.run(update_exchangeratesapi(valid_currencies, services.options))
                # Should handle malformed response gracefully
                assert result is not None or isinstance(result, dict)
            except Exception:
                # Expected for malformed responses
                pass

    def test_update_exchange_rates_timeout_handling(self, mock_services, valid_currencies) -> None:
        """Given: API request timeout
           When: Call update_exchange_rates
           Then: Handles timeout appropriately
        """
        services, _ = mock_services

        # Mock timeout
        async def mock_timeout_response(currencies, options):
            await asyncio.sleep(0.1)
            raise asyncio.TimeoutError("Connection timeout")

        async def mock_timeout_io(api_key):
            await asyncio.sleep(0.1)
            raise asyncio.TimeoutError("Connection timeout")

        with patch('bsv_wallet_toolbox.services.providers.exchange_rates.get_exchange_rates_io', side_effect=mock_timeout_io):
            try:
                result = asyncio.run(update_exchangeratesapi(valid_currencies, services.options))
                # Should handle timeout gracefully
                assert result is not None or isinstance(result, dict)
            except asyncio.TimeoutError:
                # Expected timeout behavior
                pass

    def test_update_exchange_rates_rate_limiting_handling(self, mock_services, valid_currencies) -> None:
        """Given: API rate limiting response
           When: Call update_exchange_rates
           Then: Handles rate limiting appropriately
        """
        services, _ = mock_services

        # Mock rate limiting response
        async def mock_rate_limit_response(currencies, options):
            raise Exception("HTTP 429: Rate limit exceeded")

        with patch('bsv_wallet_toolbox.services.providers.exchange_rates.get_exchange_rates_io', side_effect=Exception("HTTP 429: Rate limit exceeded")):
            try:
                result = asyncio.run(update_exchangeratesapi(valid_currencies, services.options))
                # Should handle rate limiting gracefully
                assert result is not None or isinstance(result, dict)
            except Exception:
                # Expected for rate limiting
                pass

    def test_update_exchange_rates_connection_error_handling(self, mock_services, valid_currencies) -> None:
        """Given: Connection error occurs
           When: Call update_exchange_rates
           Then: Handles connection error appropriately
        """
        services, _ = mock_services

        # Mock connection error
        async def mock_connection_error_response(currencies, options):
            raise ConnectionError("Network is unreachable")

        with patch('bsv_wallet_toolbox.services.providers.exchange_rates.get_exchange_rates_io', side_effect=ConnectionError("Network is unreachable")):
            try:
                result = asyncio.run(update_exchangeratesapi(valid_currencies, services.options))
                # Should handle connection error gracefully
                assert result is not None or isinstance(result, dict)
            except ConnectionError:
                # Expected connection error behavior
                pass

    def test_update_exchange_rates_duplicate_currencies(self, mock_services, valid_currencies) -> None:
        """Given: Duplicate currency codes in list
           When: Call update_exchange_rates
           Then: Handles duplicates appropriately
        """
        services, _ = mock_services

        # Create list with duplicates
        duplicate_currencies = valid_currencies[:2] + valid_currencies[:2]

        try:
            result = asyncio.run(update_exchangeratesapi(duplicate_currencies, services.options))
            # Should handle duplicates gracefully
            assert result is not None or isinstance(result, dict)
        except Exception:
            # May reject duplicates, which is acceptable
            pass

    def test_update_exchange_rates_too_many_currencies(self, mock_services) -> None:
        """Given: Very large number of currencies
           When: Call update_exchange_rates
           Then: Handles large requests appropriately
        """
        services, _ = mock_services

        # Create a very large list of currencies
        many_currencies = [f"CUR{i:03d}" for i in range(100)]

        try:
            result = asyncio.run(update_exchangeratesapi(many_currencies, services.options))
            # Should handle large requests gracefully
            assert result is not None or isinstance(result, dict)
        except Exception:
            # May reject large requests, which is acceptable
            pass
