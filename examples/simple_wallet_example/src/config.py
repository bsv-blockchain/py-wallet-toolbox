"""Configuration helpers for the BRC-100 demo."""

from __future__ import annotations

import json
import os
from typing import TYPE_CHECKING, Literal

from bsv.hd.bip32 import bip32_derive_xprv_from_mnemonic
from bsv.hd.bip39 import mnemonic_from_entropy
from bsv.wallet import KeyDeriver
from dotenv import load_dotenv
from sqlalchemy import create_engine

from bsv_wallet_toolbox.rpc import StorageClient
from bsv_wallet_toolbox.storage import StorageProvider

if TYPE_CHECKING:
    from bsv_wallet_toolbox import Wallet

# Load environment variables from .env if present
load_dotenv()

# Allowed network names
Chain = Literal["main", "test"]

# Remote storage endpoints (Babbage)
REMOTE_STORAGE_URLS = {
    "main": "https://storage.babbage.systems",
    "test": "https://staging-storage.babbage.systems",
}

# Wallet-infra server endpoint (default localhost)
DEFAULT_WALLET_INFRA_URL = "http://localhost:8080"


def get_network() -> Chain:
    """Read network selection from the environment."""
    network = os.getenv("BSV_NETWORK", "test").lower()

    if network not in ("test", "main"):
        print(f"⚠️  Invalid BSV_NETWORK '{network}'. Falling back to 'test'.")
        return "test"

    return network  # type: ignore


def get_mnemonic() -> str | None:
    """Return the mnemonic string from the environment if set."""
    return os.getenv("BSV_MNEMONIC")


def get_dev_keys() -> dict[str, str] | None:
    """Return the dev keys from environment if set."""
    dev_keys_json = os.getenv("DEV_KEYS")
    if dev_keys_json:
        try:
            return json.loads(dev_keys_json)
        except json.JSONDecodeError:
            pass
    return None


def get_test_identity_key() -> str | None:
    """Return the test identity key from environment if set."""
    return os.getenv("MY_TEST_IDENTITY")


def get_key_deriver() -> KeyDeriver:
    """Create a KeyDeriver from the configured mnemonic/keys (or generate one)."""
    # For wallet-infra testing, prefer random keys like walletInfraNoEnv example
    # The predefined .env keys may not be authenticated with wallet-infra
    if use_wallet_infra():
        print("🏗️  wallet-infra mode: using random key (like walletInfraNoEnv)...")
        # Generate a new random key for wallet-infra testing
        from bsv.keys import PrivateKey

        root_private_key = PrivateKey()
        return KeyDeriver(root_private_key=root_private_key)

    # First try to use predefined dev keys (for other testing)
    test_identity_key = get_test_identity_key()
    dev_keys = get_dev_keys()

    if test_identity_key and dev_keys and test_identity_key in dev_keys:
        print(f"🔑 Using predefined test identity key: {test_identity_key[:16]}...")
        root_key_hex = dev_keys[test_identity_key]
        from bsv.keys import PrivateKey

        root_private_key = PrivateKey.from_hex(root_key_hex)
        return KeyDeriver(root_private_key=root_private_key)

    # Fall back to mnemonic-based key derivation
    mnemonic = get_mnemonic()

    if not mnemonic:
        print("⚠️  No mnemonic configured. Creating a brand new wallet...")
        print()

        mnemonic = mnemonic_from_entropy(entropy=None, lang="en")

        print("=" * 70)
        print("🔑 Generated mnemonic (12 words):")
        print("=" * 70)
        print()
        print(f"   {mnemonic}")
        print()
        print("=" * 70)
        print("⚠️  IMPORTANT: store this mnemonic securely before proceeding.")
        print("=" * 70)
        print()
        print("💡 To reuse this wallet, add the line below to your .env file:")
        print(f"   BSV_MNEMONIC={mnemonic}")
        print()
        print("=" * 70)
        print()

    xprv = bip32_derive_xprv_from_mnemonic(
        mnemonic=mnemonic,
        lang="en",
        passphrase="",
        prefix="mnemonic",
        path="m/0",
    )

    return KeyDeriver(root_private_key=xprv.private_key())


def get_network_display_name(chain: Chain) -> str:
    """Helper for printing human-friendly network names."""
    return "Mainnet (production)" if chain == "main" else "Testnet (safe)"


def print_network_info(chain: Chain) -> None:
    """Display current network mode to the console."""
    display_name = get_network_display_name(chain)
    emoji = "🔴" if chain == "main" else "🟢"

    print(f"{emoji} Network: {display_name}")

    if chain == "main":
        print("⚠️  MAINNET MODE – you are dealing with real BSV funds.")


def use_remote_storage() -> bool:
    """Check if remote storage should be used (via USE_REMOTE_STORAGE env var)."""
    return os.getenv("USE_REMOTE_STORAGE", "").lower() in ("1", "true", "yes")


def use_wallet_infra() -> bool:
    """Check if wallet-infra should be used (via USE_WALLET_INFRA env var)."""
    return os.getenv("USE_WALLET_INFRA", "").lower() in ("1", "true", "yes")


def bypass_wallet_infra_auth() -> bool:
    """Check if wallet-infra authentication should be bypassed for testing."""
    return os.getenv("BYPASS_WALLET_INFRA_AUTH", "").lower() in ("1", "true", "yes")


def get_wallet_infra_url() -> str:
    """Get the wallet-infra server URL from environment or default."""
    return os.getenv("WALLET_INFRA_URL", DEFAULT_WALLET_INFRA_URL)


def get_remote_storage_url(network: Chain) -> str:
    """Get the remote storage server URL for the given network."""
    return REMOTE_STORAGE_URLS[network]


def get_storage_provider(network: Chain) -> StorageProvider:
    """Create a SQLite-backed StorageProvider."""
    db_file = f"wallet_{network}.db"

    print(f"💾 Using database file: {db_file}")

    engine = create_engine(f"sqlite:///{db_file}")

    storage = StorageProvider(
        engine=engine,
        chain=network,
        storage_identity_key=f"{network}-wallet",
    )

    try:
        storage.make_available()
        print("✅ Storage tables are ready.")
    except Exception as e:
        print(f"⚠️  Storage initialization warning: {e}")

    return storage


def get_remote_storage_client(wallet: Wallet, network: Chain) -> StorageClient:
    """Create a StorageClient for Babbage remote storage.

    Args:
        wallet: Wallet instance for BRC-104 authentication
        network: Network to connect to ('main' or 'test')

    Returns:
        StorageClient connected to the appropriate Babbage storage server

    Note:
        - mainnet: https://storage.babbage.systems
        - testnet: https://staging-storage.babbage.systems
    """
    endpoint_url = get_remote_storage_url(network)

    print(f"🌐 Connecting to remote storage: {endpoint_url}")

    client = StorageClient(wallet, endpoint_url)

    return client


def get_wallet_infra_client(wallet: Wallet) -> StorageClient:
    """Create a StorageClient for wallet-infra server.

    Args:
        wallet: Wallet instance for BRC-104 authentication

    Returns:
        StorageClient connected to the wallet-infra server

    Note:
        - Uses WALLET_INFRA_URL environment variable
        - Default: http://localhost:8080
    """
    endpoint_url = get_wallet_infra_url()

    print(f"🏗️  Connecting to wallet-infra: {endpoint_url}")

    client = StorageClient(wallet, endpoint_url)

    return client
