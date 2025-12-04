import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

"""Encrypt Example.

This example shows how to encrypt a message using the wallet.
It creates a new wallet for Alice, encrypts a message, and prints the encrypted message.


"""

from internal import setup, show

# keyID is the key ID for the encryption key.
KEY_ID = "key-id"

# originator specifies the originator domain or FQDN used to identify the source of the encryption request.
# NOTE: Replace "example.com" with the actual originator domain or FQDN in real usage.
ORIGINATOR = "example.com"

# protocolID is the default protocol ID for the encryption.
PROTOCOL_ID = "encryption"

# plaintext is the text that will be encrypted.
PLAINTEXT = "Hello, world!"


def main() -> None:
    show.process_start("Encrypt")

    if not PLAINTEXT:
        raise ValueError("plaintext cannot be empty")

    alice = setup.create_alice()

    alice_wallet, cleanup = alice.create_wallet()
    try:
        show.step("Alice", "Encrypting")

        args = {
            "encryptionArgs": {
                "protocolID": {"protocol": PROTOCOL_ID},
                "keyID": KEY_ID,
                "counterparty": {},
            },
            "plaintext": PLAINTEXT.encode("utf-8"),
        }
        show.info("EncryptArgs", args)
        show.separator()

        # encrypted, err := aliceWallet.Encrypt(ctx, args, originator)
        encrypted = alice_wallet.encrypt(args, ORIGINATOR)

        # Go SDK Encrypt returns []byte directly, but Python SDK might follow TS structure.
        # Checking parity: TS returns EncryptResult { ciphertext: Uint8Array, ... } or just ciphertext?
        # Let's assume it returns dict similar to Decrypt or just bytes.
        # Based on bsv_wallet_toolbox/wallet.py: return self.wallet_permissions_manager.encrypt(args, originator)
        # which likely returns the result structure.
        
        show.info("Encrypted", encrypted)
        show.process_complete("Encrypt")

    finally:
        cleanup()


if __name__ == "__main__":
    main()

