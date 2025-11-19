"""JSON-RPC 2.0 library for wallet storage provider communication.

This package provides JSON-RPC 2.0 compliant client and server implementations
for communicating with wallet storage providers.

Modules:
    json_rpc_client: JSON-RPC client implementation
        - Synchronous HTTPS communication via requests
        - Automatic authentication header attachment from Wallet instance
        - Thread-safe request ID management
        - Standard JSON-RPC 2.0 error code handling
        - Connection pooling for performance
        - 22 WalletStorageProvider method implementations

    json_rpc_server: JSON-RPC server base class
        - Method registration via decorator
        - Automatic request dispatch
        - Request validation and parameter checking
        - Standard JSON-RPC 2.0 error code handling
        - Batch request support

Client usage:
    >>> from bsv_wallet_toolbox import JsonRpcClient, Wallet
    >>> wallet = Wallet(...)
    >>> client = JsonRpcClient(wallet, "https://storage.example.com/wallet")
    >>> result = client.create_action(auth, args)

Server usage:
    >>> from flask import Flask, request, jsonify
    >>> from bsv_wallet_toolbox.rpc import JsonRpcServer
    >>>
    >>> app = Flask(__name__)
    >>> server = JsonRpcServer()
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

from bsv_wallet_toolbox.rpc.json_rpc_client import (
    JsonRpcClient,
    JsonRpcError,
)
from bsv_wallet_toolbox.rpc.json_rpc_server import (
    JsonRpcError as JsonRpcServerError,
)
from bsv_wallet_toolbox.rpc.json_rpc_server import (
    JsonRpcInternalError,
    JsonRpcInvalidParamsError,
    JsonRpcInvalidRequestError,
    JsonRpcMethodNotFoundError,
    JsonRpcParseError,
    JsonRpcServer,
)

__all__ = [
    "JsonRpcClient",
    "JsonRpcError",
    "JsonRpcInternalError",
    "JsonRpcInvalidParamsError",
    "JsonRpcInvalidRequestError",
    "JsonRpcMethodNotFoundError",
    "JsonRpcParseError",
    "JsonRpcServer",
    "JsonRpcServerError",
]
