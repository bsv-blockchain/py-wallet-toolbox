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


class InsufficientFundsError(Exception):
    """Raised when there are insufficient funds to cover transaction costs.

    Corresponds to TypeScript WERR_INSUFFICIENT_FUNDS error.

    Args:
        total_satoshis_needed: Total satoshis required to fund transaction
        more_satoshis_needed: Shortfall on total satoshis required

    Example:
        >>> raise InsufficientFundsError(1000, 500)
    
    Reference: ts-wallet-toolbox/src/sdk/WERR_errors.ts
               WERR_INSUFFICIENT_FUNDS class
    """

    def __init__(self, total_satoshis_needed: int, more_satoshis_needed: int) -> None:
        """Initialize InsufficientFundsError.

        Args:
            total_satoshis_needed: Total satoshis required
            more_satoshis_needed: Additional satoshis needed
        """
        self.total_satoshis_needed = total_satoshis_needed
        self.more_satoshis_needed = more_satoshis_needed
        super().__init__(
            f"Insufficient funds in the available inputs to cover the cost of the required outputs "
            f"and the transaction fee ({more_satoshis_needed} more satoshis are needed, "
            f"for a total of {total_satoshis_needed}), plus whatever would be required in order "
            f"to pay the fee to unlock and spend the outputs used to provide the additional satoshis."
        )
