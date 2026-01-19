"""Advanced demos: outputs, aborting actions, relinquishing certs."""

from bsv_wallet_toolbox import Wallet


def demo_list_outputs(wallet: Wallet) -> None:
    """List spendable outputs held by the wallet."""
    print("\n📋 Fetching outputs (basket: default)\n")

    try:
        outputs = wallet.list_outputs({"basket": "default", "limit": 10, "offset": 0})

        print(f"✅ Total outputs: {outputs.get('totalOutputs', 0)}\n")

        if outputs.get("outputs"):
            for i, output in enumerate(outputs["outputs"][:10], 1):
                print(f"   {i}. Outpoint : {output.get('outpoint', 'N/A')}")
                print(f"      Satoshis : {output.get('satoshis', 0)}")
                print(f"      Spendable: {output.get('spendable', True)}")
                print()
        else:
            print("   (no outputs tracked yet)")

    except Exception as err:
        print(f"❌ Failed to list outputs: {err}")
        import traceback

        traceback.print_exc()


def demo_relinquish_output(wallet: Wallet) -> None:
    """Relinquish an output (demo uses a dummy outpoint)."""
    print("\n🗑️  Relinquishing an output\n")
    print("⚠️  This call only succeeds if the referenced outpoint exists in storage.")
    print("   We'll call it with a dummy value so failures are expected.")
    print()

    outpoint = "0000000000000000000000000000000000000000000000000000000000000000:0"

    try:
        result = wallet.relinquish_output({"basket": "default", "output": outpoint})

        print("✅ Relinquish call completed")
        print(f"   Outpoint         : {outpoint}")
        print(f"   Relinquished cnt : {result.get('relinquished', 0)}")

    except Exception as err:
        print(f"⚠️  Relinquish failed (likely expected in demo): {err}")


def demo_abort_action(wallet: Wallet) -> None:
    """Abort a selected pending action."""
    print("\n🚫 Aborting an action\n")

    try:
        actions = wallet.list_actions({"labels": [], "limit": 10})

        if not actions["actions"]:
            print("No abortable actions yet. Create one via menu 13 first.")
            return

        print("Abort candidates:")
        for i, act in enumerate(actions["actions"], 1):
            print(f"   {i}. {act['description']}")
            print(f"      Reference: {act['reference']}")
            print()

        choice = input("Select action index to abort [Enter=1]: ").strip() or "1"
        idx = int(choice) - 1

        if 0 <= idx < len(actions["actions"]):
            reference = actions["actions"][idx]["reference"]
            result = wallet.abort_action({"reference": reference})
            print("\n✅ Action aborted")
            print(f"   Reference : {reference}")
            print(f"   Aborted # : {result.get('aborted', 0)}")
        else:
            print("❌ Invalid selection.")

    except Exception as err:
        print(f"❌ Failed to abort action: {err}")


def demo_relinquish_certificate(wallet: Wallet) -> None:
    """Allow the user to relinquish a certificate."""
    print("\n🗑️  Relinquishing a certificate\n")

    try:
        certs = wallet.list_certificates(
            {
                "certifiers": [],
                "types": [],
                "limit": 10,
                "offset": 0,
                "privileged": False,
                "privilegedReason": "List demo certificates",
            }
        )

        if not certs["certificates"]:
            print("No certificates available. Acquire one via menu 19 first.")
            return

        print("Certificates on file:")
        for i, cert in enumerate(certs["certificates"], 1):
            print(f"   {i}. {cert['type']}")
            print(f"      Certificate ID: {cert.get('certificateId', 'N/A')}")
            print()

        choice = input("Select certificate index to relinquish [Enter=1]: ").strip() or "1"
        idx = int(choice) - 1

        if 0 <= idx < len(certs["certificates"]):
            cert = certs["certificates"][idx]
            cert_type = cert["type"]
            certifier = cert.get("certifier", "self")
            serial = cert.get("serialNumber", "")

            wallet.relinquish_certificate({"type": cert_type, "certifier": certifier, "serialNumber": serial})

            print("\n✅ Certificate relinquished")
            print(f"   Type     : {cert_type}")
            print(f"   Certifier: {certifier}")
        else:
            print("❌ Invalid selection.")

    except Exception as err:
        print(f"❌ Failed to relinquish certificate: {err}")
        import traceback

        traceback.print_exc()
