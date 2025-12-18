#!/usr/bin/env python3
"""Simple Flask-based Storage Server for testing remote storage.

This server provides a JSON-RPC 2.0 endpoint that wraps a local StorageProvider,
enabling wallet clients to use remote storage over HTTP.

Usage:
    python storage_server.py

The server will start on http://localhost:5000/wallet

Features:
    - JSON-RPC 2.0 protocol compliance
    - Wraps local StorageProvider (SQLite)
    - Auto-registers all StorageProvider methods
    - Supports concurrent requests

To test with wallet examples:
    1. Start this server: python storage_server.py
    2. Update examples-config.yaml: server_url: "http://localhost:5000/wallet"
    3. Run wallet examples as usual
"""

import logging
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from flask import Flask, jsonify, request

from bsv.keys import PrivateKey
from bsv_wallet_toolbox.rpc.storage_server import StorageServer
from bsv_wallet_toolbox.storage.db import create_sqlite_engine
from bsv_wallet_toolbox.storage.provider import StorageProvider

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# Configuration
SERVER_HOST = "0.0.0.0"
SERVER_PORT = 5000
DATABASE_FILE = "server_wallet.db"  # Separate DB for server
NETWORK = "testnet"


def create_app() -> Flask:
    """Create and configure the Flask application.
    
    Returns:
        Configured Flask application with JSON-RPC endpoint
    """
    app = Flask(__name__)
    
    # Generate or load server identity key
    # For production, this should be loaded from secure storage
    server_private_key = PrivateKey()
    server_identity_key = server_private_key.public_key().hex()
    logger.info(f"Server identity key: {server_identity_key}")
    
    # Create local storage provider (SQLite)
    logger.info(f"Initializing storage: {DATABASE_FILE}")
    engine = create_sqlite_engine(DATABASE_FILE)
    
    storage_provider = StorageProvider(
        engine=engine,
        chain=NETWORK,
        storage_identity_key=server_identity_key,
    )
    
    # Initialize database tables
    logger.info("Initializing database tables...")
    storage_provider.make_available()
    
    # Create StorageServer with auto-registered methods
    rpc_server = StorageServer(storage_provider=storage_provider)
    
    # Log registered methods
    methods = rpc_server.get_registered_methods()
    logger.info(f"Registered {len(methods)} JSON-RPC methods:")
    for method in methods:
        logger.debug(f"  - {method}")
    
    @app.route("/wallet", methods=["POST"])
    def handle_wallet_request():
        """Handle JSON-RPC 2.0 requests.
        
        Request body should be a valid JSON-RPC 2.0 request:
        {
            "jsonrpc": "2.0",
            "method": "createAction",
            "params": [...],
            "id": 1
        }
        """
        try:
            request_data = request.get_json()
            
            if request_data is None:
                return jsonify({
                    "jsonrpc": "2.0",
                    "error": {
                        "code": -32700,
                        "message": "Parse error: Invalid JSON"
                    },
                    "id": None
                }), 400
            
            # Check for batch request
            if isinstance(request_data, list):
                response = rpc_server.handle_json_rpc_batch(request_data)
            else:
                response = rpc_server.handle_json_rpc_request(request_data)
            
            return jsonify(response)
            
        except Exception as e:
            logger.error(f"Unexpected error: {e}", exc_info=True)
            return jsonify({
                "jsonrpc": "2.0",
                "error": {
                    "code": -32603,
                    "message": f"Internal error: {str(e)}"
                },
                "id": None
            }), 500
    
    @app.route("/health", methods=["GET"])
    def health_check():
        """Health check endpoint."""
        return jsonify({
            "status": "ok",
            "methods": len(methods),
            "database": DATABASE_FILE,
            "network": NETWORK,
        })
    
    @app.route("/", methods=["GET"])
    def index():
        """Root endpoint with server info."""
        return jsonify({
            "name": "BSV Wallet Storage Server",
            "version": "1.0.0",
            "endpoint": "/wallet",
            "health": "/health",
            "methods": methods,
            "protocol": "JSON-RPC 2.0",
        })
    
    return app


def main():
    """Run the storage server."""
    print("=" * 60)
    print("BSV Wallet Storage Server")
    print("=" * 60)
    print(f"Network:    {NETWORK}")
    print(f"Database:   {DATABASE_FILE}")
    print(f"Endpoint:   http://localhost:{SERVER_PORT}/wallet")
    print(f"Health:     http://localhost:{SERVER_PORT}/health")
    print("=" * 60)
    print()
    print("To use remote storage in wallet examples:")
    print("  1. Keep this server running")
    print("  2. Edit examples-config.yaml:")
    print(f'     server_url: "http://localhost:{SERVER_PORT}/wallet"')
    print("  3. Run wallet examples as usual")
    print()
    print("Press Ctrl+C to stop the server")
    print("=" * 60)
    
    app = create_app()
    app.run(
        host=SERVER_HOST,
        port=SERVER_PORT,
        debug=True,
        use_reloader=False,  # Avoid double initialization
    )


if __name__ == "__main__":
    main()

