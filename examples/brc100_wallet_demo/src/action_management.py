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
        script = f"006a{length:02x}{hex_data}"

        action = wallet.create_action(
            {
                "description": f"Store message: {message}",
                "inputs": {},
                "outputs": [
                    {
                        "script": script,
                        "satoshis": 0,
                        "description": "Message output",
                    }
                ],
            }
        )

        print("\n✅ Action created")
        print(f"   Reference : {action['reference']}")
        print(f"   Desc      : {action['description']}")
        print(f"   Needs sig : {action['signActionRequired']}")

        if action["signActionRequired"]:
            print("\n✍️  Signing action...")
            signed = wallet.sign_action(
                {
                    "reference": action["reference"],
                    "accept": True,
                }
            )
            print("✅ Action signed")

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

