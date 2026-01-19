"""Identity discovery demos (by key / by attributes)."""

from bsv_wallet_toolbox import Wallet


def demo_discover_by_identity_key(wallet: Wallet) -> None:
    """Discover certificates by identity key."""
    print("\n🔍 Discover by identity key\n")

    use_own = input("Use your own identity key? (y/n) [Enter=y]: ").strip().lower()

    try:
        if use_own != "n":
            my_key = wallet.get_public_key({"identityKey": True, "reason": "Fetch my identity key"})
            identity_key = my_key["publicKey"]
            print(f"🔑 Using own identity key: {identity_key[:32]}...")
        else:
            identity_key = input("Enter identity key to search for: ").strip()

        print("\n🔍 Searching...\n")

        results = wallet.discover_by_identity_key(
            {"identityKey": identity_key, "limit": 10, "offset": 0, "seekPermission": True}
        )

        print(f"✅ Matches: {len(results['certificates'])}\n")

        for i, cert in enumerate(results["certificates"], 1):
            print(f"   {i}. {cert['type']}")
            if "fields" in cert:
                print(f"      Fields   : {list(cert['fields'].keys())}")
            if "certifier" in cert:
                print(f"      Certifier: {cert['certifier'][:32]}...")
            print()

    except Exception as err:
        print(f"❌ Discovery error: {err}")


def demo_discover_by_attributes(wallet: Wallet) -> None:
    """Discover certificates via attribute filters."""
    print("\n🔍 Discover by attributes\n")
    print("Choose a filter pattern:")
    print("  1. Country (e.g., country='Japan')")
    print("  2. Minimum age (e.g., age >= 20)")
    print("  3. Custom (basic placeholder)")

    choice = input("\nSelect (1-3) [Enter=1]: ").strip() or "1"

    try:
        if choice == "1":
            country = input("Country [Enter=Japan]: ").strip() or "Japan"
            attributes = {"country": country}
            print(f"\n🔍 Searching for country = {country}...")

        elif choice == "2":
            min_age = input("Minimum age [Enter=20]: ").strip() or "20"
            attributes = {"age": {"$gte": int(min_age)}}
            print(f"\n🔍 Searching for age >= {min_age}...")

        else:
            print("Custom filter placeholder selected; defaulting to verified=true.")
            attributes = {"verified": True}
            print("\n🔍 Searching for verified = true...")

        results = wallet.discover_by_attributes(
            {"attributes": attributes, "limit": 10, "offset": 0, "seekPermission": True}
        )

        print(f"\n✅ Matches: {len(results['certificates'])}\n")

        for i, cert in enumerate(results["certificates"], 1):
            print(f"   {i}. {cert['type']}")
            if "fields" in cert:
                for key, value in cert["fields"].items():
                    print(f"      {key}: {value}")
            print()

    except Exception as err:
        print(f"❌ Discovery error: {err}")
