#!/usr/bin/env python3
"""E2E test: Alice & Bob (2-party roundtrip).

Scenario:
  1. Initialize two separate wallets (Alice and Bob)
  2. Display Alice's receive address for Faucet deposit
  3. Wait for user to deposit via Faucet, then continue
  4. Optionally internalize the Faucet transaction (BRC-29 wallet payment)
  5. Alice sends 80% of balance to Bob (P2PKH)
  6. Bob sends 80% of balance back to Alice (P2PKH)
  7. Display final balance summary

Environment:
  - USE_STORAGE_SERVER=true: Use remote WalletStorageServer (BRC-104 auth required)
  - Otherwise: Use local SQLite (wallet_alice.db, wallet_bob.db)
  - TAAL_ARC_API_KEY required for broadcasting

Notes:
  - This script is intentionally interactive (faucet funding and txid entry cannot be automated).
  - Shared primitives (e.g., AtomicBEEF construction and rawTx retry) should live in
    `bsv_wallet_toolbox.utils.*`, so this file stays focused on Wallet API usage.
"""

from __future__ import annotations

import base64
import logging
import os
import sys
from pathlib import Path
from typing import Any, Literal

from dotenv import load_dotenv

from bsv.constants import Network
from bsv.hd.bip32 import bip32_derive_xprv_from_mnemonic
from bsv.hd.bip39 import mnemonic_from_entropy
from bsv.keys import PrivateKey, PublicKey
from bsv.wallet import KeyDeriver
from bsv_wallet_toolbox import Wallet
from bsv_wallet_toolbox.brc29 import (
    KeyID,
    address_for_counterparty,
    address_for_self,
    lock_for_counterparty,
)
from bsv_wallet_toolbox.rpc import StorageClient
from bsv_wallet_toolbox.services import Services, create_default_options
from bsv_wallet_toolbox.storage import StorageProvider
from bsv_wallet_toolbox.utils.atomic_beef_utils import build_atomic_beef_for_txid
from sqlalchemy import create_engine

Chain = Literal["main", "test"]

FAUCET_DERIVATION_PREFIX = "faucet-prefix-01"
FAUCET_DERIVATION_SUFFIX = "faucet-suffix-01"

# Deterministic BRC-29 derivation parameters for reproducible E2E runs.
# Keep them distinct per direction to avoid accidental key reuse across roles.
ALICE_TO_BOB_DERIVATION_PREFIX = "alice-to-bob-prefix-01"
ALICE_TO_BOB_DERIVATION_SUFFIX = "alice-to-bob-suffix-01"
BOB_TO_ALICE_DERIVATION_PREFIX = "bob-to-alice-prefix-01"
BOB_TO_ALICE_DERIVATION_SUFFIX = "bob-to-alice-suffix-01"


def _configure_logging() -> None:
    """Configure basic logging with env override (default INFO)."""
    if logging.getLogger().handlers:
        return
    env_level = os.getenv("PY_WALLET_TOOLBOX_LOG_LEVEL") or os.getenv("LOGLEVEL", "INFO")
    level = getattr(logging, env_level.upper(), logging.INFO)
    logging.basicConfig(level=level, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")


_configure_logging()


def load_environment() -> None:
    """Load .env file from the script's directory."""
    script_dir = Path(__file__).parent
    env_file = script_dir / ".env"
    if env_file.exists():
        load_dotenv(env_file)
    else:
        load_dotenv()


def get_network() -> Chain:
    """Get network from BSV_NETWORK env var (default: test)."""
    network = os.getenv("BSV_NETWORK", "test").lower()
    if network not in ("test", "main"):
        print(f"⚠️  Invalid BSV_NETWORK '{network}'. Falling back to 'test'.")
        return "test"
    return network  # type: ignore


def use_storage_server() -> bool:
    """Return True if the demo should use a remote WalletStorageServer."""
    return os.getenv("USE_STORAGE_SERVER", "").lower() in ("1", "true", "yes")


def get_storage_server_url() -> str:
    """Return the base URL for the configured storage server."""
    return os.getenv("STORAGE_SERVER_URL", "http://localhost:8080")


def get_arc_api_key() -> str:
    """Read the ARC API key used for broadcasting."""
    key = os.getenv("TAAL_ARC_API_KEY", "").strip()
    if not key:
        print("❌ TAAL_ARC_API_KEY is not set in .env")
        sys.exit(1)
    return key


def create_services(chain: Chain) -> Services:
    """Create Services with ARC API key and disable other providers."""
    options = create_default_options(chain)
    options["arcApiKey"] = get_arc_api_key()
    # Keep the demo deterministic-ish: ARC priority
    options["bitailsApiKey"] = None
    options["arcGorillaPoolUrl"] = None
    options["arcGorillaPoolApiKey"] = None
    options["arcGorillaPoolHeaders"] = None
    return Services(options)


def create_local_storage_provider(chain: Chain, wallet_name: str) -> StorageProvider:
    """Create a local SQLite storage provider for the given wallet name."""
    db_file = f"wallet_{wallet_name}.db"
    print(f"💾 Using local database: {db_file}")
    engine = create_engine(f"sqlite:///{db_file}")
    storage = StorageProvider(engine=engine, chain=chain, storage_identity_key=f"{chain}-{wallet_name}")
    storage.make_available()
    return storage


def create_storage_client(wallet: Wallet) -> StorageClient:
    """Create a StorageClient for the configured storage server (remote storage)."""
    url = get_storage_server_url()
    print(f"🌐 Connecting to storage server: {url}")
    return StorageClient(wallet, url)


def create_key_deriver(wallet_name: str) -> tuple[KeyDeriver, PrivateKey]:
    """Create a KeyDeriver for the wallet.

    If BSV_MNEMONIC is set, use it. Otherwise, generate a new one and display it.

    Args:
        wallet_name: 'alice' or 'bob' (for display purposes)

    Returns:
        Tuple of (KeyDeriver instance, root_private_key)
    """
    mnemonic = os.getenv("BSV_MNEMONIC")
    if not mnemonic:
        print(f"\n⚠️  No mnemonic configured for {wallet_name}. Generating a new one...\n")
        mnemonic = mnemonic_from_entropy(entropy=None, lang="en")
        print(f"   BSV_MNEMONIC={mnemonic}\n")
    path = "m/0" if wallet_name == "alice" else "m/1"
    xprv = bip32_derive_xprv_from_mnemonic(
        mnemonic=mnemonic,
        lang="en",
        passphrase="",
        prefix="mnemonic",
        path=path,
    )
    root_private_key = xprv.private_key()
    return KeyDeriver(root_private_key=root_private_key), root_private_key


def create_wallet(wallet_name: str, chain: Chain, services: Services, use_remote: bool) -> tuple[Wallet, PrivateKey]:
    """Create a Wallet instance and return it with the root private key."""
    key_deriver, root_private_key = create_key_deriver(wallet_name)

    if use_remote:
        temp_storage = create_local_storage_provider(chain, f"{wallet_name}_temp")
        temp_wallet = Wallet(chain=chain, services=services, key_deriver=key_deriver, storage_provider=temp_storage)
        storage_client = create_storage_client(temp_wallet)
        storage_client.make_available()
        wallet = Wallet(chain=chain, services=services, key_deriver=key_deriver, storage_provider=storage_client)
        return wallet, root_private_key

    storage_provider = create_local_storage_provider(chain, wallet_name)
    storage_provider.set_services(services)
    wallet = Wallet(chain=chain, services=services, key_deriver=key_deriver, storage_provider=storage_provider)
    return wallet, root_private_key


def get_wallet_balance(wallet: Wallet) -> int:
    """Return the wallet's spendable balance in satoshis (best-effort)."""
    try:
        result = wallet.balance()
        if isinstance(result, dict):
            return int(result.get("total", 0) or 0)
    except Exception:  # noqa: BLE001
        pass
    return 0


def internalize_wallet_payment_tx(
    wallet: Wallet,
    txid: str,
    output_index: int,
    remittance: dict[str, str],
    services: Services,
    description: str,
) -> bool:
    """Internalize a wallet payment output (BRC-29) into the wallet."""
    try:
        atomic_beef = build_atomic_beef_for_txid(services, txid)
    except Exception as err:  # noqa: BLE001
        print(f"❌ Failed to build Atomic BEEF: {err}")
        return False

    args: dict[str, Any] = {
        "tx": list(atomic_beef),
        "outputs": [
            {
                "outputIndex": output_index,
                "protocol": "wallet payment",
                "paymentRemittance": remittance,
            }
        ],
        "description": description,
        "labels": [f"txid:{txid}", "wallet-payment"],
    }
    try:
        wallet.internalize_action(args)
        return True
    except Exception as err:  # noqa: BLE001
        print(f"❌ Internalize failed: {err}")
        return False


def internalize_faucet_tx(wallet: Wallet, txid: str, services: Services, output_index: int = 0) -> bool:
    """Internalize a faucet funding transaction for this demo.

    The demo faucet address is derived with:
      address_for_self(sender=anyone, key_id=(FAUCET_DERIVATION_PREFIX/SUFFIX))
    so we internalize using protocol='wallet payment' + a matching paymentRemittance.
    """
    derivation_prefix_b64 = base64.b64encode(FAUCET_DERIVATION_PREFIX.encode("utf-8")).decode("ascii")
    derivation_suffix_b64 = base64.b64encode(FAUCET_DERIVATION_SUFFIX.encode("utf-8")).decode("ascii")
    anyone_key = PrivateKey(1).public_key().hex()
    remittance = {
        "senderIdentityKey": anyone_key,
        "derivationPrefix": derivation_prefix_b64,
        "derivationSuffix": derivation_suffix_b64,
    }
    return internalize_wallet_payment_tx(
        wallet=wallet,
        txid=txid,
        output_index=output_index,
        remittance=remittance,
        services=services,
        description="Internalize faucet transaction",
    )


def send_wallet_payment(
    wallet_from: Wallet,
    wallet_to: Wallet,
    amount_satoshis: int,
    chain: Chain,
    *,
    direction: Literal["alice_to_bob", "bob_to_alice"],
) -> tuple[str | None, int | None, dict[str, str] | None]:
    """Send a BRC-29 wallet payment and return (txid, vout, remittance).

    Note: This demo constructs a single output, so the destination vout is 0.
    """
    sender_identity_key = wallet_from.get_public_key({"identityKey": True, "reason": "sender"})["publicKey"]
    recipient_identity_key = wallet_to.get_public_key({"identityKey": True, "reason": "recipient"})["publicKey"]

    if direction == "alice_to_bob":
        prefix_raw = ALICE_TO_BOB_DERIVATION_PREFIX
        suffix_raw = ALICE_TO_BOB_DERIVATION_SUFFIX
    else:
        prefix_raw = BOB_TO_ALICE_DERIVATION_PREFIX
        suffix_raw = BOB_TO_ALICE_DERIVATION_SUFFIX
    remittance = {
        "senderIdentityKey": sender_identity_key,
        "derivationPrefix": base64.b64encode(prefix_raw.encode("utf-8")).decode("ascii"),
        "derivationSuffix": base64.b64encode(suffix_raw.encode("utf-8")).decode("ascii"),
    }

    key_id = KeyID(derivation_prefix=prefix_raw, derivation_suffix=suffix_raw)
    # Explorer-friendly trace:
    # - from: sender identity P2PKH address (not necessarily the exact UTXO source address)
    # - to  : derived P2PKH address used in the output locking script
    network = Network.TESTNET if chain == "test" else Network.MAINNET
    from_identity_address = PublicKey(sender_identity_key).address(network=network)
    to_derived_address = address_for_counterparty(
        sender_private_key=wallet_from.key_deriver,
        key_id=key_id,
        recipient_public_key=recipient_identity_key,
        testnet=(chain == "test"),
    )["address_string"]
    print("\n=== Wallet payment routing (for explorer correlation) ===")
    print(f"from (sender identity): {from_identity_address}")
    print(f"to   (derived address) : {to_derived_address}")
    print(f"key_id                : {key_id}")

    locking_script = lock_for_counterparty(
        sender_private_key=wallet_from.key_deriver,
        key_id=key_id,
        recipient_public_key=recipient_identity_key,
        testnet=(chain == "test"),
    )

    try:
        action_result = wallet_from.create_action(
            {
                "description": f"Send {amount_satoshis} satoshis",
                "outputs": [
                    {
                        "satoshis": amount_satoshis,
                        "lockingScript": locking_script.hex(),
                        "protocol": "wallet payment",
                        "paymentRemittance": remittance,
                        "outputDescription": "BRC29 payment",
                    }
                ],
                "options": {"signAndProcess": True, "acceptDelayedBroadcast": False},
            }
        )
    except Exception as err:  # noqa: BLE001
        print(f"❌ Create action failed: {err}")
        return None, None, None

    signable = action_result.get("signableTransaction")
    if signable:
        reference = signable.get("reference")
        if not reference:
            return None, None, None
        signed = wallet_from.sign_action({"reference": reference, "accept": True})
        txid = signed.get("txid") or signed.get("txID")
        return txid, 0, remittance

    txid = action_result.get("txid") or action_result.get("txID")
    return txid, 0, remittance


def prompt_internalize_received_tx(
    wallet: Wallet,
    services: Services,
    txid: str,
    default_output_index: int,
    payment_remittance: dict[str, str],
    wallet_name: str,
) -> None:
    """Prompt the user to internalize a received transaction for a wallet."""
    print("\n" + "=" * 80)
    print(f"📥 Internalize received funds for {wallet_name}")
    print("=" * 80)
    print()
    txid_input = input(f"Enter the transaction ID to internalize (default: {txid}, leave blank to use default): ").strip()
    if not txid_input:
        txid_input = txid
    output_index_raw = input(f"Enter the output index that paid this wallet (default {default_output_index}): ").strip()
    output_index = default_output_index
    if output_index_raw:
        try:
            output_index = int(output_index_raw)
        except ValueError:
            output_index = default_output_index

    ok = internalize_wallet_payment_tx(
        wallet=wallet,
        txid=txid_input,
        output_index=output_index,
        remittance=payment_remittance,
        services=services,
        description=f"Internalize wallet payment {txid_input} for {wallet_name}",
    )
    if ok:
        print(f"✅ Internalized. Balance now: {get_wallet_balance(wallet)} satoshis")


def prompt_ready(message: str) -> None:
    """Block until the user explicitly confirms they're ready to continue."""
    print()
    input(f"{message}\nPress Enter to continue...")


def main() -> None:
    """Run the interactive roundtrip scenario."""
    print("=" * 80)
    print("🚀 E2E Test: Alice & Bob Wallets (2-Party Roundtrip)")
    print("=" * 80)
    print()

    load_environment()
    chain = get_network()
    use_remote = use_storage_server()

    services = create_services(chain)

    alice, alice_root_priv = create_wallet("alice", chain, services, use_remote)
    bob, _bob_root_priv = create_wallet("bob", chain, services, use_remote)

    # Faucet address for Alice (BRC-29)
    anyone_key = PrivateKey(1).public_key()
    key_id = KeyID(derivation_prefix=FAUCET_DERIVATION_PREFIX, derivation_suffix=FAUCET_DERIVATION_SUFFIX)
    alice_faucet_address = address_for_self(
        sender_public_key=anyone_key.hex(),
        key_id=key_id,
        recipient_private_key=alice_root_priv,
        testnet=(chain == "test"),
    )["address_string"]

    print("=" * 80)
    print("💧 Faucet Deposit Required")
    print("=" * 80)
    print(f"\nSend BSV to Alice's BRC-29 Faucet address:\n\n   📬 Address: {alice_faucet_address}\n")
    input("Press Enter once you have confirmed the transaction in the blockchain explorer...")

    print("=" * 80)
    print("🔄 Internalizing Faucet Transaction (Optional)")
    print("=" * 80)
    txid_input = input("Enter the faucet transaction ID (64 hex chars, or leave blank to skip): ").strip()
    if txid_input:
        _ = internalize_faucet_tx(alice, txid_input, services, output_index=0)

    alice_balance = get_wallet_balance(alice)
    print(f"\nAlice's balance: {alice_balance} satoshis")
    if alice_balance < 1000:
        print("⚠️  Alice's balance is very low.")
        return

    # Phase 1: Alice -> Bob
    alice_send_amount = int(alice_balance * 0.8)
    print(f"\n💸 Alice sending {alice_send_amount} satoshis to Bob")
    alice_txid, bob_out_idx, alice_remittance = send_wallet_payment(
        alice,
        bob,
        alice_send_amount,
        chain,
        direction="alice_to_bob",
    )
    if not alice_txid or alice_remittance is None or bob_out_idx is None:
        print("❌ Alice transfer failed")
        return
    print(f"✅ Alice transfer txid: {alice_txid}")

    prompt_ready(
        "Wait until the transaction is visible to your Services provider / explorer.\n"
        "When ready, proceed to internalize the received output for Bob."
    )
    prompt_internalize_received_tx(bob, services, alice_txid, bob_out_idx, alice_remittance, "Bob")

    bob_balance = get_wallet_balance(bob)
    print(f"\nBob's balance: {bob_balance} satoshis")

    # Phase 2: Bob -> Alice
    bob_send_amount = int(bob_balance * 0.8)
    print(f"\n💸 Bob sending {bob_send_amount} satoshis to Alice")
    bob_txid, alice_out_idx, bob_remittance = send_wallet_payment(
        bob,
        alice,
        bob_send_amount,
        chain,
        direction="bob_to_alice",
    )
    if not bob_txid or bob_remittance is None or alice_out_idx is None:
        print("❌ Bob transfer failed")
        return
    print(f"✅ Bob transfer txid: {bob_txid}")

    prompt_ready(
        "Wait until the transaction is visible to your Services provider / explorer.\n"
        "When ready, proceed to internalize the received output for Alice."
    )
    prompt_internalize_received_tx(alice, services, bob_txid, alice_out_idx, bob_remittance, "Alice")

    print("\n📊 Final Balance Summary")
    print(f"Alice: {get_wallet_balance(alice)} satoshis")
    print(f"Bob  : {get_wallet_balance(bob)} satoshis")


if __name__ == "__main__":
    main()

 