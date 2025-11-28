"""Configuration helpers for the BRC-100 demo."""

import os
from typing import Literal

from bsv.hd.bip32 import bip32_derive_xprv_from_mnemonic
from bsv.hd.bip39 import mnemonic_from_entropy
from bsv.wallet import KeyDeriver
from bsv_wallet_toolbox.storage import StorageProvider
from dotenv import load_dotenv
from sqlalchemy import create_engine

# Load environment variables from .env if present
load_dotenv()

# Allowed network names
Chain = Literal["main", "test"]


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


def get_key_deriver() -> KeyDeriver:
    """Create a KeyDeriver from the configured mnemonic (or generate one)."""
    mnemonic = get_mnemonic()
    
    if not mnemonic:
        print("⚠️  No mnemonic configured. Creating a brand new wallet...")
        print()
        
        mnemonic = mnemonic_from_entropy(entropy=None, lang='en')
        
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
        lang='en',
        passphrase='',
        prefix='mnemonic',
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

