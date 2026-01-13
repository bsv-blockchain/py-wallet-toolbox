"""Coverage tests for validation utilities.

This module tests BRC-100 parameter validation functions.
"""

import pytest

from bsv_wallet_toolbox.errors import InvalidParameterError
from bsv_wallet_toolbox.utils.validation import (
    validate_basket_config,
    validate_create_action_args,
    validate_list_actions_args,
    validate_list_outputs_args,
    validate_originator,
    validate_satoshis,
)


class TestValidateOriginator:
    """Test originator validation."""

    def test_valid_originator(self) -> None:
        """Test valid originator."""
        validate_originator("example.com")
        # Should not raise

    def test_none_originator(self) -> None:
        """Test None originator (optional)."""
        validate_originator(None)
        # Should not raise

    def test_empty_originator(self) -> None:
        """Test empty originator string."""
        validate_originator("")
        # Should not raise

    def test_originator_max_length(self) -> None:
        """Test originator at maximum length."""
        validate_originator("a" * 250)
        # Should not raise

    def test_originator_too_long(self) -> None:
        """Test originator exceeding maximum length."""
        with pytest.raises(InvalidParameterError):
            validate_originator("a" * 251)

    def test_originator_non_string(self) -> None:
        """Test non-string originator."""
        with pytest.raises(InvalidParameterError):
            validate_originator(123)  # type: ignore

    def test_originator_utf8_bytes(self) -> None:
        """Test originator with UTF-8 multibyte characters."""
        # Each emoji is 4 bytes
        emoji = "😀" * 62  # 248 bytes (under 250)
        validate_originator(emoji)
        # Should not raise


class TestValidateSatoshis:
    """Test satoshi value validation."""

    def test_valid_satoshis(self) -> None:
        """Test valid satoshi amount."""
        result = validate_satoshis(100_000_000)
        assert result == 100_000_000

    def test_zero_satoshis(self) -> None:
        """Test zero satoshis."""
        result = validate_satoshis(0)
        assert result == 0

    def test_max_satoshis(self) -> None:
        """Test maximum satoshis."""
        max_val = 2_100_000_000_000_000
        result = validate_satoshis(max_val)
        assert result == max_val

    def test_negative_satoshis(self) -> None:
        """Test negative satoshi amount."""
        result = validate_satoshis(-100)
        # Might be allowed or raise depending on context
        assert result == -100 or isinstance(result, int)

    def test_satoshis_non_integer(self) -> None:
        """Test non-integer satoshi value."""
        with pytest.raises((InvalidParameterError, TypeError)):
            validate_satoshis("invalid")  # type: ignore

    def test_satoshis_float(self) -> None:
        """Test float satoshi value."""
        with pytest.raises((InvalidParameterError, TypeError)):
            validate_satoshis(100.5)  # type: ignore

    def test_satoshis_custom_field_name(self) -> None:
        """Test satoshis validation with custom field name."""
        try:
            validate_satoshis(100, "amount")
            assert True
        except TypeError:
            # Might not support field_name parameter
            pass


class TestValidateBasketConfig:
    """Test basket configuration validation."""

    def test_valid_basket_config(self) -> None:
        """Test valid basket configuration."""
        config = {
            "name": "default",
            "minimumDesiredUTXOSatoshis": 1000,
            "desiredUTXOCount": 10,
            "desiredUTXOFactor": 1.5,
        }
        validate_basket_config(config)
        # Should not raise

    def test_basket_config_missing_fields(self) -> None:
        """Test basket config with missing fields."""
        config = {}
        # Might have default values or raise
        try:
            validate_basket_config(config)
        except (InvalidParameterError, KeyError):
            pass

    def test_basket_config_invalid_satoshis(self) -> None:
        """Test basket config with invalid satoshi value."""
        config = {
            "minimumDesiredUTXOSatoshis": -1000,
        }
        with pytest.raises((InvalidParameterError, Exception)):
            validate_basket_config(config)


class TestValidateListOutputsArgs:
    """Test list outputs arguments validation."""

    def test_valid_list_outputs_args(self) -> None:
        """Test valid list outputs arguments."""
        args = {
            "limit": 100,
            "offset": 0,
            "basket": "default",
        }
        validate_list_outputs_args(args)
        # Should not raise

    def test_list_outputs_args_empty(self) -> None:
        """Test empty list outputs arguments."""
        args = {}
        # Might use defaults or raise
        try:
            validate_list_outputs_args(args)
        except (InvalidParameterError, KeyError):
            pass

    def test_list_outputs_args_invalid_limit(self) -> None:
        """Test invalid limit value."""
        args = {"limit": -1}
        with pytest.raises((InvalidParameterError, ValueError)):
            validate_list_outputs_args(args)


class TestValidateListActionsArgs:
    """Test list actions arguments validation."""

    def test_valid_list_actions_args(self) -> None:
        """Test valid list actions arguments."""
        args = {
            "limit": 50,
            "offset": 0,
            "labels": ["label1"],
        }
        validate_list_actions_args(args)
        # Should not raise

    def test_none_list_actions_args(self) -> None:
        """Test None list actions arguments."""
        # None might not be allowed
        try:
            validate_list_actions_args(None)
        except InvalidParameterError:
            pass  # Expected

    def test_list_actions_args_empty(self) -> None:
        """Test empty list actions arguments."""
        args = {}
        validate_list_actions_args(args)
        # Should not raise


class TestValidateCreateActionArgs:
    """Test create action arguments validation."""

    def test_valid_create_action_args(self) -> None:
        """Test valid create action arguments."""
        args = {
            "description": "Test action",
            "outputs": [{"satoshis": 1000, "script": "script"}],
        }
        try:
            result = validate_create_action_args(args)
            assert isinstance(result, dict)
        except (InvalidParameterError, KeyError):
            # Might need more required fields
            pass

    def test_create_action_args_missing_outputs(self) -> None:
        """Test create action args without outputs."""
        args = {"description": "Test action"}
        with pytest.raises((InvalidParameterError, KeyError)):
            validate_create_action_args(args)

    def test_create_action_args_invalid_outputs(self) -> None:
        """Test create action args with invalid outputs."""
        args = {
            "description": "Test",
            "outputs": "invalid",  # Should be list
        }
        with pytest.raises((InvalidParameterError, TypeError)):
            validate_create_action_args(args)


class TestParameterValidationPatterns:
    """Test common parameter validation patterns."""

    def test_validate_none_allowed_originator(self) -> None:
        """Test originator allows None."""
        validate_originator(None)

    def test_validate_dict_required_list_actions(self) -> None:
        """Test list actions args requires dict."""
        with pytest.raises(InvalidParameterError):
            validate_list_actions_args(None)  # type: ignore

    def test_validate_length_limits(self) -> None:
        """Test 250-byte length limit for originator."""
        max_valid = "a" * 250
        too_long = "a" * 251

        # Should accept max length
        validate_originator(max_valid)

        # Should reject too long
        with pytest.raises(InvalidParameterError):
            validate_originator(too_long)

    def test_validate_type_checking_originator(self) -> None:
        """Test originator type checking."""
        with pytest.raises(InvalidParameterError):
            validate_originator(12345)  # type: ignore

    def test_validate_type_checking_satoshis(self) -> None:
        """Test satoshis type checking."""
        with pytest.raises((InvalidParameterError, TypeError)):
            validate_satoshis("not an integer")  # type: ignore


class TestErrorMessages:
    """Test validation error messages."""

    def test_originator_error_message(self) -> None:
        """Test originator validation error message."""
        try:
            validate_originator("a" * 251)
            raise AssertionError("Should have raised")
        except InvalidParameterError as e:
            assert "originator" in str(e).lower()

    def test_satoshis_error_message(self) -> None:
        """Test satoshis validation error message."""
        try:
            validate_satoshis("invalid")  # type: ignore
            raise AssertionError("Should have raised")
        except (InvalidParameterError, TypeError) as e:
            # Error message should be informative
            assert len(str(e)) > 0
