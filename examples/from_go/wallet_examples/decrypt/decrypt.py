import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

"""Decrypt Example.

This example shows how to decrypt a message using the wallet.
It creates a new wallet for Alice, decrypts a message, and prints the decrypted message.


"""

from internal import setup, show

# keyID is the key ID for the decryption key.
KEY_ID = "key-id"

# protocolID is the protocol ID for the decryption.
PROTOCOL_ID = "encryption"

# ciphertext is the encrypted version of the plaintext
CIPHERTEXT = b""  # example: bytes.fromhex("dc7788cb11a54cce4be490e1eb2fc1da9ba4b3e92d70a0ee21156eafb0a1589d25b5e4b7c26ed8546de9dc822bfcaffe972f3a3ef68b3e752cd5bf2d82")


def main() -> None:
    show.process_start("Decrypt")

    # Validate that ciphertext is not empty
    if len(CIPHERTEXT) == 0:
        raise ValueError("ciphertext cannot be empty")

    alice = setup.create_alice()

    alice_wallet, cleanup = alice.create_wallet()
    try:
        show.step("Alice", "Decrypting")

        # Python SDK expects flat structure (not wrapped in encryptionArgs)
        # protocolID format: [securityLevel, protocolName] as list/tuple
        args = {
            "ciphertext": list(CIPHERTEXT),
            "protocolID": [0, PROTOCOL_ID],
            "keyID": KEY_ID,
            "counterparty": "self",
        }
        show.info("DecryptArgs", args)
        show.separator()

        decrypted = alice_wallet.decrypt(args)

        # Python SDK returns dict with 'plaintext' as list of bytes
        plaintext_bytes = bytes(decrypted.get("plaintext", []))
        show.info("Decrypted", plaintext_bytes.decode("utf-8"))
        show.process_complete("Decrypt")

    finally:
        cleanup()


if __name__ == "__main__":
    main()

