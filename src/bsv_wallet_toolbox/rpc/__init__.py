"""Storage client and server for wallet storage provider communication.

This package provides JSON-RPC 2.0 compliant client and server implementations
for communicating with wallet storage providers.

Equivalent to TypeScript:
    - ts-wallet-toolbox/src/storage/remoting/StorageClient.ts
    - ts-wallet-toolbox/src/storage/remoting/StorageServer.ts

Modules:
    storage_client: StorageClient implementation
        - Synchronous HTTPS communication via requests
        - Automatic authentication header attachment from Wallet instance
        - Thread-safe request ID management
        - Standard JSON-RPC 2.0 error code handling
        - Connection pooling for performance
        - 22 WalletStorageProvider method implementations

    storage_server: StorageServer base class
        - Method registration via decorator
        - Automatic request dispatch
        - Request validation and parameter checking
        - Standard JSON-RPC 2.0 error code handling
        - Batch request support

Client usage:
    >>> from bsv_wallet_toolbox import StorageClient, Wallet
    >>> wallet = Wallet(...)
    >>> client = StorageClient(wallet, "https://storage.example.com/wallet")
    >>> result = client.create_action(auth, args)

Server usage:
    >>> from flask import Flask, request, jsonify
    >>> from bsv_wallet_toolbox.rpc import StorageServer
    >>>
    >>> app = Flask(__name__)
    >>> server = StorageServer()
    >>>
    >>> @server.register_method("wallet_create_action")
    >>> def create_action(auth: dict, args: dict) -> dict:
    ...     return {"success": True}
    >>>
    >>> @app.route('/wallet', methods=['POST'])
    >>> def handle_request():
    ...     response = server.handle_json_rpc_request(request.json)
    ...     return jsonify(response)

Standard JSON-RPC 2.0 error codes:
    -32700: Parse error
    -32600: Invalid Request
    -32601: Method not found
    -32602: Invalid params
    -32603: Internal error

For additional examples and customization, see the documentation and reference
implementations in Flask and FastAPI frameworks.
"""

from bsv_wallet_toolbox.rpc.storage_client import (
    JsonRpcClient,  # Backward compatibility alias
    JsonRpcError,
    StorageClient,
)
from bsv_wallet_toolbox.rpc.storage_server import (
    JsonRpcError as JsonRpcServerError,
)
from bsv_wallet_toolbox.rpc.storage_server import (
    JsonRpcInternalError,
    JsonRpcInvalidParamsError,
    JsonRpcInvalidRequestError,
    JsonRpcMethodNotFoundError,
    JsonRpcParseError,
    JsonRpcServer,  # Backward compatibility alias
    StorageServer,
)

__all__ = [
    # Backward compatibility aliases
    "JsonRpcClient",
    # Error classes
    "JsonRpcError",
    "JsonRpcInternalError",
    "JsonRpcInvalidParamsError",
    "JsonRpcInvalidRequestError",
    "JsonRpcMethodNotFoundError",
    "JsonRpcParseError",
    "JsonRpcServer",
    "JsonRpcServerError",
    # New names (TS parity)
    "StorageClient",
    "StorageServer",
]
