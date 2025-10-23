"""Wallet error classes.

Reference: ts-wallet-toolbox/src/sdk/WERR_errors.ts
"""

from __future__ import annotations

from typing import Any


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
