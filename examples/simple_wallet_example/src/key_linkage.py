"""Key linkage reveal demos."""

from bsv_wallet_toolbox import Wallet


def demo_reveal_counterparty_key_linkage(wallet: Wallet) -> None:
    """Reveal counterparty key linkage information."""
    print("\n🔗 Reveal counterparty key linkage\n")

    counterparty = input("Counterparty (hex pubkey) [Enter=self]: ").strip() or "self"
    protocol_name = input("Protocol name [Enter=test protocol]: ").strip() or "test protocol"

    try:
        result = wallet.reveal_counterparty_key_linkage(
            {
                "counterparty": counterparty,
                "verifier": "02" + "a" * 64,  # demo verifier pubkey
                "protocolID": [0, protocol_name],
                "reason": "Demo counterparty linkage",
                "privilegedReason": "Demo",
            }
        )

        print("\n✅ Counterparty linkage revealed")
        print(f"   Protocol : {protocol_name}")
        print(f"   Prover   : {result.get('prover', '')[:32]}...")
        print(f"   Key      : {result.get('counterparty', '')[:32]}...")

    except Exception as err:
        print(f"❌ Failed to reveal linkage: {err}")
        import traceback

        traceback.print_exc()


def demo_reveal_specific_key_linkage(wallet: Wallet) -> None:
    """Reveal specific key linkage for a given key ID."""
    print("\n🔗 Reveal specific key linkage\n")

    counterparty = input("Counterparty (hex pubkey) [Enter=self]: ").strip() or "self"
    protocol_name = input("Protocol name [Enter=test protocol]: ").strip() or "test protocol"
    key_id = input("Key ID [Enter=1]: ").strip() or "1"

    try:
        result = wallet.reveal_specific_key_linkage(
            {
                "counterparty": counterparty,
                "verifier": "02" + "a" * 64,
                "protocolID": [0, protocol_name],
                "keyID": key_id,
                "reason": "Demo specific linkage",
                "privilegedReason": "Demo",
            }
        )

        print("\n✅ Specific linkage revealed")
        print(f"   Protocol : {protocol_name}")
        print(f"   Key ID   : {key_id}")
        print(f"   Prover   : {result.get('prover', '')[:32]}...")
        print(f"   Counterparty key: {result.get('counterparty', '')[:32]}...")
        print(f"   Specific key    : {result.get('specific', '')[:32]}...")

    except Exception as err:
        print(f"❌ Failed to reveal specific linkage: {err}")
        import traceback

        traceback.print_exc()
