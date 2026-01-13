"""Key management demos (get public key, sign data)."""

from bsv_wallet_toolbox import Wallet


def demo_get_public_key(wallet: Wallet) -> None:
    """Fetch a protocol-specific derived public key."""
    print("\n🔑 Fetching protocol-specific key\n")

    protocol_name = input("Protocol name [Enter=test protocol]: ").strip() or "test protocol"
    key_id = input("Key ID [Enter=1]: ").strip() or "1"
    counterparty = input("Counterparty (self/anyone) [Enter=self]: ").strip() or "self"

    try:
        result = wallet.get_public_key(
            {
                "identityKey": True,
                "protocolID": [0, protocol_name],
                "keyID": key_id,
                "counterparty": counterparty,
                "reason": f"Key for protocol {protocol_name}",
            }
        )
        print("\n✅ Public key retrieved")
        print(f"   Protocol   : {protocol_name}")
        print(f"   Key ID     : {key_id}")
        print(f"   Counterparty: {counterparty}")
        print(f"   Public key : {result['publicKey']}")
    except Exception as err:
        print(f"❌ Failed to get public key: {err}")


def demo_sign_data(wallet: Wallet) -> None:
    """Sign user-provided data and show the signature."""
    print("\n✍️  Signing data\n")

    message = input("Message to sign [Enter=Hello, BSV!]: ").strip() or "Hello, BSV!"
    protocol_name = input("Protocol name [Enter=test protocol]: ").strip() or "test protocol"
    key_id = input("Key ID [Enter=1]: ").strip() or "1"

    try:
        data = list(message.encode())
        result = wallet.create_signature(
            {
                "data": data,
                "protocolID": [0, protocol_name],
                "keyID": key_id,
                "counterparty": "self",
                "reason": "Demo signature",
            }
        )
        print("\n✅ Signature created")
        print(f"   Message  : {message}")
        print(f"   Signature: {result['signature'][:64]}...")
        print(f"   Public key: {result['publicKey']}")
    except Exception as err:
        print(f"❌ Failed to sign message: {err}")
