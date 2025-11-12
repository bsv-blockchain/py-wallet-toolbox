"""JSON-RPC 2.0 server base class implementation.

This module provides the foundation for building JSON-RPC 2.0 compliant servers.

Features:
    - JSON-RPC 2.0 protocol compliance
    - Method registration via decorator
    - Automatic method dispatch
    - Request validation and parameter checking
    - Standard JSON-RPC 2.0 error code handling
    - Batch request support
    - Thread-safe method registry

Usage example:
    >>> from bsv_wallet_toolbox.rpc import JsonRpcServer
    >>> server = JsonRpcServer()
    >>>
    >>> @server.register_method("wallet_create_action")
    >>> def handle_create_action(auth: dict, args: dict) -> dict:
    ...     return {"success": True}
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
from typing import Any

logger = logging.getLogger(__name__)


class JsonRpcParseError(Exception):
    """JSON parse error (-32700)."""

    code = -32700
    message = "Parse error"


class JsonRpcInvalidRequestError(Exception):
    """Invalid JSON-RPC request (-32600)."""

    code = -32600
    message = "Invalid Request"


class JsonRpcMethodNotFoundError(Exception):
    """Method not found in registry (-32601)."""

    code = -32601
    message = "Method not found"


class JsonRpcInvalidParamsError(Exception):
    """Invalid JSON-RPC parameters (-32602)."""

    code = -32602
    message = "Invalid params"


class JsonRpcInternalError(Exception):
    """Internal server error (-32603)."""

    code = -32603
    message = "Internal error"


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


class JsonRpcServer:
    """JSON-RPC 2.0 server base class.

    Provides method registration, request handling, and error handling for building
    JSON-RPC 2.0 compliant servers. Users typically subclass this for Flask/FastAPI
    integration.

    Reference: TypeScript StorageServer.ts

    Usage example:

    ```python
    from flask import Flask, request, jsonify
    from bsv_wallet_toolbox.rpc import JsonRpcServer

    app = Flask(__name__)
    server = JsonRpcServer()

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
    class MyJsonRpcServer(JsonRpcServer):
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

    Attributes:
        _methods: Dictionary of registered methods
    """

    def __init__(self) -> None:
        """Initialize the server with empty method registry."""
        self._methods: dict[str, Callable[..., Any]] = {}

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
            logger.error(f"Unexpected error during request validation: {e}")
            return {
                "jsonrpc": "2.0",
                "error": JsonRpcInternalError(str(e)).to_dict(),
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

        except TypeError as e:
            # Parameter type error
            logger.warning(f"Invalid params for method {method}: {e}")
            return {
                "jsonrpc": "2.0",
                "error": JsonRpcInvalidParamsError(f"Invalid parameters: {e!s}").to_dict(),
                "id": request_id,
            }

        except Exception as e:
            # Unexpected error
            logger.error(f"Internal error in method {method}: {e}", exc_info=True)
            return {
                "jsonrpc": "2.0",
                "error": JsonRpcInternalError(f"Internal error: {e!s}").to_dict(),
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
