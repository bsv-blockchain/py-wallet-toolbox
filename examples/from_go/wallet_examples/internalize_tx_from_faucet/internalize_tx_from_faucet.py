import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

"""Faucet Transaction Internalization Example.

This example demonstrates how to internalize a transaction from the faucet into the wallet database.
Uses "wallet payment" protocol with BRC-29 derivation to enable proper signing.
"""

import base64

from bsv.keys import PrivateKey
from internal import services_helpers, setup, show
from bsv_wallet_toolbox.wallet import Wallet

# The txID is the transaction ID of the transaction to internalize
# Pass in your txID from the faucet_address example
TX_ID = "27f61490d1a3bff2a50c72642a0438d4b550080b84a2575922f93af91290cb03"  # Set this to your faucet transaction ID

# Must match the values used in show_address_for_tx_from_faucet.py
# These are the raw string values - will be base64 encoded when used
FAUCET_DERIVATION_PREFIX = "faucet-prefix-01"
FAUCET_DERIVATION_SUFFIX = "faucet-suffix-01"

# Base64 encoded versions for paymentRemittance
FAUCET_DERIVATION_PREFIX_B64 = base64.b64encode(FAUCET_DERIVATION_PREFIX.encode()).decode()
FAUCET_DERIVATION_SUFFIX_B64 = base64.b64encode(FAUCET_DERIVATION_SUFFIX.encode()).decode()

# AnyoneKey - matches Go SDK's sdk.AnyoneKey() = PrivateKey(1).PublicKey()
ANYONE_KEY = PrivateKey(1).public_key()


def internalize_from_faucet(atomic_beef: bytes, wallet: Wallet, sender_identity_key: str) -> None:
    """Internalize transaction from faucet into the wallet database.
    
    Uses "wallet payment" protocol with BRC-29 derivation info so the
    wallet can properly sign when spending this output.
    
    Replicates Go's example_setup.InternalizeFromFaucet.
    """
    # Create the arguments needed for InternalizeAction
    # Using "wallet payment" protocol with paymentRemittance for proper key derivation
    internalize_args = {
        "tx": atomic_beef,
        "outputs": [
            {
                "outputIndex": 0,
                "protocol": "wallet payment",
                "paymentRemittance": {
                    "senderIdentityKey": sender_identity_key,
                    "derivationPrefix": FAUCET_DERIVATION_PREFIX_B64,
                    "derivationSuffix": FAUCET_DERIVATION_SUFFIX_B64,
                },
            },
        ],
        "description": "internalize transaction from faucet",
        "labels": ["faucet"],
    }

    # Internalize the transaction
    result = wallet.internalize_action(internalize_args)
    show.wallet_success("InternalizeAction", internalize_args, result)


def main() -> None:
    show.process_start("Faucet Transaction Internalization")

    if not TX_ID:
        raise ValueError("txID must be provided")

    # Go: txIDHash, err := chainhash.NewHashFromHex(txID)
    # Python: we use hex string mostly, or bytes

    show.step("Alice", "Creating wallet and setting up environment")
    alice = setup.create_alice()

    alice_wallet, cleanup = alice.create_wallet()
    try:
        show.step("Alice", "Retrieving transaction data")
        show.transaction(TX_ID)

        chain = services_helpers.normalize_chain(alice.environment.bsv_network)
        show.info("Wallet-Services", f"initializing services for chain '{chain}'")
        srv = services_helpers.create_services(alice.environment.bsv_network)

        show.step("Wallet-Services", f"fetching atomic BEEF for txID: '{TX_ID}'")
        atomic_beef = services_helpers.build_atomic_beef_for_txid(srv, TX_ID)

        show.step("Alice", "Internalizing transaction from faucet")
        # Use AnyoneKey as sender (matches Go SDK behavior)
        internalize_from_faucet(atomic_beef, alice_wallet, ANYONE_KEY.hex())

        show.success("Transaction internalized successfully")
        show.process_complete("Faucet Transaction Internalization")

    finally:
        cleanup()


if __name__ == "__main__":
    main()

