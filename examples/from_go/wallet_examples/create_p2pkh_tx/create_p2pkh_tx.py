import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

"""Create P2PKH Transaction Example.

This example demonstrates how to create and send a Bitcoin transaction using Alice's wallet.
The wallet automatically selects UTXOs, creates change outputs, calculates fees, and broadcasts the transaction.
"""

from bsv.script.type import P2PKH
from bsv.keys import PublicKey
from internal import setup, show

# RecipientAddress is the address to send satoshis to (P2PKH address)
RECIPIENT_ADDRESS = ""  # example: 1A6ut1tWnfg5mAD8s1drDLM6gNsLNGvgWq

# SatoshisToSend is the amount to send to the recipient
SATOSHIS_TO_SEND = 1  # example: 100

# OutputDescription describes the purpose of this output
OUTPUT_DESCRIPTION = "Payment to recipient"

# TransactionDescription describes the purpose of this transaction
TRANSACTION_DESCRIPTION = "Create P2PKH Transaction Example"

# Originator specifies the originator domain or FQDN used to identify the source of the action request.
# NOTE: Replace "example.com" with the actual originator domain or FQDN in real usage.
ORIGINATOR = "example.com"


def main() -> None:
    show.process_start("Create P2PKH Transaction")

    if not RECIPIENT_ADDRESS:
        raise ValueError("recipient address must be provided")

    if SATOSHIS_TO_SEND == 0:
        raise ValueError("satoshis to send must be provided")

    show.step("Alice", "Creating wallet and setting up environment")
    alice = setup.create_alice()

    alice_wallet, cleanup = alice.create_wallet()
    try:
        show.info("Recipient address", RECIPIENT_ADDRESS)

        # Create P2PKH locking script from the recipient address
        # Go: addr, err := script.NewAddressFromString(RecipientAddress)
        #     lockingScript, err := p2pkh.Lock(addr)
        # Python SDK: P2PKH.lock(address_string) -> Script
        locking_script = P2PKH.lock(RECIPIENT_ADDRESS)

        # Create the arguments needed for the CreateAction
        create_args = {
            "description": TRANSACTION_DESCRIPTION,
            "outputs": [
                {
                    "lockingScript": locking_script.hex(),
                    "satoshis": SATOSHIS_TO_SEND,
                    "outputDescription": OUTPUT_DESCRIPTION,
                    "tags": ["payment", "example"],
                },
            ],
            "labels": ["create_action_example"],
            "options": {
                "acceptDelayedBroadcast": False,
            },
        }

        show.step("Alice", f"Creating transaction to send {SATOSHIS_TO_SEND} satoshis")
        show.info("Transaction description", TRANSACTION_DESCRIPTION)
        show.info("Output description", OUTPUT_DESCRIPTION)

        result = alice_wallet.create_action(create_args, ORIGINATOR)

        show.wallet_success("CreateAction", create_args, result)

        tx_id = result.get("txid")
        if tx_id:
            show.transaction(tx_id)
            show.info("Status", "Transaction successfully created and broadcast")

            send_with_results = result.get("sendWithResults", [])
            if send_with_results:
                show.info("Broadcast status", send_with_results[0].get("status"))

        show.success("Transaction created and sent successfully")
        show.process_complete("Create P2PKH Transaction")

    finally:
        cleanup()


if __name__ == "__main__":
    main()

