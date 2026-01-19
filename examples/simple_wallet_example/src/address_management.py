"""Utilities for showing wallet address and balance."""

from bsv.constants import Network
from bsv.keys import PublicKey

from bsv_wallet_toolbox import Wallet


def get_wallet_address(wallet: Wallet, network: str) -> str:
    """Return the receive address for the current wallet."""
    result = wallet.get_public_key(
        {
            "identityKey": True,
            "reason": "Display receive address",
        }
    )

    public_key = PublicKey(result["publicKey"])
    network_enum = Network.TESTNET if network == "test" else Network.MAINNET
    return public_key.address(network=network_enum)


def display_wallet_info(wallet: Wallet, network: str) -> None:
    """Print receive address, balance, and explorer links."""
    print("\n" + "=" * 70)
    print("💰 Wallet information")
    print("=" * 70)
    print()

    try:
        address = get_wallet_address(wallet, network)

        print("📍 Receive address:")
        print(f"   {address}")
        print()

        try:
            balance_result = wallet.balance()
            balance_sats = balance_result.get("total", 0)
            balance_bsv = balance_sats / 100_000_000
            print("💰 Current balance:")
            print(f"   {balance_sats:,} sats ({balance_bsv:.8f} BSV)")
            print()
        except KeyError as err:
            print(f"⚠️  Failed to fetch balance: {err}")
            print("   The storage layer has not created a user record yet.")
            print("   Run any operation (e.g. menu 5: Get public key, or menu 13: Create action)")
            print("   once so the user is initialized, then retry this menu.")
            print()
        except Exception as err:
            print(f"⚠️  Failed to fetch balance: {err}")
            print()

        amount = 0.001  # default request amount
        uri = f"bitcoin:{address}?amount={amount}"
        print("💳 Payment URI (0.001 BSV):")
        print(f"   {uri}")
        print()

        print("=" * 70)
        print("📋 Explorer")
        print("=" * 70)
        print()

        if network == "test":
            print("🔍 Testnet explorer:")
            print(f"   https://test.whatsonchain.com/address/{address}")
            print()
            print("💡 Need testnet coins? Use this faucet:")
            print("   https://scrypt.io/faucet/")
        else:
            print("🔍 Mainnet explorer:")
            print(f"   https://whatsonchain.com/address/{address}")
            print()
            print("⚠️  You are dealing with real BSV funds.")

        print()
        print("=" * 70)

    except Exception as err:
        print(f"❌ Unexpected error while showing wallet info: {err}")
        import traceback

        traceback.print_exc()
