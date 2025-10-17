"""Wallet error classes.

Reference: ts-wallet-toolbox/src/sdk/WERR_errors.ts
"""


class InvalidParameterError(Exception):
    """Raised when a parameter is invalid.

    Corresponds to TypeScript WERR_INVALID_PARAMETER error.

    Args:
        parameter: The name of the invalid parameter
        message: Optional custom error message

    Example:
        >>> raise InvalidParameterError("originator", "must be a string under 250 bytes")
    """

    def __init__(self, parameter: str, message: str = "invalid") -> None:
        """Initialize InvalidParameterError.

        Args:
            parameter: Parameter name
            message: Error description
        """
        self.parameter = parameter
        self.message = message
        super().__init__(f"Invalid parameter '{parameter}': {message}")
