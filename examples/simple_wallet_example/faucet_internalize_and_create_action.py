#!/usr/bin/env python3
"""Simple demo that internalizes faucet receipts and uses them in create_action.

This is the "Step 2" script in a two-step process.

- Step 1: Initialize wallet with test_all_28_methods.py,
  send a small amount of BSV from Faucet to the "receiving address" displayed there
- Step 2: Run this script and enter the txid confirmed in block explorer:
    1) internalize that transaction into wallet (basket registration)
    2) execute one simple create_action with OP_RETURN using those funds

No advanced options or custom BRC-29 settings - only handles the minimal flow of
"Faucet receipt → internalizeAction → createAction".
"""

from __future__ import annotations

import base64
import os
from pathlib import Path

from bsv.keys import PrivateKey
from dotenv import load_dotenv
from src.config import (
    bypass_wallet_infra_auth,
    get_key_deriver,
    get_network,
    get_remote_storage_client,
    get_remote_storage_url,
    get_storage_provider,
    get_wallet_infra_client,
    get_wallet_infra_url,
    use_remote_storage,
    use_wallet_infra,
)
from src.transaction_management import _build_atomic_beef_for_txid

from bsv_wallet_toolbox import Wallet
from bsv_wallet_toolbox.errors import ReviewActionsError
from bsv_wallet_toolbox.services import Services, create_default_options

# BRC-29 derivation info for faucet (same values as test_all_28_methods.py)
FAUCET_DERIVATION_PREFIX = "faucet-prefix-01"
FAUCET_DERIVATION_SUFFIX = "faucet-suffix-01"
DEFAULT_OUTPUT_INDEX = 0


def main() -> None:
    # Change to examples directory
    os.chdir(Path(__file__).parent)
    load_dotenv()

    print("=" * 70)
    print("💧 Faucet Receipt → internalizeAction → create_action Demo")
    print("=" * 70)
    print(
        "\nPrerequisites:\n"
        "  1. First run test_all_28_methods.py and send a small amount of BSV\n"
        "     from a Faucet to the receiving address displayed.\n"
        "  2. From a block explorer (WhatsOnChain, etc.), note the transaction ID (txid).\n"
    )

    # ---- Wallet initialization (same storage switching as test_all_28_methods.py) ----
    chain = get_network()
    key_deriver = get_key_deriver()

    # Services injects TAAL ARC API key from environment variables in addition to defaults.
    # This makes TAAL ARC (testnet) the preferred route for broadcasting via post_beef.
    options = create_default_options(chain)
    options["arcApiKey"] = os.getenv("TAAL_ARC_API_KEY") or options.get("arcApiKey")
    # Disable Bitails / GorillaPool for this simple demo
    options["bitailsApiKey"] = None
    options["arcGorillaPoolUrl"] = None
    options["arcGorillaPoolApiKey"] = None
    options["arcGorillaPoolHeaders"] = None

    services = Services(options)

    # Storage mode selection (priority: wallet-infra > remote > local)
    wallet_infra_mode = use_wallet_infra()
    bypass_auth = bypass_wallet_infra_auth()
    remote_storage_mode = use_remote_storage()

    if wallet_infra_mode:
        print(f"\n🏗️  wallet-infra mode: {get_wallet_infra_url()}")
        print("⚠️  wallet-infra requires BRC-104 authentication")
        print("-" * 70)

        # First create wallet with local storage (for StorageClient authentication)
        local_storage = get_storage_provider(chain)
        wallet = Wallet(
            chain=chain,
            services=services,
            key_deriver=key_deriver,
            storage_provider=local_storage,
        )

        infra_client = get_wallet_infra_client(wallet)

        if bypass_auth:
            print("\n🔄 Bypassing wallet-infra authentication for direct connection...")
            print("   Note: This is for testing purposes only. Do not use in production.")

            print("\n🔄 Creating wallet instance using wallet-infra storage...")
            wallet = Wallet(
                chain=chain,
                services=services,
                key_deriver=key_deriver,
                storage_provider=infra_client,
            )
            print("✅ wallet-infra wallet instance created successfully (auth bypass)!")
        else:
            try:
                print("\n🔄 Connecting to wallet-infra...")
                infra_settings = infra_client.make_available()
                print("✅ wallet-infra connection successful!")
                print(f"   Storage Identity Key: {infra_settings.get('storageIdentityKey', 'N/A')}")
                print(f"   Chain: {infra_settings.get('chain', 'N/A')}")

                print("\n🔄 Creating wallet instance using wallet-infra storage...")
                wallet = Wallet(
                    chain=chain,
                    services=services,
                    key_deriver=key_deriver,
                    storage_provider=infra_client,
                )
                print("✅ wallet-infra wallet instance created successfully!")
            except Exception as err:
                print(f"⚠️  wallet-infra authentication failed: {err}")
                print("   This is a known issue with Python SDK. Continuing with local storage...")
                print("   Note: wallet-infra authentication is not currently supported in Python.")
                print("   For testing, you can set BYPASS_WALLET_INFRA_AUTH=true to bypass authentication.")
                wallet_infra_mode = False

    if not wallet_infra_mode and remote_storage_mode:
        print(f"\n🌐 Remote storage mode: {get_remote_storage_url(chain)}")
        print("⚠️  Remote storage requires BRC-104 authentication")
        print("-" * 70)

        # First create wallet with local storage (for StorageClient authentication)
        local_storage = get_storage_provider(chain)
        wallet = Wallet(
            chain=chain,
            services=services,
            key_deriver=key_deriver,
            storage_provider=local_storage,
        )

        remote_client = get_remote_storage_client(wallet, chain)

        try:
            print("\n🔄 Connecting to remote storage...")
            remote_settings = remote_client.make_available()
            print("✅ Remote storage connection successful!")
            print(f"   Storage Identity Key: {remote_settings.get('storageIdentityKey', 'N/A')}")
            print(f"   Chain: {remote_settings.get('chain', 'N/A')}")

            print("\n🔄 Creating wallet instance using remote storage...")
            wallet = Wallet(
                chain=chain,
                services=services,
                key_deriver=key_deriver,
                storage_provider=remote_client,
            )
            print("✅ Remote storage wallet instance created successfully!")
        except Exception as err:
            print(f"❌ Remote storage connection failed: {err}")
            print("   Continuing with local storage...")
            remote_storage_mode = False

    if not wallet_infra_mode and not remote_storage_mode:
        print("\n💾 Local storage mode")
        storage_provider = get_storage_provider(chain)
        # In local storage mode, also attach Services to StorageProvider so that
        # process_action → _share_reqs_with_world → services.post_beef(...) enables
        # network broadcasting.
        storage_provider.set_services(services)
        wallet = Wallet(
            chain=chain,
            services=services,
            key_deriver=key_deriver,
            storage_provider=storage_provider,
        )

    print(f"\n🟢 Network: {chain}")

    # ---- 1) Internalize transaction from Faucet ---------------------------
    txid = input(
        "\n🔎 Enter transaction ID (txid) to internalize\n"
        "    (Example: 64-character hex string. Leave empty to cancel)\n"
        "txid: "
    ).strip()

    if not txid:
        print("\n⏹ Processing cancelled as no txid was specified.")
        return

    if len(txid) != 64:
        print("\n❌ txid must be a 64-character hexadecimal string.")
        return

    try:
        int(txid, 16)
    except ValueError:
        print("\n❌ txid is not valid hexadecimal.")
        return

    # Input vout to internalize (0 if not specified)
    vout_raw = input("\n🔧 Enter output index to internalize (default 0)\n" "outputIndex: ").strip()
    if not vout_raw:
        output_index = DEFAULT_OUTPUT_INDEX
    else:
        try:
            output_index = int(vout_raw)
        except ValueError:
            print("\n❌ output index must be specified as an integer.")
            return
        if output_index < 0:
            print("\n❌ output index must be 0 or greater.")
            return

    try:
        atomic_beef = _build_atomic_beef_for_txid(chain, txid)
    except Exception as err:
        print(f"\n❌ Failed to retrieve Atomic BEEF: {err}")
        return

    # In faucet demo, internalize using BRC-29 "wallet payment" protocol
    # to make the UTXO usable as funding for create_action.
    #
    # - senderIdentityKey: Faucet side AnyoneKey (= PrivateKey(1).public_key())
    # - derivationPrefix / derivationSuffix: Fixed test strings (base64 encoded per BRC-29 spec)
    anyone_key = PrivateKey(1).public_key()
    print(f"anyone_key: {anyone_key.hex()}")
    derivation_prefix_b64 = base64.b64encode(FAUCET_DERIVATION_PREFIX.encode("utf-8")).decode("ascii")
    derivation_suffix_b64 = base64.b64encode(FAUCET_DERIVATION_SUFFIX.encode("utf-8")).decode("ascii")

    print("\n🚀 Executing internalizeAction...")
    internalize_args = {
        "tx": atomic_beef,
        "outputs": [
            {
                # By default, treat first output (0) as belonging to us.
                # Use the input outputIndex.
                "outputIndex": output_index,
                "protocol": "wallet payment",
                "paymentRemittance": {
                    "senderIdentityKey": anyone_key.hex(),
                    "derivationPrefix": derivation_prefix_b64,
                    "derivationSuffix": derivation_suffix_b64,
                },
            }
        ],
        "description": "Internalize faucet transaction into default basket",
        "labels": [f"txid:{txid}", "faucet"],
    }

    try:
        internalize_result = wallet.internalize_action(internalize_args)
    except Exception as err:
        print(f"\n❌ Error occurred in internalize_action: {err}")
        return

    print("\n✅ Transaction has been internalized.")
    # internalizeAction results are similar to BRC-100/TS implementation:
    #   - accepted: bool
    #   - isMerge: bool
    #   - txid: str
    #   - satoshis: int
    # etc., but does not have a "state" field.
    # Here we display a simple status based on the accepted flag.
    accepted = internalize_result.get("accepted")
    state_str = "accepted" if accepted is True else ("rejected" if accepted is False else "n/a")
    print(f"   state   : {state_str}")
    print(f"   txid    : {internalize_result.get('txid', 'n/a')}")
    print(f"   satoshis: {internalize_result.get('satoshis', 'n/a')}")

    # ---- 2) Execute create_action once using internalized funds ----------------
    answer = (
        input(
            "\n💡 Using the internalized funds, create a simple OP_RETURN action\n"
            "   (only 0 sat OP_RETURN output) once? [y/N]: "
        )
        .strip()
        .lower()
    )

    if not answer.startswith("y"):
        print("\n⏹ Exiting without executing create_action.")
        return

    print("\n🚀 Executing create_action (funded by faucet)...")
    try:
        action_result = wallet.create_action(
            {
                "description": "Faucet-funded demo action",
                "outputs": [
                    {
                        # OP_RETURN "faucet_demo"
                        "lockingScript": "006a0b6661756365745f64656d6f",
                        "satoshis": 0,
                        "outputDescription": "Faucet-funded demo OP_RETURN output",
                    }
                ],
                # By setting acceptDelayedBroadcast=False here,
                # storage.process_action(..., isDelayed=False) will attempt
                # immediate broadcast via _share_reqs_with_world(..., is_delayed=False).
                "options": {
                    "acceptDelayedBroadcast": False,
                },
            }
        )
    except ReviewActionsError as err:
        # "Requires review" cases such as broadcast failure.
        # Output raw TX hex as much as possible to facilitate manual debugging.
        print(f"\n❌ Error occurred in create_action: {err}")

        tx_bytes: bytes | None = None

        # 1) If exception object has tx (BRC-100 compatible byte array), prioritize it
        try:
            if getattr(err, "tx", None):
                tx_field = err.tx
                if isinstance(tx_field, (bytes, bytearray)) or isinstance(tx_field, list):
                    tx_bytes = bytes(tx_field)
        except Exception:
            tx_bytes = None

        # 2) If tx doesn't exist, try to get rawTx from txid via Services
        if tx_bytes is None and getattr(err, "txid", None):
            try:
                raw_hex = services.get_raw_tx(err.txid) or ""
                if isinstance(raw_hex, str) and raw_hex:
                    tx_bytes = bytes.fromhex(raw_hex)
            except Exception:
                pass

        # 3) If obtained, display HEX (can be used for manual posting to ARC, etc.)
        if tx_bytes:
            raw_tx_hex = tx_bytes.hex()
            if raw_tx_hex:
                print("\n🔎 Raw transaction hex (for debugging on error, manual broadcast possible):")
                print(raw_tx_hex)

        return
    except Exception as err:
        print(f"\n❌ Unexpected error occurred in create_action: {err}")
        return

    print("\n✅ create_action succeeded. Summary of results:")
    txid_created = action_result.get("txid") or action_result.get("txID") or "(txid not returned)"
    print(f"   txid : {txid_created}")

    # Display raw TX hex for manual broadcast (can be pasted into ARC, etc.)
    try:
        raw_tx_bytes = bytes(action_result.get("tx") or [])
        raw_tx_hex = raw_tx_bytes.hex()
        if raw_tx_hex:
            print("\n🔎 Raw transaction hex (for manual broadcast):")
            print(raw_tx_hex)
    except Exception:
        pass

    print("\n🎉 Demo completed: Using faucet receipts in internalize → create_action.")


if __name__ == "__main__":
    main()
