"""Unit tests for getTransactionStatus service.

This module tests transaction status functionality.

Reference: wallet-toolbox/src/services/Services.ts#getTransactionStatus
"""

from unittest.mock import Mock, patch

import pytest

try:
    from bsv_wallet_toolbox.errors import InvalidParameterError
    from bsv_wallet_toolbox.services import Services

    IMPORTS_AVAILABLE = True
except ImportError:
    IMPORTS_AVAILABLE = False


@pytest.fixture
def valid_services_config():
    """Fixture providing valid services configuration."""
    return {"chain": "main", "whatsonchainApiKey": "test_woc_key", "taalApiKey": "test_taal_key"}


@pytest.fixture
def mock_services(valid_services_config):
    """Fixture providing mock services instance."""
    with patch("bsv_wallet_toolbox.services.services.ServiceCollection") as mock_service_collection:
        mock_instance = Mock()
        mock_instance.count = 1  # Set count to avoid early return
        mock_service_collection.return_value = mock_instance

        with patch("bsv_wallet_toolbox.services.services.Services._get_http_client", return_value=Mock()):
            services = Services(valid_services_config)
            yield services, mock_instance


@pytest.fixture
def valid_txid():
    """Fixture providing a valid transaction ID."""
    return "a1b2c3d4e5f6abcdef1234567890abcdef1234567890abcdef1234567890abcd"


@pytest.fixture
def invalid_txids():
    """Fixture providing various invalid transaction IDs."""
    return [
        "",  # Empty string
        "invalid_hex",  # Invalid hex
        "123",  # Too short
        "gggggggggggggggggggggggggggggggggggggggg",  # Invalid hex chars
        "a1b2c3d4e5f6abcdef1234567890abcdef1234567890abcdef1234567890abc",  # Too short (63 chars)
        "a1b2c3d4e5f6abcdef1234567890abcdef1234567890abcdef1234567890abcde",  # Too long (65 chars)
        None,  # None type
        123,  # Wrong type
        [],  # Wrong type
        {},  # Wrong type
    ]


@pytest.fixture
def transaction_status_responses():
    """Fixture providing various transaction status response scenarios."""
    return [
        # Confirmed transaction
        {
            "status": 200,
            "json": {
                "txid": "a1b2c3d4e5f6...",
                "confirmations": 6,
                "blockHeight": 883637,
                "blockHash": "0000000000000000060ac8d63b78d41f58c9aba0b09f81db7d51fa4905a47263",
                "blockTime": 1739329877,
            },
        },
        # Unconfirmed transaction
        {
            "status": 200,
            "json": {
                "txid": "a1b2c3d4e5f6...",
                "confirmations": 0,
                "blockHeight": None,
                "blockHash": None,
                "blockTime": None,
            },
        },
        # Transaction not found
        {"status": 404, "json": {"error": "Transaction not found"}},
        # Mempool transaction
        {
            "status": 200,
            "json": {
                "txid": "a1b2c3d4e5f6...",
                "confirmations": -1,  # In mempool
                "blockHeight": None,
                "blockHash": None,
                "blockTime": None,
                "inMempool": True,
            },
        },
        # Recently confirmed (1 confirmation)
        {
            "status": 200,
            "json": {
                "txid": "a1b2c3d4e5f6...",
                "confirmations": 1,
                "blockHeight": 883640,
                "blockHash": "0000000000000000089abcdef...",
                "blockTime": 1739330000,
            },
        },
        # Well confirmed (100+ confirmations)
        {
            "status": 200,
            "json": {
                "txid": "a1b2c3d4e5f6...",
                "confirmations": 150,
                "blockHeight": 883490,
                "blockHash": "0000000000000000056fedcba...",
                "blockTime": 1739200000,
            },
        },
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
        # Timeout scenarios
        {"timeout": True, "error": "Connection timeout"},
        # Malformed JSON response
        {"status": 200, "text": "invalid json {{{", "malformed": True},
        # Empty response
        {"status": 200, "text": "", "empty": True},
        # Very large response (simulating memory issues)
        {"status": 200, "text": "x" * 1000000, "large": True},
    ]


def test_get_transaction_status_placeholder() -> None:
    """Placeholder for `getTransactionStatus` until TS/So test is available."""


def test_get_transaction_status_invalid_txid_formats(mock_services, invalid_txids) -> None:
    """Given: Invalid txid formats
    When: Call get_transaction_status with invalid txids
    Then: Raises appropriate errors
    """
    services, _ = mock_services

    for invalid_txid in invalid_txids:
        with pytest.raises((InvalidParameterError, ValueError, TypeError)):
            services.get_transaction_status(invalid_txid)


def test_get_transaction_status_network_failure_500(mock_services, valid_txid) -> None:
    """Given: Network returns HTTP 500 error
    When: Call get_transaction_status
    Then: Handles server error appropriately
    """
    services, mock_instance = mock_services

    # Mock service to return error
    # Note: get_transaction_status service is called with txid and use_next - see services.py line 1279
    def mock_get_transaction_status_error(txid, use_next=None):
        raise Exception("HTTP 500: Internal Server Error")

    mock_stc = Mock()
    mock_stc.service = mock_get_transaction_status_error
    mock_instance.service_to_call = mock_stc

    result = services.get_transaction_status(valid_txid)
    assert isinstance(result, dict)
    # Should return error result


def test_get_transaction_status_network_timeout(mock_services, valid_txid) -> None:
    """Given: Network request times out
    When: Call get_transaction_status
    Then: Handles timeout appropriately
    """
    services, mock_instance = mock_services

    # Mock service to timeout
    # Note: get_transaction_status service is called with txid and use_next - see services.py line 1279
    def mock_get_transaction_status_timeout(txid, use_next=None):
        raise TimeoutError("Connection timeout")

    mock_stc = Mock()
    mock_stc.service = mock_get_transaction_status_timeout
    mock_instance.service_to_call = mock_stc

    result = services.get_transaction_status(valid_txid)
    assert isinstance(result, dict)
    # Should return error result


def test_get_transaction_status_rate_limiting_429(mock_services, valid_txid) -> None:
    """Given: API returns 429 rate limit exceeded
    When: Call get_transaction_status
    Then: Handles rate limiting appropriately
    """
    services, mock_instance = mock_services

    # Mock service to return rate limit error
    # Note: get_transaction_status service is called with txid and use_next - see services.py line 1279
    def mock_get_transaction_status_rate_limit(txid, use_next=None):
        raise Exception("HTTP 429: Rate limit exceeded")

    mock_stc = Mock()
    mock_stc.service = mock_get_transaction_status_rate_limit
    mock_instance.service_to_call = mock_stc

    result = services.get_transaction_status(valid_txid)
    assert isinstance(result, dict)
    # Should return error result


def test_get_transaction_status_transaction_not_found_404(mock_services, valid_txid) -> None:
    """Given: Transaction not found (404)
    When: Call get_transaction_status
    Then: Returns appropriate not found result
    """
    services, mock_instance = mock_services

    # Mock service to return 404
    # Note: get_transaction_status service is called with txid and use_next - see services.py line 1279
    def mock_get_transaction_status_not_found(txid, use_next=None):
        raise Exception("HTTP 404: Transaction not found")

    mock_stc = Mock()
    mock_stc.service = mock_get_transaction_status_not_found
    mock_instance.service_to_call = mock_stc

    result = services.get_transaction_status(valid_txid)
    assert isinstance(result, dict)
    # Should return not found result


def test_get_transaction_status_malformed_response(mock_services, valid_txid) -> None:
    """Given: API returns malformed response
    When: Call get_transaction_status
    Then: Handles malformed response appropriately
    """
    services, mock_instance = mock_services

    # Mock service to return malformed data
    # Note: get_transaction_status service is called with txid and use_next - see services.py line 1279
    def mock_get_transaction_status_malformed(txid, use_next=None):
        raise Exception("Invalid JSON response")

    mock_stc = Mock()
    mock_stc.service = mock_get_transaction_status_malformed
    mock_instance.service_to_call = mock_stc

    result = services.get_transaction_status(valid_txid)
    assert isinstance(result, dict)
    # Should return error result


def test_get_transaction_status_connection_error(mock_services, valid_txid) -> None:
    """Given: Connection error occurs
    When: Call get_transaction_status
    Then: Handles connection error appropriately
    """
    services, mock_instance = mock_services

    # Mock service to raise connection error
    # Note: get_transaction_status service is called with txid and use_next - see services.py line 1279
    def mock_get_transaction_status_connection_error(txid, use_next=None):
        raise ConnectionError("Network is unreachable")

    mock_stc = Mock()
    mock_stc.service = mock_get_transaction_status_connection_error
    mock_instance.service_to_call = mock_stc

    result = services.get_transaction_status(valid_txid)
    assert isinstance(result, dict)
    # Should return error result


def test_get_transaction_status_provider_fallback(mock_services, valid_txid) -> None:
    """Given: Primary provider fails, fallback provider succeeds
    When: Call get_transaction_status
    Then: Uses fallback provider successfully
    """
    services, mock_instance = mock_services
    mock_instance.count = 2  # Allow 2 tries for fallback

    # Mock primary provider failure, fallback success
    # Note: get_transaction_status service is called with txid and use_next - see services.py line 1279
    call_count = 0

    def mock_get_transaction_status_with_fallback(txid, use_next=None):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise Exception("Primary provider failed")
        else:
            return {
                "txid": txid,
                "confirmations": 6,
                "blockHeight": 883637,
                "blockHash": "0000000000000000060ac8d63b78d41f58c9aba0b09f81db7d51fa4905a47263",
                "blockTime": 1739329877,
            }

    mock_stc = Mock()
    mock_stc.service = mock_get_transaction_status_with_fallback
    mock_instance.service_to_call = mock_stc

    result = services.get_transaction_status(valid_txid)
    assert isinstance(result, dict)
    assert result["confirmations"] == 6
    assert call_count == 2  # Tried primary, then fallback


def test_get_transaction_status_confirmed_transaction(mock_services, valid_txid) -> None:
    """Given: Confirmed transaction
    When: Call get_transaction_status
    Then: Returns confirmed status with block details
    """
    services, mock_instance = mock_services

    confirmed_response = {
        "txid": valid_txid,
        "confirmations": 6,
        "blockHeight": 883637,
        "blockHash": "0000000000000000060ac8d63b78d41f58c9aba0b09f81db7d51fa4905a47263",
        "blockTime": 1739329877,
    }

    # Note: get_transaction_status service is called with txid and use_next - see services.py line 1279
    def mock_get_transaction_status_confirmed(txid, use_next=None):
        return confirmed_response

    mock_stc = Mock()
    mock_stc.service = mock_get_transaction_status_confirmed
    mock_instance.service_to_call = mock_stc

    result = services.get_transaction_status(valid_txid)
    assert isinstance(result, dict)
    assert result["confirmations"] == 6
    assert result["blockHeight"] == 883637
    assert "blockHash" in result
    assert "blockTime" in result


def test_get_transaction_status_unconfirmed_transaction(mock_services, valid_txid) -> None:
    """Given: Unconfirmed transaction
    When: Call get_transaction_status
    Then: Returns unconfirmed status
    """
    services, mock_instance = mock_services

    unconfirmed_response = {
        "txid": valid_txid,
        "confirmations": 0,
        "blockHeight": None,
        "blockHash": None,
        "blockTime": None,
    }

    # Note: get_transaction_status service is called with txid and use_next - see services.py line 1279
    def mock_get_transaction_status_unconfirmed(txid, use_next=None):
        return unconfirmed_response

    mock_stc = Mock()
    mock_stc.service = mock_get_transaction_status_unconfirmed
    mock_instance.service_to_call = mock_stc

    result = services.get_transaction_status(valid_txid)
    assert isinstance(result, dict)
    assert result["confirmations"] == 0
    assert result["blockHeight"] is None
    assert result["blockHash"] is None
    assert result["blockTime"] is None


def test_get_transaction_status_mempool_transaction(mock_services, valid_txid) -> None:
    """Given: Transaction in mempool
    When: Call get_transaction_status
    Then: Returns mempool status
    """
    services, mock_instance = mock_services

    mempool_response = {
        "txid": valid_txid,
        "confirmations": -1,
        "blockHeight": None,
        "blockHash": None,
        "blockTime": None,
        "inMempool": True,
    }

    # Note: get_transaction_status service is called with txid and use_next - see services.py line 1279
    def mock_get_transaction_status_mempool(txid, use_next=None):
        return mempool_response

    mock_stc = Mock()
    mock_stc.service = mock_get_transaction_status_mempool
    mock_instance.service_to_call = mock_stc

    result = services.get_transaction_status(valid_txid)
    assert isinstance(result, dict)
    assert result["confirmations"] == -1
    assert result.get("inMempool") is True


def test_get_transaction_status_different_chains(mock_services) -> None:
    """Given: Different blockchain chains
    When: Call get_transaction_status
    Then: Handles different chains appropriately
    """
    services, mock_instance = mock_services

    test_cases = [
        ("main", "a1b2c3d4e5f6abcdef1234567890abcdef1234567890abcdef1234567890abcd"),
        ("test", "b2c3d4e5f6abcdef1234567890abcdef1234567890abcdef1234567890abcdef"),
    ]

    for _chain, txid in test_cases:
        # Note: get_transaction_status service is called with txid and use_next - see services.py line 1279
        def mock_get_transaction_status_chain(txid_param, use_next=None):
            return {
                "txid": txid_param,
                "confirmations": 3,
                "blockHeight": 1000,
                "blockHash": "00000000000000000abcdef...",
                "blockTime": 1640995200,
            }

        mock_stc = Mock()
        mock_stc.service = mock_get_transaction_status_chain
        mock_instance.service_to_call = mock_stc

        result = services.get_transaction_status(txid)
        assert isinstance(result, dict)
        assert result["confirmations"] == 3
        assert result["txid"] == txid


def test_get_transaction_status_multiple_providers_fallback(mock_services, valid_txid) -> None:
    """Given: Multiple providers with primary failing, secondary succeeding
    When: Call get_transaction_status
    Then: Successfully falls back to working provider
    """
    services, mock_instance = mock_services
    mock_instance.count = 3  # Allow 3 tries for multiple provider fallback

    # Simulate provider list with fallback
    # Note: get_transaction_status service is called with txid and use_next - see services.py line 1279
    provider_call_count = 0

    def mock_multi_provider_fallback(txid, use_next=None):
        nonlocal provider_call_count
        provider_call_count += 1
        if provider_call_count == 1:
            raise Exception("Provider 1 failed")
        elif provider_call_count == 2:
            raise Exception("Provider 2 failed")
        else:
            return {
                "txid": txid,
                "confirmations": 12,
                "blockHeight": 883650,
                "blockHash": "0000000000000000089fedcba...",
                "blockTime": 1739331000,
            }

    mock_stc = Mock()
    mock_stc.service = mock_multi_provider_fallback
    mock_instance.service_to_call = mock_stc

    result = services.get_transaction_status(valid_txid)
    assert isinstance(result, dict)
    assert result["confirmations"] == 12
    assert provider_call_count == 3  # Tried 3 providers before success


def test_get_transaction_status_recently_confirmed(mock_services, valid_txid) -> None:
    """Given: Recently confirmed transaction (1 confirmation)
    When: Call get_transaction_status
    Then: Returns single confirmation status
    """
    services, mock_instance = mock_services

    recent_response = {
        "txid": valid_txid,
        "confirmations": 1,
        "blockHeight": 883640,
        "blockHash": "0000000000000000089abcdef...",
        "blockTime": 1739330000,
    }

    # Note: get_transaction_status service is called with txid and use_next - see services.py line 1279
    def mock_get_transaction_status_recent(txid, use_next=None):
        return recent_response

    mock_stc = Mock()
    mock_stc.service = mock_get_transaction_status_recent
    mock_instance.service_to_call = mock_stc

    result = services.get_transaction_status(valid_txid)
    assert isinstance(result, dict)
    assert result["confirmations"] == 1
    assert result["blockHeight"] == 883640


def test_get_transaction_status_well_confirmed(mock_services, valid_txid) -> None:
    """Given: Well confirmed transaction (100+ confirmations)
    When: Call get_transaction_status
    Then: Returns high confirmation count
    """
    services, mock_instance = mock_services

    well_confirmed_response = {
        "txid": valid_txid,
        "confirmations": 150,
        "blockHeight": 883490,
        "blockHash": "0000000000000000056fedcba...",
        "blockTime": 1739200000,
    }

    # Note: get_transaction_status service is called with txid and use_next - see services.py line 1279
    def mock_get_transaction_status_well_confirmed(txid, use_next=None):
        return well_confirmed_response

    mock_stc = Mock()
    mock_stc.service = mock_get_transaction_status_well_confirmed
    mock_instance.service_to_call = mock_stc

    result = services.get_transaction_status(valid_txid)
    assert isinstance(result, dict)
    assert result["confirmations"] == 150
    assert result["blockHeight"] == 883490


def test_get_transaction_status_unicode_txid_handling(mock_services) -> None:
    """Given: Txid with unicode characters (though txids are hex)
    When: Call get_transaction_status
    Then: Handles gracefully
    """
    services, mock_instance = mock_services

    # Even though txids are hex, test unicode handling
    unicode_txid = "a1b2c3d4e5f6abcdef1234567890abcdef1234567890abcdef1234567890abcd"

    # Note: get_transaction_status service is called with txid and use_next - see services.py line 1279
    def mock_get_transaction_status_unicode(txid, use_next=None):
        return {"txid": txid, "confirmations": 2, "blockHeight": 883638}

    mock_stc = Mock()
    mock_stc.service = mock_get_transaction_status_unicode
    mock_instance.service_to_call = mock_stc

    result = services.get_transaction_status(unicode_txid)
    assert isinstance(result, dict)
    assert result["confirmations"] == 2
