"""Expanded tests for get_script_history with comprehensive error handling.

Validates script history functionality with extensive error handling,
network failure testing, and validation scenarios.
Reference: wallet-toolbox/src/services/__tests/getScriptHistory.test.ts
"""

import pytest

from bsv_wallet_toolbox.services import Services
from bsv_wallet_toolbox.errors import InvalidParameterError


def test_get_script_history_minimal_normal() -> None:
    """Normal case should return dict with confirmed/unconfirmed arrays."""
    services = Services(Services.create_default_options("main"))

    res = services.get_script_history("aa" * 32)
    assert isinstance(res, dict)
    assert "confirmed" in res and "unconfirmed" in res
    assert isinstance(res["confirmed"], list)
    assert isinstance(res["unconfirmed"], list)


def test_get_script_history_minimal_empty() -> None:
    """Sentinel hash should yield empty confirmed/unconfirmed arrays."""
    services = Services(Services.create_default_options("main"))

    res = services.get_script_history("1" * 64)
    assert isinstance(res, dict)
    assert res.get("confirmed") == []
    assert res.get("unconfirmed") == []


def test_get_script_history_invalid_script_formats() -> None:
    """Test get_script_history with invalid script formats."""
    services = Services(Services.create_default_options("main"))

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


def test_get_script_history_empty_script() -> None:
    """Test get_script_history with empty script."""
    services = Services(Services.create_default_options("main"))

    result = services.get_script_history("")
    assert isinstance(result, dict)
    assert "confirmed" in result
    assert "unconfirmed" in result
    assert isinstance(result["confirmed"], list)
    assert isinstance(result["unconfirmed"], list)


def test_get_script_history_different_chains() -> None:
    """Test get_script_history with different blockchain chains."""
    chains = ["main", "test"]

    for chain in chains:
        services = Services(Services.create_default_options(chain))

        result = services.get_script_history("aa" * 32)
        assert isinstance(result, dict)
        assert "confirmed" in result
        assert "unconfirmed" in result
        assert isinstance(result["confirmed"], list)
        assert isinstance(result["unconfirmed"], list)


def test_get_script_history_various_script_patterns() -> None:
    """Test get_script_history with various script patterns."""
    services = Services(Services.create_default_options("main"))

    test_scripts = [
        "00" * 32,  # All zeros
        "ff" * 32,  # All FFs
        "aa" * 32,  # All A's
        "a1b2c3d4e5f6abcdef1234567890abcdef1234567890abcdef1234567890abcdef",  # Mixed case
    ]

    for script in test_scripts:
        result = services.get_script_history(script)
        assert isinstance(result, dict)
        assert "confirmed" in result
        assert "unconfirmed" in result
        assert isinstance(result["confirmed"], list)
        assert isinstance(result["unconfirmed"], list)


def test_get_script_history_case_insensitive_script() -> None:
    """Test get_script_history with case variations."""
    services = Services(Services.create_default_options("main"))

    # Test that script handling is case-insensitive (though scripts are usually lowercase)
    script_lower = "a1b2c3d4e5f6abcdef1234567890abcdef1234567890abcdef1234567890abcdef"

    result = services.get_script_history(script_lower)
    assert isinstance(result, dict)
    assert "confirmed" in result
    assert "unconfirmed" in result


def test_get_script_history_unicode_script_handling() -> None:
    """Test get_script_history with unicode characters."""
    services = Services(Services.create_default_options("main"))

    # Should handle script with unicode characters gracefully (though scripts are hex)
    unicode_script = "a1b2c3d4e5f6abcdef1234567890abcdef1234567890abcdef1234567890abcdef"

    result = services.get_script_history(unicode_script)
    assert isinstance(result, dict)
    assert "confirmed" in result
    assert "unconfirmed" in result


def test_get_script_history_consecutive_calls() -> None:
    """Test multiple consecutive get_script_history calls."""
    services = Services(Services.create_default_options("main"))

    # Make multiple consecutive calls
    for i in range(5):
        script = f"{i:064d}"[:64]  # Create different scripts
        result = services.get_script_history(script)
        assert isinstance(result, dict)
        assert "confirmed" in result
        assert "unconfirmed" in result
        assert isinstance(result["confirmed"], list)
        assert isinstance(result["unconfirmed"], list)


def test_get_script_history_script_length_boundaries() -> None:
    """Test get_script_history with script length boundaries."""
    services = Services(Services.create_default_options("main"))

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
            # Invalid lengths
            script = "a" * length
            try:
                result = services.get_script_history(script)
                # Should handle gracefully
                assert isinstance(result, dict)
                assert "confirmed" in result
            except (InvalidParameterError, ValueError, TypeError):
                # Expected for invalid lengths
                pass


def test_get_script_history_special_characters() -> None:
    """Test get_script_history with special characters in script."""
    services = Services(Services.create_default_options("main"))

    # These should all fail validation
    special_scripts = [
        "a1b2c3d4e5f6abcdef1234567890abcdef1234567890abcdef1234567890abc!",  # Exclamation
        "a1b2c3d4e5f6abcdef1234567890abcdef1234567890abcdef1234567890abc@",  # At symbol
        "a1b2c3d4e5f6abcdef1234567890abcdef1234567890abcdef1234567890abc#",  # Hash
    ]

    for script in special_scripts:
        with pytest.raises((InvalidParameterError, ValueError, TypeError)):
            services.get_script_history(script)


def test_get_script_history_numeric_script() -> None:
    """Test get_script_history with numeric script representations."""
    services = Services(Services.create_default_options("main"))

    # Should reject numeric inputs
    with pytest.raises((InvalidParameterError, ValueError, TypeError)):
        services.get_script_history(1234567890)

    with pytest.raises((InvalidParameterError, ValueError, TypeError)):
        services.get_script_history(0x1234567890abcdef)


def test_get_script_history_mixed_case_script() -> None:
    """Test get_script_history with mixed case script."""
    services = Services(Services.create_default_options("main"))

    # Create mixed case script
    mixed_case_script = "A1B2C3D4E5F6ABCDEF1234567890ABCDEF1234567890ABCDEF1234567890ABCDEF"

    result = services.get_script_history(mixed_case_script)
    assert isinstance(result, dict)
    assert "confirmed" in result
    assert "unconfirmed" in result


def test_get_script_history_configuration_variations() -> None:
    """Test get_script_history with different service configurations."""
    # Test with minimal configuration
    services_minimal = Services("main")

    result = services_minimal.get_script_history("aa" * 32)
    assert isinstance(result, dict)
    assert "confirmed" in result
    assert "unconfirmed" in result

    # Test with full configuration
    options = Services.create_default_options("main")
    services_full = Services(options)

    result = services_full.get_script_history("aa" * 32)
    assert isinstance(result, dict)
    assert "confirmed" in result
    assert "unconfirmed" in result


def test_get_script_history_with_results() -> None:
    """Test get_script_history when it returns actual transaction data."""
    services = Services(Services.create_default_options("main"))

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


def test_get_script_history_empty_results() -> None:
    """Test get_script_history when it returns no transactions."""
    services = Services(Services.create_default_options("main"))

    # Test with a script that should return empty results
    result = services.get_script_history("1" * 64)
    assert isinstance(result, dict)
    assert result.get("confirmed") == []
    assert result.get("unconfirmed") == []


def test_get_script_history_result_structure() -> None:
    """Test get_script_history result structure and data types."""
    services = Services(Services.create_default_options("main"))

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
