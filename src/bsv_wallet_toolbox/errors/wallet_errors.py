"""Wallet error classes.

Pythonic error hierarchy for wallet operations.
Designed for clear, informative error handling.

Reference: ts-wallet-toolbox/src/sdk/WERR_errors.ts
"""

from __future__ import annotations

from typing import Any


class WalletError(Exception):
    """Base exception for all wallet-related errors.

    This is the root exception class for the wallet toolkit.
    Use specific subclasses for more precise error handling.

    Args:
        message: Human-readable error description
        context: Optional dict with additional error context

    Example:
        >>> raise WalletError("Operation failed")
        >>> raise WalletError("Invalid state", {"expected": "ready", "actual": "busy"})
    """

    def __init__(self, message: str, context: dict[str, Any] | None = None) -> None:
        """Initialize WalletError.

        Args:
            message: Error description
            context: Optional context dictionary with error details
        """
        self.message = message
        self.context = context or {}
        super().__init__(self._format_message())

    def _format_message(self) -> str:
        """Format error message with context if available."""
        if self.context:
            context_str = ", ".join(f"{k}={v!r}" for k, v in self.context.items())
            return f"{self.message} ({context_str})"
        return self.message


class ValidationError(WalletError):
    """Raised when input validation fails.

    Used for parameter validation, type checking, and format validation.

    Args:
        message: Error description
        field: Optional field name that failed validation
        value: Optional invalid value that was provided

    Example:
        >>> raise ValidationError("Invalid satoshi amount", field="amount", value=-100)
    """

    def __init__(self, message: str, field: str | None = None, value: Any = None) -> None:
        """Initialize ValidationError."""
        context = {}
        if field is not None:
            context["field"] = field
        if value is not None:
            context["value"] = value
        super().__init__(message, context)


class ConfigurationError(WalletError):
    """Raised when required configuration is missing or invalid.

    Used when wallet components, storage, or key derivers are not properly configured.

    Args:
        message: Error description
        component: Optional component name that is misconfigured
        required: Optional list of required items that are missing

    Example:
        >>> raise ConfigurationError("Wallet not configured", component="storage")
    """

    def __init__(self, message: str, component: str | None = None, required: list[str] | None = None) -> None:
        """Initialize ConfigurationError."""
        context = {}
        if component is not None:
            context["component"] = component
        if required is not None:
            context["required"] = required
        super().__init__(message, context)


class StateError(WalletError):
    """Raised when operation is invalid for current wallet state.

    Used for invalid state transitions or operations.

    Args:
        message: Error description
        current_state: Optional current state
        expected_state: Optional expected state(s)

    Example:
        >>> raise StateError("Cannot sign in unlocked state", current_state="unlocked")
    """

    def __init__(
        self,
        message: str,
        current_state: str | None = None,
        expected_state: str | list[str] | None = None,
    ) -> None:
        """Initialize StateError."""
        context = {}
        if current_state is not None:
            context["currentState"] = current_state
        if expected_state is not None:
            context["expectedState"] = expected_state
        super().__init__(message, context)


class OperationError(WalletError):
    """Raised when a wallet operation fails.

    Used for business logic failures, constraint violations, and operation-specific errors.

    Args:
        message: Error description
        operation: Optional operation name that failed
        reason: Optional reason for the failure

    Example:
        >>> raise OperationError("Cannot sign transaction", operation="sign_action", reason="insufficient inputs")
    """

    def __init__(self, message: str, operation: str | None = None, reason: str | None = None) -> None:
        """Initialize OperationError."""
        context = {}
        if operation is not None:
            context["operation"] = operation
        if reason is not None:
            context["reason"] = reason
        super().__init__(message, context)


class FormatError(WalletError):
    """Raised when data format is invalid or incompatible.

    Used for transaction format, BEEF format, or other data structure issues.

    Args:
        message: Error description
        data_type: Optional data type that has format issue
        expected_format: Optional expected format description

    Example:
        >>> raise FormatError("Invalid BEEF format", data_type="tx", expected_format="atomic_beef")
    """

    def __init__(self, message: str, data_type: str | None = None, expected_format: str | None = None) -> None:
        """Initialize FormatError."""
        context = {}
        if data_type is not None:
            context["dataType"] = data_type
        if expected_format is not None:
            context["expectedFormat"] = expected_format
        super().__init__(message, context)


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


class TransactionBroadcastError(Exception):
    """Raised when transaction broadcast fails.

    This error occurs when a transaction cannot be sent to the network,
    typically due to network issues, invalid transaction, or rejected by nodes.

    Args:
        message: Description of the broadcast failure

    Example:
        >>> raise TransactionBroadcastError("failed to send output creating transaction")
    """

    def __init__(self, message: str = "Transaction broadcast failed") -> None:
        """Initialize TransactionBroadcastError.

        Args:
            message: Error description
        """
        self.message = message
        super().__init__(message)


class TransactionSizeError(Exception):
    """Raised when transaction size calculation encounters an error.

    This error occurs when input or output size calculations fail,
    typically due to invalid script sizes or malformed data.

    Args:
        message: Description of the size calculation error

    Example:
        >>> raise TransactionSizeError("Invalid script size in transaction input")
    """

    def __init__(self, message: str = "Transaction size calculation error") -> None:
        """Initialize TransactionSizeError.

        Args:
            message: Error description
        """
        self.message = message
        super().__init__(message)


class ReviewActionsError(Exception):
    """Raised when actions require user review before proceeding.

    Corresponds to TypeScript WERR_REVIEW_ACTIONS error.

    When a `create_action` or `sign_action` is completed in undelayed mode
    (`accept_delayed_broadcast`: False), any unsuccessful result will return
    the results by way of this exception to ensure attention is paid to
    processing errors.

    All parameters correspond to their comparable `create_action` or `sign_action`
    results, with the exception of `review_action_results`, which contains more
    details, particularly for double spend results.

    Args:
        review_action_results: List of action results requiring review
        send_with_results: List of send results for each transaction
        txid: Transaction ID (optional)
        tx: Atomic BEEF transaction data (optional)
        no_send_change: List of outpoint strings not sent as change (optional)

    Example:
        >>> raise ReviewActionsError(
        ...     review_action_results=[{"txid": "abc...", "status": "doubleSpend"}],
        ...     send_with_results=[{"txid": "abc...", "status": "failed"}],
        ...     txid="abc123...",
        ...     tx=[1, 2, 3, ...],
        ...     no_send_change=["def456...:0"]
        ... )

    Reference: ts-wallet-toolbox/src/sdk/WERR_errors.ts
               WERR_REVIEW_ACTIONS class (lines 154-169)
    """

    def __init__(
        self,
        review_action_results: list[dict[str, Any]],
        send_with_results: list[dict[str, Any]],
        txid: str | None = None,
        tx: list[int] | None = None,
        no_send_change: list[str] | None = None,
    ) -> None:
        """Initialize ReviewActionsError.

        Args:
            review_action_results: List of ReviewActionResult dicts with keys:
                - txid: Transaction ID
                - status: 'success' | 'doubleSpend' | 'serviceError' | 'invalidTx'
                - competingTxs: Optional list of competing transaction IDs
                - competingBeef: Optional BEEF data for competing transactions
            send_with_results: List of SendWithResult dicts with keys:
                - txid: Transaction ID
                - status: 'unproven' | 'sending' | 'failed'
            txid: Transaction ID (optional)
            tx: Atomic BEEF transaction data as byte array (optional)
            no_send_change: Outpoint strings not sent as change (optional)
        """
        self.review_action_results = review_action_results
        self.send_with_results = send_with_results
        self.txid = txid
        self.tx = tx
        self.no_send_change = no_send_change

        super().__init__(
            f"Undelayed createAction or signAction results require review. "
            f"{len(review_action_results)} action(s) need attention."
        )
