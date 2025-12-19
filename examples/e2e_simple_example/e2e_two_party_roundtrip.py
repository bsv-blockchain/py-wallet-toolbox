#!/usr/bin/env python3
"""E2E test: Alice and Bob wallets exchanging 80% of their balance (P2PKH).

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
"""

from __future__ import annotations

import base64
import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import Any, Literal

from dotenv import load_dotenv
import hashlib

from bsv.constants import Network
from bsv.hd.bip32 import bip32_derive_xprv_from_mnemonic
from bsv.hd.bip39 import mnemonic_from_entropy
from bsv.keys import PrivateKey, PublicKey
from bsv.script import P2PKH
from bsv.transaction import Transaction
from bsv.transaction.beef import BEEF_V2, Beef
from bsv.transaction.beef_builder import merge_bump, merge_raw_tx
from bsv.transaction.beef_serialize import to_binary_atomic
from bsv.wallet import KeyDeriver
from bsv_wallet_toolbox import Wallet
from bsv_wallet_toolbox.brc29 import KeyID, address_for_self, lock_for_counterparty
from bsv_wallet_toolbox.services import Services, create_default_options
from bsv_wallet_toolbox.storage import StorageProvider
from bsv_wallet_toolbox.rpc import StorageClient
from bsv_wallet_toolbox.errors import ReviewActionsError
from sqlalchemy import create_engine

# Types
Chain = Literal["main", "test"]

# Faucet BRC-29 derivation config (fixed for demo)
FAUCET_DERIVATION_PREFIX = "faucet-prefix-01"
FAUCET_DERIVATION_SUFFIX = "faucet-suffix-01"
LOG_PATH = Path("/home/yasu/projects/yenpoint/porting/wallet-toolbox/.cursor/debug.log")


def _configure_logging() -> None:
    """Configure basic logging with env override (default INFO)."""
    if logging.getLogger().handlers:
        return

    env_level = os.getenv("PY_WALLET_TOOLBOX_LOG_LEVEL") or os.getenv("LOGLEVEL", "INFO")
    level = getattr(logging, env_level.upper(), logging.INFO)
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


_configure_logging()


# region agent log helper
def agent_log(hypothesis_id: str, location: str, message: str, data: dict[str, Any]) -> None:
    payload = {
        "sessionId": "debug-session",
        "runId": "run-pre-fix",
        "hypothesisId": hypothesis_id,
        "location": location,
        "message": message,
        "data": data,
        "timestamp": int(time.time() * 1000),
    }
    try:
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with LOG_PATH.open("a", encoding="utf-8") as fp:
            fp.write(json.dumps(payload) + "\n")
    except Exception:
        pass
# endregion


def build_atomic_beef_for_txid(chain: Chain, txid: str, services: Services) -> bytes:
    """Fetch raw transaction and merkle data, then build Atomic BEEF."""
    print(f"\n🔎 Fetching raw transaction for txid={txid}")
    raw_hex = services.get_raw_tx(txid)
    if not raw_hex:
        raise RuntimeError(f"Unable to fetch raw transaction for {txid}")

    print(f"✅ Raw transaction fetched ({len(raw_hex)} hex chars)")
    print("🔎 Fetching merkle path...")
    merkle_result = services.get_merkle_path_for_transaction(txid)

    beef = Beef(version=BEEF_V2)
    bump_index = None
    if merkle_result and isinstance(merkle_result, dict):
        merkle_path = merkle_result.get("merklePath")
        if isinstance(merkle_path, dict) and "blockHeight" in merkle_path:
            from bsv.merkle_path import MerklePath as PyMerklePath

            bump_path = PyMerklePath(
                merkle_path["blockHeight"], merkle_path.get("path", [])
            )
            bump_index = merge_bump(beef, bump_path)

    merge_raw_tx(beef, bytes.fromhex(raw_hex), bump_index)
    print("✅ Atomic BEEF built successfully")
    return to_binary_atomic(beef, txid)


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


def get_arc_api_key() -> str:
    """Get TAAL_ARC_API_KEY from environment."""
    key = os.getenv("TAAL_ARC_API_KEY", "").strip()
    if not key:
        print("❌ TAAL_ARC_API_KEY is not set in .env")
        sys.exit(1)
    return key


def use_storage_server() -> bool:
    """Check if USE_STORAGE_SERVER is enabled."""
    return os.getenv("USE_STORAGE_SERVER", "").lower() in ("1", "true", "yes")


def get_storage_server_url() -> str:
    """Get STORAGE_SERVER_URL from environment."""
    url = os.getenv("STORAGE_SERVER_URL", "http://localhost:8080")
    return url


def create_services(chain: Chain) -> Services:
    """Create Services with ARC API key and disable other providers."""
    options = create_default_options(chain)
    options["arcApiKey"] = get_arc_api_key()
    # Disable Bitails and GorillaPool for simplicity
    options["bitailsApiKey"] = None
    options["arcGorillaPoolUrl"] = None
    options["arcGorillaPoolApiKey"] = None
    options["arcGorillaPoolHeaders"] = None
    return Services(options)


def create_local_storage_provider(
    chain: Chain, wallet_name: str
) -> StorageProvider:
    """Create a local SQLite StorageProvider for a named wallet."""
    db_file = f"wallet_{wallet_name}.db"
    print(f"💾 Using local database: {db_file}")

    engine = create_engine(f"sqlite:///{db_file}")
    storage = StorageProvider(
        engine=engine,
        chain=chain,
        storage_identity_key=f"{chain}-{wallet_name}",
    )

    try:
        storage.make_available()
        print(f"✅ Storage tables ready for {wallet_name}.")
    except Exception as e:  # noqa: BLE001
        print(f"⚠️  Storage warning for {wallet_name}: {e}")

    return storage


def create_storage_client(wallet: Wallet, chain: Chain) -> StorageClient:
    """Create a StorageClient for the configured storage server."""
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
        print(f"\n⚠️  No mnemonic configured for {wallet_name}. Generating a new one...")
        print()

        mnemonic = mnemonic_from_entropy(entropy=None, lang="en")

        print("=" * 80)
        print(f"🔑 Generated mnemonic for {wallet_name} (12 words):")
        print("=" * 80)
        print()
        print(f"   {mnemonic}")
        print()
        print("=" * 80)
        print("⚠️  IMPORTANT: Store this mnemonic securely before proceeding.")
        print("=" * 80)
        print()
        print(
            "💡 To reuse this wallet, add the line below to your .env file:"
        )
        print(f"   BSV_MNEMONIC={mnemonic}")
        print()
        print("=" * 80)
        print()

    # Derive KeyDeriver from mnemonic using BIP-32/BIP-39
    # Use different derivation paths for Alice and Bob to get different keys:
    # Alice: m/0, Bob: m/1
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


def create_wallet(
    wallet_name: str, chain: Chain, services: Services, use_remote: bool
) -> tuple[Wallet, PrivateKey]:
    """Create a wallet for Alice or Bob.

    Args:
        wallet_name: 'alice' or 'bob'
        chain: 'main' or 'test'
        services: Services instance for broadcasting
        use_remote: Whether to use remote storage server or local SQLite

    Returns:
        Tuple of (Initialized Wallet instance, root_private_key)
    """
    # Create KeyDeriver (with mnemonic generation if needed)
    key_deriver, root_private_key = create_key_deriver(wallet_name)

    print(f"\n📱 Initializing wallet: {wallet_name}")

    if use_remote:
        print(f"🌐 Using remote storage server for {wallet_name}...")
        # First create a temporary local storage for StorageClient auth
        temp_storage = create_local_storage_provider(chain, f"{wallet_name}_temp")
        temp_wallet = Wallet(
            chain=chain,
            services=services,
            key_deriver=key_deriver,
            storage_provider=temp_storage,
        )

        # Now create StorageClient for remote auth
        try:
            storage_client = create_storage_client(temp_wallet, chain)
            settings = storage_client.make_available()
            print(f"✅ Remote storage connected for {wallet_name}")
            print(
                f"   Storage Identity Key: {settings.get('storageIdentityKey', 'N/A')}"
            )

            # Create final wallet with remote storage
            wallet = Wallet(
                chain=chain,
                services=services,
                key_deriver=key_deriver,
                storage_provider=storage_client,
            )
            print(f"✅ Wallet {wallet_name} initialized successfully")
            return wallet, root_private_key
        except Exception as err:  # noqa: BLE001
            print(f"⚠️  Remote storage failed for {wallet_name}: {err}")
            print("   Falling back to local storage...")
            storage_provider = create_local_storage_provider(chain, wallet_name)
            storage_provider.set_services(services)
            wallet = Wallet(
                chain=chain,
                services=services,
                key_deriver=key_deriver,
                storage_provider=storage_provider,
            )
            print(f"✅ Wallet {wallet_name} initialized successfully")
            return wallet, root_private_key
    else:
        print(f"💾 Using local storage for {wallet_name}...")
        storage_provider = create_local_storage_provider(chain, wallet_name)
        # Enable broadcast via post_beef for local storage
        storage_provider.set_services(services)
        wallet = Wallet(
            chain=chain,
            services=services,
            key_deriver=key_deriver,
            storage_provider=storage_provider,
        )

    print(f"✅ Wallet {wallet_name} initialized successfully")
    return wallet, root_private_key


def build_atomic_beef_for_txid(chain: Chain, txid: str, services: Services) -> bytes:
    """Build an Atomic BEEF for the given txid."""
    print(f"\n🔎 Fetching raw transaction for txid={txid}")
    raw_hex = services.get_raw_tx(txid)
    if not raw_hex:
        raise RuntimeError(f"Unable to fetch raw transaction for {txid}")

    print(f"✅ Raw transaction fetched ({len(raw_hex)} hex chars)")
    print("🔎 Fetching merkle path...")
    merkle_result = services.get_merkle_path_for_transaction(txid)

    beef = Beef(version=BEEF_V2)
    bump_index = None
    if merkle_result and isinstance(merkle_result, dict):
        merkle_path = merkle_result.get("merklePath")
        if isinstance(merkle_path, dict) and "blockHeight" in merkle_path:
            from bsv.merkle_path import MerklePath as PyMerklePath

            bump_path = PyMerklePath(
                merkle_path["blockHeight"], merkle_path.get("path", [])
            )
            bump_index = merge_bump(beef, bump_path)

    merge_raw_tx(beef, bytes.fromhex(raw_hex), bump_index)
    print("✅ Atomic BEEF built successfully")
    return to_binary_atomic(beef, txid)


def internalize_faucet_tx(
    wallet: Wallet, txid: str, chain: Chain, services: Services, output_index: int = 0
) -> bool:
    """Internalize a Faucet transaction using BRC-29 wallet payment protocol.

    Args:
        wallet: Alice's wallet
        txid: Transaction ID to internalize
        chain: Network (for BEEF building)
        services: Services for fetching transaction data
        output_index: Output index to internalize

    Returns:
        True if successful, False otherwise
    """
    try:
        atomic_beef = build_atomic_beef_for_txid(chain, txid, services)
    except Exception as err:  # noqa: BLE001
        print(f"❌ Failed to build Atomic BEEF: {err}")
        return False

    # BRC-29 wallet payment protocol config
    anyone_key = PrivateKey(1).public_key()
    derivation_prefix_b64 = base64.b64encode(
        FAUCET_DERIVATION_PREFIX.encode("utf-8")
    ).decode("ascii")
    derivation_suffix_b64 = base64.b64encode(
        FAUCET_DERIVATION_SUFFIX.encode("utf-8")
    ).decode("ascii")

    print("\n🚀 Internalizing transaction via wallet payment protocol...")
    internalize_args: dict[str, Any] = {
        "tx": atomic_beef,
        "outputs": [
            {
                "outputIndex": output_index,
                "protocol": "wallet payment",
                "paymentRemittance": {
                    "senderIdentityKey": anyone_key.hex(),
                    "derivationPrefix": derivation_prefix_b64,
                    "derivationSuffix": derivation_suffix_b64,
                },
            }
        ],
        "description": "Internalize faucet transaction",
        "labels": [f"txid:{txid}", "faucet"],
    }

    # region agent log
    agent_log(
        "H2",
        "internalize_faucet_tx",
        "Preparing faucet internalize",
        {
            "wallet_id": id(wallet),
            "txid": txid,
            "outputIndex": output_index,
            "derivationPrefix": FAUCET_DERIVATION_PREFIX,
            "derivationSuffix": FAUCET_DERIVATION_SUFFIX,
        },
    )
    # endregion

    try:
        result = wallet.internalize_action(internalize_args)
        print("\n✅ Transaction internalized successfully")
        print(f"   accepted : {result.get('accepted')}")
        print(f"   txid     : {result.get('txid', 'n/a')}")
        print(f"   satoshis : {result.get('satoshis', 'n/a')}")
        return True
    except Exception as err:  # noqa: BLE001
        print(f"❌ Internalize failed: {err}")
        return False


def internalize_standard_tx(
    wallet: Wallet,
    txid: str,
    output_indexes: list[int],
    services: Services,
    chain: Chain,
    description: str = "Internalize received transaction",
) -> bool:
    """Internalize a standard P2PKH transaction (basket insertion)."""
    try:
        atomic_beef = build_atomic_beef_for_txid(chain, txid, services)
    except Exception as err:  # noqa: BLE001
        print(f"❌ Failed to build Atomic BEEF: {err}")
        return False

    outputs = []
    for idx in output_indexes:
        outputs.append(
            {
                "outputIndex": idx,
                "protocol": "basket insertion",
                "insertionRemittance": {"basket": "default"},
            }
        )

    internalize_args: dict[str, Any] = {
        "tx": atomic_beef,
        "outputs": outputs,
        "description": description,
        "labels": [f"txid:{txid}", "p2pkh"],
    }

    # region agent log
    agent_log(
        "H2",
        "internalize_standard_tx",
        "Preparing standard internalize",
        {
            "wallet_id": id(wallet),
            "txid": txid,
            "outputIndexes": output_indexes,
            "description": description,
        },
    )
    # endregion

    try:
        result = wallet.internalize_action(internalize_args)
        print("\n✅ Transaction internalized successfully")
        print(f"   accepted : {result.get('accepted')}")
        print(f"   txid     : {result.get('txid', 'n/a')}")
        print(f"   satoshis : {result.get('satoshis', 'n/a')}")
        return True
    except Exception as err:  # noqa: BLE001
        print(f"❌ Internalize failed: {err}")
        return False


def internalize_wallet_payment_tx(
    wallet: Wallet,
    txid: str,
    output_index: int,
    remittance: dict[str, str],
    services: Services,
    chain: Chain,
    description: str,
) -> bool:
    """Internalize a wallet payment output using provided remittance data."""
    try:
        atomic_beef = build_atomic_beef_for_txid(chain, txid, services)
    except Exception as err:  # noqa: BLE001
        print(f"❌ Failed to build Atomic BEEF: {err}")
        return False

    internalize_args: dict[str, Any] = {
        "tx": atomic_beef,
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

    agent_log(
        "H2",
        "internalize_wallet_payment_tx",
        "Preparing wallet payment internalize",
        {
            "wallet_id": id(wallet),
            "txid": txid,
            "outputIndex": output_index,
            "remittance": remittance,
        },
    )

    try:
        result = wallet.internalize_action(internalize_args)
        print("\n✅ Transaction internalized successfully")
        print(f"   accepted : {result.get('accepted')}")
        print(f"   txid     : {result.get('txid', 'n/a')}")
        print(f"   satoshis : {result.get('satoshis', 'n/a')}")
        return True
    except Exception as err:  # noqa: BLE001
        print(f"❌ Internalize failed: {err}")
        return False


def get_wallet_balance(wallet: Wallet) -> int:
    """Get available balance (in satoshis)."""
    # BRC-100: wallet.balance() returns balance info
    try:
        balance_result = wallet.balance()
        if isinstance(balance_result, dict):
            # Return available or total balance
            return balance_result.get("available", balance_result.get("total", 0))
        return 0
    except Exception as err:  # noqa: BLE001
        print(f"⚠️  Error getting balance: {err}")
        return 0


def get_receive_address(wallet: Wallet, chain: Chain) -> str:
    """Get a P2PKH receive address using get_public_key (BRC-100).
    
    Based on simple_wallet_example/src/address_management.py pattern.
    """
    try:
        # Use BRC-100: get_public_key with identityKey=True to get identity public key
        result = wallet.get_public_key(
            {
                "identityKey": True,
                "reason": "Get receive address for P2PKH payment",
            }
        )
        
        # Convert to PublicKey object (same pattern as simple_wallet_example)
        public_key = PublicKey(result["publicKey"])
        
        # Generate address from public key
        network_enum = Network.TESTNET if chain == "test" else Network.MAINNET
        address = public_key.address(network=network_enum)

        # region agent log
        agent_log(
            "H1",
            "get_receive_address",
            "Derived identity address",
            {
                "wallet_id": id(wallet),
                "chain": chain,
                "address": address,
                "publicKey": result.get("publicKey"),
            },
        )
        # endregion

        return address
    except Exception as err:  # noqa: BLE001
        print(f"⚠️  Error getting address: {err}")
        import traceback
        traceback.print_exc()
        return ""


def send_wallet_payment(
    wallet_from: Wallet,
    wallet_to: Wallet,
    amount_satoshis: int,
    wallet_from_name: str,
    wallet_to_name: str,
    chain: Chain,
    services: Services | None = None,
) -> tuple[str | None, int | None, dict[str, str] | None]:
    """Send a BRC-29 wallet payment and return (txid, vout, remittance)."""

    print(
        f"\n💸 {wallet_from_name} sending {amount_satoshis} satoshis to {wallet_to_name}"
    )

    _debug_print_spendable_outputs(
        wallet_from, f"{wallet_from_name} spendable outputs (up to 5)", limit=5
    )

    sender_identity_key = wallet_from.get_public_key(
        {"identityKey": True, "reason": f"{wallet_from_name} wallet payment"}
    )["publicKey"]
    recipient_identity_key = wallet_to.get_public_key(
        {"identityKey": True, "reason": f"{wallet_to_name} wallet payment"}
    )["publicKey"]

    prefix_raw = os.urandom(16).hex()
    suffix_raw = os.urandom(8).hex()
    derivation_prefix_b64 = base64.b64encode(prefix_raw.encode("utf-8")).decode("ascii")
    derivation_suffix_b64 = base64.b64encode(suffix_raw.encode("utf-8")).decode("ascii")
    remittance = {
        "senderIdentityKey": sender_identity_key,
        "derivationPrefix": derivation_prefix_b64,
        "derivationSuffix": derivation_suffix_b64,
    }

    key_id = KeyID(derivation_prefix=prefix_raw, derivation_suffix=suffix_raw)
    locking_script = lock_for_counterparty(
        sender_private_key=wallet_from.key_deriver,
        key_id=key_id,
        recipient_public_key=recipient_identity_key,
        testnet=(chain == "test"),
    )
    locking_script_hex = locking_script.hex()

    agent_log(
        "H2",
        "send_wallet_payment",
        "Prepared wallet payment remittance",
        {
            "wallet_from_id": id(wallet_from),
            "wallet_to_id": id(wallet_to),
            "amount": amount_satoshis,
            "remittance": remittance,
            "recipientIdentityKey": recipient_identity_key,
        },
    )

    try:
        action_result = wallet_from.create_action(
            {
                "description": f"Send {amount_satoshis} satoshis to {wallet_to_name}",
                "outputs": [
                    {
                        "satoshis": amount_satoshis,
                        "lockingScript": locking_script_hex,
                        "protocol": "wallet payment",
                        "paymentRemittance": remittance,
                        "outputDescription": f"BRC29 payment to {wallet_to_name}",
                    }
                ],
                "options": {
                    "signAndProcess": True,
                    "acceptDelayedBroadcast": False,
                },
            }
        )

        print(f"\n   create_action result keys: {list(action_result.keys())}")
        destination_output_index: int | None = 0

        signable = action_result.get("signableTransaction")
        if signable is not None:
            reference = signable.get("reference")
            if not reference:
                print("❌ Missing reference in signableTransaction")
                return None, None, None

            print("✍️  Signing action...")
            print(f"   Reference: {reference}")
            signed_result = wallet_from.sign_action({"reference": reference, "accept": True})
            txid = signed_result.get("txid") or signed_result.get("txID")
            print(f"✅ Action signed and broadcast")
            print(f"   txid : {txid}")

            send_with_results = signed_result.get("sendWithResults") or []
            if send_with_results:
                for i, result in enumerate(send_with_results):
                    status = result.get("status", "unknown")
                    print(f"   Broadcast result {i+1}: {status}")
                    if "error" in result:
                        print(f"     Error: {result['error']}")

            try:
                tx_bytes = bytes(signed_result.get("tx") or [])
                if tx_bytes:
                    raw_hex = tx_bytes.hex()
                    print(f"\n   Raw transaction hex (full):")
                    print(f"   {raw_hex}")
                    _debug_print_transaction(raw_hex, "Signed transaction structure")
                    if services:
                        _debug_verify_input_scripts(raw_hex, services)
            except Exception:  # noqa: BLE001
                pass

            return txid, destination_output_index, remittance

        txid = action_result.get("txid") or action_result.get("txID")
        print(f"✅ Action created successfully")
        print(f"   txid : {txid}")

        try:
            tx_bytes = bytes(action_result.get("tx") or [])
            if tx_bytes:
                raw_hex = tx_bytes.hex()
                print(f"\n   Raw transaction hex (full):")
                print(f"   {raw_hex}")
                _debug_print_transaction(raw_hex, "Unsigned transaction structure")
                if services:
                    _debug_verify_input_scripts(raw_hex, services)
        except Exception:  # noqa: BLE001
            pass

        return txid, destination_output_index, remittance

    except ReviewActionsError as err:
        print(f"\n❌ Action review failed: {err}")
        import traceback
        traceback.print_exc()
        return None, None, None
    except Exception as err:  # noqa: BLE001
        print(f"\n❌ Create action failed: {err}")
        import traceback
        traceback.print_exc()
        return None, None, None

def prompt_internalize_received_tx(
    wallet: Wallet,
    chain: Chain,
    services: Services,
    default_txid: str,
    wallet_name: str = "Bob",
    default_output_index: int | None = None,
    payment_remittance: dict[str, str] | None = None,
) -> None:
    """Ask the user to internalize a received transaction for the wallet."""
    print("\n" + "=" * 80)
    print(f"📥 Internalize received funds for {wallet_name}")
    print("=" * 80)
    print(
        "To make the received funds spendable, internalize the transaction\n"
        "that paid this wallet (same workflow as faucet internalization)."
    )
    print()

    txid_prompt = (
        "Enter the transaction ID to internalize "
        f"(default: {default_txid}, leave blank to use default, 'skip' to ignore): "
    )
    txid_input = input(txid_prompt).strip()

    if not txid_input:
        txid_input = default_txid

    if not txid_input or txid_input.lower() == "skip":
        print(f"⏹ Skipping internalization for {wallet_name}")
        return

    if len(txid_input) != 64:
        print("⚠️  Invalid txid length. Skipping internalization.")
        return

    try:
        int(txid_input, 16)
    except ValueError:
        print("⚠️  Invalid txid hex. Skipping internalization.")
        return

    if payment_remittance:
        print("   Detected wallet payment remittance metadata for this transfer.")
        print("   Prefix/Suffix will be applied automatically during internalize.")
        print()

    default_index_text = (
        f"{default_output_index}" if default_output_index is not None else "0"
    )
    output_index_raw = input(
        f"Enter the output index that paid this wallet (default {default_index_text}): "
    ).strip()
    output_index = default_output_index if default_output_index is not None else 0
    if output_index_raw:
        try:
            output_index = int(output_index_raw)
        except ValueError:
            print("⚠️  Invalid output index. Using 0.")
            output_index = 0
        else:
            if output_index < 0:
                print("⚠️  Output index must be >= 0. Using 0.")
                output_index = 0

    if payment_remittance:
        success = internalize_wallet_payment_tx(
            wallet,
            txid_input,
            output_index,
            payment_remittance,
            services,
            chain,
            description=f"Internalize wallet payment {txid_input} for {wallet_name}",
        )
    else:
        success = internalize_standard_tx(
            wallet,
            txid_input,
            [output_index],
            services,
            chain,
            description=f"Internalize tx {txid_input} for {wallet_name}",
        )
    if success:
        new_balance = get_wallet_balance(wallet)
        print(f"   {wallet_name}'s balance after internalize: {new_balance} satoshis")


def _create_p2pkh_script(address: str) -> str:
    """Convert a P2PKH address to locking script hex.

    Uses bsv P2PKH class to create the locking script.
    """
    try:
        p2pkh = P2PKH()
        script = p2pkh.lock(address)
        script_hex = script.hex()
        # Ensure even length (pad with leading zero if needed)
        if len(script_hex) % 2 != 0:
            script_hex = "0" + script_hex
        
        # Debug: verify the script is valid P2PKH
        if not script_hex.startswith("76a914") or not script_hex.endswith("88ac"):
            print(f"⚠️  Warning: Generated script doesn't look like P2PKH: {script_hex}")
        
        return script_hex
    except Exception as err:  # noqa: BLE001
        print(f"⚠️  Error creating P2PKH script for address {address}: {err}")
        import traceback
        traceback.print_exc()
        return ""


def _debug_print_transaction(raw_hex: str, label: str) -> None:
    """Parse and print transaction details for debugging."""
    print(f"\n=== {label} ===")
    if not raw_hex:
        print("   (no raw transaction data)")
        return
    try:
        tx = Transaction.from_hex(raw_hex)
    except Exception as err:  # noqa: BLE001
        print(f"   Failed to parse transaction: {err}")
        return

    print(
        f"   Version={tx.version}, LockTime={tx.locktime}, "
        f"Inputs={len(tx.inputs)}, Outputs={len(tx.outputs)}"
    )

    for idx, tx_input in enumerate(tx.inputs):
        unlocking_hex = (
            tx_input.unlocking_script.hex() if tx_input.unlocking_script else ""
        )
        print(
            f"   Input {idx}: {tx_input.source_txid}:{tx_input.source_output_index}, "
            f"sequence={tx_input.sequence}"
        )
        if unlocking_hex:
            print(f"      unlockingScript: {unlocking_hex}")

    for idx, tx_output in enumerate(tx.outputs):
        locking_hex = tx_output.locking_script.hex() if tx_output.locking_script else ""
        print(
            f"   Output {idx}: {tx_output.satoshis} satoshis"
        )
        if locking_hex:
            print(f"      lockingScript: {locking_hex}")


def _hash160(data: bytes) -> str:
    """Compute HASH160 of the given data."""
    return hashlib.new("ripemd160", hashlib.sha256(data).digest()).hexdigest()


def _extract_pubkey_from_unlocking_script(unlocking_hex: str) -> str | None:
    """Extract public key hex from a standard P2PKH unlocking script."""
    if not unlocking_hex:
        return None
    try:
        cursor = 0
        if len(unlocking_hex) < 2:
            return None
        sig_len = int(unlocking_hex[cursor : cursor + 2], 16)
        cursor += 2 + sig_len * 2
        if cursor >= len(unlocking_hex):
            return None
        pub_len = int(unlocking_hex[cursor : cursor + 2], 16)
        cursor += 2
        pub_hex = unlocking_hex[cursor : cursor + pub_len * 2]
        if len(pub_hex) != pub_len * 2:
            return None
        return pub_hex
    except Exception:
        return None


def _extract_p2pkh_hash_from_locking(locking_hex: str) -> str | None:
    """Extract HASH160 portion from a standard P2PKH locking script."""
    if (
        locking_hex
        and locking_hex.startswith("76a914")
        and locking_hex.endswith("88ac")
        and len(locking_hex) >= 46
    ):
        return locking_hex[6:46]
    return None


def _debug_verify_input_scripts(raw_hex: str, services: Services) -> None:
    """Compare unlocking pubkeys against previous locking scripts for each input."""
    print("\n=== Input script verification ===")
    try:
        tx = Transaction.from_hex(raw_hex)
    except Exception as err:  # noqa: BLE001
        print(f"   Unable to decode transaction: {err}")
        return

    for idx, tx_input in enumerate(tx.inputs):
        src_txid = tx_input.source_txid
        vout = tx_input.source_output_index
        unlocking_hex = (
            tx_input.unlocking_script.hex() if tx_input.unlocking_script else ""
        )
        pub_hex = _extract_pubkey_from_unlocking_script(unlocking_hex)
        pub_hash = _hash160(bytes.fromhex(pub_hex)) if pub_hex else None

        expected_hash = None
        locking_hex = None
        try:
            prev_raw = services.get_raw_tx(src_txid)
            if prev_raw:
                prev_tx = Transaction.from_hex(prev_raw)
                prev_output = prev_tx.outputs[vout]
                locking_hex = (
                    prev_output.locking_script.hex()
                    if prev_output.locking_script
                    else ""
                )
                expected_hash = _extract_p2pkh_hash_from_locking(locking_hex)
        except Exception as err:  # noqa: BLE001
            print(
                f"   Input {idx}: unable to fetch previous tx {src_txid}:{vout} ({err})"
            )
            continue

        if expected_hash and pub_hash:
            status = "match" if expected_hash == pub_hash else "MISMATCH"
        elif expected_hash and not pub_hash:
            status = "no pubkey in unlocking script"
        elif pub_hash and not expected_hash:
            status = "previous output not P2PKH"
        else:
            status = "unknown"

        print(f"   Input {idx}: {src_txid}:{vout} -> status={status}")
        if pub_hex:
            print(f"      pubkey: {pub_hex}")
            print(f"      pubkey hash160: {pub_hash}")
        if locking_hex:
            print(f"      prev lockingScript: {locking_hex}")
            if expected_hash:
                print(f"      expected hash160: {expected_hash}")

        # region agent log
        agent_log(
            "H1",
            "_debug_verify_input_scripts",
            "Input verification status",
            {
                "txid": tx.txid(),
                "inputIndex": idx,
                "sourceTxid": src_txid,
                "vout": vout,
                "status": status,
                "pubHash": pub_hash,
                "expectedHash": expected_hash,
            },
        )
        # endregion


def _debug_print_spendable_outputs(wallet: Wallet, label: str, limit: int = 5) -> None:
    """Print spendable outputs for debugging."""
    print(f"\n=== {label} ===")
    try:
        outputs_result = wallet.list_outputs({"limit": limit})
    except Exception as err:  # noqa: BLE001
        print(f"   Failed to list outputs: {err}")
        return

    outputs = outputs_result.get("outputs") or []
    if not outputs:
        print("   (no outputs returned)")
        return

    for idx, output in enumerate(outputs):
        txid = output.get("txid", "unknown")
        vout = output.get("vout", output.get("outputIndex", "unknown"))
        satoshis = output.get("satoshis", "unknown")
        spent = output.get("spent", False)
        spendable = output.get("spendable", True)
        locked = output.get("locked", False)
        print(
            f"   Output {idx}: {txid}:{vout}, satoshis={satoshis}, "
            f"spent={spent}, spendable={spendable}, locked={locked}"
        )


def main() -> None:
    """Main E2E test flow."""
    print("=" * 80)
    print("🚀 E2E Test: Alice & Bob Wallets (2-Party Roundtrip)")
    print("=" * 80)
    print()

    # Load environment
    load_environment()
    chain = get_network()
    use_remote = use_storage_server()

    print(f"🟢 Network: {'Testnet' if chain == 'test' else 'Mainnet'}")
    print(f"💾 Storage: {'Remote' if use_remote else 'Local SQLite'}")
    print()

    # Create Services
    print("🔧 Setting up services...")
    services = create_services(chain)
    print("✅ Services configured (ARC priority)")
    print()

    # Create wallets
    alice, alice_root_priv = create_wallet("alice", chain, services, use_remote)
    bob, bob_root_priv = create_wallet("bob", chain, services, use_remote)
    print()

    # Display Alice's BRC-29 Faucet receive address (matching test_all_28_methods.py)
    try:
        anyone_key = PrivateKey(1).public_key()
        key_id = KeyID(
            derivation_prefix=FAUCET_DERIVATION_PREFIX,
            derivation_suffix=FAUCET_DERIVATION_SUFFIX,
        )

        # Generate BRC-29 address for Alice using address_for_self
        alice_brc29_addr_info = address_for_self(
            sender_public_key=anyone_key.hex(),
            key_id=key_id,
            recipient_private_key=alice_root_priv,
            testnet=(chain == "test"),
        )
        alice_faucet_address = alice_brc29_addr_info["address_string"]

        print("=" * 80)
        print("💧 Faucet Deposit Required")
        print("=" * 80)
        print()
        print("Send BSV to Alice's BRC-29 Faucet address:")
        print()
        print(f"   📬 Address: {alice_faucet_address}")
        print()
        print("   Faucet URLs:")
        print("     - https://testnet-faucet.bsv.dev/ (testnet)")
        print("     - https://faucet.bsv.dev/ (mainnet)")
        print()
        if chain == "test":
            print("   Testnet alternatives:")
            print("     - https://scrypt.io/faucet/")
            print("     - https://witnessonchain.com/faucet/tbsv")
        print()

        # Wait for user to deposit and confirm
        input("Press Enter once you have confirmed the transaction in the blockchain explorer...")
        print()

        # Internalize the Faucet transaction
        print("=" * 80)
        print("🔄 Internalizing Faucet Transaction (Optional)")
        print("=" * 80)
        print()
        txid_input = input(
            "Enter the faucet transaction ID (64 hex chars, or leave blank to skip): "
        ).strip()

        if not txid_input:
            print("⏹ Skipping internalization")
        elif len(txid_input) != 64:
            print("⚠️  Invalid txid length. Skipping internalization.")
        else:
            try:
                int(txid_input, 16)
            except ValueError:
                print("⚠️  Invalid hex format. Skipping internalization.")
            else:
                output_index_raw = input(
                    "Enter the output index paid to your address (default 0): "
                ).strip()
                output_index = 0
                if output_index_raw:
                    try:
                        output_index = int(output_index_raw)
                    except ValueError:
                        print("⚠️  Invalid output index. Using 0.")
                        output_index = 0
                    else:
                        if output_index < 0:
                            print("⚠️  Output index must be >= 0. Using 0.")
                            output_index = 0
                # Internalize using BRC-29 wallet payment protocol
                if not internalize_faucet_tx(
                    alice, txid_input, chain, services, output_index
                ):
                    print("⚠️  Failed to internalize transaction. Continuing anyway...")

    except Exception as err:  # noqa: BLE001
        print(f"❌ Error setting up Faucet address: {err}")
        import traceback
        traceback.print_exc()
        return

    print()
    print("=" * 80)
    print("💸 Balance Check")
    print("=" * 80)
    print()

    alice_balance = get_wallet_balance(alice)
    bob_balance = get_wallet_balance(bob)

    print(f"Alice's balance: {alice_balance} satoshis")
    print(f"Bob's balance  : {bob_balance} satoshis")
    print()

    if alice_balance < 1000:
        print("⚠️  Alice's balance is very low. Consider sending more via Faucet.")
        return

    # Alice sends 80% to Bob
    print("=" * 80)
    print("🔄 Phase 1: Alice sends 80% to Bob")
    print("=" * 80)
    print()

    alice_send_amount = int(alice_balance * 0.8)
    alice_txid, bob_destination_index, alice_remittance = send_wallet_payment(
        alice, bob, alice_send_amount, "Alice", "Bob", chain, services
    )

    if not alice_txid:
        print("❌ Alice's transfer failed")
        return

    print(f"✅ Alice's transfer complete: {alice_txid}")
    print()

    # Wait longer to ensure the transaction propagates before Bob internalizes
    print("Waiting 20 seconds for transaction propagation before Bob internalizes...")
    import time

    time.sleep(20)

    prompt_internalize_received_tx(
        bob,
        chain,
        services,
        alice_txid,
        "Bob",
        default_output_index=bob_destination_index,
        payment_remittance=alice_remittance,
    )

    # Wait a bit before checking Bob's balance
    print("Waiting a few more seconds before checking Bob's balance...")
    time.sleep(3)

    bob_balance_after = get_wallet_balance(bob)
    print(f"Bob's updated balance: {bob_balance_after} satoshis")
    print()

    if bob_balance_after < alice_send_amount + 1000:
        print("⚠️  Bob did not receive funds. Proceeding with return transfer anyway...")

    # Bob sends 80% back to Alice
    print("=" * 80)
    print("🔄 Phase 2: Bob sends 80% back to Alice")
    print("=" * 80)
    print()

    bob_send_amount = int(bob_balance_after * 0.8)
    bob_txid, alice_destination_index, bob_remittance = send_wallet_payment(
        bob, alice, bob_send_amount, "Bob", "Alice", chain, services
    )

    if not bob_txid:
        print("❌ Bob's transfer failed")
        print()
        print("=" * 80)
        print("📊 Final Balance Summary (incomplete)")
        print("=" * 80)
        print()
        alice_final = get_wallet_balance(alice)
        bob_final = get_wallet_balance(bob)
        print(f"Alice's balance: {alice_final} satoshis")
        print(f"Bob's balance  : {bob_final} satoshis")
        print()
        print(f"Alice → Bob transaction: {alice_txid}")
        return

    print(f"✅ Bob's transfer complete: {bob_txid}")
    print()

    print("Waiting 20 seconds for transaction propagation before Alice internalizes...")
    time.sleep(20)

    prompt_internalize_received_tx(
        alice,
        chain,
        services,
        bob_txid,
        "Alice",
        default_output_index=alice_destination_index,
        payment_remittance=bob_remittance,
    )

    # Final balance summary
    print("=" * 80)
    print("📊 Final Balance Summary")
    print("=" * 80)
    print()

    alice_final = get_wallet_balance(alice)
    bob_final = get_wallet_balance(bob)

    print(f"Alice's final balance: {alice_final} satoshis")
    print(f"Bob's final balance  : {bob_final} satoshis")
    print()

    print("=" * 80)
    print("✅ E2E Test Complete!")
    print("=" * 80)
    print()
    print("Transaction IDs for verification:")
    print(f"  Alice → Bob: {alice_txid}")
    print(f"  Bob → Alice: {bob_txid}")
    print()
    print("You can verify these transactions on the blockchain explorer:")
    if chain == "test":
        print("  https://whatsonchain.com/")
    else:
        print("  https://www.bsvexplorer.io/")


if __name__ == "__main__":
    main()

