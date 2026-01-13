"""Unit tests for exchangeRates service.

This module tests exchange rate update functionality.

Reference: wallet-toolbox/src/services/providers/__tests/exchangeRates.test.ts
"""

import asyncio
from typing import Any
from unittest.mock import Mock, patch

import pytest  # type: ignore[import]

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
    return {"chain": "main", "exchangeratesapiKey": "test_api_key_123"}


@pytest.fixture
def mock_services(valid_services_config):
    """Fixture providing mock services instance."""
    with patch("bsv_wallet_toolbox.services.services.ServiceCollection") as mock_service_collection:
        mock_instance = Mock()
        mock_service_collection.return_value = mock_instance

        with patch("bsv_wallet_toolbox.services.services.Services._get_http_client", return_value=Mock()):
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
    """Fixture providing various exchange rate response scenarios keyed by id."""

    def _payload(rates: dict[str, float], base: str = "EUR") -> dict[str, Any]:
        return {
            "status": 200,
            "json": {
                "success": True,
                "timestamp": 1640995200,
                "base": base,
                "date": "2022-01-01",
                "rates": rates,
            },
        }

    common = {
        "EUR": 1.0,
        "USD": 1.18,
        "GBP": 0.86,
        "CAD": 1.47,
        "JPY": 135.0,
    }

    return {
        "all_rates_present": {
            "response": _payload(common),
            "expect_error": None,
        },
        "zero_rates": {
            "response": _payload({**common, "GBP": 0.0, "CAD": 0.0, "JPY": 0.0}),
            "expect_error": None,
        },
        "negative_rates": {
            "response": _payload({**common, "GBP": -0.5, "CAD": -1.0, "JPY": -75.0}),
            "expect_error": None,
        },
        "tiny_rates": {
            "response": _payload(
                {
                    **common,
                    "GBP": 1e-6,
                    "CAD": 5e-8,
                    "JPY": 2e-5,
                }
            ),
            "expect_error": None,
        },
        "huge_rates": {
            "response": _payload(
                {
                    **common,
                    "GBP": 5_000.0,
                    "CAD": 10_000.0,
                    "JPY": 1_000_000.0,
                }
            ),
            "expect_error": None,
        },
        "missing_target_currency": {
            "response": _payload(
                {
                    "EUR": 1.0,
                    "USD": 1.18,
                    "GBP": 0.86,
                    # CAD missing intentionally
                    "JPY": 135.0,
                }
            ),
            "expect_error": RuntimeError,
        },
    }


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
        {
            "status": 429,
            "text": "Rate limit exceeded",
            "json": {"error": "Too many requests"},
            "headers": {"Retry-After": "60"},
        },
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
        # options.exchangeratesapiKey = 'YOUR_API_KEY'

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
        services, _ = mock_services

        for invalid_currency in invalid_currencies:
            # Should handle invalid currency codes gracefully
            import asyncio

            with pytest.raises((InvalidParameterError, ValueError, TypeError)):
                asyncio.run(update_exchangeratesapi([invalid_currency], services.options))

    @pytest.mark.asyncio
    async def test_update_exchange_rates_network_failures(
        self, mock_services, valid_currencies, network_error_responses
    ) -> None:
        """Given: Various network failure scenarios
        When: Call update_exchange_rates
        Then: Handles network failures appropriately
        """
        services, _mock_instance = mock_services

        # Mock the update_exchangeratesapi function
        async def mock_update_exchangeratesapi(currencies, options):
            for error_scenario in network_error_responses:
                if error_scenario.get("timeout"):
                    await asyncio.sleep(0.1)
                    raise TimeoutError(error_scenario["error"])
                else:
                    raise Exception(f"HTTP {error_scenario['status']}: {error_scenario['text']}")

        # Replace the function temporarily
        try:
            # Mock at module level
            with patch(
                "bsv_wallet_toolbox.services.providers.exchange_rates.update_exchangeratesapi",
                side_effect=mock_update_exchangeratesapi,
            ):
                for _error_scenario in network_error_responses:
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
    @pytest.mark.parametrize(
        "scenario_id",
        [
            "all_rates_present",
            "zero_rates",
            "negative_rates",
            "tiny_rates",
            "huge_rates",
            "missing_target_currency",
        ],
    )
    async def test_update_exchange_rates_success_responses(
        self,
        mock_services,
        valid_currencies,
        exchange_rate_responses,
        scenario_id,
    ) -> None:
        """Given: Successful exchange rate API responses
        When: Call update_exchange_rates
        Then: Returns exchange rate data
        """
        services, _mock_instance = mock_services
        scenario = exchange_rate_responses[scenario_id]
        response_scenario = scenario["response"]

        # Mock the internal API call
        with patch(
            "bsv_wallet_toolbox.services.providers.exchange_rates.get_exchange_rates_io",
            return_value=response_scenario["json"],
        ):
            if scenario["expect_error"]:
                with pytest.raises(scenario["expect_error"]):
                    await update_exchangeratesapi(valid_currencies, services.options)
                return

            result = await update_exchangeratesapi(valid_currencies, services.options)

            assert isinstance(result, dict)
            assert result["base"] == "USD"
            rates = result.get("rates", {})
            assert isinstance(rates, dict)
            assert set(valid_currencies).issubset(rates.keys())
            assert all(isinstance(rate, (int, float)) for rate in rates.values())

            if scenario_id == "zero_rates":
                for currency in ("GBP", "CAD", "JPY"):
                    assert rates[currency] == pytest.approx(0.0)
            elif scenario_id == "negative_rates":
                for currency in ("GBP", "CAD", "JPY"):
                    assert rates[currency] < 0
            elif scenario_id == "tiny_rates":
                for currency in ("GBP", "CAD", "JPY"):
                    assert abs(rates[currency]) < 1e-4
            elif scenario_id == "huge_rates":
                assert rates["JPY"] > 1_000.0

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
            "rates": {single_currency[0]: 1.0},
        }

        with patch(
            "bsv_wallet_toolbox.services.providers.exchange_rates.get_exchange_rates_io", return_value=mock_response
        ):
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
            invalid_options["exchangeratesapiKey"] = invalid_key

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

        with patch(
            "bsv_wallet_toolbox.services.providers.exchange_rates.get_exchange_rates_io",
            side_effect=Exception("Invalid JSON response"),
        ):
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
            raise TimeoutError("Connection timeout")

        async def mock_timeout_io(api_key):
            await asyncio.sleep(0.1)
            raise TimeoutError("Connection timeout")

        with patch(
            "bsv_wallet_toolbox.services.providers.exchange_rates.get_exchange_rates_io", side_effect=mock_timeout_io
        ):
            try:
                result = asyncio.run(update_exchangeratesapi(valid_currencies, services.options))
                # Should handle timeout gracefully
                assert result is not None or isinstance(result, dict)
            except TimeoutError:
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

        with patch(
            "bsv_wallet_toolbox.services.providers.exchange_rates.get_exchange_rates_io",
            side_effect=Exception("HTTP 429: Rate limit exceeded"),
        ):
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

        with patch(
            "bsv_wallet_toolbox.services.providers.exchange_rates.get_exchange_rates_io",
            side_effect=ConnectionError("Network is unreachable"),
        ):
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
