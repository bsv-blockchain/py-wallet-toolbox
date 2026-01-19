"""Crypto demos: HMAC, encryption/decryption, signature verification."""

from bsv_wallet_toolbox import Wallet


def demo_create_hmac(wallet: Wallet) -> None:
    """Generate an HMAC using wallet-managed keys."""
    print("\n🔐 Creating HMAC\n")

    message = input("Message [Enter=Hello, HMAC!]: ").strip() or "Hello, HMAC!"
    protocol_name = input("Protocol name [Enter=test protocol]: ").strip() or "test protocol"
    key_id = input("Key ID [Enter=1]: ").strip() or "1"

    try:
        data = list(message.encode())
        result = wallet.create_hmac(
            {
                "data": data,
                "protocolID": [0, protocol_name],
                "keyID": key_id,
                "counterparty": "self",
                "reason": "Demo create HMAC",
            }
        )
        print("\n✅ HMAC generated")
        print(f"   Message: {message}")
        print(f"   HMAC   : {result['hmac']}")
    except Exception as err:
        print(f"❌ Failed to create HMAC: {err}")


def demo_verify_hmac(wallet: Wallet) -> None:
    """Create + verify an HMAC in one flow."""
    print("\n🔍 Verifying HMAC")
    print("Creating an HMAC first, then verifying it...\n")

    message = "Test HMAC Verification"
    protocol_name = "test protocol"
    key_id = "1"

    try:
        data = list(message.encode())
        create_result = wallet.create_hmac(
            {
                "data": data,
                "protocolID": [0, protocol_name],
                "keyID": key_id,
                "counterparty": "self",
                "reason": "HMAC verification demo",
            }
        )

        hmac_value = create_result["hmac"]
        print(f"Generated HMAC preview: {hmac_value[:32]}...\n")

        verify_result = wallet.verify_hmac(
            {
                "data": data,
                "hmac": hmac_value,
                "protocolID": [0, protocol_name],
                "keyID": key_id,
                "counterparty": "self",
                "reason": "Verify HMAC demo",
            }
        )

        print(f"✅ Verification result: {verify_result['valid']}")
    except Exception as err:
        print(f"❌ Failed to verify HMAC: {err}")


def demo_verify_signature(wallet: Wallet) -> None:
    """Sign data and verify the signature."""
    print("\n🔍 Verifying signature")
    print("Creating a signature first, then verifying...\n")

    message = "Test Signature Verification"
    protocol_name = "test protocol"
    key_id = "1"

    try:
        data = list(message.encode())
        create_result = wallet.create_signature(
            {
                "data": data,
                "protocolID": [0, protocol_name],
                "keyID": key_id,
                "counterparty": "self",
                "reason": "Signature verification demo",
            }
        )

        signature = create_result["signature"]
        public_key = create_result["publicKey"]
        print(f"Signature preview : {signature[:32]}...")
        print(f"Public key preview: {public_key[:32]}...\n")

        verify_result = wallet.verify_signature(
            {
                "data": data,
                "signature": signature,
                "protocolID": [0, protocol_name],
                "keyID": key_id,
                "counterparty": "self",
                "reason": "Verify signature demo",
            }
        )

        print(f"✅ Signature valid: {verify_result['valid']}")
    except Exception as err:
        print(f"❌ Failed to verify signature: {err}")


def demo_encrypt_decrypt(wallet: Wallet) -> None:
    """Encrypt and decrypt a short message."""
    print("\n🔐 Encrypting and decrypting data\n")

    message = input("Plaintext [Enter=Secret Message!]: ").strip() or "Secret Message!"
    protocol_name = input("Protocol name [Enter=encryption protocol]: ").strip() or "encryption protocol"
    key_id = input("Key ID [Enter=1]: ").strip() or "1"

    try:
        plaintext = list(message.encode())
        encrypt_result = wallet.encrypt(
            {
                "plaintext": plaintext,
                "protocolID": [0, protocol_name],
                "keyID": key_id,
                "counterparty": "self",
                "reason": "Encrypt demo data",
            }
        )

        ciphertext = encrypt_result["ciphertext"]
        preview = ciphertext[:64] if isinstance(ciphertext, str) else ciphertext[:32]
        print("\n✅ Data encrypted")
        print(f"   Plaintext : {message}")
        print(f"   Ciphertext: {preview}...")

        decrypt_result = wallet.decrypt(
            {
                "ciphertext": ciphertext,
                "protocolID": [0, protocol_name],
                "keyID": key_id,
                "counterparty": "self",
                "reason": "Decrypt demo data",
            }
        )

        decrypted = bytes(decrypt_result["plaintext"]).decode()
        print("\n✅ Data decrypted")
        print(f"   Decrypted message: {decrypted}")
        print(f"   Matches original : {decrypted == message}")

    except Exception as err:
        print(f"❌ Encryption demo failed: {err}")
        import traceback

        traceback.print_exc()
