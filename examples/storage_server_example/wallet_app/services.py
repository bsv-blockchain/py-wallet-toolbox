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
from pathlib import Path
from typing import Optional

from sqlalchemy import create_engine

# Initialize logger first
logger = logging.getLogger(__name__)

# Try to load .env file if python-dotenv is available
try:
    from dotenv import load_dotenv
    # Load .env file from the project root (storage_server_example directory)
    env_path = Path(__file__).parent.parent / '.env'
    if env_path.exists():
        load_dotenv(env_path)
        logger.info(f"Loaded .env file from: {env_path}")
    else:
        logger.debug(f".env file not found at: {env_path}")
except ImportError:
    # python-dotenv not installed - try manual .env loading
    env_path = Path(__file__).parent.parent / '.env'
    if env_path.exists():
        logger.info(f"Loading .env file manually from: {env_path}")
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    # Strip quotes and whitespace from value
                    value = value.strip()
                    # Remove surrounding quotes if present
                    if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
                        value = value[1:-1]
                    value = value.strip()
                    # Only set if not already in environment
                    if key not in os.environ:
                        os.environ[key] = value
                        logger.debug(f"Loaded from .env: {key} (length: {len(value)})")
    else:
        logger.debug(f".env file not found at: {env_path}")
except Exception as e:
    logger.warning(f"Failed to load .env file: {e}")

from bsv_wallet_toolbox.rpc import StorageServer
from bsv_wallet_toolbox.storage import StorageProvider
from bsv_wallet_toolbox.services import Services
from bsv_wallet_toolbox.wallet import Wallet as ToolboxWallet
from bsv_wallet_toolbox.sdk.privileged_key_manager import PrivilegedKeyManager
from bsv.keys import PrivateKey
from bsv.wallet import KeyDeriver

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

# Chain configuration (default to testnet for development)
CHAIN = os.environ.get('CHAIN', 'test')  # 'main' or 'test'


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
                chain=CHAIN,
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
            chain=CHAIN,
            storage_identity_key='django-wallet-server'
        )

        # Initialize the database by calling make_available
        # This creates tables and sets up the storage
        try:
            storage_provider.make_available()
            logger.info("StorageProvider database initialized successfully")
        except Exception as e:
            logger.warning(f"StorageProvider make_available failed (may already be initialized): {e}")

        # Initialize Services for broadcast functionality
        try:
            from bsv_wallet_toolbox.services import create_default_options
            
            # Create services options with optional API keys from environment
            services_options = create_default_options(CHAIN)
            
            # Optional: Configure ARC API keys from environment variables
            # Check multiple possible environment variable names
            # Debug: log which env vars are available
            env_vars_checked = ['TAAL_ARC_API_KEY', 'ARC_API_KEY']
            if CHAIN == 'test':
                env_vars_checked.append('TEST_TAAL_API_KEY')
            else:
                env_vars_checked.append('MAIN_TAAL_API_KEY')
            
            logger.info(f"Checking for ARC API key in environment variables: {env_vars_checked}")
            # Debug: show all environment variables that might be relevant
            all_env_vars = {k: v for k, v in os.environ.items() if 'TAAL' in k.upper() or 'ARC' in k.upper()}
            if all_env_vars:
                logger.info(f"  Found relevant environment variables: {list(all_env_vars.keys())}")
            else:
                logger.warning("  No environment variables found containing 'TAAL' or 'ARC'")
            
            for var_name in env_vars_checked:
                value = os.environ.get(var_name)
                if value:
                    logger.info(f"  Found {var_name}: {'*' * min(len(value), 8)}... (length: {len(value)})")
                else:
                    logger.info(f"  {var_name}: not set")
            
            arc_api_key = (
                os.environ.get('TAAL_ARC_API_KEY') or
                os.environ.get('ARC_API_KEY') or
                (os.environ.get('TEST_TAAL_API_KEY') if CHAIN == 'test' else None) or
                (os.environ.get('MAIN_TAAL_API_KEY') if CHAIN == 'main' else None)
            )
            if arc_api_key:
                # Strip whitespace from API key (common issue with .env files)
                arc_api_key = arc_api_key.strip()
                services_options['arcApiKey'] = arc_api_key
                logger.info(f"ARC TAAL API key configured from environment (length: {len(arc_api_key)})")
                logger.info(f"  API key in services_options: {'set' if services_options.get('arcApiKey') else 'NOT SET'}")
                logger.debug(f"  API key value (first 8 chars): {arc_api_key[:8]}... (last 4 chars: ...{arc_api_key[-4:]})")
                # Note: If you get "authorization key not found" errors, verify:
                # 1. The API key is valid and active in TAAL dashboard
                # 2. The API key is enabled for the testnet endpoint (https://arc-test.taal.com)
                # 3. The API key format matches TAAL's requirements
            else:
                logger.warning("ARC TAAL API key not configured - broadcasting may fail with authentication errors")
                logger.warning(f"  Set TAAL_ARC_API_KEY, ARC_API_KEY, or {'TEST_TAAL_API_KEY' if CHAIN == 'test' else 'MAIN_TAAL_API_KEY'} environment variable to enable ARC broadcasting")
                logger.warning(f"  Current CHAIN setting: {CHAIN}")
            
            arc_gorillapool_key = os.environ.get('ARC_GORILLAPOOL_API_KEY')
            if arc_gorillapool_key:
                services_options['arcGorillaPoolApiKey'] = arc_gorillapool_key
                logger.info("ARC GorillaPool API key configured from environment")
            else:
                logger.info("ARC GorillaPool: No API key required (public endpoint)")
            
            bitails_key = os.environ.get('BITAILS_API_KEY')
            if bitails_key:
                services_options['bitailsApiKey'] = bitails_key
                logger.info("Bitails API key configured from environment")
            
            # Debug: log what's in services_options for ARC
            logger.info(f"Services options ARC config: arcUrl={services_options.get('arcUrl')}, arcApiKey={'set' if services_options.get('arcApiKey') else 'NOT SET'}")
            
            wallet_services = Services(services_options)  # Use configured options
            storage_provider.set_services(wallet_services)
            chain_name = 'mainnet' if CHAIN == 'main' else 'testnet'
            logger.info(f"Services initialized for {chain_name} (broadcast enabled)")
            
            # Verify services are actually set and check API key configuration
            try:
                verify_services = storage_provider.get_services()
                logger.info(f"Services verification: {type(verify_services).__name__} is configured")
                if hasattr(verify_services, 'arc_taal') and verify_services.arc_taal:
                    logger.info("ARC TAAL: configured")
                    # Check if API key is actually set in the ARC provider
                    if hasattr(verify_services.arc_taal, 'api_key'):
                        arc_key = verify_services.arc_taal.api_key
                        if arc_key:
                            logger.info(f"  ARC TAAL API key: {'*' * min(len(arc_key), 8)}... (length: {len(arc_key)})")
                        else:
                            logger.warning("  ARC TAAL API key: NOT SET - will fail with 401")
                    else:
                        logger.warning("  ARC TAAL: api_key attribute not found")
                else:
                    logger.info("ARC TAAL: not configured")
                if hasattr(verify_services, 'arc_gorillapool'):
                    gp_status = 'configured' if verify_services.arc_gorillapool else 'not configured'
                    logger.info(f"ARC GorillaPool: {gp_status}")
                if hasattr(verify_services, 'bitails'):
                    bitails_status = 'configured' if verify_services.bitails else 'not configured'
                    logger.info(f"Bitails: {bitails_status}")
            except Exception as verify_err:
                logger.error(f"Services verification failed: {verify_err}", exc_info=True)
        except Exception as e:
            logger.error(f"Services initialization failed: {e}", exc_info=True)
            logger.warning("Broadcasting will not be available - transactions will be marked as 'sending' for retry")

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
