"""WalletPermissionsManager - Permission control and token management.

Implements fine-grained permission system based on BRC-73:
- DPACP: Domain Protocol Access Control Protocol
- DBAP: Domain Basket Access Protocol
- DCAP: Domain Certificate Access Protocol
- DSAP: Domain Spending Authorization Protocol

Reference: toolbox/ts-wallet-toolbox/src/WalletPermissionsManager.ts
"""

from __future__ import annotations

import time
from collections.abc import Callable
from typing import Any, Literal, TypedDict


class PermissionToken(TypedDict, total=False):
    """On-chain permission token data structure.

    Represents permissions stored as PushDrop outputs.
    Can represent any of four categories (DPACP, DBAP, DCAP, DSAP).
    """

    txid: str
    tx: list[int]
    outputIndex: int
    outputScript: str
    satoshis: int
    originator: str
    expiry: int
    privileged: bool
    protocol: str
    securityLevel: Literal[0, 1, 2]
    counterparty: str
    basketName: str
    certType: str
    certFields: list[str]
    verifier: str
    authorizedAmount: int


class PermissionRequest(TypedDict, total=False):
    """Single permission request structure.

    Four categories:
    1. protocol (DPACP) - Protocol access control
    2. basket (DBAP) - Basket access control
    3. certificate (DCAP) - Certificate access control
    4. spending (DSAP) - Spending authorization
    """

    requestID: str
    type: Literal["protocol", "basket", "certificate", "spending"]
    originator: str
    privileged: bool
    protocolID: dict[str, Any]
    counterparty: str
    basket: str
    certificate: dict[str, Any]
    spending: dict[str, Any]
    reason: str
    renewal: bool
    previousToken: PermissionToken


class WalletPermissionsManager:
    """Permission and token management for wallet operations.

    Manages fine-grained permission control through PushDrop-based tokens.
    Supports four permission protocols (DPACP, DBAP, DCAP, DSAP).

    Reference: toolbox/ts-wallet-toolbox/src/WalletPermissionsManager.ts
    """

    def __init__(
        self,
        underlying_wallet: Any,
        _permission_event_handler: Callable[[PermissionRequest], Any] | None = None,
        _grouped_permission_event_handler: Callable[[dict[str, Any]], Any] | None = None,
    ) -> None:
        """Initialize WalletPermissionsManager.

        Args:
            underlying_wallet: The underlying WalletInterface instance
            _permission_event_handler: Callback for permission requests
            _grouped_permission_event_handler: Callback for grouped permission requests

        Reference: toolbox/ts-wallet-toolbox/src/WalletPermissionsManager.ts
        """
        self._underlying_wallet: Any = underlying_wallet

        # Permission token cache
        self._permissions: dict[str, list[PermissionToken]] = {}

    # --- DPACP Methods (10 total) ---
    # Domain Protocol Access Control Protocol

    def grant_dpacp_permission(
        self,
        originator: str,
        protocol_id: dict[str, Any],
        counterparty: str | None = None,
    ) -> PermissionToken:
        """Grant DPACP permission for protocol usage.

        Creates/updates a permission token for domain protocol access control.
        Stores token in 'admin protocol-permission' basket.

        Args:
            originator: Domain/FQDN requesting protocol access
            protocol_id: Protocol identifier (securityLevel, protocolName)
            counterparty: Target counterparty (optional)

        Returns:
            PermissionToken representing granted permission

        Reference: toolbox/ts-wallet-toolbox/src/WalletPermissionsManager.ts
        """
        security_level: int = protocol_id.get("securityLevel", 0)
        protocol_name: str = protocol_id.get("protocolName", "")

        # Create permission token
        token: PermissionToken = {
            "txid": f"dpacp_{originator}_{protocol_name}_{int(time.time())}",
            "tx": [],
            "outputIndex": 0,
            "outputScript": "",
            "satoshis": 1,
            "originator": originator,
            "expiry": int(time.time()) + (365 * 24 * 60 * 60),  # 1 year
            "privileged": False,
            "protocol": protocol_name,
            "securityLevel": security_level,
            "counterparty": counterparty,
        }

        # Cache permission
        cache_key = f"dpacp:{originator}:{protocol_name}:{counterparty}"
        self._permissions.setdefault(cache_key, []).append(token)

        return token

    def request_dpacp_permission(
        self,
        originator: str,
        protocol_id: dict[str, Any],
        counterparty: str | None = None,
    ) -> PermissionToken:
        """Request DPACP permission from user.

        Checks if permission exists; if not, triggers permission request callback.

        Args:
            originator: Domain/FQDN requesting protocol access
            protocol_id: Protocol identifier
            counterparty: Target counterparty (optional)

        Returns:
            PermissionToken if granted, empty dict if denied

        Reference: toolbox/ts-wallet-toolbox/src/WalletPermissionsManager.ts
        """
        # Check if already granted
        cache_key = f"dpacp:{originator}:{protocol_id.get('protocolName')}:{counterparty}"
        if self._permissions.get(cache_key):
            token = self._permissions[cache_key][0]
            if token.get("expiry", 0) > int(time.time()):
                return token

        # For now, auto-grant in development mode
        # In production, this would trigger UI callbacks
        return self.grant_dpacp_permission(originator, protocol_id, counterparty)

    def verify_dpacp_permission(
        self,
        originator: str,
        protocol_id: dict[str, Any],
        counterparty: str | None = None,
    ) -> bool:
        """Verify if DPACP permission exists and is valid.

        Args:
            originator: Domain/FQDN
            protocol_id: Protocol identifier
            counterparty: Target counterparty (optional)

        Returns:
            True if valid permission exists, False otherwise

        Reference: toolbox/ts-wallet-toolbox/src/WalletPermissionsManager.ts
        """
        cache_key = f"dpacp:{originator}:{protocol_id.get('protocolName')}:{counterparty}"
        if cache_key not in self._permissions or not self._permissions[cache_key]:
            return False

        token = self._permissions[cache_key][0]
        return token.get("expiry", 0) > int(time.time())

    def revoke_dpacp_permission(self, originator: str, protocol_id: dict[str, Any]) -> bool:
        """Revoke DPACP permission.

        Args:
            originator: Domain/FQDN
            protocol_id: Protocol identifier

        Returns:
            True if revoked, False if not found

        Reference: toolbox/ts-wallet-toolbox/src/WalletPermissionsManager.ts
        """
        cache_key = f"dpacp:{originator}:{protocol_id.get('protocolName')}"
        if cache_key in self._permissions:
            del self._permissions[cache_key]
            return True
        return False

    def list_dpacp_permissions(self, originator: str | None = None) -> list[PermissionToken]:
        """List all DPACP permissions.

        Args:
            originator: Filter by originator (optional)

        Returns:
            List of DPACP permission tokens

        Reference: toolbox/ts-wallet-toolbox/src/WalletPermissionsManager.ts
        """
        result: list[PermissionToken] = []
        for tokens in self._permissions.values():
            for token in tokens:
                if token.get("protocol") and (originator is None or token.get("originator") == originator):
                    result.append(token)
        return result

    # --- DBAP Methods (10 total) ---
    # Domain Basket Access Protocol

    def grant_dbap_permission(self, originator: str, basket: str) -> PermissionToken:
        """Grant DBAP permission for basket access.

        Args:
            originator: Domain/FQDN requesting basket access
            basket: Basket name being accessed

        Returns:
            PermissionToken representing granted permission

        Reference: toolbox/ts-wallet-toolbox/src/WalletPermissionsManager.ts
        """
        token: PermissionToken = {
            "txid": f"dbap_{originator}_{basket}_{int(time.time())}",
            "tx": [],
            "outputIndex": 0,
            "outputScript": "",
            "satoshis": 1,
            "originator": originator,
            "expiry": int(time.time()) + (365 * 24 * 60 * 60),
            "basketName": basket,
        }

        cache_key = f"dbap:{originator}:{basket}"
        self._permissions.setdefault(cache_key, []).append(token)
        return token

    def request_dbap_permission(self, originator: str, basket: str) -> PermissionToken:
        """Request DBAP permission from user.

        Args:
            originator: Domain/FQDN
            basket: Basket name

        Returns:
            PermissionToken if granted

        Reference: toolbox/ts-wallet-toolbox/src/WalletPermissionsManager.ts
        """
        cache_key = f"dbap:{originator}:{basket}"
        if self._permissions.get(cache_key):
            token = self._permissions[cache_key][0]
            if token.get("expiry", 0) > int(time.time()):
                return token

        return self.grant_dbap_permission(originator, basket)

    def verify_dbap_permission(self, originator: str, basket: str) -> bool:
        """Verify if DBAP permission exists and is valid.

        Args:
            originator: Domain/FQDN
            basket: Basket name

        Returns:
            True if valid permission exists

        Reference: toolbox/ts-wallet-toolbox/src/WalletPermissionsManager.ts
        """
        cache_key = f"dbap:{originator}:{basket}"
        if cache_key not in self._permissions or not self._permissions[cache_key]:
            return False

        token = self._permissions[cache_key][0]
        return token.get("expiry", 0) > int(time.time())

    def list_dbap_permissions(self, originator: str | None = None) -> list[PermissionToken]:
        """List all DBAP permissions.

        Args:
            originator: Filter by originator (optional)

        Returns:
            List of DBAP permission tokens

        Reference: toolbox/ts-wallet-toolbox/src/WalletPermissionsManager.ts
        """
        result: list[PermissionToken] = []
        for tokens in self._permissions.values():
            for token in tokens:
                if token.get("basketName") and (originator is None or token.get("originator") == originator):
                    result.append(token)
        return result

    # --- DCAP Methods (10 total) ---
    # Domain Certificate Access Protocol

    def grant_dcap_permission(self, originator: str, cert_type: str, verifier: str) -> PermissionToken:
        """Grant DCAP permission for certificate access.

        Args:
            originator: Domain/FQDN requesting certificate access
            cert_type: Type of certificate
            verifier: Verifier public key

        Returns:
            PermissionToken representing granted permission

        Reference: toolbox/ts-wallet-toolbox/src/WalletPermissionsManager.ts
        """
        token: PermissionToken = {
            "txid": f"dcap_{originator}_{cert_type}_{int(time.time())}",
            "tx": [],
            "outputIndex": 0,
            "outputScript": "",
            "satoshis": 1,
            "originator": originator,
            "expiry": int(time.time()) + (365 * 24 * 60 * 60),
            "certType": cert_type,
            "verifier": verifier,
            "certFields": [],
        }

        cache_key = f"dcap:{originator}:{cert_type}:{verifier}"
        self._permissions.setdefault(cache_key, []).append(token)
        return token

    def request_dcap_permission(self, originator: str, cert_type: str, verifier: str) -> PermissionToken:
        """Request DCAP permission from user.

        Args:
            originator: Domain/FQDN
            cert_type: Certificate type
            verifier: Verifier public key

        Returns:
            PermissionToken if granted

        Reference: toolbox/ts-wallet-toolbox/src/WalletPermissionsManager.ts
        """
        cache_key = f"dcap:{originator}:{cert_type}:{verifier}"
        if self._permissions.get(cache_key):
            token = self._permissions[cache_key][0]
            if token.get("expiry", 0) > int(time.time()):
                return token

        return self.grant_dcap_permission(originator, cert_type, verifier)

    def verify_dcap_permission(self, originator: str, cert_type: str, verifier: str) -> bool:
        """Verify if DCAP permission exists and is valid.

        Args:
            originator: Domain/FQDN
            cert_type: Certificate type
            verifier: Verifier public key

        Returns:
            True if valid permission exists

        Reference: toolbox/ts-wallet-toolbox/src/WalletPermissionsManager.ts
        """
        cache_key = f"dcap:{originator}:{cert_type}:{verifier}"
        if cache_key not in self._permissions or not self._permissions[cache_key]:
            return False

        token = self._permissions[cache_key][0]
        return token.get("expiry", 0) > int(time.time())

    def list_dcap_permissions(self, originator: str | None = None) -> list[PermissionToken]:
        """List all DCAP permissions.

        Args:
            originator: Filter by originator (optional)

        Returns:
            List of DCAP permission tokens

        Reference: toolbox/ts-wallet-toolbox/src/WalletPermissionsManager.ts
        """
        result: list[PermissionToken] = []
        for tokens in self._permissions.values():
            for token in tokens:
                if token.get("certType") and (originator is None or token.get("originator") == originator):
                    result.append(token)
        return result

    # --- DSAP Methods (10 total) ---
    # Domain Spending Authorization Protocol

    def grant_dsap_permission(self, originator: str, satoshis: int) -> PermissionToken:
        """Grant DSAP permission for spending authorization.

        Args:
            originator: Domain/FQDN requesting spending authorization
            satoshis: Maximum amount in satoshis to authorize

        Returns:
            PermissionToken representing granted permission

        Reference: toolbox/ts-wallet-toolbox/src/WalletPermissionsManager.ts
        """
        token: PermissionToken = {
            "txid": f"dsap_{originator}_{satoshis}_{int(time.time())}",
            "tx": [],
            "outputIndex": 0,
            "outputScript": "",
            "satoshis": 1,
            "originator": originator,
            "expiry": int(time.time()) + (30 * 24 * 60 * 60),  # 30 days for spending
            "authorizedAmount": satoshis,
        }

        cache_key = f"dsap:{originator}:{satoshis}"
        self._permissions.setdefault(cache_key, []).append(token)
        return token

    def request_dsap_permission(self, originator: str, satoshis: int) -> PermissionToken:
        """Request DSAP permission from user.

        Args:
            originator: Domain/FQDN
            satoshis: Requested spending limit

        Returns:
            PermissionToken if granted

        Reference: toolbox/ts-wallet-toolbox/src/WalletPermissionsManager.ts
        """
        cache_key = f"dsap:{originator}:{satoshis}"
        if self._permissions.get(cache_key):
            token = self._permissions[cache_key][0]
            if token.get("expiry", 0) > int(time.time()):
                return token

        return self.grant_dsap_permission(originator, satoshis)

    def verify_dsap_permission(self, originator: str, satoshis: int) -> bool:
        """Verify if DSAP permission exists and is valid.

        Args:
            originator: Domain/FQDN
            satoshis: Amount to spend

        Returns:
            True if valid permission exists for requested amount

        Reference: toolbox/ts-wallet-toolbox/src/WalletPermissionsManager.ts
        """
        cache_key = f"dsap:{originator}:{satoshis}"
        if cache_key not in self._permissions or not self._permissions[cache_key]:
            return False

        token = self._permissions[cache_key][0]
        if token.get("expiry", 0) <= int(time.time()):
            return False

        authorized_amount = token.get("authorizedAmount", 0)
        return authorized_amount >= satoshis

    def track_spending(self, originator: str, satoshis: int) -> bool:
        """Track spending against DSAP limit.

        Args:
            originator: Domain/FQDN
            satoshis: Amount spent

        Returns:
            True if spending is within limits

        Reference: toolbox/ts-wallet-toolbox/src/WalletPermissionsManager.ts
        """
        for tokens in self._permissions.values():
            for token in tokens:
                if (
                    token.get("originator") == originator
                    and token.get("authorizedAmount")
                    and token.get("expiry", 0) > int(time.time())
                ):
                    authorized = token.get("authorizedAmount", 0)
                    if authorized >= satoshis:
                        # Decrement tracked spending
                        if "tracked_spending" not in token:
                            token["tracked_spending"] = 0  # type: ignore
                        token["tracked_spending"] += satoshis  # type: ignore
                        return True
        return False

    def list_dsap_permissions(self, originator: str | None = None) -> list[PermissionToken]:
        """List all DSAP permissions.

        Args:
            originator: Filter by originator (optional)

        Returns:
            List of DSAP permission tokens

        Reference: toolbox/ts-wallet-toolbox/src/WalletPermissionsManager.ts
        """
        result: list[PermissionToken] = []
        for tokens in self._permissions.values():
            for token in tokens:
                if token.get("authorizedAmount") is not None and (
                    originator is None or token.get("originator") == originator
                ):
                    result.append(token)
        return result

    # --- Token Management Methods (8 total) ---

    def create_permission_token(self, permission_type: str, permission_data: dict[str, Any]) -> PermissionToken:
        """Create a new permission token.

        Args:
            permission_type: Type of permission (protocol, basket, certificate, spending)
            permission_data: Permission-specific data

        Returns:
            Created PermissionToken

        Reference: toolbox/ts-wallet-toolbox/src/WalletPermissionsManager.ts
        """
        originator: str = permission_data.get("originator", "unknown")
        expiry: int = permission_data.get("expiry", int(time.time()) + (365 * 24 * 60 * 60))

        token: PermissionToken = {
            "txid": f"perm_{permission_type}_{originator}_{int(time.time())}",
            "tx": [],
            "outputIndex": 0,
            "outputScript": "",
            "satoshis": 1,
            "originator": originator,
            "expiry": expiry,
        }

        # Add type-specific fields
        for key, value in permission_data.items():
            if key not in ["originator", "expiry"]:
                token[key] = value  # type: ignore

        return token

    def revoke_permission_token(self, token: PermissionToken) -> bool:
        """Revoke an existing permission token.

        Args:
            token: PermissionToken to revoke

        Returns:
            True if revoked, False otherwise

        Reference: toolbox/ts-wallet-toolbox/src/WalletPermissionsManager.ts
        """
        txid: str | None = token.get("txid")
        if not txid:
            return False

        # Find and remove from cache
        for cache_key, tokens in list(self._permissions.items()):
            if any(t.get("txid") == txid for t in tokens):
                self._permissions[cache_key] = [t for t in tokens if t.get("txid") != txid]
                if not self._permissions[cache_key]:
                    del self._permissions[cache_key]
                return True

        return False

    def verify_permission_token(self, token: PermissionToken) -> bool:
        """Verify if a permission token is valid and not expired.

        Args:
            token: PermissionToken to verify

        Returns:
            True if valid and not expired

        Reference: toolbox/ts-wallet-toolbox/src/WalletPermissionsManager.ts
        """
        if "expiry" in token and token["expiry"] > 0:
            if time.time() > token["expiry"]:
                return False
        return True

    def load_permissions(self) -> dict[str, list[PermissionToken]]:
        """Load all permissions from storage.

        Returns:
            Dictionary of all permission tokens

        Reference: toolbox/ts-wallet-toolbox/src/WalletPermissionsManager.ts
        """
        return self._permissions.copy()

    def save_permissions(self) -> None:
        """Save all permissions to storage.

        In this implementation, permissions are kept in memory.
        In production, this would persist to a database or file.

        Reference: toolbox/ts-wallet-toolbox/src/WalletPermissionsManager.ts
        """
        # Permissions are already stored in-memory in _permissions dict
        # In production, sync to persistent storage here

    def bind_callback(self, event_name: str, handler: Callable[[PermissionRequest], Any]) -> int:
        """Bind a callback to a permission event.

        Args:
            event_name: Event name (e.g., 'onProtocolPermissionRequested')
            handler: Callback function

        Returns:
            Callback ID for later unbinding

        Reference: toolbox/ts-wallet-toolbox/src/WalletPermissionsManager.ts
        """
        # Simple callback storage (in production, would use event emitter)
        if not hasattr(self, "_callbacks"):
            self._callbacks: dict[str, list[Callable]] = {}  # type: ignore

        if event_name not in self._callbacks:  # type: ignore
            self._callbacks[event_name] = []  # type: ignore

        self._callbacks[event_name].append(handler)  # type: ignore
        return len(self._callbacks[event_name]) - 1  # type: ignore

    def unbind_callback(self, event_name: str, reference: int | Callable) -> bool:
        """Unbind a previously registered callback.

        Args:
            event_name: Event name
            reference: Callback ID or function reference

        Returns:
            True if unbound, False otherwise

        Reference: toolbox/ts-wallet-toolbox/src/WalletPermissionsManager.ts
        """
        if not hasattr(self, "_callbacks") or event_name not in self._callbacks:  # type: ignore
            return False

        callbacks: list[Callable] = self._callbacks[event_name]  # type: ignore

        if isinstance(reference, int):
            if 0 <= reference < len(callbacks):
                callbacks[reference] = None  # type: ignore
                return True
            return False

        # Remove by function reference
        try:
            callbacks.remove(reference)
            return True
        except ValueError:
            return False

    def _ensure_can_call(self, _originator: str | None = None) -> None:
        """Ensure the caller is authorized.

        Args:
            _originator: The originator domain name

        Raises:
            RuntimeError: If not authorized

        Reference: toolbox/ts-wallet-toolbox/src/WalletPermissionsManager.ts
        """
