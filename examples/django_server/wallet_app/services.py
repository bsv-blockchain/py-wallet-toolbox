"""
Services for wallet_app.

This module provides service layer integration with py-wallet-toolbox,
specifically the JsonRpcServer for handling JSON-RPC requests.
"""

import logging
import os
from typing import Optional

from sqlalchemy import create_engine
from bsv_wallet_toolbox.rpc import JsonRpcServer
from bsv_wallet_toolbox.storage import StorageProvider

logger = logging.getLogger(__name__)

# Global JsonRpcServer instance
_json_rpc_server: Optional[JsonRpcServer] = None


def get_json_rpc_server() -> JsonRpcServer:
    """
    Get or create the global JsonRpcServer instance.

    This function ensures we have a single JsonRpcServer instance
    that is configured with StorageProvider methods.

    Returns:
        JsonRpcServer: Configured JSON-RPC server instance
    """
    global _json_rpc_server

    if _json_rpc_server is None:
        logger.info("Initializing JsonRpcServer with StorageProvider")

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

        # Create JsonRpcServer with StorageProvider auto-registration
        _json_rpc_server = JsonRpcServer(storage_provider=storage_provider)

        logger.info(f"JsonRpcServer initialized with SQLite database: {db_path}")

    return _json_rpc_server


def reset_json_rpc_server():
    """
    Reset the global JsonRpcServer instance.

    Useful for testing or reconfiguration.
    """
    global _json_rpc_server
    _json_rpc_server = None
    logger.info("JsonRpcServer instance reset")
