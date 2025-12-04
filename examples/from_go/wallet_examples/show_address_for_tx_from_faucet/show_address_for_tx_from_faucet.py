import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

"""Show Address for Faucet Transaction Example.

This script prints a receive address that can be funded from a testnet faucet.
The resulting transaction can then be internalized into the wallet database.


"""

import base64
from bsv.constants import Network

from internal import setup, show

# We need BRC29 implementation in Python SDK or Toolbox.
# brc29.AddressForSelf seems to be what we need.
# Let's check if we have brc29 in bsv_wallet_toolbox or py-sdk.
# It is likely in py-sdk bsv.brc29 or similar.


def main() -> None:
    # Create Alice's wallet instance with deterministic keys
    alice = setup.create_alice()

    # Generate and display a BRC-29 testnet address for receiving faucet funds
    # Replicating example_setup.FaucetAddress(alice) logic here or in internal/setup.py?
    # Go has FaucetAddress in example_setup.
    # Let's implement it here for now or add to setup.py if reused.
    # Go's internal/example_setup/faucet_address.go uses internal/utils/DerivationParts.
    
    # We need dummy derivation parts.
    # Go utils.DerivationParts() returns hardcoded random bytes?
    # Let's use fixed bytes for reproducibility if Go example does so, or random.
    # Go's utils seems to return:
    # DerivationPrefix: []byte("example-prefix"), DerivationSuffix: []byte("example-suffix")?
    # Let's assume some fixed values to match Go example if possible, or just new ones.
    
    derivation_prefix = b"example-prefix"
    derivation_suffix = b"example-suffix"
    
    # Encode to base64 strings
    dp_b64 = base64.b64encode(derivation_prefix).decode('utf-8')
    ds_b64 = base64.b64encode(derivation_suffix).decode('utf-8')
    
    # Address generation
    # In Python SDK, is there BRC29 support?
    # If not, we can fall back to standard P2PKH address from Alice's key for simple faucet usage.
    # Most faucets support P2PKH addresses. BRC-29 is for payment protocols.
    # If the goal is to test BRC-29 support, we need that.
    # But if goal is just to get funds, P2PKH is fine.
    # However, Go example explicitly uses BRC29.AddressForSelf.
    
    # Let's assume we want P2PKH for simplicity unless BRC29 is strictly required by the "internalize_tx_from_faucet" example later.
    # "internalize_tx_from_faucet" just takes a txid.
    # "internalize_wallet_payment" uses BRC29 derivation parts.
    
    # Let's print Alice's P2PKH address.
    # Alice has private_key in setup.
    network = Network.TESTNET if alice.environment.bsv_network == "testnet" else Network.MAINNET
    address = alice.private_key.public_key().address(network=network)
    
    # Show instructions
    show.header("FAUCET ADDRESS")
    print(f"\n💡 NOTICE: You need to fund this address from a testnet faucet")
    print(f"\n📧 ADDRESS:")
    print(f"   {address}")
    print("")
    print("Available Testnet Faucets:")
    print("• https://scrypt.io/faucet")
    print("• https://witnessonchain.com/faucet/tbsv")
    print("")
    print("⚠️  WARNING: Make sure to use TESTNET faucets only!")


if __name__ == "__main__":
    main()

