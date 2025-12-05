"""Special operation constants for wallet SpecOp optimization.

Reference: ts-wallet-toolbox/src/sdk/types.ts
"""

# Special operation basket names for storage layer optimizations
# These are used to indicate special operations to the storage layer

specOpWalletBalance = "893b7646de0e1c9f741bd6e9169b76a8847ae34adef7bef1e6a285371206d2e8"  # noqa: N816
"""Special operation basket name for wallet balance computation.

Signals to storage layer to use optimized balance calculation.
Used in listOutputs() to efficiently compute wallet balance.
"""

specOpInvalidChange = "5a76fd430a311f8bc0553859061710a4475c19fed46e2ff95969aa918e612e57"  # noqa: N816
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

specOpSetWalletChangeParams = "a4979d28ced8581e9c1c92f1001cc7cb3aabf8ea32e10888ad898f0a509a3929"  # noqa: N816
"""Special operation basket name for setting wallet change parameters.

Signals to storage layer to update wallet change parameters using
tags [count, satoshis] format.
Used in setWalletChangeParams() method.
"""

specOpNoSendActions = "ac6b20a3bb320adafecd637b25c84b792ad828d3aa510d05dc841481f664277d"  # noqa: N816
"""Special operation label for no-send actions filtering.

Signals to storage layer to filter actions that should not be sent.
Used in listNoSendActions() method.
"""

specOpFailedActions = "97d4eb1e49215e3374cc2c1939a7c43a55e95c7427bf2d45ed63e3b4e0c88153"  # noqa: N816
"""Special operation label for failed actions filtering.

Signals to storage layer to filter actions with 'failed' status.
Used in listFailedActions() method.
"""
