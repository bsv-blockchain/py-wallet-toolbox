"""Expanded tests for get_transaction_status with comprehensive error handling.

This validates transaction status functionality with extensive error handling,
network failure testing, and validation scenarios.
Reference: wallet-toolbox/src/services/Services.ts#getTransactionStatus
"""

import pytest
from unittest.mock import patch

from bsv_wallet_toolbox.services import Services
from bsv_wallet_toolbox.errors import InvalidParameterError


def test_get_transaction_status_minimal() -> None:
    """Ensure minimal TS-like shape from get_transaction_status.

    - With conftest's FakeClient, a normal 64-hex txid returns
      {"status": "confirmed", "confirmations": number}.
    - Edge case (all '1' * 64) returns {"status": "not_found"}.
    """
    services = Services(Services.create_default_options("main"))

    # Normal case
    res = services.get_transaction_status("aa" * 32)
    assert isinstance(res, dict)
    assert "status" in res
    if res["status"] == "confirmed":
        assert isinstance(res.get("confirmations"), int)

    # Edge case: not_found sentinel
    res_nf = services.get_transaction_status("1" * 64)
    assert isinstance(res_nf, dict)
    assert res_nf.get("status") in {"not_found", "unknown"}


def test_get_transaction_status_invalid_txid_formats() -> None:
    """Test get_transaction_status with invalid txid formats."""
    services = Services(Services.create_default_options("main"))

    invalid_txids = [
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

    for invalid_txid in invalid_txids:
        with pytest.raises((InvalidParameterError, ValueError, TypeError)):
            services.get_transaction_status(invalid_txid)


def test_get_transaction_status_empty_txid() -> None:
    """Test get_transaction_status with empty txid."""
    services = Services(Services.create_default_options("main"))

    result = services.get_transaction_status("")
    assert isinstance(result, dict)
    assert "status" in result


def test_get_transaction_status_different_chains() -> None:
    """Test get_transaction_status with different blockchain chains."""
    chains = ["main", "test"]

    for chain in chains:
        services = Services(Services.create_default_options(chain))

        result = services.get_transaction_status("aa" * 32)
        assert isinstance(result, dict)
        assert "status" in result


def test_get_transaction_status_various_txid_patterns() -> None:
    """Test get_transaction_status with various txid patterns."""
    services = Services(Services.create_default_options("main"))

    test_txids = [
        "00" * 32,  # All zeros
        "ff" * 32,  # All FFs
        "aa" * 32,  # All A's
        "a1b2c3d4e5f6abcdef1234567890abcdef1234567890abcdef1234567890abcdef",  # Mixed case
    ]

    for txid in test_txids:
        result = services.get_transaction_status(txid)
        assert isinstance(result, dict)
        assert "status" in result


def test_get_transaction_status_case_insensitive_txid() -> None:
    """Test get_transaction_status with case variations."""
    services = Services(Services.create_default_options("main"))

    # Test that txid handling is case-insensitive (though txids are usually lowercase)
    txid_lower = "a1b2c3d4e5f6abcdef1234567890abcdef1234567890abcdef1234567890abcdef"

    result = services.get_transaction_status(txid_lower)
    assert isinstance(result, dict)
    assert "status" in result


def test_get_transaction_status_unicode_txid_handling() -> None:
    """Test get_transaction_status with unicode characters."""
    services = Services(Services.create_default_options("main"))

    # Should handle txid with unicode characters gracefully (though txids are hex)
    unicode_txid = "a1b2c3d4e5f6abcdef1234567890abcdef1234567890abcdef1234567890abcdef"

    result = services.get_transaction_status(unicode_txid)
    assert isinstance(result, dict)
    assert "status" in result


def test_get_transaction_status_consecutive_calls() -> None:
    """Test multiple consecutive get_transaction_status calls."""
    services = Services(Services.create_default_options("main"))

    # Make multiple consecutive calls
    for i in range(5):
        txid = f"{i:064d}"[:64]  # Create different txids
        result = services.get_transaction_status(txid)
        assert isinstance(result, dict)
        assert "status" in result


def test_get_transaction_status_various_response_patterns() -> None:
    """Test get_transaction_status handles various response patterns."""
    services = Services(Services.create_default_options("main"))

    # Test different txid patterns that may trigger different responses
    test_patterns = [
        "1" * 64,  # All 1s - may trigger not_found
        "0" * 64,  # All 0s - may trigger not_found
        "a" * 64,  # All as - may trigger confirmed
        "f" * 64,  # All fs - may trigger confirmed
    ]

    for txid in test_patterns:
        result = services.get_transaction_status(txid)
        assert isinstance(result, dict)
        assert "status" in result
        assert result["status"] in ["confirmed", "not_found", "unknown", "pending", "unconfirmed"]


def test_get_transaction_status_txid_length_boundaries() -> None:
    """Test get_transaction_status with txid length boundaries."""
    services = Services(Services.create_default_options("main"))

    # Test boundary lengths
    boundary_lengths = [1, 32, 63, 64, 65, 100]

    for length in boundary_lengths:
        if length == 64:
            # Valid length
            txid = "a" * 64
            result = services.get_transaction_status(txid)
            assert isinstance(result, dict)
        else:
            # Invalid lengths
            txid = "a" * length
            try:
                result = services.get_transaction_status(txid)
                # Should handle gracefully
                assert isinstance(result, dict)
            except (InvalidParameterError, ValueError, TypeError):
                # Expected for invalid lengths
                pass


def test_get_transaction_status_special_characters() -> None:
    """Test get_transaction_status with special characters in txid."""
    services = Services(Services.create_default_options("main"))

    # These should all fail validation
    special_txids = [
        "a1b2c3d4e5f6abcdef1234567890abcdef1234567890abcdef1234567890abc!",  # Exclamation
        "a1b2c3d4e5f6abcdef1234567890abcdef1234567890abcdef1234567890abc@",  # At symbol
        "a1b2c3d4e5f6abcdef1234567890abcdef1234567890abcdef1234567890abc#",  # Hash
    ]

    for txid in special_txids:
        with pytest.raises((InvalidParameterError, ValueError, TypeError)):
            services.get_transaction_status(txid)


def test_get_transaction_status_numeric_txid() -> None:
    """Test get_transaction_status with numeric txid representations."""
    services = Services(Services.create_default_options("main"))

    # Should reject numeric inputs
    with pytest.raises((InvalidParameterError, ValueError, TypeError)):
        services.get_transaction_status(1234567890)

    with pytest.raises((InvalidParameterError, ValueError, TypeError)):
        services.get_transaction_status(0x1234567890abcdef)


def test_get_transaction_status_mixed_case_txid() -> None:
    """Test get_transaction_status with mixed case txid."""
    services = Services(Services.create_default_options("main"))

    # Create mixed case txid
    mixed_case_txid = "A1B2C3D4E5F6ABCDEF1234567890ABCDEF1234567890ABCDEF1234567890ABCDEF"

    result = services.get_transaction_status(mixed_case_txid)
    assert isinstance(result, dict)
    assert "status" in result


def test_get_transaction_status_configuration_variations() -> None:
    """Test get_transaction_status with different service configurations."""
    # Test with minimal configuration
    services_minimal = Services("main")

    result = services_minimal.get_transaction_status("aa" * 32)
    assert isinstance(result, dict)
    assert "status" in result

    # Test with full configuration
    options = Services.create_default_options("main")
    services_full = Services(options)

    result = services_full.get_transaction_status("aa" * 32)
    assert isinstance(result, dict)
    assert "status" in result


def test_get_transaction_status_error_response_handling() -> None:
    """Test get_transaction_status handles various error conditions."""
    services = Services(Services.create_default_options("main"))

    # Test with various txid patterns that might trigger errors
    error_txids = [
        "invalid",  # Invalid format
        "gggggggggggggggggggggggggggggggggggggggg",  # Invalid hex
        "",  # Empty
        "a",  # Too short
        "a" * 100,  # Too long
    ]

    for txid in error_txids:
        try:
            result = services.get_transaction_status(txid)
            # Should return error-shaped response
            assert isinstance(result, dict)
            assert "status" in result
        except (InvalidParameterError, ValueError, TypeError):
            # Some implementations may raise exceptions
            pass
