"""StorageServer - JSON-RPC 2.0 server for wallet storage provider.

This module provides the foundation for building JSON-RPC 2.0 compliant servers
for wallet storage providers.

Equivalent to TypeScript: ts-wallet-toolbox/src/storage/remoting/StorageServer.ts

Features:
    - JSON-RPC 2.0 protocol compliance
    - Method registration via decorator
    - Automatic method dispatch
    - Request validation and parameter checking
    - Standard JSON-RPC 2.0 error code handling
    - Batch request support
    - Thread-safe method registry

Usage example:

    **Basic usage (manual method registration):**
    >>> from bsv_wallet_toolbox.rpc import StorageServer
    >>> server = StorageServer()
    >>>
    >>> @server.register_method("wallet_create_action")
    >>> def handle_create_action(auth: dict, args: dict) -> dict:
    ...     return {"success": True}
    >>>
    >>> @app.route('/wallet', methods=['POST'])
    >>> def handle_request():
    ...     return server.handle_json_rpc_request(request.json)

    **TS parity usage (auto-register StorageProvider methods):**
    >>> from bsv_wallet_toolbox.rpc import StorageServer
    >>> from bsv_wallet_toolbox.storage import StorageProvider
    >>> storage = StorageProvider(...)  # Initialize StorageProvider
    >>> server = StorageServer(storage_provider=storage)  # Auto-register all methods
    >>>
    >>> # Now camelCase JSON-RPC methods are available:
    >>> # createAction, findCertificatesAuth, setActive, etc.
    >>>
    >>> @app.route('/wallet', methods=['POST'])
    >>> def handle_request():
    ...     return server.handle_json_rpc_request(request.json)

Reference:
    TypeScript: ts-wallet-toolbox/src/storage/remoting/StorageServer.ts

Standard JSON-RPC 2.0 error codes:
    -32700: Parse error (JSON format error)
    -32600: Invalid Request (request structure error)
    -32601: Method not found (unregistered method)
    -32602: Invalid params (parameter error)
    -32603: Internal error (implementation error)

This is a base class designed for user implementation via Flask/FastAPI inheritance.
Customize by subclassing and adding authentication, business logic, and middleware.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from functools import partial
from typing import Any

from ..errors import WalletError
from ..storage.methods.generate_change import InsufficientFundsError as GenerateChangeInsufficientFundsError
from ..storage.provider import StorageProvider

logger = logging.getLogger(__name__)


class JsonRpcError(Exception):
    """Base class for JSON-RPC protocol errors.

    Attributes:
        code: JSON-RPC error code (-32700 to -32603)
        message: Error message
    """

    code = -32603  # Internal error (default)
    message = "Internal error"

    def __init__(self, message: str | None = None) -> None:
        """Initialize the error.

        Args:
            message: Custom error message (optional)
        """
        if message:
            self.message = message
        super().__init__(self.message)

    def to_dict(self) -> dict[str, Any]:
        """Convert to JSON-RPC error object.

        Returns:
            Dictionary with code and message keys
        """
        return {
            "code": self.code,
            "message": self.message,
        }


class JsonRpcParseError(JsonRpcError):
    """JSON parse error (-32700)."""

    code = -32700
    message = "Parse error"


class JsonRpcInvalidRequestError(JsonRpcError):
    """Invalid JSON-RPC request (-32600)."""

    code = -32600
    message = "Invalid Request"


class JsonRpcMethodNotFoundError(JsonRpcError):
    """Method not found in registry (-32601)."""

    code = -32601
    message = "Method not found"


class JsonRpcInvalidParamsError(JsonRpcError):
    """Invalid JSON-RPC parameters (-32602)."""

    code = -32602
    message = "Invalid params"


class JsonRpcInternalError(JsonRpcError):
    """Internal server error (-32603)."""

    code = -32603
    message = "Internal error"


def wallet_error_to_json(error: Exception) -> dict[str, Any]:
    """Convert a WalletError instance to JSON format compatible with TypeScript WalletErrorFromJson.

    This function mirrors the behavior of TypeScript WalletError.unknownToJson() to ensure
    proper error serialization across the Python/TypeScript boundary.

    Reference:
        - TypeScript: ts-sdk/src/wallet/WalletError.ts (unknownToJson)
        - TypeScript: wallet-toolbox/src/sdk/WalletError.ts (unknownToJson)
        - TypeScript: wallet-toolbox/src/sdk/WalletErrorFromJson.ts

    Args:
        error: Exception instance to convert

    Returns:
        Dictionary with error details in format expected by TypeScript client
    """
    # Check if it's InsufficientFundsError from generate_change.py
    if isinstance(error, GenerateChangeInsufficientFundsError):
        # Map required/short to totalSatoshisNeeded/moreSatoshisNeeded (camelCase for TS)
        # Use a generic, non-sensitive message instead of the raw exception text.
        return {
            "name": "WERR_INSUFFICIENT_FUNDS",
            "message": "Insufficient funds.",
            "isError": True,
            "code": 7,
            "totalSatoshisNeeded": error.required,
            "moreSatoshisNeeded": error.short,
        }

    # Check if it's a WalletError base class
    if isinstance(error, WalletError):
        # Get error class name
        error_name = error.__class__.__name__

        # Map common error names to WERR_ format
        if error_name == "InsufficientFundsError":
            # This is the one from errors/wallet_errors.py
            if hasattr(error, "total_satoshis_needed") and hasattr(error, "more_satoshis_needed"):
                return {
                    "name": "WERR_INSUFFICIENT_FUNDS",
                    "message": str(error),
                    "isError": True,
                    "code": 7,
                    "totalSatoshisNeeded": error.total_satoshis_needed,
                    "moreSatoshisNeeded": error.more_satoshis_needed,
                }

        # For other WalletError subclasses, use the class name
        # Convert Python class names to WERR_ format if needed
        if not error_name.startswith("WERR_"):
            # Try to map common names
            name_mapping = {
                "InvalidParameterError": "WERR_INVALID_PARAMETER",
                "ValidationError": "WERR_INVALID_PARAMETER",
                "OperationError": "WERR_INVALID_OPERATION",
                "StateError": "WERR_INVALID_OPERATION",
            }
            error_name = name_mapping.get(error_name, f"WERR_{error_name.upper()}")

        result = {
            "name": error_name,
            "message": str(error),
            "isError": True,
        }

        # Add InvalidParameterError parameter if available
        if error_name == "WERR_INVALID_PARAMETER" and hasattr(error, "parameter"):
            result["parameter"] = error.parameter
            result["code"] = 6

        return result

    # For regular Exception instances
    if isinstance(error, Exception):
        # Log a generic internal error message server-side while returning a generic message to the client.
        # Do not include the raw exception text in the log message itself, but capture full details via exc_info.
        logger.error(
            "Unhandled internal exception serialized as WERR_INTERNAL (details redacted from client)",
            exc_info=True,
        )
        return {
            "name": "WERR_INTERNAL",
            "message": "An internal error occurred.",
            "isError": True,
        }

    # For unknown error types
    return {
        "name": "WERR_UNKNOWN",
        "message": "An unknown error occurred.",
        "isError": True,
    }


class StorageServer:
    """JSON-RPC 2.0 server for wallet storage provider.

    Provides method registration, request handling, and error handling for building
    JSON-RPC 2.0 compliant servers. Users typically subclass this for Flask/FastAPI
    integration.

    Reference: TypeScript StorageServer.ts

    Usage example:

    ```python
    from flask import Flask, request, jsonify
    from bsv_wallet_toolbox.rpc import StorageServer

    app = Flask(__name__)
    server = StorageServer()

    @server.register_method("wallet_create_action")
    def create_action(auth: dict, args: dict) -> dict:
        # Authentication check
        if not auth or "contextUser" not in auth:
            raise JsonRpcInvalidParams("Missing auth context")

        # Business logic
        return {"success": True, "txid": "..."}

    @app.route('/wallet', methods=['POST'])
    def handle_request():
        try:
            response = server.handle_json_rpc_request(request.json)
            return jsonify(response)
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return jsonify({
                "jsonrpc": "2.0",
                "error": JsonRpcInternalError().to_dict(),
                "id": None
            }), 500
    ```

    For custom authentication:

    ```python
    class MyStorageServer(StorageServer):
        def _validate_auth(self, auth: dict) -> bool:
            \"\"\"Validate authentication information.\"\"\"
            # Wallet signature verification, etc.
            return True

        def handle_json_rpc_request(self, request_data: dict) -> dict:
            # Parent class validation
            response = super().handle_json_rpc_request(request_data)

            # Authentication check
            if "auth" in request_data.get("params", {}):
                if not self._validate_auth(request_data["params"]["auth"]):
                    return {
                        "jsonrpc": "2.0",
                        "error": {
                            "code": -32700,
                            "message": "Unauthorized"
                        },
                        "id": request_data.get("id")
                    }

            return response
    ```

    Args:
        storage_provider: Optional StorageProvider to auto-register all methods as JSON-RPC endpoints.
                         If provided, all StorageProvider methods are automatically registered,
                         matching TypeScript StorageServer.ts behavior.

    Attributes:
        _methods: Dictionary of registered methods
    """

    def __init__(self, storage_provider: StorageProvider | None = None) -> None:
        """Initialize the server with empty method registry.

        Args:
            storage_provider: Optional StorageProvider to auto-register all methods as JSON-RPC endpoints.
                             When provided, automatically registers all StorageProvider methods matching
                             TypeScript StorageServer.ts behavior.
        """
        self._methods: dict[str, Callable[..., Any]] = {}
        if storage_provider:
            self.register_storage_provider_methods(storage_provider)

    def register_method(
        self,
        method_name: str,
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        """Decorator to register a JSON-RPC method handler.

        Args:
            method_name: JSON-RPC method name (e.g., "wallet_create_action")

        Returns:
            Decorator function

        Example:
            ```python
            @server.register_method("wallet_create_action")
            def create_action(auth: dict, args: dict) -> dict:
                return {"success": True}
            ```
        """

        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            self._methods[method_name] = func
            logger.debug(f"Registered JSON-RPC method: {method_name}")
            return func

        return decorator

    def is_method_registered(self, method_name: str) -> bool:
        """Check if a method is registered.

        Args:
            method_name: Method name to check

        Returns:
            True if registered, False otherwise
        """
        return method_name in self._methods

    def get_registered_methods(self) -> list[str]:
        """Get all registered method names.

        Returns:
            Sorted list of method names
        """
        return sorted(self._methods.keys())

    def register_storage_provider_methods(self, storage_provider: StorageProvider) -> None:
        """Auto-register all StorageProvider methods as JSON-RPC methods.

        TS parity: Mirrors StorageServer.ts automatic method registration.
        Maps camelCase JSON-RPC method names to snake_case Python method names.

        JSON-RPC methods (camelCase):
            createAction, findCertificatesAuth, setActive, etc.

        Python methods (snake_case):
            create_action, find_certificates, set_active, etc.

        Args:
            storage_provider: StorageProvider instance to register methods from

        Reference:
            toolbox/ts-wallet-toolbox/src/storage/remoting/StorageServer.ts
        """
        # JSON-RPC method names (camelCase) mapped to Python method names (snake_case)
        # TS parity: JSON-RPC method names must match TypeScript StorageClient interface
        json_rpc_to_python_methods = {
            # Core StorageProvider methods
            "makeAvailable": "make_available",
            "migrate": "migrate",
            "destroy": "destroy",
            "findOrInsertUser": "find_or_insert_user",
            "abortAction": "abort_action",
            "createAction": "create_action",
            "processAction": "process_action",
            "internalizeAction": "internalize_action",
            "findCertificatesAuth": "find_certificates",  # Note: TS has Auth suffix
            "findOutputBaskets": "find_output_baskets",  # TS/Go/Python clients call 'findOutputBaskets' with [auth, args]
            "findOutputsAuth": "find_outputs",  # Note: TS has Auth suffix
            "findProvenTxReqs": "find_proven_tx_reqs",
            "listActions": "list_actions",
            "listCertificates": "list_certificates",
            "listOutputs": "list_outputs",
            "insertCertificateAuth": "insert_certificate",  # Note: TS has Auth suffix
            "relinquishCertificate": "relinquish_certificate",
            "relinquishOutput": "relinquish_output",
            "findOrInsertSyncStateAuth": "find_or_insert_sync_state_auth",
            "setActive": "set_active",
            "getSyncChunk": "get_sync_chunk",
            "processSyncChunk": "process_sync_chunk",
            "updateProvenTxReqWithNewProvenTx": "update_proven_tx_req_with_new_proven_tx",
        }

        for json_rpc_method, python_method in json_rpc_to_python_methods.items():
            # Debug: Check if method exists
            has_method = hasattr(storage_provider, python_method)

            if has_method:
                method = getattr(storage_provider, python_method)
                if callable(method):
                    # Create wrapper that passes params directly to storage method
                    # TS parity: Mirrors StorageServer.ts behavior: (this.storage as any)[method](...(params || []))
                    # JSON-RPC params are passed as *args array, matching TypeScript spread operator
                    def create_method_wrapper(
                        storage_method: Callable[..., Any],
                        python_method: str,
                        *params: Any,
                    ) -> Any:
                        try:
                            # TS parity: Pass params directly to storage method (same as TS spread operator)
                            # TypeScript: (this.storage as any)[method](...(params || []))
                            # Python: storage_method(*params)
                            return storage_method(*params)
                        except Exception as e:
                            logger.error(f"Error in storage method ({python_method}): {e}")
                            raise

                    # Use partial to bind the method and python_method name
                    wrapper = partial(create_method_wrapper, method, python_method)
                    self._methods[json_rpc_method] = wrapper
                    logger.debug(f"Auto-registered JSON-RPC method: {json_rpc_method} -> {python_method}")
                else:
                    logger.warning(f"StorageProvider.{python_method} is not callable")
            else:
                logger.warning(f"StorageProvider missing method: {python_method} (for JSON-RPC: {json_rpc_method})")

        logger.debug(f"Registered {len(self._methods)} StorageProvider methods as JSON-RPC endpoints")

    def _validate_json_rpc_request(
        self,
        request_data: Any,
    ) -> tuple[str, list[Any] | dict[str, Any], Any]:
        """Validate a JSON-RPC 2.0 request.

        JSON-RPC 2.0 specification:
        - jsonrpc: "2.0" (required)
        - method: string (required)
        - params: array | object (optional)
        - id: string | number | NULL (required unless notification)

        Args:
            request_data: Request object

        Returns:
            Tuple of (method, params, id)

        Raises:
            JsonRpcParseError: If JSON is not parseable
            JsonRpcInvalidRequestError: If request structure is invalid
        """
        # Verify it's a JSON object
        if not isinstance(request_data, dict):
            raise JsonRpcInvalidRequestError("Request must be a JSON object")

        # Check jsonrpc version
        if request_data.get("jsonrpc") != "2.0":
            raise JsonRpcInvalidRequestError('Missing or invalid "jsonrpc": "2.0"')

        # Verify method field
        method = request_data.get("method")
        if not isinstance(method, str):
            raise JsonRpcInvalidRequestError("method must be a string")

        # Get params (optional, defaults to [])
        params = request_data.get("params", [])
        if not isinstance(params, (list, dict)):
            raise JsonRpcInvalidRequestError("params must be an array or object")

        # Get id (required unless notification)
        request_id = request_data.get("id")

        return method, params, request_id

    def handle_json_rpc_request(
        self,
        request_data: Any,
    ) -> dict[str, Any]:
        """Handle a JSON-RPC request and return a response.

        Request format:

        ```json
        {
          "jsonrpc": "2.0",
          "method": "wallet_create_action",
          "params": {
            "auth": {...},
            "args": {...}
          },
          "id": 1
        }
        ```

        Success response format:

        ```json
        {
          "jsonrpc": "2.0",
          "result": {...},
          "id": 1
        }
        ```

        Error response format:

        ```json
        {
          "jsonrpc": "2.0",
          "error": {
            "code": -32601,
            "message": "Method not found"
          },
          "id": 1
        }
        ```

        Args:
            request_data: JSON-RPC request object

        Returns:
            JSON-RPC response object
        """
        request_id = None

        try:
            # Validate the request
            method, params, request_id = self._validate_json_rpc_request(request_data)

        except JsonRpcParseError as e:
            logger.warning(f"JSON parse error: {e}")
            return {
                "jsonrpc": "2.0",
                "error": e.to_dict(),
                "id": None,
            }

        except JsonRpcInvalidRequestError as e:
            logger.warning(f"Invalid request: {e}")
            return {
                "jsonrpc": "2.0",
                "error": e.to_dict(),
                "id": request_id,
            }

        except Exception as e:
            logger.error(f"Unexpected error during request validation: {e}", exc_info=True)
            return {
                "jsonrpc": "2.0",
                "error": JsonRpcInternalError().to_dict(),
                "id": request_id,
            }

        # Check if method is registered
        if not self.is_method_registered(method):
            logger.warning(f"Method not found: {method}")
            return {
                "jsonrpc": "2.0",
                "error": JsonRpcMethodNotFoundError(f"Method '{method}' not found").to_dict(),
                "id": request_id,
            }

        # Execute the method
        try:
            handler = self._methods[method]

            # If params is dict, pass as kwargs; if list, pass as args
            if isinstance(params, dict):
                result = handler(**params)
            else:
                result = handler(*params)

            logger.debug(f"Method executed successfully: {method}")

            return {
                "jsonrpc": "2.0",
                "result": result,
                "id": request_id,
            }

        except JsonRpcError as e:
            logger.warning(f"JSON-RPC error in method {method}: {e}")
            return {
                "jsonrpc": "2.0",
                "error": e.to_dict(),
                "id": request_id,
            }

        except WalletError as e:
            # Convert WalletError instances to JSON format compatible with TypeScript
            # TS parity: Mirrors StorageServer.ts behavior where WalletError.unknownToJson(error)
            # is placed directly in the error field
            # This includes InsufficientFundsError from generate_change.py and other WalletError subclasses
            logger.warning(f"WalletError in method {method}: {e}")
            error_json = wallet_error_to_json(e)
            return {
                "jsonrpc": "2.0",
                "error": error_json,
                "id": request_id,
            }

        except TypeError as e:
            # Parameter type error
            logger.warning(f"Invalid params for method {method}: {e}")
            return {
                "jsonrpc": "2.0",
                "error": JsonRpcInvalidParamsError().to_dict(),
                "id": request_id,
            }

        except Exception as e:
            # Unexpected error - log full details but return a generic internal error to the client
            logger.error(f"Internal error in method {method}: {e}", exc_info=True)
            return {
                "jsonrpc": "2.0",
                "error": JsonRpcInternalError().to_dict(),
                "id": request_id,
            }

    def handle_json_rpc_batch(
        self,
        request_data_list: list[Any],
    ) -> list[dict[str, Any]]:
        """Handle a batch of JSON-RPC requests.

        JSON-RPC 2.0 allows sending multiple requests in an array. Multiple
        corresponding responses are returned as an array.

        Batch request format:

        ```json
        [
          {"jsonrpc": "2.0", "method": "wallet_create_action", "params": {...}, "id": 1},
          {"jsonrpc": "2.0", "method": "wallet_list_actions", "params": {...}, "id": 2}
        ]
        ```

        Batch response format:

        ```json
        [
          {"jsonrpc": "2.0", "result": {...}, "id": 1},
          {"jsonrpc": "2.0", "result": {...}, "id": 2}
        ]
        ```

        Args:
            request_data_list: List of JSON-RPC request objects

        Returns:
            List of JSON-RPC response objects
        """
        if not isinstance(request_data_list, list):
            raise JsonRpcInvalidRequestError("Batch request must be an array")

        if len(request_data_list) == 0:
            raise JsonRpcInvalidRequestError("Batch request array must not be empty")

        responses: list[dict[str, Any]] = []

        for request_data in request_data_list:
            response = self.handle_json_rpc_request(request_data)
            responses.append(response)

        return responses


# Backward compatibility alias
# Deprecated: Use StorageServer instead
JsonRpcServer = StorageServer
