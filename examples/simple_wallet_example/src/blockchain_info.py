"""Demo helpers for blockchain-related methods."""

from bsv_wallet_toolbox import Wallet


def demo_get_height(wallet: Wallet) -> None:
    """Fetch the current chain height (requires Services)."""
    print("\n📊 Fetching current block height...\n")

    try:
        result = wallet.get_height({})
        print(f"✅ Height: {result['height']}")
    except Exception as err:
        print(f"⚠️  Failed to fetch height: {err}")
        print("   (This is expected until Services are configured.)")


def demo_get_header_for_height(wallet: Wallet) -> None:
    """Retrieve a block header for a user-specified height."""
    print("\n📊 Fetching block header\n")

    height_input = input("Block height [Enter=1]: ").strip() or "1"

    try:
        height = int(height_input)
        result = wallet.get_header_for_height({"height": height})

        print(f"\n✅ Header for height {height}")
        print(f"   Hash        : {result.get('hash', 'N/A')}")
        print(f"   Version     : {result.get('version', 'N/A')}")
        print(f"   Prev hash   : {result.get('previousHash', 'N/A')}")
        print(f"   Merkle root : {result.get('merkleRoot', 'N/A')}")
        print(f"   Timestamp   : {result.get('time', 'N/A')}")
        print(f"   Bits        : {result.get('bits', 'N/A')}")
        print(f"   Nonce       : {result.get('nonce', 'N/A')}")

    except ValueError:
        print("❌ Invalid height.")
    except Exception as err:
        print(f"⚠️  Failed to fetch header: {err}")
        print("   (Requires Services to be configured.)")


def demo_wait_for_authentication(wallet: Wallet) -> None:
    """Call wait_for_authentication (instant for the base wallet)."""
    print("\n⏳ Waiting for authentication...\n")

    try:
        result = wallet.wait_for_authentication({})
        print(f"✅ Authenticated: {result['authenticated']}")
        print("   (Base wallet resolves immediately.)")
    except Exception as err:
        print(f"❌ Failed to wait for authentication: {err}")
