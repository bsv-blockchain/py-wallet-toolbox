import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

"""Internalize Wallet Payment Example.

This example demonstrates how to internalize a transaction into Alice's wallet.
AtomicBeefHex, IdentityKey, Prefix, and Suffix are required to internalize a transaction.
"""

import base64
from bsv.keys import PublicKey
from internal import setup, show

# AtomicBeefHex is the transaction data in atomic beef hex format
ATOMIC_BEEF_HEX = ""  # example: 01010101c8c06c5fac63510b2b02ccab974a6ef0b0a4910dd8e881c06964f2b52d7ff4150200beef...

# Originator specifies the originator domain or FQDN used to identify the source of the action listing request.
# NOTE: Replace "example.com" with the actual originator domain or FQDN in real usage.
ORIGINATOR = "example.com"

# Prefix is the derivation prefix for the payment remittance
PREFIX = ""  # example: SfKxPIJNgdI=

# Suffix is the derivation suffix for the payment remittance
SUFFIX = ""  # example: NaGLC6fMH50=

# IdentityKey is the sender identity key for the payment remittance
IDENTITY_KEY = ""  # example: 0231c72ef229534d40d08af5b9a586b619d0b2ee2ace2874339c9cbcc4a79281c0


def main() -> None:
    show.process_start("Internalize Wallet Payment")

    if not PREFIX or not SUFFIX or not ATOMIC_BEEF_HEX or not IDENTITY_KEY:
        raise ValueError("Prefix, Suffix, AtomicBeefHex, and IdentityKey are required")

    show.step("Alice", "Creating wallet and setting up environment")
    alice = setup.create_alice()

    alice_wallet, cleanup = alice.create_wallet()
    try:
        try:
            derivation_prefix = base64.b64decode(PREFIX).decode("utf-8") # Go decodes to bytes, Python string in JSON often expects str or bytes
            # Wait, SDK expects derivationPrefix as string usually (base64 encoded? or raw bytes?)
            # Let's check TS/Python SDK. DTO usually carries strings.
            # validation.py: derivationPrefix must be base64 string.
            # So we should pass the base64 string directly?
            # Go example: derivationPrefix, err := base64.StdEncoding.DecodeString(Prefix)
            # SDK InternalizeActionArgs struct has DerivationPrefix []byte
            # Python SDK InternalizeActionArgs validation checks for base64 string.
            # So we keep it as base64 string.
            pass
        except Exception as e:
            raise ValueError(f"failed to decode derivation prefix: {e}")

        # senderIdentityKey, err := ec.PublicKeyFromString(IdentityKey)
        # Python SDK might expect hex string or PublicKey object?
        # validation.py doesn't strictly check type of senderIdentityKey deep inside yet?
        # Let's assume hex string is fine if validation allows, or convert.
        # TS parity uses IdentityKey string usually.
        
        decoded_beef = bytes.fromhex(ATOMIC_BEEF_HEX)

        # Create internalization arguments with payment remittance configuration
        internalize_args = {
            "tx": decoded_beef,
            "outputs": [
                {
                    "outputIndex": 0,
                    "protocol": "wallet payment",
                    "paymentRemittance": {
                        "derivationPrefix": PREFIX,
                        "derivationSuffix": SUFFIX,
                        "senderIdentityKey": IDENTITY_KEY,
                    },
                },
            ],
            "description": "internalize transaction",
        }

        show.step("Alice", "Internalizing transaction")

        # Execute the internalization to add external transaction to wallet history
        result = alice_wallet.internalize_action(internalize_args, ORIGINATOR)

        show.wallet_success("InternalizeAction", internalize_args, result)
        show.success("Transaction internalized successfully")
        show.process_complete("Internalize Wallet Payment")

    finally:
        cleanup()


if __name__ == "__main__":
    main()

