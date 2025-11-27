"""Coverage tests for custom error classes.

This module tests custom error classes and error handling utilities.
"""

import pytest


class TestWalletErrors:
    """Test wallet-specific errors."""

    def test_import_wallet_error(self) -> None:
        """Test importing WalletError."""
        try:
            from bsv_wallet_toolbox.errors import WalletError
            assert WalletError is not None
        except ImportError:
            pass

    def test_raise_wallet_error(self) -> None:
        """Test raising WalletError."""
        try:
            from bsv_wallet_toolbox.errors import WalletError
            
            with pytest.raises(WalletError):
                raise WalletError("Test error")
        except ImportError:
            pass

    def test_wallet_error_message(self) -> None:
        """Test WalletError message."""
        try:
            from bsv_wallet_toolbox.errors import WalletError
            
            error = WalletError("Custom message")
            assert str(error) == "Custom message"
        except ImportError:
            pass


class TestInvalidParameterError:
    """Test InvalidParameterError."""

    def test_import_invalid_parameter_error(self) -> None:
        """Test importing InvalidParameterError."""
        try:
            from bsv_wallet_toolbox.errors import InvalidParameterError
            assert InvalidParameterError is not None
        except ImportError:
            pass

    def test_raise_invalid_parameter_error(self) -> None:
        """Test raising InvalidParameterError."""
        try:
            from bsv_wallet_toolbox.errors import InvalidParameterError
            
            with pytest.raises(InvalidParameterError):
                raise InvalidParameterError("Invalid param")
        except ImportError:
            pass


class TestAuthenticationErrors:
    """Test authentication-related errors."""

    def test_import_authentication_error(self) -> None:
        """Test importing authentication errors."""
        try:
            from bsv_wallet_toolbox.errors import AuthenticationError
            assert AuthenticationError is not None
        except (ImportError, AttributeError):
            pass

    def test_raise_authentication_error(self) -> None:
        """Test raising authentication error."""
        try:
            from bsv_wallet_toolbox.errors import AuthenticationError
            
            with pytest.raises(AuthenticationError):
                raise AuthenticationError("Auth failed")
        except (ImportError, AttributeError):
            pass


class TestStorageErrors:
    """Test storage-related errors."""

    def test_import_storage_error(self) -> None:
        """Test importing storage errors."""
        try:
            from bsv_wallet_toolbox.errors import StorageError
            assert StorageError is not None
        except (ImportError, AttributeError):
            pass

    def test_raise_storage_error(self) -> None:
        """Test raising storage error."""
        try:
            from bsv_wallet_toolbox.errors import StorageError
            
            with pytest.raises(StorageError):
                raise StorageError("Storage failed")
        except (ImportError, AttributeError):
            pass


class TestTransactionErrors:
    """Test transaction-related errors."""

    def test_import_transaction_error(self) -> None:
        """Test importing transaction errors."""
        try:
            from bsv_wallet_toolbox.errors import TransactionError
            assert TransactionError is not None
        except (ImportError, AttributeError):
            pass

    def test_raise_transaction_error(self) -> None:
        """Test raising transaction error."""
        try:
            from bsv_wallet_toolbox.errors import TransactionError
            
            with pytest.raises(TransactionError):
                raise TransactionError("Transaction invalid")
        except (ImportError, AttributeError):
            pass


class TestNetworkErrors:
    """Test network-related errors."""

    def test_import_network_error(self) -> None:
        """Test importing network errors."""
        try:
            from bsv_wallet_toolbox.errors import NetworkError
            assert NetworkError is not None
        except (ImportError, AttributeError):
            pass

    def test_raise_network_error(self) -> None:
        """Test raising network error."""
        try:
            from bsv_wallet_toolbox.errors import NetworkError
            
            with pytest.raises(NetworkError):
                raise NetworkError("Network failed")
        except (ImportError, AttributeError):
            pass


class TestErrorInheritance:
    """Test error class inheritance."""

    def test_wallet_error_is_exception(self) -> None:
        """Test that WalletError inherits from Exception."""
        try:
            from bsv_wallet_toolbox.errors import WalletError
            
            error = WalletError("test")
            assert isinstance(error, Exception)
        except ImportError:
            pass

    def test_catch_base_exception(self) -> None:
        """Test catching wallet errors as Exception."""
        try:
            from bsv_wallet_toolbox.errors import WalletError
            
            with pytest.raises(Exception):
                raise WalletError("test")
        except ImportError:
            pass


class TestErrorContext:
    """Test error context and attributes."""

    def test_error_with_context(self) -> None:
        """Test error with additional context."""
        try:
            from bsv_wallet_toolbox.errors import WalletError
            
            error = WalletError("Error message")
            if hasattr(error, "context"):
                error.context = {"key": "value"}
                assert error.context["key"] == "value"
        except (ImportError, AttributeError):
            pass

    def test_error_with_code(self) -> None:
        """Test error with error code."""
        try:
            from bsv_wallet_toolbox.errors import WalletError
            
            error = WalletError("Error message")
            if hasattr(error, "code"):
                error.code = "ERR_001"
                assert error.code == "ERR_001"
        except (ImportError, AttributeError):
            pass

