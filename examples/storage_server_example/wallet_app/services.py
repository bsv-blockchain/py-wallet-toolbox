"""
Services for wallet_app.

This module provides service layer integration with py-wallet-toolbox,
specifically the StorageServer for handling JSON-RPC requests.

Equivalent to TypeScript: ts-wallet-toolbox/src/storage/remoting/StorageServer.ts

Also provides server wallet for BRC-104 authentication middleware.
Reference: go-wallet-toolbox/pkg/storage/server.go
"""

import logging
import os
from typing import Optional

from sqlalchemy import create_engine
from bsv_wallet_toolbox.rpc import StorageServer
from bsv_wallet_toolbox.storage import StorageProvider
from bsv_wallet_toolbox.services import WalletServices
from bsv_wallet_toolbox.wallet import Wallet as ToolboxWallet
from bsv_wallet_toolbox.sdk.privileged_key_manager import PrivilegedKeyManager
from bsv.keys import PrivateKey
from bsv.wallet import KeyDeriver

logger = logging.getLogger(__name__)

# Global StorageServer instance
_storage_server: Optional[StorageServer] = None

# Global server wallet for authentication
_server_wallet: Optional[ToolboxWallet] = None

# Server private key (from examples-config.yaml or environment)
# NOTE: This must be DIFFERENT from the client's private key!
# The default key was the same as the client, causing authentication failures.
# New server key (hex): b4a609a63dc91bebf3823a8ff2470c23e2da9af18f5138990ef390373f8969d7
# New server public key: 0320295654f4c8d4d2bc2ed79b0169f7584e62519b17f6a829adebe400316c90d6
SERVER_PRIVATE_KEY = os.environ.get(
    'SERVER_PRIVATE_KEY',
    'b4a609a63dc91bebf3823a8ff2470c23e2da9af18f5138990ef390373f8969d7'  # Different from client's key
)


def get_server_wallet() -> ToolboxWallet:
    """
    Get or create the server wallet for BRC-104 authentication.
    
    This wallet is used by the BSV auth middleware to sign and verify
    authentication messages.
    
    Reference: go-wallet-toolbox/pkg/storage/server.go (Server.Handler())
    
    Returns:
        ToolboxWallet: Server wallet instance for authentication
    """
    global _server_wallet
    
    if _server_wallet is None:
        logger.info("Initializing server wallet for BRC-104 authentication")
        
        try:
            # Create server private key from hex
            private_key = PrivateKey.from_hex(SERVER_PRIVATE_KEY)
            identity_key = private_key.public_key()
            
            logger.info(f"Server identity key: {identity_key.hex()}")
            
            # Create wallet components
            key_deriver = KeyDeriver(private_key)
            privileged_manager = PrivilegedKeyManager(private_key)
            
            # Create server wallet (without storage - only for auth)
            _server_wallet = ToolboxWallet(
                chain='test',
                key_deriver=key_deriver,
                storage_provider=None,  # Server wallet doesn't need storage
                privileged_key_manager=privileged_manager,
            )
            
            # Debug: Check if proto was initialized
            logger.info(f"Server wallet proto: {_server_wallet.proto}")
            if _server_wallet.proto is None:
                logger.error("Server wallet proto is None! verify_signature will fail!")
            else:
                logger.info(f"Server wallet proto initialized: {type(_server_wallet.proto)}")
            
            logger.info("Server wallet initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize server wallet: {e}")
            raise
    
    return _server_wallet


def get_storage_server() -> StorageServer:
    """
    Get or create the global StorageServer instance.

    This function ensures we have a single StorageServer instance
    that is configured with StorageProvider methods.

    Returns:
        StorageServer: Configured storage server instance
    """
    global _storage_server

    if _storage_server is None:
        logger.info("Initializing StorageServer with StorageProvider")

        # Initialize StorageProvider with SQLite database
        # Create database file in the project directory
        db_path = os.path.join(os.path.dirname(__file__), '..', 'wallet_storage.sqlite3')
        db_url = f'sqlite:///{db_path}'

        # Create SQLAlchemy engine for SQLite
        engine = create_engine(db_url, echo=False)  # Set echo=True for SQL logging in development

        # Initialize StorageProvider with SQLite configuration
        storage_provider = StorageProvider(
            engine=engine,
            chain='test',  # Use testnet for development
            storage_identity_key='django-wallet-server'
        )

        # Initialize the database by calling make_available
        # This creates tables and sets up the storage
        try:
            storage_provider.make_available()
            logger.info("StorageProvider database initialized successfully")
        except Exception as e:
            logger.warning(f"StorageProvider make_available failed (may already be initialized): {e}")

        # Initialize WalletServices for broadcast functionality
        try:
            wallet_services = WalletServices(chain='test')
            storage_provider.set_services(wallet_services)
            logger.info("WalletServices initialized for testnet (broadcast enabled)")
        except Exception as e:
            logger.warning(f"WalletServices initialization failed: {e}")

        # Create StorageServer with StorageProvider auto-registration
        _storage_server = StorageServer(storage_provider=storage_provider)

        logger.info(f"StorageServer initialized with SQLite database: {db_path}")

    return _storage_server


# Backward compatibility alias
def get_json_rpc_server() -> StorageServer:
    """Backward compatibility alias for get_storage_server()."""
    return get_storage_server()


def reset_storage_server():
    """
    Reset the global StorageServer instance.

    Useful for testing or reconfiguration.
    """
    global _storage_server
    _storage_server = None
    logger.info("StorageServer instance reset")


# Backward compatibility alias
def reset_json_rpc_server():
    """Backward compatibility alias for reset_storage_server()."""
    reset_storage_server()
