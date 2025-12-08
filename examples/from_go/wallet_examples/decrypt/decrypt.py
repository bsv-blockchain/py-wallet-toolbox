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

# ciphertext is the encrypted version of the plaintext (from encrypt example output)
CIPHERTEXT = bytes([66, 73, 69, 49, 2, 74, 179, 47, 48, 122, 160, 174, 206, 114, 76, 17, 153, 39, 180, 70, 231, 14, 47, 6, 119, 34, 143, 253, 239, 22, 79, 101, 220, 126, 134, 248, 101, 174, 208, 103, 180, 91, 133, 31, 8, 182, 187, 185, 174, 229, 169, 150, 71, 39, 16, 58, 170, 59, 135, 243, 148, 119, 237, 142, 225, 8, 86, 178, 201, 39, 155, 44, 88, 51, 154, 245, 143, 208, 132, 100, 10, 130, 141, 44, 195])


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

