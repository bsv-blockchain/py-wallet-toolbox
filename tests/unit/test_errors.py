"""Unit tests for wallet error classes.

Reference: wallet-toolbox/src/sdk/WERR_errors.ts
"""

import pytest

from bsv_wallet_toolbox.errors import InvalidParameterError


class TestInvalidParameterError:
    """Test suite for InvalidParameterError class.

    Reference: wallet-toolbox/src/sdk/WERR_errors.ts
               WERR_INVALID_PARAMETER class
    """

    def test_creates_error_with_parameter_name(self) -> None:
        """Given: Parameter name
           When: Create InvalidParameterError
           Then: Error message includes parameter name

        Reference: wallet-toolbox/src/sdk/WERR_errors.ts
                   WERR_INVALID_PARAMETER constructor
        """
        # Given
        parameter = "testParam"

        # When
        error = InvalidParameterError(parameter)

        # Then
        assert parameter in str(error)
        assert error.parameter == parameter

    def test_creates_error_with_custom_message(self) -> None:
        """Given: Parameter name and custom message
           When: Create InvalidParameterError
           Then: Error message includes both parameter and custom message

        Reference: wallet-toolbox/src/sdk/WERR_errors.ts
                   WERR_INVALID_PARAMETER constructor with mustBe parameter
        """
        # Given
        parameter = "originator"
        message = "a string under 250 bytes"

        # When
        error = InvalidParameterError(parameter, message)

        # Then
        assert parameter in str(error)
        assert message in str(error)
        assert error.parameter == parameter
        assert error.message == message

    def test_is_exception_instance(self) -> None:
        """Given: InvalidParameterError instance
           When: Check instance type
           Then: Is an Exception

        Reference: wallet-toolbox/src/sdk/WalletError.ts
                   WalletError extends Error
        """
        # Given
        error = InvalidParameterError("test")

        # When/Then
        assert isinstance(error, Exception)

    def test_can_be_raised_and_caught(self) -> None:
        """Given: InvalidParameterError
           When: Raise and catch error
           Then: Can be caught as Exception

        Reference: wallet-toolbox/src/sdk/WERR_errors.ts
                   Usage in validation functions
        """
        # Given
        parameter = "testParam"

        # When/Then
        with pytest.raises(InvalidParameterError) as exc_info:
            raise InvalidParameterError(parameter)

        assert exc_info.value.parameter == parameter
