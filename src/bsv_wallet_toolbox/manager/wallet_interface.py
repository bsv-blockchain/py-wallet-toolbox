"""WalletInterface protocol definition.

Defines the expected interface for wallet implementations used by the
CWI wallet manager and permissions manager.

Reference: @bsv/sdk WalletInterface
"""

from __future__ import annotations

from typing import Any, Protocol


class WalletInterface(Protocol):
    """Protocol defining the wallet interface expected by managers.

    This protocol defines the methods that wallet implementations must provide
    to work with CWIStyleWalletManager and WalletPermissionsManager.

    Reference: @bsv/sdk WalletInterface
    """

    def create_action(self, args: dict[str, Any], originator: str | None = None) -> dict[str, Any]:
        """Create a wallet action (transaction).

        Args:
            args: Action arguments (inputs, outputs, options, etc.)
            originator: Domain/FQDN of the originator

        Returns:
            Action result with txid, tx data, etc.
        """
        ...

    def sign_action(self, args: dict[str, Any], originator: str | None = None) -> dict[str, Any]:
        """Sign a wallet action.

        Args:
            args: Signing arguments (reference, spends, etc.)
            originator: Domain/FQDN of the originator

        Returns:
            Signing result with txid, tx data, etc.
        """
        ...

    def abort_action(self, args: dict[str, Any], originator: str | None = None) -> dict[str, Any]:
        """Abort a wallet action.

        Args:
            args: Abort arguments (reference)
            originator: Domain/FQDN of the originator

        Returns:
            Abort result
        """
        ...

    def list_actions(self, args: dict[str, Any], originator: str | None = None) -> dict[str, Any]:
        """List wallet actions.

        Args:
            args: List arguments (filters, etc.)
            originator: Domain/FQDN of the originator

        Returns:
            List of actions
        """
        ...

    def list_outputs(self, args: dict[str, Any], originator: str | None = None) -> dict[str, Any]:
        """List wallet outputs.

        Args:
            args: List arguments (basket, etc.)
            originator: Domain/FQDN of the originator

        Returns:
            List of outputs
        """
        ...

    def relinquish_output(self, args: dict[str, Any], originator: str | None = None) -> dict[str, Any]:
        """Relinquish (spend) an output.

        Args:
            args: Relinquish arguments (output, basket, etc.)
            originator: Domain/FQDN of the originator

        Returns:
            Relinquish result
        """
        ...

    def internalize_action(self, args: dict[str, Any], originator: str | None = None) -> dict[str, Any]:
        """Internalize an action (add to wallet).

        Args:
            args: Internalize arguments (tx, etc.)
            originator: Domain/FQDN of the originator

        Returns:
            Internalize result
        """
        ...

    def create_signature(self, args: dict[str, Any], originator: str | None = None) -> dict[str, Any]:
        """Create a cryptographic signature.

        Args:
            args: Signature arguments (data, keyID, etc.)
            originator: Domain/FQDN of the originator

        Returns:
            Signature result
        """
        ...

    def verify_signature(self, args: dict[str, Any], originator: str | None = None) -> dict[str, Any]:
        """Verify a cryptographic signature.

        Args:
            args: Verification arguments (signature, data, etc.)
            originator: Domain/FQDN of the originator

        Returns:
            Verification result
        """
        ...

    def encrypt(self, args: dict[str, Any], originator: str | None = None) -> dict[str, Any]:
        """Encrypt data.

        Args:
            args: Encryption arguments (plaintext, protocolID, etc.)
            originator: Domain/FQDN of the originator

        Returns:
            Encryption result
        """
        ...

    def decrypt(self, args: dict[str, Any], originator: str | None = None) -> dict[str, Any]:
        """Decrypt data.

        Args:
            args: Decryption arguments (ciphertext, etc.)
            originator: Domain/FQDN of the originator

        Returns:
            Decryption result
        """
        ...

    def create_hmac(self, args: dict[str, Any], originator: str | None = None) -> dict[str, Any]:
        """Create HMAC.

        Args:
            args: HMAC arguments (data, etc.)
            originator: Domain/FQDN of the originator

        Returns:
            HMAC result
        """
        ...

    def verify_hmac(self, args: dict[str, Any], originator: str | None = None) -> dict[str, Any]:
        """Verify HMAC.

        Args:
            args: HMAC verification arguments
            originator: Domain/FQDN of the originator

        Returns:
            Verification result
        """
        ...

    def get_public_key(self, args: dict[str, Any], originator: str | None = None) -> dict[str, Any]:
        """Get public key.

        Args:
            args: Public key arguments (keyID, etc.)
            originator: Domain/FQDN of the originator

        Returns:
            Public key result
        """
        ...

    def reveal_counterparty_key_linkage(self, args: dict[str, Any], originator: str | None = None) -> dict[str, Any]:
        """Reveal counterparty key linkage.

        Args:
            args: Key linkage arguments
            originator: Domain/FQDN of the originator

        Returns:
            Key linkage result
        """
        ...

    def reveal_specific_key_linkage(self, args: dict[str, Any], originator: str | None = None) -> dict[str, Any]:
        """Reveal specific key linkage.

        Args:
            args: Key linkage arguments
            originator: Domain/FQDN of the originator

        Returns:
            Key linkage result
        """
        ...

    def acquire_certificate(self, args: dict[str, Any], originator: str | None = None) -> dict[str, Any]:
        """Acquire certificate.

        Args:
            args: Certificate arguments
            originator: Domain/FQDN of the originator

        Returns:
            Certificate result
        """
        ...

    def list_certificates(self, args: dict[str, Any], originator: str | None = None) -> dict[str, Any]:
        """List certificates.

        Args:
            args: List arguments
            originator: Domain/FQDN of the originator

        Returns:
            Certificates list
        """
        ...

    def prove_certificate(self, args: dict[str, Any], originator: str | None = None) -> dict[str, Any]:
        """Prove certificate.

        Args:
            args: Proof arguments
            originator: Domain/FQDN of the originator

        Returns:
            Proof result
        """
        ...

    def disclose_certificate(self, args: dict[str, Any], originator: str | None = None) -> dict[str, Any]:
        """Disclose certificate.

        Args:
            args: Disclosure arguments
            originator: Domain/FQDN of the originator

        Returns:
            Disclosure result
        """
        ...

    def relinquish_certificate(self, args: dict[str, Any], originator: str | None = None) -> dict[str, Any]:
        """Relinquish certificate.

        Args:
            args: Relinquish arguments
            originator: Domain/FQDN of the originator

        Returns:
            Relinquish result
        """
        ...

    def discover_by_identity_key(self, args: dict[str, Any], originator: str | None = None) -> dict[str, Any]:
        """Discover by identity key.

        Args:
            args: Discovery arguments
            originator: Domain/FQDN of the originator

        Returns:
            Discovery result
        """
        ...

    def discover_by_attributes(self, args: dict[str, Any], originator: str | None = None) -> dict[str, Any]:
        """Discover by attributes.

        Args:
            args: Discovery arguments
            originator: Domain/FQDN of the originator

        Returns:
            Discovery result
        """
        ...

    def get_network(self, originator: str | None = None) -> dict[str, Any]:
        """Get network information.

        Args:
            originator: Domain/FQDN of the originator

        Returns:
            Network information
        """
        ...

    def get_version(self, originator: str | None = None) -> dict[str, Any]:
        """Get version information.

        Args:
            originator: Domain/FQDN of the originator

        Returns:
            Version information
        """
        ...
