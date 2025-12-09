"""
Services for wallet_app.

This module provides service layer integration with py-wallet-toolbox,
specifically the StorageServer for handling JSON-RPC requests.

Equivalent to TypeScript: ts-wallet-toolbox/src/storage/remoting/StorageServer.ts
"""

import logging
import os
from typing import Optional

from sqlalchemy import create_engine
from bsv_wallet_toolbox.rpc import StorageServer
from bsv_wallet_toolbox.storage import StorageProvider
from bsv_wallet_toolbox.services import WalletServices

logger = logging.getLogger(__name__)

# Global StorageServer instance
_storage_server: Optional[StorageServer] = None


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
