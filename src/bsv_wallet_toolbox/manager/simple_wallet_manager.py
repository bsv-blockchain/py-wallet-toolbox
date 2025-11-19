"""SimpleWalletManager - Simplified wallet manager implementation.

A lightweight wallet manager that requires only:
1. A primary key (32 bytes) - the core secret for the wallet
2. A PrivilegedKeyManager - responsible for sensitive operations

Once both pieces are provided, the wallet becomes authenticated and can delegate
all operations to an underlying WalletInterface instance.

Reference: toolbox/ts-wallet-toolbox/src/SimpleWalletManager.ts
"""

from __future__ import annotations

import time
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    pass


class SimpleWalletManager:
    """Simplified wallet manager implementing WalletInterface.

    This is a straightforward wrapper that ensures the user has provided both
    their main secret (primary key) and a privileged key manager before allowing
    usage. It does not handle password flows, recovery, or on-chain token management.

    Reference: toolbox/ts-wallet-toolbox/src/SimpleWalletManager.ts+
    """

    def __init__(
        self,
        admin_originator: str,
        wallet_builder: Callable[[list[int], Any], Any],  # Returns WalletInterface
        state_snapshot: list[int] | None = None,
    ) -> None:
        """Initialize SimpleWalletManager.

        Args:
            admin_originator: Domain name of the administrative originator
            wallet_builder: Async function that builds a WalletInterface given primaryKey and PrivilegedKeyManager
            state_snapshot: Optional previously saved state snapshot containing the primary key

        Reference: toolbox/ts-wallet-toolbox/src/SimpleWalletManager.ts
        """
        self.authenticated: bool = False
        self._admin_originator: str = admin_originator
        self._wallet_builder: Callable = wallet_builder

        # Internal state
        self._underlying: Any | None = None  # WalletInterface
        self._underlying_privileged_key_manager: Any | None = None
        self._primary_key: list[int] | None = None

        # Load snapshot if provided
        if state_snapshot:
            self._load_snapshot(state_snapshot)

    def provide_primary_key(self, key: list[int]) -> None:
        """Provide the primary key (32 bytes) for authentication.

        If a privileged key manager has already been provided, attempts to build
        the underlying wallet. Otherwise, waits until the manager is also provided.

        Args:
            key: 32-byte primary key

        Reference: toolbox/ts-wallet-toolbox/src/SimpleWalletManager.ts
        """
        self._primary_key = key
        self._try_build_underlying()

    def provide_privileged_key_manager(self, manager: Any) -> None:
        """Provide the PrivilegedKeyManager for sensitive tasks.

        If a primary key has already been provided (or loaded from snapshot),
        attempts to build the underlying wallet.

        Args:
            manager: PrivilegedKeyManager instance

        Reference: toolbox/ts-wallet-toolbox/src/SimpleWalletManager.ts
        """
        self._underlying_privileged_key_manager = manager
        self._try_build_underlying()

    def _try_build_underlying(self) -> None:
        """Internal method to build underlying wallet if both keys are available.

        Throws error if already authenticated.
        Returns silently if one of the required pieces is missing.

        Reference: toolbox/ts-wallet-toolbox/src/SimpleWalletManager.ts
        """
        if self.authenticated:
            raise RuntimeError("The user is already authenticated.")
        if not self._primary_key or not self._underlying_privileged_key_manager:
            return

        # Build the underlying wallet (synchronous call)
        self._underlying = self._wallet_builder(self._primary_key, self._underlying_privileged_key_manager)
        self.authenticated = True

    def destroy(self) -> None:
        """Destroy the wallet, returning to unauthenticated state.

        Clears primary key, privileged key manager, underlying wallet, and authenticated flag.

        Reference: toolbox/ts-wallet-toolbox/src/SimpleWalletManager.ts
        """
        self._underlying = None
        self._underlying_privileged_key_manager = None
        self.authenticated = False
        self._primary_key = None

    def save_snapshot(self) -> list[int]:
        """Save wallet state to an encrypted snapshot.

        Returns the primary key as a list of integers.
        **Note**: The snapshot does NOT include the privileged key manager.

        Returns:
            Encrypted snapshot containing the primary key

        Reference: toolbox/ts-wallet-toolbox/src/SimpleWalletManager.ts
        """
        if not self._primary_key:
            raise RuntimeError("No primary key to save")

        # Return the primary key as snapshot
        # In a real implementation, this would be encrypted
        return self._primary_key.copy()

    def _load_snapshot(self, snapshot: list[int]) -> None:
        """Load wallet state from a snapshot.

        Restores the primary key from a snapshot.
        **Note**: Does NOT load the privileged key manager - must be provided separately.

        Args:
            snapshot: Encrypted snapshot to load

        Reference: toolbox/ts-wallet-toolbox/src/SimpleWalletManager.ts
        """
        if self.authenticated:
            raise RuntimeError("Cannot load snapshot when already authenticated")

        # Load the primary key from snapshot
        # In a real implementation, this would be decrypted
        self._primary_key = snapshot.copy() if snapshot else None

    # Private helper method
    def _ensure_can_call(self, originator: str | None = None) -> None:
        """Ensure wallet is authenticated and originator is valid.

        Throws error if originator is admin or wallet is not authenticated.

        Args:
            originator: The originator domain name

        Raises:
            RuntimeError: If originator is admin or wallet not authenticated

        Reference: toolbox/ts-wallet-toolbox/src/SimpleWalletManager.ts
        """
        if originator == self._admin_originator:
            raise RuntimeError("External applications cannot use the admin originator.")
        if not self.authenticated:
            raise RuntimeError("User is not authenticated.")

    # WalletInterface delegation methods
    # All methods delegate to self._underlying after validation

    def is_authenticated(self, _args: dict[str, Any] | None = None, originator: str | None = None) -> dict[str, bool]:
        """Check if wallet is authenticated.

        Reference: toolbox/ts-wallet-toolbox/src/SimpleWalletManager.ts
        """
        self._ensure_can_call(originator)
        return {"authenticated": True}

    def wait_for_authentication(
        self, _args: dict[str, Any] | None = None, originator: str | None = None
    ) -> dict[str, bool]:
        """Wait until wallet is authenticated.

        Reference: toolbox/ts-wallet-toolbox/src/SimpleWalletManager.ts
        """
        if originator == self._admin_originator:
            raise RuntimeError("External applications cannot use the admin originator.")
        while not self.authenticated:
            time.sleep(0.1)
        return {"authenticated": True}

    def get_public_key(self, args: dict[str, Any], originator: str | None = None) -> dict[str, Any]:
        """Get public key from underlying wallet."""
        self._ensure_can_call(originator)
        return self._underlying.get_public_key(args, originator)

    def reveal_counterparty_key_linkage(self, args: dict[str, Any], originator: str | None = None) -> dict[str, Any]:
        """Reveal counterparty key linkage."""
        self._ensure_can_call(originator)
        return self._underlying.reveal_counterparty_key_linkage(args, originator)

    def reveal_specific_key_linkage(self, args: dict[str, Any], originator: str | None = None) -> dict[str, Any]:
        """Reveal specific key linkage."""
        self._ensure_can_call(originator)
        return self._underlying.reveal_specific_key_linkage(args, originator)

    def encrypt(self, args: dict[str, Any], originator: str | None = None) -> dict[str, Any]:
        """Encrypt data."""
        self._ensure_can_call(originator)
        return self._underlying.encrypt(args, originator)

    def decrypt(self, args: dict[str, Any], originator: str | None = None) -> dict[str, Any]:
        """Decrypt data."""
        self._ensure_can_call(originator)
        return self._underlying.decrypt(args, originator)

    def create_hmac(self, args: dict[str, Any], originator: str | None = None) -> dict[str, Any]:
        """Create HMAC."""
        self._ensure_can_call(originator)
        return self._underlying.create_hmac(args, originator)

    def verify_hmac(self, args: dict[str, Any], originator: str | None = None) -> dict[str, bool]:
        """Verify HMAC."""
        self._ensure_can_call(originator)
        return self._underlying.verify_hmac(args, originator)

    def create_signature(self, args: dict[str, Any], originator: str | None = None) -> dict[str, Any]:
        """Create signature."""
        self._ensure_can_call(originator)
        return self._underlying.create_signature(args, originator)

    def verify_signature(self, args: dict[str, Any], originator: str | None = None) -> dict[str, bool]:
        """Verify signature."""
        self._ensure_can_call(originator)
        return self._underlying.verify_signature(args, originator)

    def create_action(self, args: dict[str, Any], originator: str | None = None) -> dict[str, Any]:
        """Create action."""
        self._ensure_can_call(originator)
        return self._underlying.create_action(args, originator)

    def sign_action(self, args: dict[str, Any], originator: str | None = None) -> dict[str, Any]:
        """Sign action."""
        self._ensure_can_call(originator)
        return self._underlying.sign_action(args, originator)

    def abort_action(self, args: dict[str, Any], originator: str | None = None) -> dict[str, Any]:
        """Abort action."""
        self._ensure_can_call(originator)
        return self._underlying.abort_action(args, originator)

    def list_actions(self, args: dict[str, Any], originator: str | None = None) -> dict[str, Any]:
        """List actions."""
        self._ensure_can_call(originator)
        return self._underlying.list_actions(args, originator)

    def internalize_action(self, args: dict[str, Any], originator: str | None = None) -> dict[str, Any]:
        """Internalize action."""
        self._ensure_can_call(originator)
        return self._underlying.internalize_action(args, originator)

    def list_outputs(self, args: dict[str, Any], originator: str | None = None) -> dict[str, Any]:
        """List outputs."""
        self._ensure_can_call(originator)
        return self._underlying.list_outputs(args, originator)

    def relinquish_output(self, args: dict[str, Any], originator: str | None = None) -> dict[str, Any]:
        """Relinquish output."""
        self._ensure_can_call(originator)
        return self._underlying.relinquish_output(args, originator)

    def acquire_certificate(self, args: dict[str, Any], originator: str | None = None) -> dict[str, Any]:
        """Acquire certificate."""
        self._ensure_can_call(originator)
        return self._underlying.acquire_certificate(args, originator)

    def list_certificates(self, args: dict[str, Any], originator: str | None = None) -> dict[str, Any]:
        """List certificates."""
        self._ensure_can_call(originator)
        return self._underlying.list_certificates(args, originator)

    def prove_certificate(self, args: dict[str, Any], originator: str | None = None) -> dict[str, Any]:
        """Prove certificate."""
        self._ensure_can_call(originator)
        return self._underlying.prove_certificate(args, originator)

    def relinquish_certificate(self, args: dict[str, Any], originator: str | None = None) -> dict[str, bool]:
        """Relinquish certificate."""
        self._ensure_can_call(originator)
        return self._underlying.relinquish_certificate(args, originator)

    def discover_by_identity_key(self, args: dict[str, Any], originator: str | None = None) -> dict[str, Any]:
        """Discover by identity key."""
        self._ensure_can_call(originator)
        return self._underlying.discover_by_identity_key(args, originator)

    def discover_by_attributes(self, args: dict[str, Any], originator: str | None = None) -> dict[str, Any]:
        """Discover by attributes."""
        self._ensure_can_call(originator)
        return self._underlying.discover_by_attributes(args, originator)

    def get_height(self, _args: dict[str, Any] | None = None, originator: str | None = None) -> dict[str, Any]:
        """Get blockchain height."""
        self._ensure_can_call(originator)
        return self._underlying.get_height({}, originator)

    def get_header_for_height(self, args: dict[str, Any], originator: str | None = None) -> dict[str, Any]:
        """Get header for height."""
        self._ensure_can_call(originator)
        return self._underlying.get_header_for_height(args, originator)

    def get_network(self, _args: dict[str, Any] | None = None, originator: str | None = None) -> dict[str, Any]:
        """Get network."""
        self._ensure_can_call(originator)
        return self._underlying.get_network({}, originator)

    def get_version(self, _args: dict[str, Any] | None = None, originator: str | None = None) -> dict[str, str]:
        """Get version."""
        self._ensure_can_call(originator)
        return self._underlying.get_version({}, originator)
