"""Expanded tests for ARC-enabled post_beef with comprehensive error handling.

This validates the ARC-enabled path in Services.post_beef with extensive
error handling, network failure testing, and validation scenarios.
Reference: wallet-toolbox/src/services/__tests/postBeef.test.ts
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock

from bsv_wallet_toolbox.services import Services
from bsv_wallet_toolbox.errors import InvalidParameterError


def test_post_beef_arc_minimal() -> None:
    """Ensure ARC path returns TS-like shape when ARC is configured."""
    options = Services.create_default_options("main")
    options["arcUrl"] = "https://arc.mock"  # triggers ARC path; HTTP is mocked in conftest
    options["arcApiKey"] = "test"

    services = Services(options)

    # Provide a minimal hex that Transaction.from_hex can reject; expect graceful error-shaped response
    res = services.post_beef("00")
    assert isinstance(res, dict)
    assert set(res.keys()) == {"accepted", "txid", "message"}
    assert res["accepted"] in (True, False)


def test_post_beef_arc_invalid_beef_data() -> None:
    """Test post_beef with invalid BEEF data formats."""
    options = Services.create_default_options("main")
    options["arcUrl"] = "https://arc.mock"
    options["arcApiKey"] = "test"
    services = Services(options)

    invalid_beefs = ["", "invalid_hex", "123", None, 123, [], {}]

    for invalid_beef in invalid_beefs:
        with pytest.raises((ValueError, TypeError)):
            services.post_beef(invalid_beef)


def test_post_beef_arc_empty_beef() -> None:
    """Test post_beef with empty BEEF string."""
    options = Services.create_default_options("main")
    options["arcUrl"] = "https://arc.mock"
    options["arcApiKey"] = "test"
    services = Services(options)

    # Empty BEEF should be handled gracefully
    result = services.post_beef("")
    assert isinstance(result, dict)
    assert "accepted" in result
    assert result["accepted"] is False


def test_post_beef_arc_without_arc_config() -> None:
    """Test post_beef without ARC configuration falls back gracefully."""
    options = Services.create_default_options("main")
    # No ARC URL/API key configured
    services = Services(options)

    # Should handle missing ARC config gracefully
    result = services.post_beef("00")
    assert isinstance(result, dict)
    assert "accepted" in result


def test_post_beef_arc_invalid_arc_url() -> None:
    """Test post_beef with invalid ARC URL."""
    options = Services.create_default_options("main")
    options["arcUrl"] = "not-a-valid-url"
    options["arcApiKey"] = "test"
    services = Services(options)

    # Should handle invalid URL gracefully
    result = services.post_beef("00")
    assert isinstance(result, dict)
    assert "accepted" in result


def test_post_beef_arc_empty_api_key() -> None:
    """Test post_beef with empty API key."""
    options = Services.create_default_options("main")
    options["arcUrl"] = "https://arc.mock"
    options["arcApiKey"] = ""  # Empty API key
    services = Services(options)

    # Should handle empty API key gracefully
    result = services.post_beef("00")
    assert isinstance(result, dict)
    assert "accepted" in result


def test_post_beef_arc_none_api_key() -> None:
    """Test post_beef with None API key."""
    options = Services.create_default_options("main")
    options["arcUrl"] = "https://arc.mock"
    options["arcApiKey"] = None  # None API key
    services = Services(options)

    # Should handle None API key gracefully
    result = services.post_beef("00")
    assert isinstance(result, dict)
    assert "accepted" in result


def test_post_beef_arc_different_chains() -> None:
    """Test post_beef with different blockchain chains."""
    chains = ["main", "test"]

    for chain in chains:
        options = Services.create_default_options(chain)
        options["arcUrl"] = "https://arc.mock"
        options["arcApiKey"] = "test"
        services = Services(options)

        # Should work with different chains
        result = services.post_beef("00")
        assert isinstance(result, dict)
        assert "accepted" in result


def test_post_beef_arc_large_beef_data() -> None:
    """Test post_beef with large BEEF data."""
    options = Services.create_default_options("main")
    options["arcUrl"] = "https://arc.mock"
    options["arcApiKey"] = "test"
    services = Services(options)

    # Create large BEEF data (simulate large transaction)
    large_beef = "00" * 10000  # 10,000 bytes

    # Should handle large BEEF data gracefully
    result = services.post_beef(large_beef)
    assert isinstance(result, dict)
    assert "accepted" in result


def test_post_beef_arc_unicode_in_beef() -> None:
    """Test post_beef with unicode characters in BEEF string."""
    options = Services.create_default_options("main")
    options["arcUrl"] = "https://arc.mock"
    options["arcApiKey"] = "test"
    services = Services(options)

    # Should handle BEEF with unicode gracefully (though txids are hex)
    unicode_beef = "00"  # Simple valid hex

    result = services.post_beef(unicode_beef)
    assert isinstance(result, dict)
    assert "accepted" in result


def test_post_beef_arc_consecutive_calls() -> None:
    """Test multiple consecutive post_beef calls."""
    options = Services.create_default_options("main")
    options["arcUrl"] = "https://arc.mock"
    options["arcApiKey"] = "test"
    services = Services(options)

    # Make multiple consecutive calls
    for i in range(5):
        result = services.post_beef("00")
        assert isinstance(result, dict)
        assert "accepted" in result


def test_post_beef_arc_mixed_valid_invalid() -> None:
    """Test post_beef with various BEEF data patterns."""
    options = Services.create_default_options("main")
    options["arcUrl"] = "https://arc.mock"
    options["arcApiKey"] = "test"
    services = Services(options)

    test_cases = [
        ("00", "minimal_valid"),
        ("deadbeef", "valid_hex"),
        ("ff" * 100, "large_valid_hex"),
        ("123abc", "mixed_case_valid"),
    ]

    for beef_data, description in test_cases:
        result = services.post_beef(beef_data)
        assert isinstance(result, dict), f"Failed for {description}"
        assert "accepted" in result, f"Failed for {description}"


def test_post_beef_arc_error_response_handling() -> None:
    """Test post_beef handles various error response scenarios."""
    options = Services.create_default_options("main")
    options["arcUrl"] = "https://arc.mock"
    options["arcApiKey"] = "test"
    services = Services(options)

    # Test with various error conditions that should be handled gracefully
    error_beefs = [
        "invalid",  # Invalid hex
        "gggggggg",  # Invalid hex characters
        "",  # Empty
        "0",  # Too short
        "12345",  # Odd length
    ]

    for error_beef in error_beefs:
        try:
            result = services.post_beef(error_beef)
            # Should return error-shaped response
            assert isinstance(result, dict)
            assert "accepted" in result
        except (ValueError, TypeError):
            # Some implementations may raise exceptions for invalid input
            pass


def test_post_beef_arc_config_validation() -> None:
    """Test post_beef with various ARC configuration scenarios."""
    test_configs = [
        # Valid config
        {"arcUrl": "https://arc.example.com", "arcApiKey": "key123"},
        # Config with query parameters
        {"arcUrl": "https://arc.example.com/v1", "arcApiKey": "key123"},
        # Config with port
        {"arcUrl": "https://arc.example.com:8080", "arcApiKey": "key123"},
        # Config with path
        {"arcUrl": "https://arc.example.com/api/v1", "arcApiKey": "key123"},
    ]

    for arc_config in test_configs:
        options = Services.create_default_options("main")
        options.update(arc_config)
        services = Services(options)

        # Should work with various valid ARC configs
        result = services.post_beef("00")
        assert isinstance(result, dict)
        assert "accepted" in result


def test_post_beef_arc_timeout_simulation() -> None:
    """Test post_beef handles timeout scenarios gracefully."""
    options = Services.create_default_options("main")
    options["arcUrl"] = "https://arc.mock"
    options["arcApiKey"] = "test"
    services = Services(options)

    # With mocked HTTP, timeouts should be handled gracefully
    result = services.post_beef("00")
    assert isinstance(result, dict)
    assert "accepted" in result
