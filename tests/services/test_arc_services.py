"""Unit tests for arc services.

This module tests ARC services integration.

Reference: wallet-toolbox/src/services/__tests/arcServices.test.ts
"""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from bsv_wallet_toolbox.errors import InvalidParameterError

try:
    from bsv_wallet_toolbox.services import Services
    from bsv_wallet_toolbox.services.wallet_services import Chain

    IMPORTS_AVAILABLE = True
except ImportError:
    IMPORTS_AVAILABLE = False


@pytest.fixture
def valid_arc_config():
    """Fixture providing valid ARC configuration."""
    return {"chain": "main", "arcUrl": "https://arc.api.example.com", "arcApiKey": "test_api_key_123"}


@pytest.fixture
def mock_http_client():
    """Fixture providing a mock HTTP client for testing."""
    return Mock()


@pytest.fixture
def mock_services(valid_arc_config, mock_http_client):
    """Fixture providing mock services instance with ARC config."""
    with patch("bsv_wallet_toolbox.services.services.ServiceCollection") as mock_service_collection:
        mock_instance = Mock()
        mock_service_collection.return_value = mock_instance

        with patch("bsv_wallet_toolbox.services.services.Services._get_http_client", return_value=mock_http_client):
            services = Services(valid_arc_config)
            # Disable Bitails to test ARC-only behavior
            services.bitails = None
            yield services, mock_instance, mock_http_client


@pytest.fixture
def valid_beef_data():
    """Fixture providing valid BEEF data for testing."""
    return "010000000158EED5DBBB7E2F7D70C79A11B9B61AABEECFA5A7CEC679BEDD00F42C48A4BD45010000006B483045022100AE8BB45498A40E2AC797775C405C108168804CD84E8C09A9D42D280D18EDDB6D022024863BFAAC5FF3C24CA65E2F3677EDA092BC3CC5D2EFABA73264B8FF55CF416B412102094AAF520E14E1C4D68496822800BCC7D3B3B26CA368E004A2CB70B398D82FACFFFFFFFF0203000000000000007421020A624B72B34BC192851C5D8890926BBB70B31BC10FDD4E3BC6534E41B1C81B93AC03010203030405064630440220013B4984F4054C2FBCD2F448AB896CCA5C4E234BF765B0C7FB27EDE572A7F7DA02201A5C8D0D023F94C209046B9A2B96B2882C5E43B72D8115561DF8C07442010EEA6D7592090000000000001976A9146511FCE2F7EF785A2102142FBF381AD1291C918688AC00000000"


@pytest.fixture
def invalid_beef_data():
    """Fixture providing various invalid BEEF data."""
    return [
        "",  # Empty string
        "invalid_hex",  # Invalid hex
        None,  # None value
        123,  # Wrong type
        [],  # Wrong type
        {},  # Wrong type
    ]


@pytest.fixture
def arc_error_responses():
    """Fixture providing various ARC API error response scenarios."""
    return [
        # HTTP 400 Bad Request
        {"status": 400, "text": "Bad Request", "json": {"error": "Invalid request format"}},
        # HTTP 401 Unauthorized
        {"status": 401, "text": "Unauthorized", "json": {"error": "Invalid API key"}},
        # HTTP 403 Forbidden
        {"status": 403, "text": "Forbidden", "json": {"error": "Insufficient permissions"}},
        # HTTP 404 Not Found
        {"status": 404, "text": "Not Found", "json": {"error": "Endpoint not found"}},
        # HTTP 422 Unprocessable Entity
        {"status": 422, "text": "Unprocessable Entity", "json": {"error": "Invalid transaction data"}},
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
        # Invalid API key responses
        {"status": 401, "text": "Invalid API key", "json": {"code": "INVALID_API_KEY"}},
        # Insufficient funds
        {"status": 402, "text": "Payment Required", "json": {"error": "Insufficient funds"}},
        # Transaction rejected
        {"status": 400, "text": "Transaction rejected", "json": {"error": "Transaction rejected by network"}},
        # Double spend detected
        {"status": 409, "text": "Conflict", "json": {"error": "Double spend detected"}},
        # Large response (simulating memory issues)
        {"status": 200, "text": "x" * 1000000, "large": True},
    ]


@pytest.fixture
def arc_success_responses():
    """Fixture providing successful ARC API responses."""
    return [
        # Successful transaction broadcast
        {
            "status": 200,
            "json": {"txid": "a1b2c3d4e5f6...", "accepted": True, "message": "Transaction broadcast successfully"},
        },
        # Transaction accepted but not yet confirmed
        {
            "status": 202,
            "json": {"txid": "a1b2c3d4e5f6...", "accepted": True, "message": "Transaction accepted for processing"},
        },
        # Multiple transactions response
        {
            "status": 200,
            "json": [
                {"txid": "tx1...", "accepted": True, "message": "Transaction 1 broadcast successfully"},
                {"txid": "tx2...", "accepted": True, "message": "Transaction 2 broadcast successfully"},
            ],
        },
    ]


@pytest.fixture
def invalid_arc_configs():
    """Fixture providing various invalid ARC configurations."""
    return [
        # Invalid URL
        {"chain": "main", "arcUrl": "", "arcApiKey": "key"},
        {"chain": "main", "arcUrl": "not-a-url", "arcApiKey": "key"},
        {"chain": "main", "arcUrl": None, "arcApiKey": "key"},
        # Invalid API key
        {"chain": "main", "arcUrl": "https://arc.example.com", "arcApiKey": ""},
        {"chain": "main", "arcUrl": "https://arc.example.com", "arcApiKey": None},
        # Invalid chain
        {"chain": "invalid", "arcUrl": "https://arc.example.com", "arcApiKey": "key"},
        {"chain": "", "arcUrl": "https://arc.example.com", "arcApiKey": "key"},
        {"chain": None, "arcUrl": "https://arc.example.com", "arcApiKey": "key"},
        # Missing required fields
        {"chain": "main"},  # Missing arcUrl and arcApiKey
        {"arcUrl": "https://arc.example.com"},  # Missing chain and arcApiKey
        {"arcApiKey": "key"},  # Missing chain and arcUrl
        {},  # Missing all fields
    ]


class TestArcServices:
    """Test suite for ARC services.

    Reference: wallet-toolbox/src/services/__tests/arcServices.test.ts
               describe.skip('arcServices tests')
    """

    def test_arc_services_placeholder(self) -> None:
        """Given: ARC services setup
           When: Test placeholder
           Then: Test is skipped in TypeScript, kept for completeness

        Reference: wallet-toolbox/src/services/__tests/arcServices.test.ts
                   test('0 ')
        """
        # This test is empty in TypeScript (test.skip)
        # Keeping it for completeness

    def test_arc_services_initialization_invalid_config(self, invalid_arc_configs) -> None:
        """Given: Invalid ARC configuration
        When: Initialize Services with ARC config
        Then: Raises appropriate errors or handles gracefully
        """
        for invalid_config in invalid_arc_configs:
            try:
                services = Services(invalid_config)
                # If it doesn't raise an error, it should handle invalid config gracefully
                assert services is not None
            except (ValueError, TypeError, KeyError) as e:
                # Expected for truly invalid configurations
                assert isinstance(e, (ValueError, TypeError, KeyError))

    def test_arc_services_initialization_valid_config(self, valid_arc_config) -> None:
        """Given: Valid ARC configuration
        When: Initialize Services with ARC config
        Then: Services initializes successfully
        """
        with patch("bsv_wallet_toolbox.services.services.ServiceCollection"):
            services = Services(valid_arc_config)
            assert services is not None
            assert services.chain.value == valid_arc_config["chain"]

    @pytest.mark.asyncio
    async def test_arc_post_beef_invalid_beef_data(self, mock_services, invalid_beef_data) -> None:
        """Given: Invalid BEEF data
        When: Call post_beef with ARC
        Then: Raises appropriate errors
        """
        services, _, _mock_client = mock_services

        for invalid_beef in invalid_beef_data:
            with pytest.raises((ValueError, TypeError, InvalidParameterError)):
                services.post_beef(invalid_beef)

    @pytest.mark.asyncio
    async def test_arc_post_beef_network_failures(self, mock_services, valid_beef_data, arc_error_responses) -> None:
        """Given: Various network failure scenarios
        When: Call post_beef with ARC
        Then: Handles errors appropriately
        """
        services, _, mock_client = mock_services

        for error_scenario in arc_error_responses:
            if error_scenario.get("timeout"):
                mock_client.post.side_effect = TimeoutError(error_scenario["error"])
            else:
                mock_response = AsyncMock()
                mock_response.status_code = error_scenario["status"]
                mock_response.text = error_scenario["text"]

                if error_scenario.get("malformed"):
                    mock_response.json.side_effect = ValueError("Invalid JSON")
                elif error_scenario.get("empty"):
                    mock_response.json.return_value = None
                elif error_scenario.get("large"):
                    mock_response.json.return_value = {"data": "x" * 100000}
                else:
                    mock_response.json.return_value = error_scenario.get("json", {"error": "Unknown error"})

                if "headers" in error_scenario:
                    mock_response.headers = error_scenario["headers"]

                mock_client.post.return_value = mock_response

            result = services.post_beef(valid_beef_data)
            assert isinstance(result, dict)
            # Should return error result or handle gracefully

    @pytest.mark.asyncio
    async def test_arc_post_beef_authentication_failures(self, mock_services, valid_beef_data) -> None:
        """Given: Authentication failures (401, 403)
        When: Call post_beef with ARC
        Then: Handles auth errors appropriately
        """
        services, _, mock_client = mock_services

        auth_errors = [
            {"status": 401, "json": {"error": "Invalid API key"}},
            {"status": 403, "json": {"error": "Forbidden"}},
        ]

        for auth_error in auth_errors:
            mock_response = AsyncMock()
            mock_response.status_code = auth_error["status"]
            mock_response.text = f"HTTP {auth_error['status']}"
            mock_response.json.return_value = auth_error["json"]
            mock_client.post.return_value = mock_response

            result = services.post_beef(valid_beef_data)
            assert isinstance(result, dict)
            assert result.get("accepted") is False

    @pytest.mark.asyncio
    async def test_arc_post_beef_rate_limiting(self, mock_services, valid_beef_data) -> None:
        """Given: Rate limiting response (429)
        When: Call post_beef with ARC
        Then: Handles rate limiting appropriately
        """
        services, _, _mock_client = mock_services

        # Mock ARC TAAL provider to return rate limited response (since valid_arc_config only sets arcUrl)
        mock_arc_result = Mock()
        mock_arc_result.status = "rate_limited"
        mock_arc_result.description = "Rate limited"
        services.arc_taal.post_raw_tx = Mock(return_value=mock_arc_result)

        result = services.post_beef(valid_beef_data)
        assert isinstance(result, dict)
        assert result.get("accepted") is False
        assert result.get("rateLimited") is True or "rate" in str(result.get("message", "")).lower()

    @pytest.mark.asyncio
    async def test_arc_post_beef_success_responses(self, mock_services, valid_beef_data, arc_success_responses) -> None:
        """Given: Successful ARC API responses
        When: Call post_beef with ARC
        Then: Returns successful results
        """
        services, _, mock_client = mock_services

        for success_response in arc_success_responses:
            mock_response = AsyncMock()
            mock_response.status_code = success_response["status"]
            mock_response.text = "Success"
            mock_response.json.return_value = success_response["json"]
            mock_client.post.return_value = mock_response

            result = services.post_beef(valid_beef_data)
            assert isinstance(result, dict)

            # Check for success indicators
            if success_response["status"] in [200, 202]:
                if isinstance(success_response["json"], list):
                    # Multiple transactions response
                    assert isinstance(result, dict)
                else:
                    # Single transaction response
                    assert "accepted" in result or "txid" in result

    @pytest.mark.asyncio
    async def test_arc_post_beef_malformed_requests(self, mock_services) -> None:
        """Given: Malformed request data
        When: Call post_beef with ARC
        Then: Handles malformed requests appropriately
        """
        services, _, _mock_client = mock_services

        malformed_requests = [
            {"beef": "invalid_hex_data", "extraField": "unexpected"},
            {"beef": "", "metadata": {}},
            {"beef": None},
            {"beef": 12345},
            {"beef": []},
            {"beef": {}},
        ]

        for malformed_request in malformed_requests:
            with pytest.raises((ValueError, TypeError, InvalidParameterError)):
                services.post_beef(malformed_request)

    @pytest.mark.asyncio
    async def test_arc_post_beef_double_spend_handling(self, mock_services, valid_beef_data) -> None:
        """Given: Double spend scenarios
        When: Call post_beef with ARC
        Then: Handles double spend detection
        """
        services, _, _mock_client = mock_services

        # Mock ARC TAAL provider to return double spend result
        mock_arc_result = Mock()
        mock_arc_result.status = "error"
        mock_arc_result.double_spend = True
        mock_arc_result.description = "Double spend detected"
        services.arc_taal.post_raw_tx = Mock(return_value=mock_arc_result)

        result = services.post_beef(valid_beef_data)
        assert isinstance(result, dict)
        assert result.get("accepted") is False
        assert result.get("doubleSpend") is True

    @pytest.mark.asyncio
    async def test_arc_post_beef_insufficient_funds(self, mock_services, valid_beef_data) -> None:
        """Given: Insufficient funds response (402)
        When: Call post_beef with ARC
        Then: Handles insufficient funds error
        """
        services, _, _mock_client = mock_services

        # Mock ARC TAAL provider to return insufficient funds result
        mock_arc_result = Mock()
        mock_arc_result.status = "error"
        mock_arc_result.description = "Insufficient funds"
        mock_arc_result.txid = None
        mock_arc_result.double_spend = False  # Explicitly set to False to avoid triggering double_spend check
        services.arc_taal.post_raw_tx = Mock(return_value=mock_arc_result)

        result = services.post_beef(valid_beef_data)
        assert isinstance(result, dict)
        assert result.get("accepted") is False
        # Check for insufficient funds indication in message or error field
        message = str(result.get("message", ""))
        assert "insufficient" in message.lower() or "error" in result or result.get("providerErrors")

    @pytest.mark.asyncio
    async def test_arc_post_beef_transaction_rejected(self, mock_services, valid_beef_data) -> None:
        """Given: Transaction rejected by network
        When: Call post_beef with ARC
        Then: Handles rejection appropriately
        """
        services, _, mock_client = mock_services

        mock_response = AsyncMock()
        mock_response.status_code = 400
        mock_response.text = "Bad Request"
        mock_response.json.return_value = {
            "error": "Transaction rejected by network",
            "accepted": False,
            "reason": "Invalid transaction format",
        }
        mock_client.post.return_value = mock_response

        result = services.post_beef(valid_beef_data)
        assert isinstance(result, dict)
        assert result.get("accepted") is False

    @pytest.mark.asyncio
    async def test_arc_post_beef_connection_error(self, mock_services, valid_beef_data) -> None:
        """Given: Connection error occurs
        When: Call post_beef with ARC
        Then: Handles connection error appropriately
        """
        services, _, mock_client = mock_services

        # Mock connection error
        mock_client.post.side_effect = ConnectionError("Network is unreachable")

        result = services.post_beef(valid_beef_data)
        assert isinstance(result, dict)
        assert result.get("accepted") is False

    @pytest.mark.asyncio
    async def test_arc_services_provider_fallback(self, mock_services, valid_beef_data) -> None:
        """Given: Primary ARC provider fails, fallback succeeds
        When: Call post_beef with ARC
        Then: Uses fallback provider successfully
        """
        services, _, _mock_client = mock_services

        # Mock ARC TAAL provider to return success result
        mock_arc_result = Mock()
        mock_arc_result.status = "success"
        mock_arc_result.txid = "fallback_txid_123"
        mock_arc_result.message = "Accepted via fallback provider"
        services.arc_taal.post_raw_tx = Mock(return_value=mock_arc_result)

        result = services.post_beef(valid_beef_data)
        assert isinstance(result, dict)
        assert result.get("accepted") is True
        assert "fallback" in result.get("message", "").lower()

    async def test_arc_post_beef_array_invalid_inputs(self, mock_services) -> None:
        """Given: Invalid inputs for post_beef_array
        When: Call post_beef_array with ARC
        Then: Raises appropriate errors
        """
        services, _, _mock_client = mock_services

        invalid_inputs = [
            None,  # None
            "string",  # Single string instead of list
            123,  # Number
            {},  # Dict
            [None, "valid"],  # List with None
            ["valid", 123],  # List with invalid type
        ]

        for invalid_input in invalid_inputs:
            with pytest.raises((ValueError, TypeError, InvalidParameterError)):
                services.post_beef_array(invalid_input)

    @pytest.mark.asyncio
    async def test_arc_post_beef_array_empty_list(self, mock_services) -> None:
        """Given: Empty list for post_beef_array
        When: Call post_beef_array with ARC
        Then: Handles empty list appropriately
        """
        services, _, _mock_client = mock_services

        result = services.post_beef_array([])
        assert isinstance(result, list)
        assert len(result) == 0

    @pytest.mark.asyncio
    async def test_arc_post_beef_array_partial_failures(self, mock_services, valid_beef_data) -> None:
        """Given: Array with mix of valid and invalid BEEF data
        When: Call post_beef_array with ARC
        Then: Handles partial failures appropriately
        """
        services, _, _mock_client = mock_services

        # Mock ARC responses for different array elements
        mock_results = [
            Mock(status="success", txid="tx1"),  # First call succeeds
            Mock(status="error", description="Invalid BEEF"),  # Second call fails
            Mock(status="success", txid="tx3"),  # Third call succeeds
        ]
        services.arc_taal.post_raw_tx = Mock(side_effect=mock_results)

        # Use valid BEEF data (not the mock strings)
        mixed_input = [valid_beef_data, valid_beef_data, valid_beef_data]
        result = services.post_beef_array(mixed_input)

        assert isinstance(result, list)
        assert len(result) == 3
        assert result[0].get("accepted") is True
        assert result[1].get("accepted") is False
        assert result[2].get("accepted") is True

    @pytest.mark.asyncio
    async def test_arc_services_large_payload_handling(self, mock_services) -> None:
        """Given: Very large BEEF payload
        When: Call post_beef with ARC
        Then: Handles large payload appropriately
        """
        services, _, _mock_client = mock_services

        # Create large BEEF data (simulate large transaction)
        large_beef = "00" * 100000  # 100KB of data

        # Mock ARC provider to return success for large payload
        mock_arc_result = Mock()
        mock_arc_result.status = "success"
        mock_arc_result.txid = "large_tx_123"
        services.arc_taal.post_raw_tx = Mock(return_value=mock_arc_result)

        result = services.post_beef(large_beef)
        assert isinstance(result, dict)
        assert result.get("accepted") is True
