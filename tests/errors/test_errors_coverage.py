"""Coverage tests for custom error classes.

This module tests custom error classes and error handling utilities.
"""

import pytest

from bsv_wallet_toolbox.errors import (
    ConfigurationError,
    FormatError,
    InsufficientFundsError,
    InvalidParameterError,
    OperationError,
    ReviewActionsError,
    StateError,
    TransactionBroadcastError,
    TransactionSizeError,
    ValidationError,
    WalletError,
)


class TestWalletErrors:
    """Test wallet-specific errors."""

    def test_import_wallet_error(self) -> None:
        """Test importing WalletError."""
        assert WalletError is not None

    def test_raise_wallet_error(self) -> None:
        """Test raising WalletError."""
        with pytest.raises(WalletError):
            raise WalletError("Test error")

    def test_wallet_error_message(self) -> None:
        """Test WalletError message."""
        error = WalletError("Custom message")
        assert str(error) == "Custom message"
        assert error.message == "Custom message"
        assert error.context == {}

    def test_wallet_error_with_context(self) -> None:
        """Test WalletError with context."""
        error = WalletError("Error occurred", {"key": "value", "status": 500})
        assert "Error occurred" in str(error)
        assert "key='value'" in str(error)
        assert "status=500" in str(error)
        assert error.context == {"key": "value", "status": 500}

    def test_wallet_error_format_message(self) -> None:
        """Test WalletError message formatting."""
        error = WalletError("Failed", {"expected": "ready", "actual": "busy"})
        formatted = error._format_message()
        assert "Failed" in formatted
        assert "expected='ready'" in formatted
        assert "actual='busy'" in formatted


class TestValidationError:
    """Test ValidationError class."""

    def test_validation_error_basic(self) -> None:
        """Test basic ValidationError."""
        error = ValidationError("Invalid input")
        assert "Invalid input" in str(error)
        assert error.message == "Invalid input"
        assert isinstance(error, WalletError)

    def test_validation_error_with_field(self) -> None:
        """Test ValidationError with field."""
        error = ValidationError("Invalid amount", field="satoshis")
        assert "Invalid amount" in str(error)
        assert error.context["field"] == "satoshis"

    def test_validation_error_with_value(self) -> None:
        """Test ValidationError with value."""
        error = ValidationError("Invalid amount", value=-100)
        assert "Invalid amount" in str(error)
        assert error.context["value"] == -100

    def test_validation_error_with_field_and_value(self) -> None:
        """Test ValidationError with field and value."""
        error = ValidationError("Invalid amount", field="satoshis", value=-100)
        assert error.context["field"] == "satoshis"
        assert error.context["value"] == -100


class TestConfigurationError:
    """Test ConfigurationError class."""

    def test_configuration_error_basic(self) -> None:
        """Test basic ConfigurationError."""
        error = ConfigurationError("Missing configuration")
        assert "Missing configuration" in str(error)
        assert isinstance(error, WalletError)

    def test_configuration_error_with_component(self) -> None:
        """Test ConfigurationError with component."""
        error = ConfigurationError("Not configured", component="storage")
        assert error.context["component"] == "storage"

    def test_configuration_error_with_required(self) -> None:
        """Test ConfigurationError with required list."""
        error = ConfigurationError("Missing items", required=["key", "storage"])
        assert error.context["required"] == ["key", "storage"]

    def test_configuration_error_full(self) -> None:
        """Test ConfigurationError with all parameters."""
        error = ConfigurationError("Incomplete setup", component="wallet", required=["key_deriver", "storage"])
        assert error.context["component"] == "wallet"
        assert error.context["required"] == ["key_deriver", "storage"]


class TestStateError:
    """Test StateError class."""

    def test_state_error_basic(self) -> None:
        """Test basic StateError."""
        error = StateError("Invalid state")
        assert "Invalid state" in str(error)
        assert isinstance(error, WalletError)

    def test_state_error_with_current_state(self) -> None:
        """Test StateError with current state."""
        error = StateError("Cannot proceed", current_state="locked")
        assert error.context["currentState"] == "locked"

    def test_state_error_with_expected_state_string(self) -> None:
        """Test StateError with expected state as string."""
        error = StateError("Wrong state", expected_state="unlocked")
        assert error.context["expectedState"] == "unlocked"

    def test_state_error_with_expected_state_list(self) -> None:
        """Test StateError with expected state as list."""
        error = StateError("Wrong state", expected_state=["ready", "active"])
        assert error.context["expectedState"] == ["ready", "active"]

    def test_state_error_full(self) -> None:
        """Test StateError with all parameters."""
        error = StateError("Cannot sign in current state", current_state="locked", expected_state="unlocked")
        assert error.context["currentState"] == "locked"
        assert error.context["expectedState"] == "unlocked"


class TestOperationError:
    """Test OperationError class."""

    def test_operation_error_basic(self) -> None:
        """Test basic OperationError."""
        error = OperationError("Operation failed")
        assert "Operation failed" in str(error)
        assert isinstance(error, WalletError)

    def test_operation_error_with_operation(self) -> None:
        """Test OperationError with operation name."""
        error = OperationError("Failed", operation="sign_action")
        assert error.context["operation"] == "sign_action"

    def test_operation_error_with_reason(self) -> None:
        """Test OperationError with reason."""
        error = OperationError("Failed", reason="insufficient inputs")
        assert error.context["reason"] == "insufficient inputs"

    def test_operation_error_full(self) -> None:
        """Test OperationError with all parameters."""
        error = OperationError("Cannot complete operation", operation="create_action", reason="missing outputs")
        assert error.context["operation"] == "create_action"
        assert error.context["reason"] == "missing outputs"


class TestFormatError:
    """Test FormatError class."""

    def test_format_error_basic(self) -> None:
        """Test basic FormatError."""
        error = FormatError("Invalid format")
        assert "Invalid format" in str(error)
        assert isinstance(error, WalletError)

    def test_format_error_with_data_type(self) -> None:
        """Test FormatError with data type."""
        error = FormatError("Invalid format", data_type="transaction")
        assert error.context["dataType"] == "transaction"

    def test_format_error_with_expected_format(self) -> None:
        """Test FormatError with expected format."""
        error = FormatError("Invalid format", expected_format="atomic_beef")
        assert error.context["expectedFormat"] == "atomic_beef"

    def test_format_error_full(self) -> None:
        """Test FormatError with all parameters."""
        error = FormatError("Invalid BEEF format", data_type="tx", expected_format="atomic_beef")
        assert error.context["dataType"] == "tx"
        assert error.context["expectedFormat"] == "atomic_beef"


class TestInvalidParameterError:
    """Test InvalidParameterError."""

    def test_invalid_parameter_error_basic(self) -> None:
        """Test basic InvalidParameterError."""
        error = InvalidParameterError("originator")
        assert "originator" in str(error)
        assert error.parameter == "originator"
        assert error.message == "invalid"

    def test_invalid_parameter_error_with_message(self) -> None:
        """Test InvalidParameterError with custom message."""
        error = InvalidParameterError("originator", "must be a string under 250 bytes")
        assert "originator" in str(error)
        assert "must be a string under 250 bytes" in str(error)
        assert error.parameter == "originator"
        assert error.message == "must be a string under 250 bytes"

    def test_raise_invalid_parameter_error(self) -> None:
        """Test raising InvalidParameterError."""
        with pytest.raises(InvalidParameterError):
            raise InvalidParameterError("test_param", "invalid value")


class TestInsufficientFundsError:
    """Test InsufficientFundsError class."""

    def test_insufficient_funds_error_basic(self) -> None:
        """Test basic InsufficientFundsError."""
        error = InsufficientFundsError(1000, 500)
        assert "1000" in str(error)
        assert "500" in str(error)
        assert error.total_satoshis_needed == 1000
        assert error.more_satoshis_needed == 500

    def test_insufficient_funds_error_message(self) -> None:
        """Test InsufficientFundsError message format."""
        error = InsufficientFundsError(2000, 750)
        msg = str(error)
        assert "Insufficient funds" in msg
        assert "750 more satoshis are needed" in msg
        assert "for a total of 2000" in msg

    def test_raise_insufficient_funds_error(self) -> None:
        """Test raising InsufficientFundsError."""
        with pytest.raises(InsufficientFundsError):
            raise InsufficientFundsError(1500, 300)


class TestTransactionBroadcastError:
    """Test TransactionBroadcastError class."""

    def test_transaction_broadcast_error_default(self) -> None:
        """Test TransactionBroadcastError with default message."""
        error = TransactionBroadcastError()
        assert "Transaction broadcast failed" in str(error)
        assert error.message == "Transaction broadcast failed"

    def test_transaction_broadcast_error_custom(self) -> None:
        """Test TransactionBroadcastError with custom message."""
        error = TransactionBroadcastError("failed to send output creating transaction")
        assert "failed to send output creating transaction" in str(error)
        assert error.message == "failed to send output creating transaction"

    def test_raise_transaction_broadcast_error(self) -> None:
        """Test raising TransactionBroadcastError."""
        with pytest.raises(TransactionBroadcastError):
            raise TransactionBroadcastError("Network error")


class TestTransactionSizeError:
    """Test TransactionSizeError class."""

    def test_transaction_size_error_default(self) -> None:
        """Test TransactionSizeError with default message."""
        error = TransactionSizeError()
        assert "Transaction size calculation error" in str(error)
        assert error.message == "Transaction size calculation error"

    def test_transaction_size_error_custom(self) -> None:
        """Test TransactionSizeError with custom message."""
        error = TransactionSizeError("Invalid script size in transaction input")
        assert "Invalid script size in transaction input" in str(error)
        assert error.message == "Invalid script size in transaction input"

    def test_raise_transaction_size_error(self) -> None:
        """Test raising TransactionSizeError."""
        with pytest.raises(TransactionSizeError):
            raise TransactionSizeError("Size too large")


class TestReviewActionsError:
    """Test ReviewActionsError class."""

    def test_review_actions_error_minimal(self) -> None:
        """Test ReviewActionsError with minimal parameters."""
        review_results = [{"txid": "abc123", "status": "success"}]
        send_results = [{"txid": "abc123", "status": "unproven"}]
        error = ReviewActionsError(review_results, send_results)

        assert error.review_action_results == review_results
        assert error.send_with_results == send_results
        assert error.txid is None
        assert error.tx is None
        assert error.no_send_change is None
        assert "1 action(s) need attention" in str(error)

    def test_review_actions_error_full(self) -> None:
        """Test ReviewActionsError with all parameters."""
        review_results = [{"txid": "abc123", "status": "doubleSpend", "competingTxs": ["def456"]}]
        send_results = [{"txid": "abc123", "status": "failed"}]
        tx_data = [1, 2, 3, 4, 5]
        no_send = ["xyz789:0"]

        error = ReviewActionsError(review_results, send_results, txid="abc123", tx=tx_data, no_send_change=no_send)

        assert error.review_action_results == review_results
        assert error.send_with_results == send_results
        assert error.txid == "abc123"
        assert error.tx == tx_data
        assert error.no_send_change == no_send

    def test_review_actions_error_multiple_actions(self) -> None:
        """Test ReviewActionsError with multiple actions."""
        review_results = [
            {"txid": "tx1", "status": "success"},
            {"txid": "tx2", "status": "doubleSpend"},
            {"txid": "tx3", "status": "serviceError"},
        ]
        send_results = [
            {"txid": "tx1", "status": "sending"},
            {"txid": "tx2", "status": "failed"},
            {"txid": "tx3", "status": "failed"},
        ]
        error = ReviewActionsError(review_results, send_results)
        assert "3 action(s) need attention" in str(error)

    def test_raise_review_actions_error(self) -> None:
        """Test raising ReviewActionsError."""
        with pytest.raises(ReviewActionsError):
            raise ReviewActionsError([{"txid": "test", "status": "success"}], [{"txid": "test", "status": "unproven"}])


class TestErrorInheritance:
    """Test error class inheritance."""

    def test_wallet_error_is_exception(self) -> None:
        """Test that WalletError inherits from Exception."""
        error = WalletError("test")
        assert isinstance(error, Exception)

    def test_validation_error_is_wallet_error(self) -> None:
        """Test that ValidationError inherits from WalletError."""
        error = ValidationError("test")
        assert isinstance(error, WalletError)
        assert isinstance(error, Exception)

    def test_configuration_error_is_wallet_error(self) -> None:
        """Test that ConfigurationError inherits from WalletError."""
        error = ConfigurationError("test")
        assert isinstance(error, WalletError)

    def test_state_error_is_wallet_error(self) -> None:
        """Test that StateError inherits from WalletError."""
        error = StateError("test")
        assert isinstance(error, WalletError)

    def test_operation_error_is_wallet_error(self) -> None:
        """Test that OperationError inherits from WalletError."""
        error = OperationError("test")
        assert isinstance(error, WalletError)

    def test_format_error_is_wallet_error(self) -> None:
        """Test that FormatError inherits from WalletError."""
        error = FormatError("test")
        assert isinstance(error, WalletError)

    def test_catch_base_exception(self) -> None:
        """Test catching wallet errors as Exception."""
        with pytest.raises(Exception):
            raise WalletError("test")

    def test_catch_as_wallet_error(self) -> None:
        """Test catching subclasses as WalletError."""
        with pytest.raises(WalletError):
            raise ValidationError("test")


class TestErrorStringRepresentations:
    """Test string representations of errors."""

    def test_wallet_error_str(self) -> None:
        """Test WalletError string representation."""
        error = WalletError("Test message")
        assert str(error) == "Test message"

    def test_wallet_error_str_with_context(self) -> None:
        """Test WalletError string with context."""
        error = WalletError("Error", {"key": "value"})
        result = str(error)
        assert "Error" in result
        assert "key" in result
        assert "value" in result

    def test_invalid_parameter_error_str(self) -> None:
        """Test InvalidParameterError string representation."""
        error = InvalidParameterError("param", "must be positive")
        result = str(error)
        assert "param" in result
        assert "must be positive" in result

    def test_insufficient_funds_error_str(self) -> None:
        """Test InsufficientFundsError string representation."""
        error = InsufficientFundsError(1000, 500)
        result = str(error)
        assert "1000" in result
        assert "500" in result
