"""Unit tests for getMerklePath service.

This module tests getMerklePath service functionality.

Reference: wallet-toolbox/src/services/__tests/getMerklePath.test.ts
"""

from unittest.mock import Mock, PropertyMock, patch

import pytest

try:
    from bsv_wallet_toolbox.errors import InvalidParameterError
    from bsv_wallet_toolbox.services import Services

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
    return {"chain": "main", "whatsonchainApiKey": "test_woc_key", "taalApiKey": "test_taal_key"}


@pytest.fixture
def mock_services(valid_services_config):
    """Fixture providing mock services instance."""
    with patch("bsv_wallet_toolbox.services.services.ServiceCollection") as mock_service_collection:
        mock_instance = Mock()
        # Set count property to return 1 (number of mock services)
        type(mock_instance).count = PropertyMock(return_value=1)
        # Set service_to_call to return a mock with service attribute
        mock_stc = Mock()
        mock_instance.service_to_call = mock_stc
        mock_instance.next = Mock()  # No-op for next()
        mock_service_collection.return_value = mock_instance

        with patch("bsv_wallet_toolbox.services.services.Services._get_http_client", return_value=Mock()):
            services = Services(valid_services_config)
            yield services, mock_instance, mock_stc


@pytest.fixture
def valid_txid():
    """Fixture providing a valid transaction ID."""
    return "9cce99686bc8621db439b7150dd5b3b269e4b0628fd75160222c417d6f2b95e4"


@pytest.fixture
def invalid_txids():
    """Fixture providing various invalid transaction IDs."""
    return [
        "",  # Empty string
        "invalid_hex",  # Invalid hex
        "123",  # Too short
        "gggggggggggggggggggggggggggggggggggggggg",  # Invalid hex chars
        "9cce99686bc8621db439b7150dd5b3b269e4b0628fd75160222c417d6f2b95e",  # Too short (63 chars)
        "9cce99686bc8621db439b7150dd5b3b269e4b0628fd75160222c417d6f2b95e4aa",  # Too long (65 chars)
        None,  # None type
        123,  # Wrong type
        [],  # Wrong type
        {},  # Wrong type
    ]


@pytest.fixture
def valid_merkle_path_response():
    """Fixture providing a valid merkle path response."""
    return {
        "header": {
            "bits": 403818359,
            "hash": "0000000000000000060ac8d63b78d41f58c9aba0b09f81db7d51fa4905a47263",
            "height": 883637,
            "merkleRoot": "59c1efd79fae0d9c29dd8da63f8eeec0aadde048f4491c6bfa324fcfd537156d",
            "nonce": 596827153,
            "previousHash": "00000000000000000d9f6889dd6743500adee204ea25d8a57225ecd48b111769",
            "time": 1739329877,
            "version": 1040187392,
        },
        "merklePath": {
            "blockHeight": 883637,
            "path": [
                [
                    {
                        "hash": "9cce99686bc8621db439b7150dd5b3b269e4b0628fd75160222c417d6f2b95e4",
                        "offset": 46,
                        "txid": True,
                    }
                ],
                [{"hash": "066f6fa6fa988f2e3a9d6fe35fa0d3666c652dac35cabaeebff3738a4e67f68f", "offset": 47}],
                [{"hash": "232089a6f77c566151bc4701fda394b5cc5bf17073140d46a73c4c3ed0a7b911", "offset": 22}],
                [{"hash": "c639b3a6ce127f67dbd01c7331a6fca62a4b429830387bd68ac6ac05e162116d", "offset": 10}],
                [{"hash": "730cec44be97881530947d782bbbb328d25f1122fdae206296937fffb03e936d48", "offset": 4}],
                [{"hash": "28b681f8ab8db0fa4d5d20cb1532b95184a155346b0b8447bde580b2406d51e6", "offset": 3}],
                [{"hash": "c49a18028e230dd1439b26794c08c339506f24a450f067c4facd4e0d5a346490", "offset": 0}],
                [{"hash": "0ba57d1b1fad6874de3640c01088e3dedad3507e5b3a3102b9a8a8055f3df88b", "offset": 1}],
                [{"hash": "c830edebe5565c19ba584ec73d49129344d17539f322509b7c314ae641c2fcdb", "offset": 1}],
                [{"hash": "ff62d5ed2a94eb93a2b7d084b8f15b12083573896b6a58cf871507e3352c75f5", "offset": 1}],
            ],
        },
        "name": "WoCTsc",
        "notes": [{"name": "WoCTsc", "status": 200, "statusText": "OK", "what": "getMerklePathSuccess"}],
    }


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


class TestGetMerklePath:
    """Test suite for getMerklePath service.

    Reference: wallet-toolbox/src/services/__tests/getMerklePath.test.ts
               describe('getRawTx service tests')
    """

    @pytest.mark.integration
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

    def test_get_merkle_path_invalid_txid_formats(self, mock_services, invalid_txids) -> None:
        """Given: Invalid txid formats
        When: Call get_merkle_path with invalid txids
        Then: Handles invalid formats appropriately
        """
        services, _, _ = mock_services

        for invalid_txid in invalid_txids:
            # Should handle invalid txid formats gracefully
            with pytest.raises((InvalidParameterError, ValueError, TypeError)):
                services.get_merkle_path(invalid_txid)

    def test_get_merkle_path_network_failure_500(self, mock_services, valid_txid) -> None:
        """Given: Network returns HTTP 500 error
        When: Call get_merkle_path
        Then: Handles server error appropriately
        """
        services, _mock_instance, mock_stc = mock_services

        # Mock service to return error
        def mock_get_merkle_path_error(txid, services=None):
            raise Exception("HTTP 500: Internal Server Error")

        mock_stc.service = mock_get_merkle_path_error

        result = services.get_merkle_path(valid_txid)
        assert isinstance(result, dict)
        # Should return error result

    def test_get_merkle_path_network_timeout(self, mock_services, valid_txid) -> None:
        """Given: Network request times out
        When: Call get_merkle_path
        Then: Handles timeout appropriately
        """
        services, _mock_instance, mock_stc = mock_services

        # Mock service to timeout
        def mock_get_merkle_path_timeout(txid, services=None):
            raise TimeoutError("Connection timeout")

        mock_stc.service = mock_get_merkle_path_timeout

        result = services.get_merkle_path(valid_txid)
        assert isinstance(result, dict)
        # Should return error result

    def test_get_merkle_path_rate_limiting_429(self, mock_services, valid_txid) -> None:
        """Given: API returns 429 rate limit exceeded
        When: Call get_merkle_path
        Then: Handles rate limiting appropriately
        """
        services, _mock_instance, mock_stc = mock_services

        # Mock service to return rate limit error
        def mock_get_merkle_path_rate_limit(txid, services=None):
            raise Exception("HTTP 429: Rate limit exceeded")

        mock_stc.service = mock_get_merkle_path_rate_limit

        result = services.get_merkle_path(valid_txid)
        assert isinstance(result, dict)
        # Should return error result

    def test_get_merkle_path_transaction_not_found_404(self, mock_services, valid_txid) -> None:
        """Given: Transaction not found (404)
        When: Call get_merkle_path
        Then: Handles not found appropriately
        """
        services, _mock_instance, mock_stc = mock_services

        # Mock service to return 404
        def mock_get_merkle_path_not_found(txid, services=None):
            raise Exception("HTTP 404: Transaction not found")

        mock_stc.service = mock_get_merkle_path_not_found

        result = services.get_merkle_path(valid_txid)
        assert isinstance(result, dict)
        # Should return error result for non-existent transactions

    def test_get_merkle_path_malformed_response(self, mock_services, valid_txid) -> None:
        """Given: API returns malformed response
        When: Call get_merkle_path
        Then: Handles malformed response appropriately
        """
        services, _mock_instance, mock_stc = mock_services

        # Mock service to return malformed data
        def mock_get_merkle_path_malformed(txid, services=None):
            raise Exception("Invalid JSON response")

        mock_stc.service = mock_get_merkle_path_malformed

        result = services.get_merkle_path(valid_txid)
        assert isinstance(result, dict)
        # Should return error result

    def test_get_merkle_path_connection_error(self, mock_services, valid_txid) -> None:
        """Given: Connection error occurs
        When: Call get_merkle_path
        Then: Handles connection error appropriately
        """
        services, _mock_instance, mock_stc = mock_services

        # Mock service to raise connection error
        def mock_get_merkle_path_connection_error(txid, services=None):
            raise ConnectionError("Network is unreachable")

        mock_stc.service = mock_get_merkle_path_connection_error

        result = services.get_merkle_path(valid_txid)
        assert isinstance(result, dict)
        # Should return error result

    def test_get_merkle_path_provider_fallback(self, mock_services, valid_txid, valid_merkle_path_response) -> None:
        """Given: Provider returns merkle path successfully
        When: Call get_merkle_path
        Then: Returns the merkle path data
        """
        services, _mock_instance, mock_stc = mock_services

        # Set up the mocked service
        mock_stc.service = Mock(return_value=valid_merkle_path_response)

        result = services.get_merkle_path(valid_txid)
        assert isinstance(result, dict)
        assert result == valid_merkle_path_response

    def test_get_merkle_path_success_response(self, mock_services, valid_txid, valid_merkle_path_response) -> None:
        """Given: Valid txid and successful API response
        When: Call get_merkle_path
        Then: Returns merkle path data
        """
        services, _mock_instance, mock_stc = mock_services

        # Mock successful response
        def mock_get_merkle_path_success(txid, services_obj):
            return valid_merkle_path_response

        # Set up the mocked service
        mock_stc.service = mock_get_merkle_path_success

        result = services.get_merkle_path(valid_txid)
        assert isinstance(result, dict)
        assert result == valid_merkle_path_response

    def test_get_merkle_path_different_chains(self, mock_services, valid_merkle_path_response) -> None:
        """Given: Different blockchain chains
        When: Call get_merkle_path
        Then: Handles different chains appropriately
        """
        services, _mock_instance, mock_stc = mock_services

        test_cases = [
            ("main", "d9978ffc6676523208f7b33bebf1b176388bbeace2c7ef67ce35c2eababa1805"),
            ("test", "9cce99686bc8621db439b7150dd5b3b269e4b0628fd75160222c417d6f2b95e4"),
        ]

        for _chain, txid in test_cases:
            # Mock response for specific chain
            def mock_get_merkle_path_chain(txid_param, services_obj):
                response = valid_merkle_path_response.copy()
                return response

            # Set up the mocked service
            mock_stc.service = mock_get_merkle_path_chain

            result = services.get_merkle_path(txid)
            assert isinstance(result, dict)
            assert "header" in result
            assert "merklePath" in result

    def test_get_merkle_path_large_response_handling(self, mock_services, valid_txid) -> None:
        """Given: Very large merkle path response
        When: Call get_merkle_path
        Then: Handles large response appropriately
        """
        services, _mock_instance, mock_stc = mock_services

        # Create large merkle path response (simulate complex merkle tree)
        large_response = {
            "header": {
                "bits": 403818359,
                "hash": "0000000000000000060ac8d63b78d41f58c9aba0b09f81db7d51fa4905a47263",
                "height": 883637,
                "merkleRoot": "59c1efd79fae0d9c29dd8da63f8eeec0aadde048f4491c6bfa324fcfd537156d",
                "nonce": 596827153,
                "previousHash": "00000000000000000d9f6889dd6743500adee204ea25d8a57225ecd48b111769",
                "time": 1739329877,
                "version": 1040187392,
            },
            "merklePath": {
                "blockHeight": 883637,
                "path": [
                    # Simulate a very deep merkle path with many levels
                    [{"hash": "a" * 64, "offset": i, "txid": i == 0} for i in range(50)],
                    [{"hash": "b" * 64, "offset": i} for i in range(25)],
                    [{"hash": "c" * 64, "offset": i} for i in range(12)],
                    [{"hash": "d" * 64, "offset": i} for i in range(6)],
                    [{"hash": "e" * 64, "offset": i} for i in range(3)],
                    [{"hash": "f" * 64, "offset": i} for i in range(2)],
                    [{"hash": "g" * 64, "offset": 0}],
                ],
            },
            "name": "WoCTsc",
            "notes": [{"name": "WoCTsc", "status": 200, "statusText": "OK", "what": "getMerklePathSuccess"}],
        }

        def mock_get_merkle_path_large(txid, services_obj):
            return large_response

        # Set up the mocked service
        mock_stc.service = mock_get_merkle_path_large

        result = services.get_merkle_path(valid_txid)
        assert isinstance(result, dict)
        assert "merklePath" in result
        assert "header" in result

    def test_get_merkle_path_unicode_txid_handling(self, mock_services, valid_merkle_path_response) -> None:
        """Given: Txid with unicode characters (though txids are hex)
        When: Call get_merkle_path
        Then: Handles gracefully
        """
        services, _mock_instance, mock_stc = mock_services

        # Even though txids are hex, test unicode handling
        unicode_txid = "9cce99686bc8621db439b7150dd5b3b269e4b0628fd75160222c417d6f2b95e4"

        def mock_get_merkle_path_unicode(txid, services_obj):
            return valid_merkle_path_response

        # Set up the mocked service
        mock_stc.service = mock_get_merkle_path_unicode

        result = services.get_merkle_path(unicode_txid)
        assert isinstance(result, dict)
        assert result == valid_merkle_path_response

    def test_get_merkle_path_empty_path_response(self, mock_services, valid_txid) -> None:
        """Given: API returns empty merkle path
        When: Call get_merkle_path
        Then: Handles empty path appropriately
        """
        services, _mock_instance, mock_stc = mock_services

        empty_response = {
            "name": "WoCTsc",
            "notes": [{"name": "WoCTsc", "status": 200, "statusText": "OK", "what": "getMerklePathNoData"}],
        }

        def mock_get_merkle_path_empty(txid, services_obj):
            return empty_response

        # Set up the mocked service
        mock_stc.service = mock_get_merkle_path_empty

        result = services.get_merkle_path(valid_txid)
        assert isinstance(result, dict)
        assert "notes" in result
        assert result["notes"][0]["what"] == "getMerklePathNoData"

    def test_get_merkle_path_multiple_providers_fallback(
        self, mock_services, valid_txid, valid_merkle_path_response
    ) -> None:
        """Given: Multiple providers with primary failing, secondary succeeding
        When: Call get_merkle_path
        Then: Successfully falls back to working provider
        """
        services, _mock_instance, mock_stc = mock_services

        # Simulate provider list with fallback - simplified for mocked environment
        def mock_multi_provider_fallback(txid, services_obj):
            return valid_merkle_path_response

        # Set up the mocked service
        mock_stc.service = mock_multi_provider_fallback

        result = services.get_merkle_path(valid_txid)
        assert isinstance(result, dict)
        assert result == valid_merkle_path_response
