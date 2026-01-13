"""StorageClient - JSON-RPC 2.0 client for remote storage provider.

This module provides a JSON-RPC 2.0 compliant client for communicating with
remote wallet storage providers via HTTPS.

Equivalent to TypeScript: ts-wallet-toolbox/src/storage/remoting/StorageClient.ts

Features:
    - JSON-RPC 2.0 protocol compliance
    - BRC-104 authenticated HTTPS communication via AuthFetch
    - Automatic request ID management (thread-safe)
    - Mutual authentication with remote storage servers
    - Standard JSON-RPC 2.0 error code handling
    - 402 Payment Required handling via AuthFetch
    - 22 WalletStorageProvider method implementations

Usage example:
    >>> from bsv_wallet_toolbox import StorageClient, Wallet
    >>> wallet = Wallet(...)
    >>> client = StorageClient(wallet, "https://storage.example.com/wallet")
    >>> result = client.create_action(auth, args)

Reference:
    TypeScript: ts-wallet-toolbox/src/storage/remoting/StorageClient.ts

Standard JSON-RPC 2.0 error codes:
    -32700: Parse error
    -32600: Invalid Request
    -32601: Method not found
    -32602: Invalid params
    -32603: Internal error

Network and parsing errors are propagated as exceptions.
"""

from __future__ import annotations

import asyncio
import json
import logging
import threading
from typing import Any, TypeVar
from urllib.parse import urlparse, urlunparse

import requests

from ..auth_fetch import AuthFetch, SimplifiedFetchRequestOptions
from ..utils.trace import trace

if False:  # TYPE_CHECKING
    pass

T = TypeVar("T")

logger = logging.getLogger(__name__)


def normalize_url_for_brc104(endpoint_url: str) -> str:
    """Normalize URL path for BRC-104 signature compatibility.

    IMPORTANT (BRC-104 signature compatibility):
    If the URL has an empty path (e.g. "http://host:port"), different stacks may
    canonicalize it as "" vs "/". That can change the signed payload for the
    authenticated request and cause server-side "Invalid signature".

    This function ensures empty paths are normalized to "/" to maintain consistent
    signature computation across different URL parsing implementations.

    Args:
        endpoint_url: The endpoint URL to normalize

    Returns:
        The normalized URL with empty path replaced by "/"
    """
    parsed = urlparse(endpoint_url)
    if not parsed.path:
        endpoint_url = urlunparse(
            (
                parsed.scheme,
                parsed.netloc,
                "/",
                parsed.params,
                parsed.query,
                parsed.fragment,
            )
        )
    return endpoint_url


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


class StorageClient:
    """JSON-RPC 2.0 client for remote WalletStorageProvider implementation.

    Uses AuthFetch for BRC-104 authenticated communication with remote storage,
    following the same pattern as TypeScript StorageClient.

    Reference: TypeScript StorageClient.ts

    Usage:
        >>> wallet = Wallet(...)
        >>> client = StorageClient(wallet, "https://storage.example.com/wallet")
        >>> result = client.create_action(auth, args)
        >>> settings = client.make_available()

    Authentication:
        Uses AuthFetch for BRC-104 mutual authentication. The AuthFetch component
        handles session management, certificate exchange, and 402 Payment Required
        responses automatically.

    Attributes:
        wallet: Wallet instance for authentication
        endpoint_url: Remote storage server endpoint URL
        timeout: Request timeout in seconds (default: 30)
        auth_client: AuthFetch instance for authenticated requests
    """

    def __init__(
        self,
        wallet: Any,
        endpoint_url: str,
        timeout: float = 30.0,
        requested_certificates: Any = None,
    ) -> None:
        """Initialize StorageClient.

        Args:
            wallet: Wallet instance for authentication (BRC-100 WalletInterface)
            endpoint_url: Remote storage server URL
            timeout: Request timeout in seconds (default: 30)
            requested_certificates: Optional certificate requirements for mutual auth

        Raises:
            ValueError: If endpoint_url is empty or invalid
        """
        if not endpoint_url or not isinstance(endpoint_url, str):
            msg = "endpoint_url must be a non-empty string"
            raise ValueError(msg)

        # Normalize URL for BRC-104 signature compatibility
        endpoint_url = normalize_url_for_brc104(endpoint_url)

        self.wallet = wallet
        self.endpoint_url = endpoint_url
        self.timeout = timeout

        # Use AuthFetch for BRC-104 authenticated requests (TS pattern)
        self.auth_client = AuthFetch(wallet, requested_certificates)

        # Request ID counter (TS: nextId)
        self._next_id = 1
        self._id_lock = threading.Lock()

        # Cached settings retrieved from remote server
        self.settings: dict[str, Any] | None = None

    def __enter__(self) -> StorageClient:
        """Support for context manager protocol."""
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Clean up resources when exiting context manager."""
        self.close()

    def close(self) -> None:
        """Close resources (no-op for AuthFetch)."""
        # AuthFetch manages its own resources via peer connections

    def _get_next_id(self) -> int:
        """Generate next request ID (thread-safe).

        Returns:
            Sequential request ID
        """
        with self._id_lock:
            request_id = self._next_id
            self._next_id += 1
            return request_id

    def _rpc_call(self, method: str, params: list[Any]) -> dict[str, Any]:
        """Execute JSON-RPC 2.0 call using AuthFetch.

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

        def _jsonify(value: Any) -> Any:
            """Convert Python objects to JSON-safe payloads (BRC-100 bytes => list[int])."""
            if value is None:
                return None
            if isinstance(value, (str, int, float, bool)):
                return value
            if isinstance(value, (bytes, bytearray)):
                return list(bytes(value))
            if isinstance(value, list):
                return [_jsonify(v) for v in value]
            if isinstance(value, dict):
                return {str(k): _jsonify(v) for k, v in value.items()}
            # PublicKey objects etc: fall back to string representation
            return str(value)

        # NOTE (TS parity / python ergonomics):
        # Remote JSON-RPC servers encode bytes as number[] (list[int]) because JSON has no bytes type.
        # We must de-serialize those fields back to `bytes` on the client side so downstream code
        # (py-sdk Beef/Transaction parsers) can operate on real bytes.
        _BYTES_KEYS: set[str] = {
            # BEEF / tx payloads
            "inputBeef",
            "inputBEEF",
            "outputBeef",
            "outputBEEF",
            "beef",
            "tx",
            "rawTx",
            "atomicBeef",
            # proofs / ancillary binary blobs
            "merklePath",
        }

        def _looks_like_byte_array(value: Any) -> bool:
            if not isinstance(value, list):
                return False
            # empty list can represent empty bytes
            if len(value) == 0:
                return True
            for x in value:
                if not isinstance(x, int):
                    return False
                if x < 0 or x > 255:
                    return False
            return True

        def _dejsonify(value: Any, parent_key: str | None = None) -> Any:
            # Convert known byte-array fields back to bytes
            if parent_key in _BYTES_KEYS:
                if isinstance(value, (bytes, bytearray)):
                    return bytes(value)
                if _looks_like_byte_array(value):
                    return bytes(value)
            if isinstance(value, dict):
                return {k: _dejsonify(v, k) for k, v in value.items()}
            if isinstance(value, list):
                # For non-byte fields, preserve list structure and recurse.
                return [_dejsonify(v, None) for v in value]
            return value

        # Build request body (TS: body)
        request_body = {
            "jsonrpc": "2.0",
            "method": method,
            "params": _jsonify(params),
            "id": request_id,
        }

        try:
            trace(
                logger,
                "rpc.request",
                method=method,
                id=request_id,
                endpoint=self.endpoint_url,
                params=request_body.get("params"),
            )
            logger.debug(
                f"RPC call: {method} (id={request_id})",
                extra={"endpoint": self.endpoint_url, "paramsCount": len(params)},
            )

            # Use AuthFetch for BRC-104 authenticated request (TS pattern)
            config = SimplifiedFetchRequestOptions(
                method="POST",
                headers={"Content-Type": "application/json"},
                body=json.dumps(request_body).encode("utf-8"),
            )

            logger.debug(
                f"AuthFetch request: method={method}, url={self.endpoint_url}, body_size={len(config.body) if config.body else 0}",
                extra={"method": method, "endpoint": self.endpoint_url, "requestBody": request_body},
            )

            response = asyncio.run(self.auth_client.fetch(self.endpoint_url, config))

            trace(
                logger,
                "rpc.http.response",
                method=method,
                id=request_id,
                endpoint=self.endpoint_url,
                status=response.status_code,
                headers=dict(response.headers),
            )
            logger.debug(
                f"AuthFetch response: status={response.status_code}, headers={dict(response.headers)}",
                extra={"method": method, "statusCode": response.status_code, "responseHeaders": dict(response.headers)},
            )

            # Parse JSON response (even on HTTP errors) when the server advertises JSON.
            # Some servers return JSON-RPC errors with HTTP 500; the JSON-RPC error is the real signal.
            content_type = (response.headers or {}).get("Content-Type", "")
            expects_json = "json" in content_type.lower()
            if not response.ok and not expects_json:
                msg = f"JSON-RPC call failed: HTTP {response.status_code} {response.reason}"
                trace(
                    logger,
                    "rpc.http_error",
                    method=method,
                    id=request_id,
                    endpoint=self.endpoint_url,
                    http_status=response.status_code,
                    reason=response.reason,
                    response_body=None,
                )
                logger.error(
                    msg,
                    extra={"method": method, "id": request_id, "responseHeaders": dict(response.headers)},
                )
                raise requests.RequestException(msg)

            try:
                response_data = response.json()
            except json.JSONDecodeError as e:
                trace(
                    logger,
                    "rpc.response.decode_error",
                    method=method,
                    id=request_id,
                    endpoint=self.endpoint_url,
                    status=response.status_code,
                    body_text=response.text,
                )
                logger.error(
                    f"RPC JSON parse error: {e}",
                    extra={"method": method, "id": request_id, "statusCode": response.status_code},
                )
                # If HTTP status is error and body isn't JSON, raise as network/protocol error.
                if not response.ok:
                    msg = f"JSON-RPC call failed: HTTP {response.status_code} {response.reason}"
                    logger.error(msg)
                    raise requests.RequestException(msg) from e
                raise

            # Check for JSON-RPC error first (even if HTTP status is 500).
            if "error" in response_data and response_data["error"] is not None:
                error_obj = response_data["error"]
                code = error_obj.get("code", -32603)
                message = error_obj.get("message", "Unknown error")
                data = error_obj.get("data")

                trace(
                    logger,
                    "rpc.error",
                    method=method,
                    id=request_id,
                    endpoint=self.endpoint_url,
                    http_status=response.status_code,
                    code=code,
                    message=message,
                    data=data,
                )
                logger.warning(
                    f"RPC error response: {message} (code={code})",
                    extra={"method": method, "id": request_id, "httpStatus": response.status_code},
                )

                raise JsonRpcError(code, message, data)

            # If HTTP status is not OK but no JSON-RPC error is present, treat as HTTP failure.
            if not response.ok:
                msg = f"JSON-RPC call failed: HTTP {response.status_code} {response.reason}"
                trace(
                    logger,
                    "rpc.http_error",
                    method=method,
                    id=request_id,
                    endpoint=self.endpoint_url,
                    http_status=response.status_code,
                    reason=response.reason,
                    response_body=response_data,
                )
                logger.error(
                    msg,
                    extra={"method": method, "id": request_id, "responseBody": response_data},
                )
                raise requests.RequestException(msg)

            # Return result on success
            result = _dejsonify(response_data.get("result"))
            trace(logger, "rpc.result", method=method, id=request_id, endpoint=self.endpoint_url, result=result)
            logger.debug(
                f"RPC call succeeded: {method} (id={request_id})",
                extra={"resultType": type(result).__name__},
            )

            return result

        except requests.RequestException as e:
            trace(logger, "rpc.network_error", method=method, id=request_id, endpoint=self.endpoint_url, error=str(e))
            logger.error(
                f"RPC network error: {e}",
                extra={"method": method, "id": request_id},
            )
            raise
        except json.JSONDecodeError as e:
            trace(logger, "rpc.json_error", method=method, id=request_id, endpoint=self.endpoint_url, error=str(e))
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

    def find_or_insert_user(self, identity_key: str) -> dict[str, Any]:
        """Find or insert user.

        Args:
            identity_key: Identity key

        Returns:
            User and isNew flag
        """
        result = self._rpc_call("findOrInsertUser", [identity_key])
        return result

    def get_or_create_user_id(self, identity_key: str) -> int:
        """Get or create a user by identity key.

        Wrapper around find_or_insert_user for Wallet compatibility.

        Args:
            identity_key: Hex-encoded public key string (identity key)

        Returns:
            int: User ID (primary key)
        """
        result = self.find_or_insert_user(identity_key)
        user = result.get("user", {})
        return user.get("userID", 0)

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
        result = self._rpc_call("findOutputBaskets", [auth, args])
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

    def is_available(self) -> bool:
        """Check if storage is available.

        Returns:
            True if available
        """
        result = self._rpc_call("isAvailable", [])
        return bool(result)

    def get_services(self) -> dict[str, Any]:
        """Get available services.

        Returns:
            Services configuration
        """
        result = self._rpc_call("getServices", [])
        return result

    def get_settings(self) -> dict[str, Any]:
        """Get storage settings.

        Returns:
            Settings dictionary
        """
        result = self._rpc_call("getSettings", [])
        return result


# Backward compatibility alias
JsonRpcClient = StorageClient
