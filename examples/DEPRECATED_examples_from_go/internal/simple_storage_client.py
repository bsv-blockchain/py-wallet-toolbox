"""Simple HTTP Storage Client for testing (without BRC-104 authentication).

This is a simplified version of StorageClient that uses plain HTTP requests
without the AuthFetch authentication layer. It's intended for local testing
with the simple Flask storage server.

For production use, prefer the full StorageClient with AuthFetch.
"""

from __future__ import annotations

import json
import logging
import threading
from typing import Any

import requests

logger = logging.getLogger(__name__)


class BytesEncoder(json.JSONEncoder):
    """Custom JSON encoder that handles bytes objects."""
    def default(self, obj):
        if isinstance(obj, bytes):
            # Convert bytes to list of integers (matching TypeScript behavior)
            return list(obj)
        return super().default(obj)


class SimpleStorageClient:
    """Simple HTTP-based storage client for testing.

    Uses plain HTTP POST requests (no authentication) for communication
    with a local storage server.
    """

    def __init__(
        self,
        endpoint_url: str,
        timeout: float = 30.0,
    ) -> None:
        """Initialize SimpleStorageClient.

        Args:
            endpoint_url: Remote storage server URL
            timeout: Request timeout in seconds (default: 30)
        """
        if not endpoint_url or not isinstance(endpoint_url, str):
            raise ValueError("endpoint_url must be a non-empty string")

        self.endpoint_url = endpoint_url
        self.timeout = timeout

        # Request ID counter
        self._next_id = 1
        self._id_lock = threading.Lock()

    def close(self) -> None:
        """Close resources (no-op for simple client)."""
        pass

    def _get_next_id(self) -> int:
        """Generate next request ID (thread-safe)."""
        with self._id_lock:
            request_id = self._next_id
            self._next_id += 1
            return request_id

    def _rpc_call(self, method: str, params: list[Any]) -> Any:
        """Execute JSON-RPC 2.0 call using plain HTTP.

        Args:
            method: RPC method name
            params: Method parameters

        Returns:
            The result field from the response
        """
        request_id = self._get_next_id()

        request_body = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
            "id": request_id,
        }

        logger.debug(f"RPC call: {method} (id={request_id})")

        # Use custom encoder to handle bytes objects
        json_body = json.dumps(request_body, cls=BytesEncoder)
        
        response = requests.post(
            self.endpoint_url,
            data=json_body,
            headers={"Content-Type": "application/json"},
            timeout=self.timeout,
        )
        response.raise_for_status()

        response_data = response.json()

        if "error" in response_data and response_data["error"] is not None:
            error_obj = response_data["error"]
            code = error_obj.get("code", -32603)
            message = error_obj.get("message", "Unknown error")
            raise RuntimeError(f"RPC Error ({code}): {message}")

        return response_data.get("result")

    # =========================================================================
    # WalletStorageProvider Interface Implementation
    # =========================================================================

    def is_available(self) -> bool:
        """Check if storage is available."""
        result = self._rpc_call("isAvailable", [])
        return bool(result)

    def make_available(self) -> dict[str, Any]:
        """Make storage available."""
        result = self._rpc_call("makeAvailable", [])
        return result

    def get_settings(self) -> dict[str, Any]:
        """Get storage settings."""
        result = self._rpc_call("getSettings", [])
        return result

    def set_services(self, services: Any) -> None:
        """Set wallet services (no-op for remote client)."""
        pass

    def find_or_insert_user(self, identity_key: str) -> dict[str, Any]:
        """Find or insert user."""
        result = self._rpc_call("findOrInsertUser", [identity_key])
        return result

    def get_or_create_user_id(self, identity_key: str) -> int:
        """Get or create a user by identity key."""
        result = self.find_or_insert_user(identity_key)
        # TS-compatible format: { user: { userId: ... }, isNew: boolean }
        user = result.get("user", {})
        return user.get("userId", user.get("user_id", 0))

    def list_outputs(
        self,
        auth: dict[str, Any],
        args: dict[str, Any],
    ) -> dict[str, Any]:
        """List outputs."""
        result = self._rpc_call("listOutputs", [auth, args])
        return result

    def list_actions(
        self,
        auth: dict[str, Any],
        args: dict[str, Any],
    ) -> dict[str, Any]:
        """List transaction actions."""
        result = self._rpc_call("listActions", [auth, args])
        return result

    def list_certificates(
        self,
        auth: dict[str, Any],
        args: dict[str, Any],
    ) -> dict[str, Any]:
        """List certificates."""
        result = self._rpc_call("listCertificates", [auth, args])
        return result

    def create_action(
        self,
        auth: dict[str, Any],
        args: dict[str, Any],
    ) -> dict[str, Any]:
        """Create transaction action."""
        result = self._rpc_call("createAction", [auth, args])
        return result

    def process_action(
        self,
        auth: dict[str, Any],
        args: dict[str, Any],
    ) -> dict[str, Any]:
        """Process transaction action."""
        result = self._rpc_call("processAction", [auth, args])
        return result

    def abort_action(
        self,
        auth: dict[str, Any],
        args: dict[str, Any],
    ) -> dict[str, Any]:
        """Abort transaction action."""
        result = self._rpc_call("abortAction", [auth, args])
        return result

    def internalize_action(
        self,
        auth: dict[str, Any],
        args: dict[str, Any],
    ) -> dict[str, Any]:
        """Internalize transaction action."""
        result = self._rpc_call("internalizeAction", [auth, args])
        return result

    def relinquish_output(
        self,
        auth: dict[str, Any],
        args: dict[str, Any],
    ) -> int:
        """Relinquish output."""
        result = self._rpc_call("relinquishOutput", [auth, args])
        return int(result)

    def relinquish_certificate(
        self,
        auth: dict[str, Any],
        args: dict[str, Any],
    ) -> int:
        """Relinquish certificate."""
        result = self._rpc_call("relinquishCertificate", [auth, args])
        return int(result)

    def destroy(self) -> None:
        """Destroy storage."""
        self._rpc_call("destroy", [])

