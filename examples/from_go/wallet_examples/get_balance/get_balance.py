import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

"""Get Wallet Balance Example.

This example demonstrates how to get the balance of a wallet.
"""

from internal import setup, show


def main() -> None:
    show.process_start("Get Wallet Balance")

    show.step("Alice", "Creating wallet and setting up environment")
    alice = setup.create_alice()

    alice_wallet, cleanup = alice.create_wallet()
    try:
        show.step("Alice", "Getting balance")

        # Use the balance() method which uses specOpWalletBalance internally
        balance = alice_wallet.balance()

        show.wallet_success("Balance", None, balance)
        show.process_complete("Get Wallet Balance")

    finally:
        cleanup()


if __name__ == "__main__":
    main()

