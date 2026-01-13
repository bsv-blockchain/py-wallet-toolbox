#!/usr/bin/env python3
"""BSV Wallet Toolbox - BRC-100 Interactive Demo."""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from bsv_wallet_toolbox import Wallet
from bsv_wallet_toolbox.services import Services, create_default_options
from bsv_wallet_toolbox.services.wallet_services_options import WalletServicesOptions
from src import (
    demo_abort_action,
    # certificates
    demo_acquire_certificate,
    # actions
    demo_create_action,
    # crypto utilities
    demo_create_hmac,
    demo_discover_by_attributes,
    # identity discovery
    demo_discover_by_identity_key,
    demo_encrypt_decrypt,
    demo_get_header_for_height,
    # blockchain info
    demo_get_height,
    # key management
    demo_get_public_key,
    # transactions
    demo_internalize_action,
    demo_list_actions,
    demo_list_certificates,
    # outputs
    demo_list_outputs,
    demo_relinquish_certificate,
    demo_relinquish_output,
    # key linkage
    demo_reveal_counterparty_key_linkage,
    demo_reveal_specific_key_linkage,
    demo_sign_data,
    demo_verify_hmac,
    demo_verify_signature,
    demo_wait_for_authentication,
    # wallet info
    display_wallet_info,
    # configuration helpers
    get_key_deriver,
    get_network,
    get_storage_provider,
    print_network_info,
)


class WalletDemo:
    """Main driver that wires every demo menu together."""

    def __init__(self) -> None:
        """Prepare shared dependencies."""
        load_dotenv(dotenv_path=Path(__file__).parent / ".env")
        self.wallet: Wallet | None = None
        self.network = get_network()
        self.key_deriver = get_key_deriver()
        self.storage_provider = get_storage_provider(self.network)

    def init_wallet(self) -> None:
        """Instantiate Wallet once and show the basics."""
        if self.wallet is not None:
            print("\n✅ Wallet already initialized.")
            return

        print("\n📝 Initializing wallet...")
        print_network_info(self.network)
        print()

        try:
            services = self._build_services()
            self.wallet = Wallet(
                chain=self.network,
                services=services,
                key_deriver=self.key_deriver,
                storage_provider=self.storage_provider,
            )
            print("✅ Wallet initialized.")
            print()

            auth = self.wallet.is_authenticated({})
            network_info = self.wallet.get_network({})
            version = self.wallet.get_version({})

            print(f"   Authenticated : {auth['authenticated']}")
            print(f"   Network       : {network_info['network']}")
            print(f"   Wallet version: {version['version']}")

        except Exception as err:
            print(f"❌ Failed to initialize wallet: {err}")
            self.wallet = None

    def _build_services(self) -> Services:
        """Create a Services instance configured to prioritize TAAL ARC."""
        options: WalletServicesOptions = create_default_options(self.network)

        # Prefer TAAL ARC, avoid Bitails / GorillaPool unless explicitly configured
        options["arcApiKey"] = os.getenv("TAAL_ARC_API_KEY") or options.get("arcApiKey")
        options["arcHeaders"] = options.get("arcHeaders")
        options["bitailsApiKey"] = None
        options["arcGorillaPoolUrl"] = None
        options["arcGorillaPoolApiKey"] = None
        options["arcGorillaPoolHeaders"] = None

        return Services(options)

    def show_basic_info(self) -> None:
        """Display core metadata (auth/network/version)."""
        if not self.wallet:
            print("\n❌ Wallet is not initialized.")
            return

        print("\n" + "=" * 70)
        print("ℹ️  Wallet basics")
        print("=" * 70)
        print()

        auth = self.wallet.is_authenticated({})
        print(f"✅ Authenticated: {auth['authenticated']}")

        network = self.wallet.get_network({})
        print(f"🌐 Network      : {network['network']}")

        version = self.wallet.get_version({})
        print(f"📦 Version      : {version['version']}")

    def show_menu(self) -> None:
        """Render the interactive menu."""
        print("\n" + "=" * 70)
        print("🎮 BSV Wallet Toolbox - BRC-100 Demo")
        print("=" * 70)
        print()
        print("[Basics]")
        print("  1. Initialize wallet (setup helper)")
        print("  2. Show wallet basics -> isAuthenticated / getNetwork / getVersion")
        print("  3. Wait for authentication -> waitForAuthentication")
        print()
        print("[Wallet info]")
        print("  4. Show receive address & balance -> getPublicKey (+ balance helper)")
        print()
        print("[Keys & signatures]")
        print("  5. Get public key -> getPublicKey")
        print("  6. Sign data -> createSignature")
        print("  7. Verify signature -> verifySignature")
        print("  8. Create HMAC -> createHmac")
        print("  9. Verify HMAC -> verifyHmac")
        print(" 10. Encrypt / decrypt data -> encrypt / decrypt")
        print(" 11. Reveal counterparty key linkage -> revealCounterpartyKeyLinkage")
        print(" 12. Reveal specific key linkage -> revealSpecificKeyLinkage")
        print()
        print("[Actions]")
        print(" 13. Create action -> createAction (+ signAction)")
        print(" 14. -- signAction (handled inside option 13)")
        print(" 15. List actions -> listActions")
        print(" 16. Abort action -> abortAction")
        print()
        print("[Outputs]")
        print(" 17. List outputs -> listOutputs")
        print(" 18. Relinquish output -> relinquishOutput")
        print()
        print("[Certificates]")
        print(" 19. Acquire certificate -> acquireCertificate (+ proveCertificate)")
        print(" 20. List certificates -> listCertificates")
        print(" 21. Relinquish certificate -> relinquishCertificate")
        print(" 22. -- proveCertificate (handled inside option 19)")
        print()
        print("[Identity discovery]")
        print(" 23. Discover by identity key -> discoverByIdentityKey")
        print(" 24. Discover by attributes -> discoverByAttributes")
        print()
        print("[Transactions]")
        print(" 25. Internalize external transaction -> internalizeAction")
        print()
        print("[Blockchain info]")
        print(" 26. Get block height -> getHeight")
        print(" 27. Get block header for height -> getHeaderForHeight")
        print()
        print("  0. Exit demo")
        print("=" * 70)
        print("📊 Implemented: 28 / 28 BRC-100 methods")
        print("=" * 70)

    def run(self) -> None:
        """Entry point for the CLI loop."""
        print("\n" + "=" * 70)
        print("🎉 Welcome to the BRC-100 Wallet Demo")
        print("=" * 70)
        print()
        print("All 28 BRC-100 methods are wired into this menu.")
        print("Select any option to trigger the corresponding call.")
        print()

        if self.network == "main":
            print("⚠️  MAINNET MODE: you are handling real BSV. Triple-check inputs.")
        else:
            print("💡 TESTNET MODE: safe sandbox for experimentation.")

        while True:
            self.show_menu()
            choice = input("\nSelect a menu option (0-27): ").strip()

            if choice == "0":
                print("\n" + "=" * 70)
                print("👋 Exiting demo. Thanks for trying the toolbox!")
                print("=" * 70)
                if self.network == "main":
                    print("⚠️  Reminder: secure your mnemonic before closing the terminal.")
                break

            elif choice == "1":
                self.init_wallet()

            elif choice == "2":
                self.show_basic_info()

            elif choice == "3":
                if not self.wallet:
                    print("\n❌ Wallet is not initialized.")
                else:
                    demo_wait_for_authentication(self.wallet)

            elif choice == "4":
                if not self.wallet:
                    print("\n❌ Wallet is not initialized.")
                else:
                    display_wallet_info(self.wallet, self.network)

            elif choice == "5":
                if not self.wallet:
                    print("\n❌ Wallet is not initialized.")
                else:
                    demo_get_public_key(self.wallet)

            elif choice == "6":
                if not self.wallet:
                    print("\n❌ Wallet is not initialized.")
                else:
                    demo_sign_data(self.wallet)

            elif choice == "7":
                if not self.wallet:
                    print("\n❌ Wallet is not initialized.")
                else:
                    demo_verify_signature(self.wallet)

            elif choice == "8":
                if not self.wallet:
                    print("\n❌ Wallet is not initialized.")
                else:
                    demo_create_hmac(self.wallet)

            elif choice == "9":
                if not self.wallet:
                    print("\n❌ Wallet is not initialized.")
                else:
                    demo_verify_hmac(self.wallet)

            elif choice == "10":
                if not self.wallet:
                    print("\n❌ Wallet is not initialized.")
                else:
                    demo_encrypt_decrypt(self.wallet)

            elif choice == "11":
                if not self.wallet:
                    print("\n❌ Wallet is not initialized.")
                else:
                    demo_reveal_counterparty_key_linkage(self.wallet)

            elif choice == "12":
                if not self.wallet:
                    print("\n❌ Wallet is not initialized.")
                else:
                    demo_reveal_specific_key_linkage(self.wallet)

            elif choice == "13":
                if not self.wallet:
                    print("\n❌ Wallet is not initialized.")
                else:
                    demo_create_action(self.wallet)

            elif choice == "14":
                print("\n💡 signAction is triggered inside option 13 (Create action).")

            elif choice == "15":
                if not self.wallet:
                    print("\n❌ Wallet is not initialized.")
                else:
                    demo_list_actions(self.wallet)

            elif choice == "16":
                if not self.wallet:
                    print("\n❌ Wallet is not initialized.")
                else:
                    demo_abort_action(self.wallet)

            elif choice == "17":
                if not self.wallet:
                    print("\n❌ Wallet is not initialized.")
                else:
                    demo_list_outputs(self.wallet)

            elif choice == "18":
                if not self.wallet:
                    print("\n❌ Wallet is not initialized.")
                else:
                    demo_relinquish_output(self.wallet)

            elif choice == "19":
                if not self.wallet:
                    print("\n❌ Wallet is not initialized.")
                else:
                    demo_acquire_certificate(self.wallet)

            elif choice == "20":
                if not self.wallet:
                    print("\n❌ Wallet is not initialized.")
                else:
                    demo_list_certificates(self.wallet)

            elif choice == "21":
                if not self.wallet:
                    print("\n❌ Wallet is not initialized.")
                else:
                    demo_relinquish_certificate(self.wallet)

            elif choice == "22":
                print("\n💡 proveCertificate is executed as part of option 19.")

            elif choice == "23":
                if not self.wallet:
                    print("\n❌ Wallet is not initialized.")
                else:
                    demo_discover_by_identity_key(self.wallet)

            elif choice == "24":
                if not self.wallet:
                    print("\n❌ Wallet is not initialized.")
                else:
                    demo_discover_by_attributes(self.wallet)

            elif choice == "25":
                if not self.wallet:
                    print("\n❌ Wallet is not initialized.")
                else:
                    demo_internalize_action(self.wallet, self.network)

            elif choice == "26":
                if not self.wallet:
                    print("\n❌ Wallet is not initialized.")
                else:
                    demo_get_height(self.wallet)

            elif choice == "27":
                if not self.wallet:
                    print("\n❌ Wallet is not initialized.")
                else:
                    demo_get_header_for_height(self.wallet)

            else:
                print("\n❌ Invalid choice. Please type a number between 0 and 27.")

            input("\nPress Enter to continue...")


def main() -> None:
    """Bootstraps the interactive CLI."""
    try:
        demo = WalletDemo()
        demo.run()
    except KeyboardInterrupt:
        print("\n\n👋 Interrupted. Exiting demo.")
        sys.exit(0)
    except Exception as err:
        print(f"\n❌ Unexpected error: {err}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
