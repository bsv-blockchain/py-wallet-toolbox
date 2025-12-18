import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

"""Show Address for Faucet Transaction Example.

This script prints a receive address that can be funded from a testnet faucet.
The resulting transaction can then be internalized into the wallet database.

Uses BRC-29 derived address so that the wallet can properly sign when spending.
"""

from bsv.constants import Network
from bsv.keys import PrivateKey
from bsv.wallet import KeyDeriver
from bsv.wallet.key_deriver import Protocol, Counterparty, CounterpartyType

from internal import setup, show

# Fixed derivation values for faucet address (must match internalize_tx_from_faucet.py)
FAUCET_DERIVATION_PREFIX = "faucet-prefix-01"
FAUCET_DERIVATION_SUFFIX = "faucet-suffix-01"

# AnyoneKey - matches Go SDK's sdk.AnyoneKey() = PrivateKey(1).PublicKey()
ANYONE_KEY = PrivateKey(1).public_key()


def main() -> None:
    # Create Alice's wallet instance with deterministic keys
    alice = setup.create_alice()
    
    # Use KeyDeriver to generate BRC-29 derived address
    key_deriver = KeyDeriver(alice.private_key)
    
    # Derive key using BRC-29 protocol
    # Protocol: security_level=2, protocol="3241645161d8" is standard for BRC-29 payment
    protocol = Protocol(security_level=2, protocol="3241645161d8")
    
    # Derive the private key (same derivation as internalize uses)
    # Use AnyoneKey as counterparty with CounterpartyType.OTHER (matches Go SDK behavior)
    counterparty = Counterparty(type=CounterpartyType.OTHER, counterparty=ANYONE_KEY)
    derived_privkey = key_deriver.derive_private_key(
        protocol=protocol,
        key_id=f"{FAUCET_DERIVATION_PREFIX} {FAUCET_DERIVATION_SUFFIX}",
        counterparty=counterparty
    )
    derived_pubkey = derived_privkey.public_key()
    
    # Generate P2PKH address from derived public key
    network = Network.TESTNET if alice.environment.bsv_network == "testnet" else Network.MAINNET
    address = derived_pubkey.address(network=network)
    
    # Show instructions
    show.header("FAUCET ADDRESS (BRC-29 Derived)")
    print(f"\n💡 NOTICE: You need to fund this address from a testnet faucet")
    print(f"\n📧 ADDRESS:")
    print(f"   {address}")
    print(f"\n🔑 DERIVATION INFO (for internalization):")
    print(f"   Prefix: {FAUCET_DERIVATION_PREFIX}")
    print(f"   Suffix: {FAUCET_DERIVATION_SUFFIX}")
    print("")
    print("Available Testnet Faucets:")
    print("• https://scrypt.io/faucet")
    print("• https://witnessonchain.com/faucet/tbsv")
    print("")
    print("⚠️  WARNING: Make sure to use TESTNET faucets only!")


if __name__ == "__main__":
    main()

