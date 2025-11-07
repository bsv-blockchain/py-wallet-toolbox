"""Special operation constants for wallet SpecOp optimization.

Reference: ts-wallet-toolbox/src/sdk/types.ts
"""

# Special operation basket names for storage layer optimizations
# These are used to indicate special operations to the storage layer

specOpWalletBalance = "wallet-balance"  # noqa: N816
"""Special operation basket name for wallet balance computation.

Signals to storage layer to use optimized balance calculation.
Used in listOutputs() to efficiently compute wallet balance.
"""

specOpInvalidChange = "invalid-change"  # noqa: N816
"""Special operation basket name for detecting invalid change outputs.

Signals to storage layer to identify outputs that are not valid UTXOs
(e.g., outputs that don't meet validation criteria).
Used in reviewSpendableOutputs() for UTXO validation.
"""

specOpThrowReviewActions = "throw-review-actions"  # noqa: N816
"""Special operation tag name for error handling in review actions.

Signals to storage layer to throw errors when review actions contain
error statuses, instead of continuing.
"""
