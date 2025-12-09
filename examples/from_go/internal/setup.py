"""Example setup utilities.

Replicates the functionality of Go's internal/example_setup package.
Handles configuration loading, wallet initialization, and environment setup.

Supports both local storage (SQLite) and remote storage (JSON-RPC over HTTP).
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Tuple, Union

import yaml
from dotenv import load_dotenv

from bsv.keys import PrivateKey, PublicKey
from bsv.wallet import KeyDeriver
from bsv_wallet_toolbox.sdk.privileged_key_manager import PrivilegedKeyManager
from bsv_wallet_toolbox.wallet import Wallet as ToolboxWallet
from bsv_wallet_toolbox.storage.provider import StorageProvider
from bsv_wallet_toolbox.storage.db import create_sqlite_engine

from . import show
from .simple_storage_client import SimpleStorageClient

# Load environment variables from .env file
load_dotenv()


def normalize_chain(network: str) -> str:
    """Convert environment network string to wallet chain literal."""
    net = (network or "").lower()
    if net.startswith("main"):
        return "main"
    return "test"


@dataclass
class UserConfig:
    identity_key: str
    private_key: str

    def verify(self) -> None:
        if not self.identity_key:
            raise ValueError("identity key value is required")
        if not self.private_key:
            raise ValueError("private key value is required")


@dataclass
class SetupConfig:
    network: str = "testnet"
    server_url: str = ""
    server_private_key: str = ""
    alice: UserConfig = field(default_factory=lambda: UserConfig("", ""))
    bob: UserConfig = field(default_factory=lambda: UserConfig("", ""))

    def validate(self) -> None:
        if not self.network:
            raise ValueError("network is required")
        if not self.server_private_key:
            raise ValueError("server_private_key is required")
        self.alice.verify()
        self.bob.verify()


@dataclass
class Environment:
    bsv_network: str
    server_url: str


@dataclass
class Setup:
    environment: Environment
    identity_key: PublicKey
    private_key: PrivateKey
    server_private_key: str

    def create_wallet(self) -> Tuple[ToolboxWallet, Callable[[], None]]:
        """Create a new wallet for the user.

        Returns:
            Tuple containing the wallet instance and a cleanup function.

        Supports both local storage (SQLite) and remote storage (JSON-RPC client).
        When server_url is configured, uses StorageClient for remote storage.
        """
        # In Python, we don't need a factory pattern like Go because we can pass the storage provider directly
        # or construct the wallet with the appropriate storage.
        # However, to match Go's behavior (switching between local/remote), we'll do logic here.

        storage: Union[StorageProvider, StorageClient]
        
        if self.environment.server_url:
            show.info("Using remote storage", self.environment.server_url)
            
            # Use SimpleStorageClient for testing (no authentication required)
            # For production, use the full StorageClient with AuthFetch
            storage = SimpleStorageClient(
                endpoint_url=self.environment.server_url,
                timeout=30.0,
            )
            
            show.info("Remote storage connected", self.environment.server_url)
        else:
            sqlite_file = "wallet.db"  # Default for local examples
            show.info("Using local storage", sqlite_file)
            
            # Create local storage provider
            engine = create_sqlite_engine(sqlite_file)
            # Use default storage identity key for examples, or generate one?
            # StorageProvider needs identity_key
            storage = StorageProvider(
                engine=engine,
                chain=self.environment.bsv_network,
                storage_identity_key=self.identity_key.hex()
            )
            
            # Setup initial storage state if needed (e.g. creating tables is handled by provider)
            # Go's CreateLocalStorage also inserts the Master Certificate based on ServerPrivateKey
            # We might need to replicate that logic here or in a helper.
            
        # Initialize Wallet components (KeyDeriver + PrivilegedKeyManager)
        chain = normalize_chain(self.environment.bsv_network)
        key_deriver = KeyDeriver(self.private_key)
        privileged_manager = PrivilegedKeyManager(self.private_key)

        user_wallet = ToolboxWallet(
            chain=chain,
            key_deriver=key_deriver,
            storage_provider=storage,
            privileged_key_manager=privileged_manager,
        )
        
        # Cleanup function to close storage connection
        def cleanup():
            if hasattr(storage, "close"):
                storage.close()
            # Also remove db file if it's a temporary test run? 
            # Go example doesn't seem to delete it automatically in cleanup based on snippet,
            # but `userWallet.Close` is called.
        show.info("CreateWallet", self.identity_key.hex())
        return user_wallet, cleanup


def get_config_file_path() -> str:
    """Get the absolute path to the config file."""
    # Assuming running from project root or similar structure
    # We'll try to locate examples-config.yaml relative to this file
    current_dir = Path(__file__).parent.parent
    return str(current_dir / "examples-config.yaml")


def generate_user_config() -> UserConfig:
    """Generate a new user configuration with random keys."""
    priv_key = PrivateKey()
    return UserConfig(
        identity_key=priv_key.public_key().hex(),
        private_key=priv_key.hex(),
    )


def generate_config() -> SetupConfig:
    """Generate a new setup configuration with default values and random keys."""
    alice = generate_user_config()
    bob = generate_user_config()
    server_priv_key = PrivateKey()

    cfg = SetupConfig(
        network="testnet",
        server_url="",
        server_private_key=server_priv_key.hex(),
        alice=alice,
        bob=bob,
    )

    config_path = get_config_file_path()
    with open(config_path, "w") as f:
        # Convert dataclass to dict for yaml dump
        data = {
            "network": cfg.network,
            "server_url": cfg.server_url,
            "server_private_key": cfg.server_private_key,
            "alice": {
                "identity_key": cfg.alice.identity_key,
                "private_key": cfg.alice.private_key,
            },
            "bob": {
                "identity_key": cfg.bob.identity_key,
                "private_key": cfg.bob.private_key,
            },
        }
        yaml.dump(data, f)

    return cfg


def load_config() -> SetupConfig:
    """Load configuration from examples-config.yaml."""
    config_path = get_config_file_path()

    if not os.path.exists(config_path):
        show.info("Config file not found, generating new configuration", config_path)
        return generate_config()

    with open(config_path, "r") as f:
        data = yaml.safe_load(f)

    cfg = SetupConfig(
        network=data.get("network", "testnet"),
        server_url=data.get("server_url", ""),
        server_private_key=data.get("server_private_key", ""),
        alice=UserConfig(
            identity_key=data.get("alice", {}).get("identity_key", ""),
            private_key=data.get("alice", {}).get("private_key", ""),
        ),
        bob=UserConfig(
            identity_key=data.get("bob", {}).get("identity_key", ""),
            private_key=data.get("bob", {}).get("private_key", ""),
        ),
    )
    cfg.validate()
    return cfg


def create_alice() -> Setup:
    """Create a Setup instance for Alice."""
    try:
        cfg = load_config()
    except Exception as e:
        raise RuntimeError(f"Failed to load config: {e}")

    private_key = PrivateKey.from_hex(cfg.alice.private_key)
    identity_key = private_key.public_key()

    if identity_key.hex() != cfg.alice.identity_key:
        raise ValueError("Identity key does not match the public key derived from private key")

    return Setup(
        environment=Environment(
            bsv_network=cfg.network,
            server_url=cfg.server_url,
        ),
        identity_key=identity_key,
        private_key=private_key,
        server_private_key=cfg.server_private_key,
    )

