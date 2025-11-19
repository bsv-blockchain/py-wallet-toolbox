"""JSON-RPC 2.0 client implementation for remote storage provider.

This module provides a JSON-RPC 2.0 compliant client for communicating with
remote wallet storage providers via HTTPS.

Features:
    - JSON-RPC 2.0 protocol compliance
    - Synchronous HTTPS communication via requests
    - Automatic request ID management (thread-safe)
    - Authentication header attachment from Wallet instance
    - Standard JSON-RPC 2.0 error code handling
    - Connection pooling for performance
    - 22 WalletStorageProvider method implementations

Usage example:
    >>> from bsv_wallet_toolbox import JsonRpcClient, Wallet
    >>> wallet = Wallet(...)
    >>> client = JsonRpcClient(wallet, "https://storage.example.com/wallet")
    >>> result = client.create_action(auth, args)

Reference:
    TypeScript: ts-wallet-toolbox/src/storage/remoting/StorageClient.ts (rpcCall)

Standard JSON-RPC 2.0 error codes:
    -32700: Parse error
    -32600: Invalid Request
    -32601: Method not found
    -32602: Invalid params
    -32603: Internal error

Network and parsing errors are propagated as exceptions.
"""

from __future__ import annotations

import json
import logging
import threading
from typing import Any, TypeVar

import requests

if False:  # TYPE_CHECKING
    pass

T = TypeVar("T")

logger = logging.getLogger(__name__)


class JsonRpcError(Exception):
    """Exception raised when JSON-RPC error response is received.

    Attributes:
        code: JSON-RPC error code (-32700 to -32603)
        message: Error message
        data: Additional error information (optional)
    """

    def __init__(
        self,
        code: int,
        message: str,
        data: Any = None,
    ) -> None:
        """Initialize JSON-RPC error.

        Args:
            code: Error code
            message: Error message
            data: Additional information (optional)
        """
        self.code = code
        self.message = message
        self.data = data
        super().__init__(f"RPC Error ({code}): {message}")


class JsonRpcClient:
    """JSON-RPC 2.0 client for remote WalletStorageProvider implementation.

    Equivalent to TypeScript StorageClient. Provides synchronous HTTP communication
    using requests library with JSON-RPC 2.0 protocol-compliant request/response handling.

    Reference: TypeScript StorageClient.ts (rpcCall method)

    Usage:
        >>> wallet = Wallet(...)
        >>> client = JsonRpcClient(wallet, "https://storage.example.com/wallet")
        >>> result = client.create_action(auth, args)
        >>> settings = client.make_available()

    Authentication:
        Passing a Wallet instance automatically attaches authentication headers to all
        requests. Authentication logic is implemented via Wallet.get_auth_headers()
        method from py-sdk.

    Attributes:
        wallet: Wallet instance for authentication
        endpoint_url: Remote storage server endpoint URL
        timeout: Request timeout in seconds (default: 30)
        session: requests.Session for connection pooling
    """

    def __init__(
        self,
        wallet: Any,
        endpoint_url: str,
        timeout: float = 30.0,
    ) -> None:
        """Initialize JSON-RPC client.

        Args:
            wallet: Wallet instance for authentication
            endpoint_url: Remote storage server URL
            timeout: Request timeout in seconds (default: 30)

        Raises:
            TypeError: If wallet is not a Wallet instance
            ValueError: If endpoint_url is empty or invalid
        """
        if not hasattr(wallet, "get_auth_headers"):
            msg = "wallet must be a Wallet instance with get_auth_headers method"
            raise TypeError(msg)

        if not endpoint_url or not isinstance(endpoint_url, str):
            msg = "endpoint_url must be a non-empty string"
            raise ValueError(msg)

        self.wallet = wallet
        self.endpoint_url = endpoint_url
        self.timeout = timeout

        # Request ID counter (TS: nextId)
        self._next_id = 1
        self._id_lock = threading.Lock()

        # Session for connection pooling
        self._session = requests.Session()
        self._session.headers.update({"Content-Type": "application/json"})

        # Cached settings retrieved from remote server
        self.settings: dict[str, Any] | None = None

    def __enter__(self) -> JsonRpcClient:
        """Support for context manager protocol."""
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Clean up resources when exiting context manager."""
        self.close()

    def close(self) -> None:
        """Close session and release resources."""
        if self._session:
            self._session.close()

    def _get_next_id(self) -> int:
        """Generate next request ID (thread-safe).

        Returns:
            Sequential request ID
        """
        with self._id_lock:
            request_id = self._next_id
            self._next_id += 1
            return request_id

    def _get_auth_headers(self) -> dict[str, str]:
        """Get authentication headers from wallet.

        Returns:
            Dictionary of authentication headers

        Raises:
            RuntimeError: If authentication header retrieval fails
        """
        try:
            # Expected to use py-sdk Wallet method
            if hasattr(self.wallet, "get_auth_headers"):
                return self.wallet.get_auth_headers()
            else:
                # Fall back to empty headers if auth not available
                return {}
        except Exception as e:
            msg = f"Failed to get auth headers from wallet: {e}"
            raise RuntimeError(msg) from e

    def _rpc_call(self, method: str, params: list[Any]) -> dict[str, Any]:
        """Execute JSON-RPC 2.0 call.

        Reference: TypeScript StorageClient.rpcCall()

        Request format:
            {
              "jsonrpc": "2.0",
              "method": "wallet_create_action",
              "params": [...],
              "id": 1
            }

        Success response format:
            {
              "jsonrpc": "2.0",
              "result": {...},
              "id": 1
            }

        Error response format:
            {
              "jsonrpc": "2.0",
              "error": {
                "code": -32601,
                "message": "Method not found",
                "data": null
              },
              "id": 1
            }

        Args:
            method: RPC method name (e.g., "wallet_create_action")
            params: Method parameters in list format

        Returns:
            The result field from the response

        Raises:
            JsonRpcError: On JSON-RPC error response
            requests.RequestException: On network error
            json.JSONDecodeError: On JSON parse error
        """
        request_id = self._get_next_id()

        # Build request body (TS: body)
        request_body = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
            "id": request_id,
        }

        try:
            # Get authentication headers
            auth_headers = self._get_auth_headers()

            # Merge headers
            headers = {**self._session.headers, **auth_headers}

            # Execute HTTPS request
            logger.debug(
                f"RPC call: {method} (id={request_id})",
                extra={"endpoint": self.endpoint_url, "params_count": len(params)},
            )

            response = self._session.post(
                self.endpoint_url,
                json=request_body,
                headers=headers,
                timeout=self.timeout,
            )

            # Check HTTP status code
            if not response.ok:
                msg = f"JSON-RPC call failed: HTTP {response.status_code} " f"{response.reason}"
                logger.error(msg)
                raise requests.RequestException(msg)

            # Parse JSON response
            response_data = response.json()

            # Check for JSON-RPC error
            if "error" in response_data and response_data["error"] is not None:
                error_obj = response_data["error"]
                code = error_obj.get("code", -32603)
                message = error_obj.get("message", "Unknown error")
                data = error_obj.get("data")

                logger.warning(
                    f"RPC error response: {message} (code={code})",
                    extra={"method": method, "id": request_id},
                )

                raise JsonRpcError(code, message, data)

            # Return result on success
            result = response_data.get("result")
            logger.debug(
                f"RPC call succeeded: {method} (id={request_id})",
                extra={"result_type": type(result).__name__},
            )

            return result

        except requests.RequestException as e:
            logger.error(
                f"RPC network error: {e}",
                extra={"method": method, "id": request_id},
            )
            raise
        except json.JSONDecodeError as e:
            logger.error(
                f"RPC JSON parse error: {e}",
                extra={"method": method, "id": request_id},
            )
            raise

    # =========================================================================
    # WalletStorageProvider Interface Implementation
    # =========================================================================
    # The following 22 methods provide remote implementation of WalletStorageProvider.
    # Each method uses _rpc_call to invoke the corresponding server-side method via JSON-RPC.
    # =========================================================================

    def is_available(self) -> bool:
        """Check if storage is available.

        Returns:
            True if storage is available, False otherwise
        """
        result = self._rpc_call("isAvailable", [])
        return bool(result)

    def make_available(self) -> dict[str, Any]:
        """Make storage available.

        Returns:
            Table settings
        """
        result = self._rpc_call("makeAvailable", [])
        return result

    def migrate(self, storage_name: str, identity_key: str) -> str:
        """Migrate storage.

        Args:
            storage_name: Storage name
            identity_key: Identity key

        Returns:
            Migration result
        """
        result = self._rpc_call("migrate", [storage_name, identity_key])
        return result

    def destroy(self) -> None:
        """Destroy storage."""
        self._rpc_call("destroy", [])

    def get_services(self) -> dict[str, Any]:
        """Get WalletServices.

        Returns:
            Services configuration
        """
        result = self._rpc_call("getServices", [])
        return result

    def get_settings(self) -> dict[str, Any]:
        """Get storage settings.

        Returns:
            Table settings
        """
        result = self._rpc_call("getSettings", [])
        return result

    def find_or_insert_user(self, identity_key: str) -> dict[str, Any]:
        """Find or insert user.

        Args:
            identity_key: Identity key

        Returns:
            User and isNew flag
        """
        result = self._rpc_call("findOrInsertUser", [identity_key])
        return result

    def find_certificates_auth(
        self,
        auth: dict[str, Any],
        args: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Find certificates for authenticated user.

        Args:
            auth: Authentication context
            args: Search arguments

        Returns:
            List of certificates
        """
        result = self._rpc_call("findCertificatesAuth", [auth, args])
        return result

    def find_output_baskets_auth(
        self,
        auth: dict[str, Any],
        args: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Find output baskets for authenticated user.

        Args:
            auth: Authentication context
            args: Search arguments

        Returns:
            List of output baskets
        """
        result = self._rpc_call("findOutputBasketsAuth", [auth, args])
        return result

    def find_outputs_auth(
        self,
        auth: dict[str, Any],
        args: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Find outputs for authenticated user.

        Args:
            auth: Authentication context
            args: Search arguments

        Returns:
            List of outputs
        """
        result = self._rpc_call("findOutputsAuth", [auth, args])
        return result

    def find_proven_tx_reqs(self, args: dict[str, Any]) -> list[dict[str, Any]]:
        """Find proven transaction requests.

        Args:
            args: Search arguments

        Returns:
            List of proven tx requests
        """
        result = self._rpc_call("findProvenTxReqs", [args])
        return result

    def list_actions(
        self,
        auth: dict[str, Any],
        args: dict[str, Any],
    ) -> dict[str, Any]:
        """List transaction actions.

        Args:
            auth: Authentication context
            args: List arguments

        Returns:
            List actions result
        """
        result = self._rpc_call("listActions", [auth, args])
        return result

    def list_certificates(
        self,
        auth: dict[str, Any],
        args: dict[str, Any],
    ) -> dict[str, Any]:
        """List certificates.

        Args:
            auth: Authentication context
            args: List arguments

        Returns:
            List certificates result
        """
        result = self._rpc_call("listCertificates", [auth, args])
        return result

    def list_outputs(
        self,
        auth: dict[str, Any],
        args: dict[str, Any],
    ) -> dict[str, Any]:
        """List outputs.

        Args:
            auth: Authentication context
            args: List arguments

        Returns:
            List outputs result
        """
        result = self._rpc_call("listOutputs", [auth, args])
        return result

    def abort_action(
        self,
        auth: dict[str, Any],
        args: dict[str, Any],
    ) -> dict[str, Any]:
        """Abort transaction action.

        Args:
            auth: Authentication context
            args: Abort arguments

        Returns:
            Abort action result
        """
        result = self._rpc_call("abortAction", [auth, args])
        return result

    def create_action(
        self,
        auth: dict[str, Any],
        args: dict[str, Any],
    ) -> dict[str, Any]:
        """Create transaction action.

        Args:
            auth: Authentication context
            args: Create arguments

        Returns:
            Create action result
        """
        result = self._rpc_call("createAction", [auth, args])
        return result

    def process_action(
        self,
        auth: dict[str, Any],
        args: dict[str, Any],
    ) -> dict[str, Any]:
        """Process transaction action.

        Args:
            auth: Authentication context
            args: Process arguments

        Returns:
            Process action result
        """
        result = self._rpc_call("processAction", [auth, args])
        return result

    def internalize_action(
        self,
        auth: dict[str, Any],
        args: dict[str, Any],
    ) -> dict[str, Any]:
        """Internalize transaction action.

        Args:
            auth: Authentication context
            args: Internalize arguments

        Returns:
            Internalize action result
        """
        result = self._rpc_call("internalizeAction", [auth, args])
        return result

    def insert_certificate_auth(
        self,
        auth: dict[str, Any],
        cert: dict[str, Any],
    ) -> int:
        """Insert certificate for authenticated user.

        Args:
            auth: Authentication context
            cert: Certificate data

        Returns:
            Number of inserted rows
        """
        result = self._rpc_call("insertCertificateAuth", [auth, cert])
        return int(result)

    def relinquish_certificate(
        self,
        auth: dict[str, Any],
        args: dict[str, Any],
    ) -> int:
        """Relinquish certificate.

        Args:
            auth: Authentication context
            args: Relinquish arguments

        Returns:
            Number of affected rows
        """
        result = self._rpc_call("relinquishCertificate", [auth, args])
        return int(result)

    def relinquish_output(
        self,
        auth: dict[str, Any],
        args: dict[str, Any],
    ) -> int:
        """Relinquish output.

        Args:
            auth: Authentication context
            args: Relinquish arguments

        Returns:
            Number of affected rows
        """
        result = self._rpc_call("relinquishOutput", [auth, args])
        return int(result)

    def get_sync_chunk(self, args: dict[str, Any]) -> dict[str, Any]:
        """Get sync chunk.

        Args:
            args: Sync arguments

        Returns:
            Sync chunk result
        """
        result = self._rpc_call("getSyncChunk", [args])
        return result
