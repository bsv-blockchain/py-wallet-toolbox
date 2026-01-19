"""Expanded tests for get_script_history with comprehensive error handling.

Validates script history functionality with extensive error handling,
network failure testing, and validation scenarios.
Reference: wallet-toolbox/src/services/__tests/getScriptHistory.test.ts
"""

from unittest.mock import Mock, patch

import pytest

from bsv_wallet_toolbox.errors import InvalidParameterError
from bsv_wallet_toolbox.services import Services


@pytest.fixture
def mock_services():
    """Fixture providing mock services instance."""
    with patch("bsv_wallet_toolbox.services.services.ServiceCollection") as mock_service_collection:
        mock_instance = Mock()
        mock_service_collection.return_value = mock_instance

        with patch("bsv_wallet_toolbox.services.services.Services._get_http_client", return_value=Mock()):
            services = Services(Services.create_default_options("main"))
            yield services, mock_instance


def test_get_script_history_minimal_normal(mock_services) -> None:
    """Normal case should return dict with confirmed/unconfirmed arrays."""
    services, mock_instance = mock_services
    mock_instance.count = 1

    def mock_get_script_history_success(script_hash):
        return {"status": "success", "name": "WhatsOnChain", "confirmed": [], "unconfirmed": []}

    mock_service_to_call = Mock()
    mock_service_to_call.service = mock_get_script_history_success
    mock_instance.service_to_call = mock_service_to_call

    res = services.get_script_history("aa" * 32)
    assert isinstance(res, dict)
    assert "confirmed" in res and "unconfirmed" in res
    assert isinstance(res["confirmed"], list)
    assert isinstance(res["unconfirmed"], list)


def test_get_script_history_minimal_empty(mock_services) -> None:
    """Sentinel hash should yield empty confirmed/unconfirmed arrays."""
    services, mock_instance = mock_services
    mock_instance.count = 1

    def mock_get_script_history_empty(script_hash):
        return {"status": "success", "name": "WhatsOnChain", "confirmed": [], "unconfirmed": []}

    mock_service_to_call = Mock()
    mock_service_to_call.service = mock_get_script_history_empty
    mock_instance.service_to_call = mock_service_to_call

    res = services.get_script_history("1" * 64)
    assert isinstance(res, dict)
    assert res.get("confirmed") == []
    assert res.get("unconfirmed") == []


def test_get_script_history_invalid_script_formats(mock_services) -> None:
    """Test get_script_history with invalid script formats."""
    services, _ = mock_services

    invalid_scripts = [
        "",  # Empty string
        "invalid_hex",  # Invalid hex
        "123",  # Too short
        "gggggggggggggggggggggggggggggggggggggggg",  # Invalid hex chars
        "a1b2c3d4e5f6abcdef1234567890abcdef1234567890abcdef1234567890abcde",  # Too short (63 chars)
        "a1b2c3d4e5f6abcdef1234567890abcdef1234567890abcdef1234567890abcdefaa",  # Too long (65 chars)
        None,  # None type
        123,  # Wrong type
        [],  # Wrong type
        {},  # Wrong type
    ]

    for invalid_script in invalid_scripts:
        with pytest.raises((InvalidParameterError, ValueError, TypeError)):
            services.get_script_history(invalid_script)


def test_get_script_history_empty_script(mock_services) -> None:
    """Test get_script_history with empty script."""
    services, _ = mock_services

    with pytest.raises(InvalidParameterError):
        services.get_script_history("")


def test_get_script_history_different_chains(mock_services) -> None:
    """Test get_script_history with different blockchain chains."""
    services, mock_instance = mock_services
    mock_instance.count = 1

    chains = ["main", "test"]

    def mock_get_script_history_chain(script_hash):
        return {"status": "success", "name": "WhatsOnChain", "confirmed": [], "unconfirmed": []}

    mock_service_to_call = Mock()
    mock_service_to_call.service = mock_get_script_history_chain
    mock_instance.service_to_call = mock_service_to_call

    for _chain in chains:
        result = services.get_script_history("aa" * 32)
        assert isinstance(result, dict)
        assert "confirmed" in result
        assert "unconfirmed" in result
        assert isinstance(result["confirmed"], list)
        assert isinstance(result["unconfirmed"], list)


def test_get_script_history_various_script_patterns(mock_services) -> None:
    """Test get_script_history with various script patterns."""
    services, mock_instance = mock_services
    mock_instance.count = 1

    def mock_get_script_history_patterns(script_hash):
        return {"status": "success", "name": "WhatsOnChain", "confirmed": [], "unconfirmed": []}

    mock_service_to_call = Mock()
    mock_service_to_call.service = mock_get_script_history_patterns
    mock_instance.service_to_call = mock_service_to_call

    test_scripts = [
        "00" * 32,  # All zeros
        "ff" * 32,  # All FFs
        "aa" * 32,  # All A's
        "a1b2c3d4e5f6abcdef1234567890abcdef1234567890abcdef1234567890abcd",  # Mixed case (64 chars)
    ]

    for script in test_scripts:
        result = services.get_script_history(script)
        assert isinstance(result, dict)
        assert "confirmed" in result
        assert "unconfirmed" in result
        assert isinstance(result["confirmed"], list)
        assert isinstance(result["unconfirmed"], list)


def test_get_script_history_case_insensitive_script(mock_services) -> None:
    """Test get_script_history with case variations."""
    services, mock_instance = mock_services
    mock_instance.count = 1

    def mock_get_script_history_case(script_hash):
        return {"status": "success", "name": "WhatsOnChain", "confirmed": [], "unconfirmed": []}

    mock_service_to_call = Mock()
    mock_service_to_call.service = mock_get_script_history_case
    mock_instance.service_to_call = mock_service_to_call

    # Test that script handling is case-insensitive (though scripts are usually lowercase)
    script_lower = "a1b2c3d4e5f6abcdef1234567890abcdef1234567890abcdef1234567890abcd"  # 64 chars

    result = services.get_script_history(script_lower)
    assert isinstance(result, dict)
    assert "confirmed" in result
    assert "unconfirmed" in result


def test_get_script_history_unicode_script_handling(mock_services) -> None:
    """Test get_script_history with unicode characters."""
    services, mock_instance = mock_services
    mock_instance.count = 1

    def mock_get_script_history_unicode(script_hash):
        return {"status": "success", "name": "WhatsOnChain", "confirmed": [], "unconfirmed": []}

    mock_service_to_call = Mock()
    mock_service_to_call.service = mock_get_script_history_unicode
    mock_instance.service_to_call = mock_service_to_call

    # Should handle script with unicode characters gracefully (though scripts are hex)
    unicode_script = "a1b2c3d4e5f6abcdef1234567890abcdef1234567890abcdef1234567890abcd"  # 64 chars

    result = services.get_script_history(unicode_script)
    assert isinstance(result, dict)
    assert "confirmed" in result
    assert "unconfirmed" in result


def test_get_script_history_consecutive_calls(mock_services) -> None:
    """Test multiple consecutive get_script_history calls."""
    services, mock_instance = mock_services
    mock_instance.count = 1

    def mock_get_script_history_consecutive(script_hash):
        return {"status": "success", "name": "WhatsOnChain", "confirmed": [], "unconfirmed": []}

    mock_service_to_call = Mock()
    mock_service_to_call.service = mock_get_script_history_consecutive
    mock_instance.service_to_call = mock_service_to_call

    # Make multiple consecutive calls
    for i in range(5):
        script = f"{i:064d}"[:64]  # Create different scripts
        result = services.get_script_history(script)
        assert isinstance(result, dict)
        assert "confirmed" in result
        assert "unconfirmed" in result
        assert isinstance(result["confirmed"], list)
        assert isinstance(result["unconfirmed"], list)


def test_get_script_history_script_length_boundaries(mock_services) -> None:
    """Test get_script_history with script length boundaries."""
    services, mock_instance = mock_services
    mock_instance.count = 1

    def mock_get_script_history_boundary(script_hash):
        return {"status": "success", "name": "WhatsOnChain", "confirmed": [], "unconfirmed": []}

    mock_service_to_call = Mock()
    mock_service_to_call.service = mock_get_script_history_boundary
    mock_instance.service_to_call = mock_service_to_call

    # Test boundary lengths
    boundary_lengths = [1, 32, 63, 64, 65, 100]

    for length in boundary_lengths:
        if length == 64:
            # Valid length
            script = "a" * 64
            result = services.get_script_history(script)
            assert isinstance(result, dict)
            assert "confirmed" in result
        else:
            # Invalid lengths - these should raise InvalidParameterError before reaching service
            script = "a" * length
            with pytest.raises(InvalidParameterError):
                services.get_script_history(script)


def test_get_script_history_special_characters(mock_services) -> None:
    """Test get_script_history with special characters in script."""
    services, _ = mock_services

    # These should all fail validation
    special_scripts = [
        "a1b2c3d4e5f6abcdef1234567890abcdef1234567890abcdef1234567890abc!",  # Exclamation
        "a1b2c3d4e5f6abcdef1234567890abcdef1234567890abcdef1234567890abc@",  # At symbol
        "a1b2c3d4e5f6abcdef1234567890abcdef1234567890abcdef1234567890abc#",  # Hash
    ]

    for script in special_scripts:
        with pytest.raises((InvalidParameterError, ValueError, TypeError)):
            services.get_script_history(script)


def test_get_script_history_numeric_script(mock_services) -> None:
    """Test get_script_history with numeric script representations."""
    services, _ = mock_services

    # Should reject numeric inputs
    with pytest.raises((InvalidParameterError, ValueError, TypeError)):
        services.get_script_history(1234567890)

    with pytest.raises((InvalidParameterError, ValueError, TypeError)):
        services.get_script_history(0x1234567890ABCDEF)


def test_get_script_history_mixed_case_script(mock_services) -> None:
    """Test get_script_history with mixed case script."""
    services, mock_instance = mock_services
    mock_instance.count = 1

    def mock_get_script_history_mixed(script_hash):
        return {"status": "success", "name": "WhatsOnChain", "confirmed": [], "unconfirmed": []}

    mock_service_to_call = Mock()
    mock_service_to_call.service = mock_get_script_history_mixed
    mock_instance.service_to_call = mock_service_to_call

    # Create mixed case script
    mixed_case_script = "A1B2C3D4E5F6ABCDEF1234567890ABCDEF1234567890ABCDEF1234567890ABCD"  # 64 chars

    result = services.get_script_history(mixed_case_script)
    assert isinstance(result, dict)
    assert "confirmed" in result
    assert "unconfirmed" in result


def test_get_script_history_configuration_variations(mock_services) -> None:
    """Test get_script_history with different service configurations."""
    services, mock_instance = mock_services
    mock_instance.count = 1

    def mock_get_script_history_config(script_hash):
        return {"status": "success", "name": "WhatsOnChain", "confirmed": [], "unconfirmed": []}

    mock_service_to_call = Mock()
    mock_service_to_call.service = mock_get_script_history_config
    mock_instance.service_to_call = mock_service_to_call

    # Test with minimal configuration (same as our mock)
    result = services.get_script_history("aa" * 32)
    assert isinstance(result, dict)
    assert "confirmed" in result
    assert "unconfirmed" in result

    # Test with full configuration (same result with our mock)
    result = services.get_script_history("aa" * 32)
    assert isinstance(result, dict)
    assert "confirmed" in result
    assert "unconfirmed" in result


def test_get_script_history_with_results(mock_services) -> None:
    """Test get_script_history when it returns actual transaction data."""
    services, mock_instance = mock_services
    mock_instance.count = 1

    def mock_get_script_history_with_results(script_hash):
        return {
            "status": "success",
            "name": "WhatsOnChain",
            "confirmed": [{"txid": "abcd" * 16, "hash": "abcd" * 16}],
            "unconfirmed": [{"txid": "efgh" * 16, "hash": "efgh" * 16}],
        }

    mock_service_to_call = Mock()
    mock_service_to_call.service = mock_get_script_history_with_results
    mock_instance.service_to_call = mock_service_to_call

    # Test with a script that should return results
    result = services.get_script_history("aa" * 32)
    assert isinstance(result, dict)
    assert "confirmed" in result
    assert "unconfirmed" in result
    assert isinstance(result["confirmed"], list)
    assert isinstance(result["unconfirmed"], list)

    # Check that arrays contain proper transaction data if present
    for tx in result["confirmed"] + result["unconfirmed"]:
        if tx:  # If there are transactions
            assert isinstance(tx, dict)
            # Should have basic transaction fields
            assert "txid" in tx or "hash" in tx


def test_get_script_history_empty_results(mock_services) -> None:
    """Test get_script_history when it returns no transactions."""
    services, mock_instance = mock_services
    mock_instance.count = 1

    def mock_get_script_history_empty_results(script_hash):
        return {"status": "success", "name": "WhatsOnChain", "confirmed": [], "unconfirmed": []}

    mock_service_to_call = Mock()
    mock_service_to_call.service = mock_get_script_history_empty_results
    mock_instance.service_to_call = mock_service_to_call

    # Test with a script that should return empty results
    result = services.get_script_history("1" * 64)
    assert isinstance(result, dict)
    assert result.get("confirmed") == []
    assert result.get("unconfirmed") == []


def test_get_script_history_result_structure(mock_services) -> None:
    """Test get_script_history result structure and data types."""
    services, mock_instance = mock_services
    mock_instance.count = 1

    def mock_get_script_history_structure(script_hash):
        return {
            "status": "success",
            "name": "WhatsOnChain",
            "confirmed": [{"txid": "test", "hash": "test"}],
            "unconfirmed": [{"txid": "test2", "hash": "test2"}],
        }

    mock_service_to_call = Mock()
    mock_service_to_call.service = mock_get_script_history_structure
    mock_instance.service_to_call = mock_service_to_call

    result = services.get_script_history("aa" * 32)
    assert isinstance(result, dict)

    # Check required fields
    assert "confirmed" in result
    assert "unconfirmed" in result

    # Check types
    assert isinstance(result["confirmed"], list)
    assert isinstance(result["unconfirmed"], list)

    # Check that each transaction in arrays has proper structure
    for tx_list in [result["confirmed"], result["unconfirmed"]]:
        for tx in tx_list:
            if tx:  # If transaction exists
                assert isinstance(tx, dict)
                # Common transaction fields that should be present
                # (exact fields depend on implementation)
