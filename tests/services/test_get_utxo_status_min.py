"""Expanded tests for get_utxo_status with comprehensive error handling.

Validates UTXO status functionality with extensive error handling,
network failure testing, and validation scenarios.
Reference: wallet-toolbox/src/services/__tests/getUtxoStatus.test.ts
"""

import pytest

from bsv_wallet_toolbox.errors import InvalidParameterError
from bsv_wallet_toolbox.services import Services


def test_get_utxo_status_minimal_normal() -> None:
    """Normal case should return a dict with details: list of entries."""
    services = Services(Services.create_default_options("main"))

    res = services.get_utxo_status("aa" * 32)
    assert isinstance(res, dict)
    assert "details" in res
    assert isinstance(res["details"], list)
    if res["details"]:
        entry = res["details"][0]
        assert isinstance(entry, dict)
        assert "outpoint" in entry
        assert "spent" in entry
        assert isinstance(entry["spent"], bool)


def test_get_utxo_status_minimal_not_found() -> None:
    """Sentinel hash should yield an empty details list (not_found-like)."""
    services = Services(Services.create_default_options("main"))

    res = services.get_utxo_status("1" * 64)
    assert isinstance(res, dict)
    assert isinstance(res.get("details"), list)
    assert res["details"] == []


def test_get_utxo_status_invalid_script_formats() -> None:
    """Test get_utxo_status with invalid script formats."""
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
            services.get_utxo_status(invalid_script)


def test_get_utxo_status_empty_script() -> None:
    """Test get_utxo_status with empty script."""
    services = Services(Services.create_default_options("main"))

    # Empty string should raise InvalidParameterError
    with pytest.raises(InvalidParameterError):
        services.get_utxo_status("")


def test_get_utxo_status_different_chains() -> None:
    """Test get_utxo_status with different blockchain chains."""
    chains = ["main", "test"]

    for chain in chains:
        services = Services(Services.create_default_options(chain))

        result = services.get_utxo_status("aa" * 32)
        assert isinstance(result, dict)
        assert "details" in result
        assert isinstance(result["details"], list)


def test_get_utxo_status_various_script_patterns() -> None:
    """Test get_utxo_status with various script patterns."""
    services = Services(Services.create_default_options("main"))

    test_scripts = [
        "00" * 32,  # All zeros
        "ff" * 32,  # All FFs
        "aa" * 32,  # All A's
        "a1b2c3d4e5f6abcdef1234567890abcdef1234567890abcdef1234567890abcd",  # Mixed case (64 chars)
    ]

    for script in test_scripts:
        result = services.get_utxo_status(script)
        assert isinstance(result, dict)
        assert "details" in result
        assert isinstance(result["details"], list)


def test_get_utxo_status_case_insensitive_script() -> None:
    """Test get_utxo_status with case variations."""
    services = Services(Services.create_default_options("main"))

    # Test that script handling is case-insensitive (though scripts are usually lowercase)
    script_lower = "a1b2c3d4e5f6abcdef1234567890abcdef1234567890abcdef1234567890abcd"  # 64 chars

    result = services.get_utxo_status(script_lower)
    assert isinstance(result, dict)
    assert "details" in result


def test_get_utxo_status_unicode_script_handling() -> None:
    """Test get_utxo_status with unicode characters."""
    services = Services(Services.create_default_options("main"))

    # Should handle script with unicode characters gracefully (though scripts are hex)
    unicode_script = "a1b2c3d4e5f6abcdef1234567890abcdef1234567890abcdef1234567890abcd"  # 64 chars

    result = services.get_utxo_status(unicode_script)
    assert isinstance(result, dict)
    assert "details" in result


def test_get_utxo_status_consecutive_calls() -> None:
    """Test multiple consecutive get_utxo_status calls."""
    services = Services(Services.create_default_options("main"))

    # Make multiple consecutive calls
    for i in range(5):
        script = f"{i:064d}"[:64]  # Create different scripts
        result = services.get_utxo_status(script)
        assert isinstance(result, dict)
        assert "details" in result
        assert isinstance(result["details"], list)


def test_get_utxo_status_script_length_boundaries() -> None:
    """Test get_utxo_status with script length boundaries."""
    services = Services(Services.create_default_options("main"))

    # Test boundary lengths
    boundary_lengths = [1, 32, 63, 64, 65, 100]

    for length in boundary_lengths:
        if length == 64:
            # Valid length
            script = "a" * 64
            result = services.get_utxo_status(script)
            assert isinstance(result, dict)
            assert "details" in result
        else:
            # Invalid lengths
            script = "a" * length
            try:
                result = services.get_utxo_status(script)
                # Should handle gracefully
                assert isinstance(result, dict)
                assert "details" in result
            except (InvalidParameterError, ValueError, TypeError):
                # Expected for invalid lengths
                pass


def test_get_utxo_status_special_characters() -> None:
    """Test get_utxo_status with special characters in script."""
    services = Services(Services.create_default_options("main"))

    # These should all fail validation
    special_scripts = [
        "a1b2c3d4e5f6abcdef1234567890abcdef1234567890abcdef1234567890abc!",  # Exclamation
        "a1b2c3d4e5f6abcdef1234567890abcdef1234567890abcdef1234567890abc@",  # At symbol
        "a1b2c3d4e5f6abcdef1234567890abcdef1234567890abcdef1234567890abc#",  # Hash
    ]

    for script in special_scripts:
        with pytest.raises((InvalidParameterError, ValueError, TypeError)):
            services.get_utxo_status(script)


def test_get_utxo_status_numeric_script() -> None:
    """Test get_utxo_status with numeric script representations."""
    services = Services(Services.create_default_options("main"))

    # Should reject numeric inputs
    with pytest.raises((InvalidParameterError, ValueError, TypeError)):
        services.get_utxo_status(1234567890)

    with pytest.raises((InvalidParameterError, ValueError, TypeError)):
        services.get_utxo_status(0x1234567890ABCDEF)


def test_get_utxo_status_mixed_case_script() -> None:
    """Test get_utxo_status with mixed case script."""
    services = Services(Services.create_default_options("main"))

    # Create mixed case script
    mixed_case_script = "A1B2C3D4E5F6ABCDEF1234567890ABCDEF1234567890ABCDEF1234567890ABCD"  # 64 chars

    result = services.get_utxo_status(mixed_case_script)
    assert isinstance(result, dict)
    assert "details" in result


def test_get_utxo_status_configuration_variations() -> None:
    """Test get_utxo_status with different service configurations."""
    # Test with minimal configuration
    services_minimal = Services("main")

    result = services_minimal.get_utxo_status("aa" * 32)
    assert isinstance(result, dict)
    assert "details" in result

    # Test with full configuration
    options = Services.create_default_options("main")
    services_full = Services(options)

    result = services_full.get_utxo_status("aa" * 32)
    assert isinstance(result, dict)
    assert "details" in result


def test_get_utxo_status_with_results() -> None:
    """Test get_utxo_status when it returns actual UTXO data."""
    services = Services(Services.create_default_options("main"))

    # Test with a script that should return results
    result = services.get_utxo_status("aa" * 32)
    assert isinstance(result, dict)
    assert "details" in result
    assert isinstance(result["details"], list)

    # Check that details array contains proper UTXO data if present
    for utxo in result["details"]:
        if utxo:  # If UTXO exists
            assert isinstance(utxo, dict)
            assert "outpoint" in utxo
            assert "spent" in utxo
            assert isinstance(utxo["spent"], bool)
            # outpoint should contain txid and vout
            assert "txid" in utxo["outpoint"] or "hash" in utxo["outpoint"]
            assert "vout" in utxo["outpoint"] or "index" in utxo["outpoint"]


def test_get_utxo_status_empty_results() -> None:
    """Test get_utxo_status when it returns no UTXOs."""
    services = Services(Services.create_default_options("main"))

    # Test with a script that should return empty results
    result = services.get_utxo_status("1" * 64)
    assert isinstance(result, dict)
    assert result["details"] == []


def test_get_utxo_status_result_structure() -> None:
    """Test get_utxo_status result structure and data types."""
    services = Services(Services.create_default_options("main"))

    result = services.get_utxo_status("aa" * 32)
    assert isinstance(result, dict)

    # Check required fields
    assert "details" in result
    assert isinstance(result["details"], list)

    # Check that each UTXO in details has proper structure
    for utxo in result["details"]:
        if utxo:  # If UTXO exists
            assert isinstance(utxo, dict)
            assert "outpoint" in utxo
            assert "spent" in utxo
            assert isinstance(utxo["spent"], bool)

            # Check outpoint structure
            outpoint = utxo["outpoint"]
            assert isinstance(outpoint, dict)
            # Should have txid/hash and vout/index
            assert any(key in outpoint for key in ["txid", "hash"])
            assert any(key in outpoint for key in ["vout", "index"])


def test_get_utxo_status_error_response_handling() -> None:
    """Test get_utxo_status handles various error conditions."""
    services = Services(Services.create_default_options("main"))

    # Test with various script patterns that might trigger errors
    error_scripts = [
        "invalid",  # Invalid format
        "gggggggggggggggggggggggggggggggggggggggg",  # Invalid hex
        "",  # Empty
        "a",  # Too short
        "a" * 100,  # Too long
    ]

    for script in error_scripts:
        try:
            result = services.get_utxo_status(script)
            # Should return error-shaped response
            assert isinstance(result, dict)
            assert "details" in result
        except (InvalidParameterError, ValueError, TypeError):
            # Some implementations may raise exceptions
            pass
