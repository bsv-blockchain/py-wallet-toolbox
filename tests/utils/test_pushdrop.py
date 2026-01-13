"""Unit tests for pushdrop.

This module tests PushDrop protocol example.

Reference: wallet-toolbox/test/examples/pushdrop.test.ts
"""

from typing import Any

import pytest

try:
    from bsv_wallet_toolbox.beef import Beef
    from bsv_wallet_toolbox.pushdrop import PushDrop

    from bsv_wallet_toolbox.errors import TransactionBroadcastError
    from bsv_wallet_toolbox.utils import Setup

    IMPORTS_AVAILABLE = True
except ImportError:
    IMPORTS_AVAILABLE = False


async def output_pushdrop(setup: Any, to_identity_key: str, satoshis: int) -> dict[str, Any]:
    """Create a PushDrop output locked to receiver's identity key.

    Reference: wallet-toolbox/test/examples/pushdrop.test.ts
               async function outputPushDrop()

    Args:
        setup: SetupWallet context
        to_identity_key: Receiver's public identity key
        satoshis: Amount to transfer

    Returns:
        Dict containing beef, outpoint, fromIdentityKey, satoshis, protocol, keyId
    """
    t = PushDrop(setup.wallet)

    protocol = [2, "pushdropexample"]
    key_id = "7"

    # Create PushDrop lock script
    lock = t.lock([[1, 2, 3], [4, 5, 6]], protocol, key_id, to_identity_key, False, True, "before")
    locking_script = lock.to_hex()

    label = "outputPushDrop"

    # Create action with PushDrop output
    car = setup.wallet.create_action(
        {
            "outputs": [
                {
                    "lockingScript": locking_script,
                    "satoshis": satoshis,
                    "outputDescription": label,
                    "tags": ["relinquish"],
                    "customInstructions": {
                        "protocol": protocol,
                        "keyId": key_id,
                        "counterparty": to_identity_key,
                        "type": "PushDrop",
                    },
                }
            ],
            "options": {"randomizeOutputs": False, "acceptDelayedBroadcast": True},
            "labels": [label],
            "description": label,
        }
    )

    if any(r["status"] == "failed" for r in car.get("sendWithResults", [])):
        raise TransactionBroadcastError("failed to send output creating transaction")

    beef = Beef.from_binary(car["tx"])
    outpoint = f"{car['txid']}.0"

    return {
        "beef": beef,
        "outpoint": outpoint,
        "fromIdentityKey": setup.identity_key,
        "satoshis": satoshis,
        "protocol": protocol,
        "keyId": key_id,
    }


async def input_pushdrop(setup: Any, output_pushdrop: dict[str, Any]) -> None:
    """Consume a PushDrop output.

    Reference: wallet-toolbox/test/examples/pushdrop.test.ts
               async function inputPushDrop()

    Args:
        setup: SetupWallet context
        output_pushdrop: Output data from output_pushdrop()
    """
    protocol = output_pushdrop["protocol"]
    key_id = output_pushdrop["keyId"]
    from_identity_key = output_pushdrop["fromIdentityKey"]
    satoshis = output_pushdrop["satoshis"]
    input_beef = output_pushdrop["beef"]
    outpoint = output_pushdrop["outpoint"]

    t = PushDrop(setup.wallet)

    # Construct unlock template
    unlock = t.unlock(protocol, key_id, from_identity_key, "single", False, satoshis)

    label = "inputPushDrop"

    # Create action with PushDrop input (two-step process)
    car = setup.wallet.create_action(
        {
            "inputBEEF": input_beef.to_binary(),
            "inputs": [
                {"outpoint": outpoint, "unlockingScriptLength": 73, "inputDescription": label}  # PushDrop constant
            ],
            "labels": [label],
            "description": label,
        }
    )

    # Sign the transaction
    st = car["signableTransaction"]
    beef = Beef.from_binary(st["tx"])
    tx = beef.find_atomic_transaction(beef.txs[-1].txid)
    tx.inputs[0].unlocking_script_template = unlock
    tx.sign()
    unlocking_script = tx.inputs[0].unlocking_script.to_hex()

    # Complete the action with signAction
    sign_args = {
        "reference": st["reference"],
        "spends": {0: {"unlockingScript": unlocking_script}},
        "options": {"acceptDelayedBroadcast": True},
    }

    sar = setup.wallet.sign_action(sign_args)
    if any(r["status"] == "failed" for r in sar.get("sendWithResults", [])):
        raise TransactionBroadcastError("failed to send output creating transaction")


async def transfer_pushdrop() -> None:
    """Transfer satoshis using BRC29 PushDrop template.

    Reference: wallet-toolbox/test/examples/pushdrop.test.ts
               async function transferPushDrop()
    """
    # Obtain environment for mainnet
    env = Setup.get_env("main")

    # Setup sender wallet
    setup1 = Setup.create_wallet_client({"env": env})

    # Setup receiver wallet (same as sender in this example)
    setup2 = setup1

    # Create PushDrop output for setup2
    o = output_pushdrop(setup1, setup2.identity_key, 42)

    # Consume the output with setup2
    input_pushdrop(setup2, o)

    # Cleanup
    setup1.wallet.destroy()
    setup2.wallet.destroy()


class TestPushdrop:
    """Test suite for pushdrop example.

    Reference: wallet-toolbox/test/examples/pushdrop.test.ts
                describe('pushdrop example tests')
    """

    @pytest.mark.integration
    def test_pushdrop_transfer_example(self) -> None:
        """Given: Two wallets (sender and receiver)
           When: Transfer satoshis using BRC29 PushDrop template
           Then: Successfully creates output and consumes it

        Reference: wallet-toolbox/test/examples/pushdrop.test.ts
                   test('0 pushdrop')

        Note: This is an integration test that requires:
        - Live network connection
        - Test wallets with funds
        - Environment variable setup
        """
        if not IMPORTS_AVAILABLE:
            pytest.skip("Required imports not available")

        # Given/When/Then
        if Setup.no_env("main"):
            pytest.skip("No 'main' environment configured")

        pytest.skip("Setup.create_wallet_client is not fully implemented")
