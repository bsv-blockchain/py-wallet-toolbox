"""Expanded tests for post_beef_array with comprehensive error handling.

Validates ARC-enabled path with extensive error handling, network failure testing,
and validation scenarios for array-based BEEF posting.
Reference: wallet-toolbox/src/services/__tests/postBeef.test.ts
"""

import pytest

from bsv_wallet_toolbox.errors import InvalidParameterError
from bsv_wallet_toolbox.services import Services


def test_post_beef_array_minimal() -> None:
    options = Services.create_default_options("main")
    options["arcUrl"] = "https://arc.mock"
    options["arcApiKey"] = "test"
    services = Services(options)

    res_list = services.post_beef_array(["00", "11"])
    assert isinstance(res_list, list)
    assert len(res_list) == 2
    for res in res_list:
        assert isinstance(res, dict)
        assert set(res.keys()) == {"accepted", "txid", "message"}
        assert res["accepted"] in (True, False)


def test_post_beef_array_empty_list() -> None:
    """Test post_beef_array with empty list."""
    options = Services.create_default_options("main")
    options["arcUrl"] = "https://arc.mock"
    options["arcApiKey"] = "test"
    services = Services(options)

    result = services.post_beef_array([])
    assert isinstance(result, list)
    assert len(result) == 0


def test_post_beef_array_invalid_input_types() -> None:
    """Test post_beef_array with invalid input types."""
    options = Services.create_default_options("main")
    options["arcUrl"] = "https://arc.mock"
    options["arcApiKey"] = "test"
    services = Services(options)

    invalid_inputs = [
        None,  # None
        "string",  # Single string instead of list
        123,  # Number
        {},  # Dict
    ]

    for invalid_input in invalid_inputs:
        with pytest.raises((ValueError, TypeError, InvalidParameterError)):
            services.post_beef_array(invalid_input)


def test_post_beef_array_mixed_valid_invalid_elements() -> None:
    """Test post_beef_array with mix of valid and invalid BEEF elements."""
    options = Services.create_default_options("main")
    options["arcUrl"] = "https://arc.mock"
    options["arcApiKey"] = "test"
    services = Services(options)

    # Mix of valid and invalid BEEF data
    mixed_array = ["00", "invalid_hex", "11", "", "22"]

    result = services.post_beef_array(mixed_array)
    assert isinstance(result, list)
    assert len(result) == 5  # Should return result for each input

    # Each result should be a dict with expected structure
    for res in result:
        assert isinstance(res, dict)
        assert "accepted" in res
        assert "txid" in res
        assert "message" in res
        assert res["accepted"] in (True, False)


def test_post_beef_array_without_arc_config() -> None:
    """Test post_beef_array without ARC configuration."""
    options = Services.create_default_options("main")
    # No ARC URL/API key configured
    services = Services(options)

    result = services.post_beef_array(["00", "11"])
    assert isinstance(result, list)
    assert len(result) == 2
    for res in result:
        assert isinstance(res, dict)
        assert "accepted" in res


def test_post_beef_array_invalid_arc_url() -> None:
    """Test post_beef_array with invalid ARC URL."""
    options = Services.create_default_options("main")
    options["arcUrl"] = "not-a-valid-url"
    options["arcApiKey"] = "test"
    services = Services(options)

    result = services.post_beef_array(["00", "11"])
    assert isinstance(result, list)
    assert len(result) == 2
    for res in result:
        assert isinstance(res, dict)
        assert "accepted" in res


def test_post_beef_array_empty_api_key() -> None:
    """Test post_beef_array with empty API key."""
    options = Services.create_default_options("main")
    options["arcUrl"] = "https://arc.mock"
    options["arcApiKey"] = ""  # Empty API key
    services = Services(options)

    result = services.post_beef_array(["00", "11"])
    assert isinstance(result, list)
    assert len(result) == 2
    for res in result:
        assert isinstance(res, dict)
        assert "accepted" in res


def test_post_beef_array_none_api_key() -> None:
    """Test post_beef_array with None API key."""
    options = Services.create_default_options("main")
    options["arcUrl"] = "https://arc.mock"
    options["arcApiKey"] = None  # None API key
    services = Services(options)

    result = services.post_beef_array(["00", "11"])
    assert isinstance(result, list)
    assert len(result) == 2
    for res in result:
        assert isinstance(res, dict)
        assert "accepted" in res


def test_post_beef_array_single_element() -> None:
    """Test post_beef_array with single element."""
    options = Services.create_default_options("main")
    options["arcUrl"] = "https://arc.mock"
    options["arcApiKey"] = "test"
    services = Services(options)

    result = services.post_beef_array(["00"])
    assert isinstance(result, list)
    assert len(result) == 1
    assert isinstance(result[0], dict)
    assert set(result[0].keys()) == {"accepted", "txid", "message"}
    assert result[0]["accepted"] in (True, False)


def test_post_beef_array_large_array() -> None:
    """Test post_beef_array with large number of elements."""
    options = Services.create_default_options("main")
    options["arcUrl"] = "https://arc.mock"
    options["arcApiKey"] = "test"
    services = Services(options)

    # Test with 10 elements
    large_array = [f"{i:02x}" for i in range(10)]  # ["00", "01", "02", ..., "09"]

    result = services.post_beef_array(large_array)
    assert isinstance(result, list)
    assert len(result) == 10
    for res in result:
        assert isinstance(res, dict)
        assert set(res.keys()) == {"accepted", "txid", "message"}
        assert res["accepted"] in (True, False)


def test_post_beef_array_duplicate_elements() -> None:
    """Test post_beef_array with duplicate BEEF elements."""
    options = Services.create_default_options("main")
    options["arcUrl"] = "https://arc.mock"
    options["arcApiKey"] = "test"
    services = Services(options)

    # Array with duplicate elements
    duplicate_array = ["00", "00", "11", "00"]

    result = services.post_beef_array(duplicate_array)
    assert isinstance(result, list)
    assert len(result) == 4  # Should return result for each element
    for res in result:
        assert isinstance(res, dict)
        assert set(res.keys()) == {"accepted", "txid", "message"}
        assert res["accepted"] in (True, False)


def test_post_beef_array_different_chains() -> None:
    """Test post_beef_array with different blockchain chains."""
    chains = ["main", "test"]

    for chain in chains:
        options = Services.create_default_options(chain)
        options["arcUrl"] = "https://arc.mock"
        options["arcApiKey"] = "test"
        services = Services(options)

        result = services.post_beef_array(["00", "11"])
        assert isinstance(result, list)
        assert len(result) == 2
        for res in result:
            assert isinstance(res, dict)
            assert set(res.keys()) == {"accepted", "txid", "message"}
            assert res["accepted"] in (True, False)


def test_post_beef_array_all_invalid_elements() -> None:
    """Test post_beef_array with all invalid elements."""
    options = Services.create_default_options("main")
    options["arcUrl"] = "https://arc.mock"
    options["arcApiKey"] = "test"
    services = Services(options)

    # All elements are invalid (invalid beef content, but valid strings)
    invalid_array = ["", "invalid", "gggggggg", "odd", "12345"]

    result = services.post_beef_array(invalid_array)
    assert isinstance(result, list)
    assert len(result) == 5  # Should return result for each element
    for res in result:
        assert isinstance(res, dict)
        assert "accepted" in res
        # May be True or False depending on implementation


def test_post_beef_array_mixed_types_in_array() -> None:
    """Test post_beef_array with mixed types in array."""
    options = Services.create_default_options("main")
    options["arcUrl"] = "https://arc.mock"
    options["arcApiKey"] = "test"
    services = Services(options)

    # Mix of valid and invalid beef strings (all are strings, but some have invalid content)
    mixed_array = ["00", "invalid_hex", "", "11", "odd_length", "gg"]

    result = services.post_beef_array(mixed_array)
    assert isinstance(result, list)
    assert len(result) == 6  # Should return result for each element
    for res in result:
        assert isinstance(res, dict)
        assert "accepted" in res
        assert "txid" in res
        assert "message" in res
        assert res["accepted"] in (True, False)


def test_post_beef_array_consecutive_calls() -> None:
    """Test multiple consecutive post_beef_array calls."""
    options = Services.create_default_options("main")
    options["arcUrl"] = "https://arc.mock"
    options["arcApiKey"] = "test"
    services = Services(options)

    # Make multiple consecutive calls
    for _i in range(3):
        result = services.post_beef_array(["00", "11"])
        assert isinstance(result, list)
        assert len(result) == 2
        for res in result:
            assert isinstance(res, dict)
            assert set(res.keys()) == {"accepted", "txid", "message"}
            assert res["accepted"] in (True, False)


def test_post_beef_array_config_validation() -> None:
    """Test post_beef_array with various ARC configuration scenarios."""
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

        result = services.post_beef_array(["00"])
        assert isinstance(result, list)
        assert len(result) == 1
        assert isinstance(result[0], dict)
        assert set(result[0].keys()) == {"accepted", "txid", "message"}
        assert result[0]["accepted"] in (True, False)
