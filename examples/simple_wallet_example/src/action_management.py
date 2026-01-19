"""Helpers for create/list/sign action flows."""

from bsv_wallet_toolbox import Wallet


def demo_create_action(wallet: Wallet) -> None:
    """Create a simple OP_RETURN action and sign it."""
    print("\n📋 Creating a demo action (OP_RETURN message)")
    print()

    message = input("Message to embed (press Enter for default): ").strip() or "Hello, World!"

    try:
        message_bytes = message.encode()
        hex_data = message_bytes.hex()
        length = len(message_bytes)
        locking_script = f"006a{length:02x}{hex_data}"

        create_args = {
            "description": f"Store message: {message}",
            "outputs": [
                {
                    "lockingScript": locking_script,
                    "satoshis": 0,
                    "outputDescription": "Message output",
                    "tags": ["demo", "opreturn"],
                }
            ],
            "labels": ["demo:create_action"],
            "options": {
                # Broadcast immediately after signAction completes (TS parity)
                "acceptDelayedBroadcast": False,
            },
        }

        action = wallet.create_action(create_args)

        print("\n✅ Action created")
        signable = action.get("signableTransaction")
        sign_required = signable is not None
        print(f"   Needs sig : {sign_required}")

        if sign_required:
            reference = signable.get("reference")
            if not reference:
                print("❌ Missing reference in signableTransaction; cannot sign.")
                return

            print("\n✍️  Signing action...")
            signed = wallet.sign_action({"reference": reference, "accept": True})
            print("✅ Action signed & broadcast requested")

            txid = signed.get("txid")
            if txid:
                print(f"   TxID   : {txid}")
            send_with_results = signed.get("sendWithResults") or []
            if send_with_results:
                status = send_with_results[0].get("status", "unknown")
                print(f"   Network: {status}")
            else:
                print("   Network: (no sendWithResults returned)")
        else:
            txid = action.get("txid")
            if txid:
                print(f"   TxID   : {txid}")
            else:
                print("   TxID   : (not returned)")

    except Exception as err:
        print(f"❌ Failed to create action: {err}")
        import traceback

        traceback.print_exc()


def demo_list_actions(wallet: Wallet) -> None:
    """List the most recent actions stored in the wallet."""
    print("\n📋 Fetching recent actions...")

    try:
        actions = wallet.list_actions({"labels": [], "limit": 10})
        print(f"\n✅ Found {len(actions['actions'])} actions\n")

        if not actions["actions"]:
            print("   (no actions recorded yet)")
        else:
            for i, act in enumerate(actions["actions"], 1):
                print(f"   {i}. {act['description']}")
                print(f"      Reference: {act['reference']}")
                print(f"      Status   : {act.get('status', 'unknown')}")
                print()
    except Exception as err:
        print(f"❌ Failed to list actions: {err}")
