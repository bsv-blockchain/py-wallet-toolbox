import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

"""Faucet Transaction Internalization Example.

This example demonstrates how to internalize a transaction from the faucet into the wallet database.
"""

import sys

from internal import services_helpers, setup, show
from bsv_wallet_toolbox.wallet import Wallet

# The txID is the transaction ID of the transaction to internalize
# Pass in your txID from the faucet_address example
TX_ID = "c9a45c4a7a5b61e0302ed7572d20f3fa76fcb23716513759857b70ea675bd386"  # example: 15f47f2db5f26469c081e8d80d91a4b0f06e4a97abcc022b0b5163ac5f6cc0c8


def internalize_from_faucet(atomic_beef: bytes, wallet: Wallet) -> None:
    """Internalize transaction from faucet into the wallet database.
    
    Replicates Go's example_setup.InternalizeFromFaucet.
    """
    # Create the arguments needed for InternalizeAction
    internalize_args = {
        "tx": atomic_beef,
        "outputs": [
            {
                "outputIndex": 0,
                "protocol": "basket insertion",
                "basket": "default",
            },
            {
                "outputIndex": 1,
                "protocol": "basket insertion",
                "basket": "default",
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
        internalize_from_faucet(atomic_beef, alice_wallet)

        show.success("Transaction internalized successfully")
        show.process_complete("Faucet Transaction Internalization")

    finally:
        cleanup()


if __name__ == "__main__":
    main()

