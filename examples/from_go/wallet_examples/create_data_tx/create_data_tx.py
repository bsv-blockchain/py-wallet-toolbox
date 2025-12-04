import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

"""Create Data Transaction Example.

This example demonstrates how to create and send a Bitcoin transaction with an OP_RETURN data output using Alice's wallet.
"""

import sys

from bsv.script.type import OpReturn
from internal import setup, show

# DataToEmbed is the string that will be embedded in an OP_RETURN output
# example: "hello world"
DATA_TO_EMBED = "hello world"

# OutputDescription describes the purpose of this output
OUTPUT_DESCRIPTION = "Data output"

# TransactionDescription describes the purpose of this transaction
TRANSACTION_DESCRIPTION = "Create Data Transaction Example"

# Originator specifies the originator domain or FQDN used to identify the source of the action request
# NOTE: Replace "example.com" with the actual originator domain or FQDN in real usage
ORIGINATOR = "example.com"


def main() -> None:
    show.process_start("Create Data Transaction")

    if not DATA_TO_EMBED:
        raise ValueError("data to embed must be provided")

    show.step("Alice", "Creating wallet and setting up environment")
    alice = setup.create_alice()

    alice_wallet, cleanup = alice.create_wallet()
    try:
        show.info("Data", DATA_TO_EMBED)

        # Create OP_RETURN output containing the provided data
        # Go: dataOutput, err := transaction.CreateOpReturnOutput([][]byte{[]byte(DataToEmbed)})
        # Python SDK: OpReturn().lock([data]) -> Script
        op_return = OpReturn()
        # OpReturn.lock expects list of str or bytes.
        locking_script = op_return.lock([DATA_TO_EMBED.encode("utf-8")])

        # Create the arguments needed for the CreateAction
        create_args = {
            "description": TRANSACTION_DESCRIPTION,
            "outputs": [
                {
                    "lockingScript": locking_script.hex(),
                    "satoshis": 0,
                    "outputDescription": OUTPUT_DESCRIPTION,
                    "tags": ["data", "example"],
                },
            ],
            "labels": ["create_action_example"],
            "options": {
                "acceptDelayedBroadcast": False,
            },
        }

        show.step("Alice", "Creating transaction with OP_RETURN data")
        show.info("Transaction description", TRANSACTION_DESCRIPTION)
        show.info("Output description", OUTPUT_DESCRIPTION)

        # result, err := aliceWallet.CreateAction(ctx, createArgs, Originator)
        result = alice_wallet.create_action(create_args, ORIGINATOR)

        show.wallet_success("CreateAction", create_args, result)

        tx_id = result.get("txid")
        if not tx_id:
            raise RuntimeError("transaction ID is empty, action creation failed")

        show.transaction(tx_id)
        show.info("Status", "Transaction successfully created and broadcast")

        send_with_results = result.get("sendWithResults", [])
        if send_with_results:
            show.info("Broadcast status", send_with_results[0].get("status"))
        
        show.process_complete("Create Data Transaction")

    finally:
        cleanup()


if __name__ == "__main__":
    main()

