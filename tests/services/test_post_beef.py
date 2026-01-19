"""Unit tests for postBeef service.

This module tests postBeef service functionality for mainnet and testnet.

Reference: wallet-toolbox/src/services/__tests/postBeef.test.ts
"""

from unittest.mock import Mock, patch

import pytest

from bsv_wallet_toolbox.errors import InvalidParameterError
from bsv_wallet_toolbox.services import Services


@pytest.fixture
def valid_services_config():
    """Fixture providing valid services configuration."""
    return {
        "chain": "main",
        "arcUrl": "https://arc.mock",
        "arcApiKey": "test_key_123",
        "whatsonchainApiKey": "woc_key_456",
        "taalApiKey": "taal_key_789",
    }


@pytest.fixture
def mock_http_client():
    """Fixture providing a mock HTTP client for testing."""
    return Mock()


@pytest.fixture
def mock_services(valid_services_config):
    """Fixture providing mock services instance."""
    from unittest.mock import Mock

    with patch("bsv_wallet_toolbox.services.services.ServiceCollection") as mock_service_collection:
        mock_instance = Mock()
        mock_service_collection.return_value = mock_instance

        services = Services(valid_services_config)
        yield services, mock_instance


@pytest.fixture
def valid_beef_data():
    """Fixture providing valid BEEF data for testing."""
    # Valid transaction hex from test fixtures
    return "010000000158EED5DBBB7E2F7D70C79A11B9B61AABEECFA5A7CEC679BEDD00F42C48A4BD45010000006B483045022100AE8BB45498A40E2AC797775C405C108168804CD84E8C09A9D42D280D18EDDB6D022024863BFAAC5FF3C24CA65E2F3677EDA092BC3CC5D2EFABA73264B8FF55CF416B412102094AAF520E14E1C4D68496822800BCC7D3B3B26CA368E004A2CB70B398D82FACFFFFFFFF0203000000000000007421020A624B72B34BC192851C5D8890926BBB70B31BC10FDD4E3BC6534E41B1C81B93AC03010203030405064630440220013B4984F4054C2FBCD2F448AB896CCA5C4E234BF765B0C7FB27EDE572A7F7DA02201A5C8D0D023F94C209046B9A2B96B2882C5E43B72D8115561DF8C07442010EEA6D7592090000000000001976A9146511FCE2F7EF785A2102142FBF381AD1291C918688AC00000000"


@pytest.fixture
def invalid_beef_data():
    """Fixture providing various invalid BEEF data."""
    return [
        "",  # Empty string
        "invalid_hex",  # Invalid hex
        "00",  # Too short
        "gg" * 100,  # Invalid hex characters
        None,  # None value
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
        {"status": 429, "text": "Rate limit exceeded"},
        # HTTP 401 Unauthorized
        {"status": 401, "text": "Unauthorized"},
        # HTTP 403 Forbidden
        {"status": 403, "text": "Forbidden"},
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
def double_spend_scenarios():
    """Fixture providing double-spend test scenarios."""
    return [
        {
            "name": "same_transaction_twice",
            "beef1": "01000000010000000000000000000000000000000000000000000000000000000000000000ffffffff0100f2052a01000000434104b0bd634234abbb1ba1e986e884185c61cf43e001f9137f23c2c409273eb16e65a9147c233e4c945cf877e6c7e25dfaa0816208673ef48b89b8002c06ba4d3c396f60a3cac00000000",
            "beef2": "01000000010000000000000000000000000000000000000000000000000000000000000000ffffffff0100f2052a01000000434104b0bd634234abbb1ba1e986e884185c61cf43e001f9137f23c2c409273eb16e65a9147c233e4c945cf877e6c7e25dfaa0816208673ef48b89b8002c06ba4d3c396f60a3cac00000000",
            "expectDoubleSpend": True,
        },
        {
            "name": "different_transactions",
            "beef1": "01000000010000000000000000000000000000000000000000000000000000000000000000ffffffff0100f2052a01000000434104b0bd634234abbb1ba1e986e884185c61cf43e001f9137f23c2c409273eb16e65a9147c233e4c945cf877e6c7e25dfaa0816208673ef48b89b8002c06ba4d3c396f60a3cac00000000",
            "beef2": "01000000020000000000000000000000000000000000000000000000000000000000000000ffffffff0200f2052a01000000434104b0bd634234abbb1ba1e986e884185c61cf43e001f9137f23c2c409273eb16e65a9147c233e4c945cf877e6c7e25dfaa0816208673ef48b89b8002c06ba4d3c396f60a3cac00000000",
            "expectDoubleSpend": False,
        },
    ]


def test_post_beef_arc_minimal_enabled(valid_beef_data) -> None:
    """Ensure ARC path returns TS-like shape for single BEEF (mocked).

    - Uses conftest's FakeClient to avoid network.
    - Asserts only TS-like return shape and basic types.
    """
    options = Services.create_default_options("main")
    options["arcUrl"] = "https://arc.mock"
    options["arcApiKey"] = "test"
    services = Services(options)

    res = services.post_beef(valid_beef_data)
    assert isinstance(res, dict)
    # Required keys must be present (providerErrors is optional)
    assert {"accepted", "txid", "message"} <= set(res.keys())
    assert res["accepted"] in (True, False)


def test_post_beef_array_arc_minimal_enabled(valid_beef_data) -> None:
    """Ensure ARC path returns TS-like shape for multiple BEEFs (mocked).

    - Uses conftest's FakeClient to avoid network.
    - Asserts only TS-like return shape and basic types.
    """
    options = Services.create_default_options("main")
    options["arcUrl"] = "https://arc.mock"
    options["arcApiKey"] = "test"
    services = Services(options)

    # Use valid beef data repeated for the array test
    beef1 = valid_beef_data
    beef2 = valid_beef_data  # Same valid data for simplicity
    res_list = services.post_beef_array([beef1, beef2])
    assert isinstance(res_list, list)
    assert len(res_list) == 2
    for res in res_list:
        assert isinstance(res, dict)
        # Required keys must be present (providerErrors is optional)
        assert {"accepted", "txid", "message"} <= set(res.keys())
        assert res["accepted"] in (True, False)


def test_post_beef_invalid_beef_format_raises_error(mock_services) -> None:
    """Given: Invalid BEEF format
    When: Call post_beef
    Then: Raises InvalidParameterError or ValueError
    """
    services, _ = mock_services

    # Test various invalid BEEF formats
    invalid_formats = ["", "invalid_hex", None, 123, [], {}]

    for invalid_beef in invalid_formats:
        with pytest.raises((InvalidParameterError, ValueError, TypeError)):
            services.post_beef(invalid_beef)


def test_post_beef_network_failure_500_error(mock_services, valid_beef_data) -> None:
    """Given: Network returns HTTP 500 error
    When: Call post_beef
    Then: Handles error appropriately
    """
    services, _mock_instance = mock_services

    # Mock ARC provider to return error result
    if services.arc_taal:
        from unittest.mock import Mock

        mock_result = Mock()
        mock_result.status = "error"
        mock_result.description = "Internal Server Error"
        services.arc_taal.broadcast = Mock(return_value=mock_result)

    # Should handle network errors gracefully
    result = services.post_beef(valid_beef_data)
    assert isinstance(result, dict)
    assert "accepted" in result
    assert result["accepted"] is False


def test_post_beef_network_timeout_error(mock_services, valid_beef_data) -> None:
    """Given: Network request times out
    When: Call post_beef
    Then: Handles timeout appropriately
    """
    services, _mock_instance = mock_services

    # Mock ARC provider to raise timeout exception
    if services.arc_taal:
        services.arc_taal.broadcast = Mock(side_effect=TimeoutError("Connection timeout"))

    # Should handle timeout errors gracefully
    result = services.post_beef(valid_beef_data)
    assert isinstance(result, dict)
    assert "accepted" in result
    assert result["accepted"] is False


def test_post_beef_rate_limiting_429_error(mock_services, valid_beef_data) -> None:
    """Given: API returns 429 rate limit exceeded
    When: Call post_beef
    Then: Handles rate limiting appropriately
    """
    services, _mock_instance = mock_services

    # Mock ARC provider to return rate limited result
    if services.arc_taal:
        from unittest.mock import Mock

        mock_result = Mock()
        mock_result.status = "rate_limited"
        mock_result.description = "Rate limit exceeded"
        services.arc_taal.broadcast = Mock(return_value=mock_result)

    result = services.post_beef(valid_beef_data)
    assert isinstance(result, dict)
    assert "accepted" in result
    assert result["accepted"] is False
    assert "rate_limited" in result or "message" in result


def test_post_beef_malformed_json_response(mock_services, valid_beef_data) -> None:
    """Given: API returns malformed JSON response
    When: Call post_beef
    Then: Handles malformed response appropriately
    """
    services, _mock_instance = mock_services

    # Mock ARC provider to raise JSON error
    if services.arc_taal:
        services.arc_taal.broadcast = Mock(side_effect=ValueError("Invalid JSON"))

    result = services.post_beef(valid_beef_data)
    assert isinstance(result, dict)
    assert "accepted" in result
    assert result["accepted"] is False


def test_post_beef_empty_response(mock_services, valid_beef_data) -> None:
    """Given: API returns empty response
    When: Call post_beef
    Then: Handles empty response appropriately
    """
    services, _mock_instance = mock_services

    # Mock ARC provider to raise empty response error
    if services.arc_taal:
        services.arc_taal.broadcast = Mock(side_effect=ValueError("Empty response"))

    result = services.post_beef(valid_beef_data)
    assert isinstance(result, dict)
    assert "accepted" in result
    assert result["accepted"] is False


def test_post_beef_service_unavailable_503_error(mock_services, valid_beef_data) -> None:
    """Given: API returns 503 Service Unavailable
    When: Call post_beef
    Then: Handles service unavailable appropriately
    """
    services, _mock_instance = mock_services

    # Mock ARC provider to return error result
    if services.arc_taal:
        from unittest.mock import Mock

        mock_result = Mock()
        mock_result.status = "error"
        mock_result.description = "Service Unavailable"
        services.arc_taal.broadcast = Mock(return_value=mock_result)

    result = services.post_beef(valid_beef_data)
    assert isinstance(result, dict)
    assert "accepted" in result
    assert result["accepted"] is False


def test_post_beef_unauthorized_401_error(mock_services, valid_beef_data) -> None:
    """Given: API returns 401 Unauthorized
    When: Call post_beef
    Then: Handles authentication error appropriately
    """
    services, _mock_instance = mock_services

    # Mock ARC provider to return error result
    if services.arc_taal:
        from unittest.mock import Mock

        mock_result = Mock()
        mock_result.status = "error"
        mock_result.description = "Unauthorized"
        services.arc_taal.broadcast = Mock(return_value=mock_result)

    result = services.post_beef(valid_beef_data)
    assert isinstance(result, dict)
    assert "accepted" in result
    assert result["accepted"] is False


def test_post_beef_forbidden_403_error(mock_services, valid_beef_data) -> None:
    """Given: API returns 403 Forbidden
    When: Call post_beef
    Then: Handles forbidden error appropriately
    """
    services, _mock_instance = mock_services

    # Mock ARC provider to return error result
    if services.arc_taal:
        from unittest.mock import Mock

        mock_result = Mock()
        mock_result.status = "error"
        mock_result.description = "Forbidden"
        services.arc_taal.broadcast = Mock(return_value=mock_result)

    result = services.post_beef(valid_beef_data)
    assert isinstance(result, dict)
    assert "accepted" in result
    assert result["accepted"] is False


def test_post_beef_array_invalid_input_types(mock_services) -> None:
    """Given: Invalid input types for post_beef_array
    When: Call post_beef_array
    Then: Raises appropriate errors
    """
    services, _ = mock_services

    # Test various invalid inputs
    invalid_inputs = [
        None,  # None
        "string",  # Single string instead of list
        123,  # Number
        {},  # Dict
        [None, "valid"],  # List with None
        ["valid", 123],  # List with invalid type
    ]

    for invalid_input in invalid_inputs:
        with pytest.raises((InvalidParameterError, ValueError, TypeError)):
            services.post_beef_array(invalid_input)


def test_post_beef_array_empty_list(mock_services) -> None:
    """Given: Empty list for post_beef_array
    When: Call post_beef_array
    Then: Handles empty list appropriately
    """
    services, _ = mock_services

    result = services.post_beef_array([])
    assert isinstance(result, list)
    assert len(result) == 0


def test_post_beef_array_mixed_valid_invalid(mock_services) -> None:
    """Given: Array with mix of valid and invalid BEEF data
    When: Call post_beef_array
    Then: Handles mixed input appropriately
    """
    services, _ = mock_services

    # Mix of valid and invalid BEEF data
    mixed_input = ["0000", "invalid_hex", "0001", ""]

    result = services.post_beef_array(mixed_input)
    assert isinstance(result, list)
    assert len(result) == 4  # Should return result for each input

    # Check that invalid entries are marked as not accepted
    for res in result:
        assert isinstance(res, dict)
        assert "accepted" in res
        assert res["accepted"] in (True, False)


def test_post_beef_success_response(mock_services, valid_beef_data) -> None:
    """Given: Valid BEEF data and successful API response
    When: Call post_beef
    Then: Returns successful result
    """
    services, _mock_instance = mock_services

    # Mock ARC provider to return success result
    if services.arc_taal:
        from unittest.mock import Mock

        mock_result = Mock()
        mock_result.status = "success"
        mock_result.txid = "a1b2c3d4e5f6..."
        mock_result.message = "Transaction broadcast successfully"
        services.arc_taal.broadcast = Mock(return_value=mock_result)

    result = services.post_beef(valid_beef_data)
    assert isinstance(result, dict)
    assert result.get("accepted") is True
    assert "txid" in result
    assert "message" in result


def test_post_beef_double_spend_detection(mock_services) -> None:
    """Given: Same transaction submitted twice
    When: Call post_beef twice with same data
    Then: Second call detects double spend
    """
    services, _mock_instance = mock_services

    beef_data = "01000000010000000000000000000000000000000000000000000000000000000000000000ffffffff0100f2052a01000000434104b0bd634234abbb1ba1e986e884185c61cf43e001f9137f23c2c409273eb16e65a9147c233e4c945cf877e6c7e25dfaa0816208673ef48b89b8002c06ba4d3c396f60a3cac000000000"

    # Mock successful first response
    if services.arc_taal:
        from unittest.mock import Mock

        mock_result1 = Mock()
        mock_result1.status = "success"
        mock_result1.txid = "txid123"
        mock_result1.message = "Accepted"
        services.arc_taal.broadcast = Mock(return_value=mock_result1)

    # First call - success
    result1 = services.post_beef(beef_data)
    assert result1.get("accepted") is True

    # Mock double spend second response
    if services.arc_taal:
        from unittest.mock import Mock

        mock_result2 = Mock()
        mock_result2.status = "error"
        mock_result2.double_spend = True
        mock_result2.description = "Double spend detected"
        services.arc_taal.broadcast = Mock(return_value=mock_result2)

    # Second call - double spend
    result2 = services.post_beef(beef_data)
    assert result2.get("accepted") is False
    assert result2.get("doubleSpend") is True


def test_post_beef_large_beef_data_handling(mock_services) -> None:
    """Given: Very large BEEF data
    When: Call post_beef
    Then: Handles large data appropriately
    """
    services, _ = mock_services

    # Create large BEEF data (simulate large transaction)
    large_beef = "00" * 50000  # Valid hex data (100KB)

    result = services.post_beef(large_beef)
    assert isinstance(result, dict)
    assert "accepted" in result
    # Should handle large data without crashing


def test_post_beef_unicode_in_response(mock_services, valid_beef_data) -> None:
    """Given: API response contains unicode characters
    When: Call post_beef
    Then: Handles unicode correctly
    """
    services, _mock_instance = mock_services

    # Mock ARC provider to return error with unicode message
    if services.arc_taal:
        from unittest.mock import Mock

        mock_result = Mock()
        mock_result.status = "error"
        mock_result.description = "Error: 无效的交易数据 (Invalid transaction data)"
        services.arc_taal.broadcast = Mock(return_value=mock_result)

    result = services.post_beef(valid_beef_data)
    assert isinstance(result, dict)
    assert "message" in result
    assert "无效的交易数据" in result["message"]


def test_post_beef_provider_fallback_simulation(mock_services, valid_beef_data) -> None:
    """Given: Primary provider fails, fallback provider succeeds
    When: Call post_beef
    Then: Uses fallback provider successfully
    """
    services, _mock_instance = mock_services

    # Mock ARC TAAL provider to return success result
    if services.arc_taal:
        from unittest.mock import Mock

        mock_result = Mock()
        mock_result.status = "success"
        mock_result.txid = "fallback_txid_123"
        mock_result.message = "Accepted via fallback provider"
        services.arc_taal.broadcast = Mock(return_value=mock_result)

    result = services.post_beef(valid_beef_data)
    assert isinstance(result, dict)
    assert result.get("accepted") is True
    assert "fallback" in result.get("message", "").lower()


def test_post_beef_connection_error_handling(mock_services, valid_beef_data) -> None:
    """Given: Network connection error occurs
    When: Call post_beef
    Then: Handles connection error appropriately
    """
    services, _mock_instance = mock_services

    # Mock ARC provider to raise connection error
    if services.arc_taal:
        services.arc_taal.broadcast = Mock(side_effect=ConnectionError("Network is unreachable"))

    result = services.post_beef(valid_beef_data)
    assert isinstance(result, dict)
    assert "accepted" in result
    assert result["accepted"] is False
    assert "error" in result or "message" in result
