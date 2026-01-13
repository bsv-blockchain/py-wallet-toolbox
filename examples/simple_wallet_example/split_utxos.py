#!/usr/bin/env python3
"""Split spendable change outputs into smaller UTXOs.

This helper script updates the wallet's change basket preferences
and triggers a zero-value action so that storage re-balances change
into many smaller outputs (useful for local testing).
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path

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

from bsv_wallet_toolbox import Wallet
from bsv_wallet_toolbox.services import Services, create_default_options


def _init_wallet() -> Wallet:
    """Initialize wallet using the same storage selection logic as other examples."""
    chain = get_network()
    key_deriver = get_key_deriver()
    options = create_default_options(chain)
    services = Services(options)

    wallet_infra_mode = use_wallet_infra()
    bypass_auth = bypass_wallet_infra_auth()
    remote_storage_mode = use_remote_storage()
    wallet: Wallet | None = None

    if wallet_infra_mode:
        print(f"\n🏗️  wallet-infra mode: {get_wallet_infra_url()}")
        local_storage = get_storage_provider(chain)
        wallet = Wallet(chain=chain, services=services, key_deriver=key_deriver, storage_provider=local_storage)
        infra_client = get_wallet_infra_client(wallet)
        if bypass_auth:
            print("🔄 wallet-infra (auth bypass)")
            wallet = Wallet(chain=chain, services=services, key_deriver=key_deriver, storage_provider=infra_client)
        else:
            try:
                infra_client.make_available()
                print("✅ wallet-infra connection successful")
                wallet = Wallet(chain=chain, services=services, key_deriver=key_deriver, storage_provider=infra_client)
            except Exception as exc:
                print(f"⚠️  wallet-infra connection failed: {exc}")
                wallet_infra_mode = False

    if not wallet_infra_mode and remote_storage_mode:
        print(f"\n🌐 Remote storage mode: {get_remote_storage_url(chain)}")
        local_storage = get_storage_provider(chain)
        wallet = Wallet(chain=chain, services=services, key_deriver=key_deriver, storage_provider=local_storage)
        remote_client = get_remote_storage_client(wallet, chain)
        try:
            remote_client.make_available()
            print("✅ Remote storage connection successful")
            wallet = Wallet(chain=chain, services=services, key_deriver=key_deriver, storage_provider=remote_client)
        except Exception as exc:
            print(f"❌ Remote storage connection failed: {exc}")
            remote_storage_mode = False

    if not wallet_infra_mode and not remote_storage_mode:
        print("\n💾 Local storage mode")
        storage = get_storage_provider(chain)
        wallet = Wallet(chain=chain, services=services, key_deriver=key_deriver, storage_provider=storage)

    return wallet


def _set_change_params(wallet: Wallet, desired_utxos: int, min_value: int) -> None:
    """Call SpecOp to update change basket preferences."""
    print(f"🔧 Updating change settings: numberOfDesiredUTXOs={desired_utxos}, minimumDesiredUTXOValue={min_value}")
    wallet.list_outputs(
        {
            "basket": "specOpSetWalletChangeParams",
            "tags": [str(desired_utxos), str(min_value)],
        }
    )


def _trigger_split_action(wallet: Wallet, description: str, accept_delayed: bool) -> None:
    """Send a zero-sat OP_RETURN action to force change regeneration."""
    print("🚀 Executing create_action for change regeneration…")
    action = wallet.create_action(
        {
            "description": description,
            "outputs": [
                {
                    "lockingScript": "006a136368616e67655f7574786f5f73706c6974",  # OP_RETURN "change_utxo_split"
                    "satoshis": 0,
                    "outputDescription": "Split helper",
                }
            ],
            "options": {
                "acceptDelayedBroadcast": accept_delayed,
            },
        }
    )
    print("✅ create_action completed")
    if action.get("txid"):
        print(f"   txid: {action['txid']}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Split UTXOs in wallet into multiple pieces.")
    parser.add_argument(
        "--count",
        type=int,
        default=10,
        help="Number of UTXOs to create (default: 10)",
    )
    parser.add_argument(
        "--min-value",
        type=int,
        default=5000,
        help="Minimum UTXO value per piece (sats, default: 5000)",
    )
    parser.add_argument(
        "--accept-delayed",
        action="store_true",
        help="Allow delayed broadcast (default is immediate broadcast)",
    )
    parser.add_argument(
        "--description",
        type=str,
        default="Split local change UTXOs",
        help="Description for create_action",
    )
    args = parser.parse_args()

    os.chdir(Path(__file__).parent)
    load_dotenv()

    wallet = _init_wallet()
    balance = wallet.balance().get("total") or 0
    print(f"💵 Current balance: {balance} satoshis")

    if balance <= 0:
        raise SystemExit("Cannot split due to zero balance. Please receive funds from faucet.")

    if args.count <= 0:
        raise SystemExit("Please specify --count as 1 or greater.")

    min_value = max(1, args.min_value)
    estimated_required = args.count * min_value

    if balance < estimated_required:
        print(
            f"⚠️  Balance {balance} sats cannot satisfy the specified value ({args.count} x {min_value} sats)."
            " Please specify a smaller min-value."
        )

    _set_change_params(wallet, desired_utxos=args.count, min_value=min_value)
    _trigger_split_action(wallet, args.description, args.accept_delayed)

    # Verification
    outputs = wallet.list_outputs({"basket": "default", "limit": 100}).get("outputs", [])
    spendable = [o for o in outputs if not o.get("spent") and o.get("spendable") is not False]
    print("\n🔍 UTXO list after regeneration (top 100):")
    for idx, out in enumerate(spendable, start=1):
        print(f"  {idx:02d}: {out.get('outpoint')} → {out.get('satoshis', 0)} sats")


if __name__ == "__main__":
    main()
