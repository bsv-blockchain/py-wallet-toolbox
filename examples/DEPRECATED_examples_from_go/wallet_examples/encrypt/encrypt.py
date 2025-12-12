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

        # Python SDK expects flat structure (not wrapped in encryptionArgs)
        # protocolID format: [securityLevel, protocolName] as list/tuple
        args = {
            "plaintext": list(PLAINTEXT.encode("utf-8")),
            "protocolID": [0, PROTOCOL_ID],
                "keyID": KEY_ID,
            "counterparty": "self",
        }
        show.info("EncryptArgs", args)
        show.separator()

        encrypted = alice_wallet.encrypt(args)

        # Python SDK returns dict with 'ciphertext' key
        show.info("Encrypted", encrypted)
        show.process_complete("Encrypt")

    finally:
        cleanup()


if __name__ == "__main__":
    main()

