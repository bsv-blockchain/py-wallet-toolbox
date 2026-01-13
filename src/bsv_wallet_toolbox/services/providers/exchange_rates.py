"""Exchange rates provider implementation.

Provides functions to fetch fiat exchange rates from external APIs.
"""

import asyncio
from datetime import UTC, datetime
from typing import Any

from ...errors import InvalidParameterError


async def get_exchange_rates_io(api_key: str) -> dict[str, Any]:
    """Fetch exchange rates from exchangeratesapi.io.

    Args:
        api_key: API key for exchangeratesapi.io service

    Returns:
        dict with keys: success (bool), timestamp (int), base (str), rates (dict)

    Raises:
        RuntimeError: If API request fails
    """
    import aiohttp

    url = f"https://api.exchangeratesapi.io/v1/latest?access_key={api_key}"
    try:
        async with aiohttp.ClientSession() as session, session.get(url) as response:
            if response.status != 200:
                raise RuntimeError(f"exchangeratesapi.io returned status {response.status}")
            data = await response.json()
            return data
    except Exception as e:
        raise RuntimeError(f"Failed to fetch exchange rates: {e!s}") from e


async def update_exchangeratesapi(
    target_currencies: list[str],
    options: dict[str, Any],
) -> dict[str, Any]:
    """Update exchange rates using exchangeratesapi.io service.

    Fetches current exchange rates for specified currencies and converts
    them to USD base rates.

    Args:
        target_currencies: List of currency codes to fetch (e.g., ['EUR', 'GBP', 'USD'])
        options: Services options dict containing exchangeratesapiKey

    Returns:
        dict with keys:
            - timestamp: datetime object
            - base: 'USD'
            - rates: dict mapping currency codes to rates

    Raises:
        InvalidParameterError: If API key is missing or currencies are invalid
        RuntimeError: If API request fails

    Reference:
        - toolbox/ts-wallet-toolbox/src/services/providers/exchangeRates.ts
    """
    if not options.get("exchangeratesapiKey"):
        raise InvalidParameterError("exchangeratesapiKey is required")

    api_key = options.get("exchangeratesapiKey")

    # Validate currencies
    if not target_currencies or not isinstance(target_currencies, list):
        raise InvalidParameterError("target_currencies must be a non-empty list")

    for currency in target_currencies:
        if not isinstance(currency, str):
            raise InvalidParameterError(f"Invalid currency code: {currency}")
        if len(currency) != 3:
            raise InvalidParameterError(f"Invalid currency code: {currency} (must be 3 characters)")
        if not currency.isalpha() or not currency.isupper():
            raise InvalidParameterError(f"Invalid currency code: {currency} (must be 3 uppercase letters)")

    # Fetch rates from API
    iorates = await get_exchange_rates_io(api_key)

    if not iorates.get("success"):
        raise RuntimeError(f"getExchangeRatesIo returned success {iorates.get('success')}")

    rates = iorates.get("rates", {})
    base = iorates.get("base", "EUR")

    if "USD" not in rates or base not in rates:
        raise RuntimeError(f"getExchangeRatesIo missing rates for 'USD' or base '{base}'")

    # Convert to USD base
    base_per_usd = rates[base] / rates["USD"]

    result: dict[str, Any] = {
        "timestamp": datetime.fromtimestamp(iorates.get("timestamp", 0), tz=UTC),
        "base": "USD",
        "rates": {},
    }

    updates = 0
    for key, value in rates.items():
        if key in target_currencies:
            result["rates"][key] = value * base_per_usd
            updates += 1

    if updates != len(target_currencies):
        raise RuntimeError(
            f"getExchangeRatesIo failed to update all target currencies. "
            f"Expected {len(target_currencies)}, got {updates}"
        )

    return result


def update_exchangeratesapi_sync(
    target_currencies: list[str],
    options: dict[str, Any],
) -> dict[str, Any]:
    """Synchronous wrapper for update_exchangeratesapi.

    Args:
        target_currencies: List of currency codes to fetch
        options: Services options dict

    Returns:
        dict with exchange rate data

    Raises:
        InvalidParameterError: If parameters are invalid
        RuntimeError: If API request fails
    """
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If we're already in an async context, we can't use run()
            # This shouldn't happen in sync context, but handle it
            raise RuntimeError("Cannot call sync wrapper from async context")
    except RuntimeError:
        # No event loop running, create a new one
        pass

    return asyncio.run(update_exchangeratesapi(target_currencies, options))
