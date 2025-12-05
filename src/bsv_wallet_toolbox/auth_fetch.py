"""AuthFetch - Authenticated HTTP client for BSV wallet operations.

Provides BRC-104 compliant authenticated HTTP requests using wallet-based authentication.
This module wraps py-sdk's AuthFetch implementation.

Reference:
  - py-sdk/bsv/auth/clients/auth_fetch.py
  - wallet-toolbox/src/storage/remoting/StorageClient.ts
"""

from __future__ import annotations

from typing import Any, Optional

# Re-export from py-sdk for full BRC-104 authentication
from bsv.auth.clients.auth_fetch import (
    AuthFetch as _AuthFetch,
    AuthPeer,
    SimplifiedFetchRequestOptions,
    p2pkh_locking_script_from_pubkey,
)
from bsv.auth.session_manager import DefaultSessionManager
from bsv.auth.requested_certificate_set import RequestedCertificateSet


class AuthFetch:
    """Authenticated HTTP client using py-sdk BRC-104 implementation.

    This class wraps py-sdk's AuthFetch to provide authenticated HTTP requests
    for BSV wallet operations, following the same pattern as TypeScript StorageClient.

    Reference: wallet-toolbox/src/storage/remoting/StorageClient.ts

    Usage:
        >>> from bsv_wallet_toolbox import AuthFetch, Wallet
        >>> wallet = Wallet(...)
        >>> auth_client = AuthFetch(wallet)
        >>> response = auth_client.fetch("https://api.example.com/data", options)
    """

    def __init__(
        self,
        wallet: Any,
        requested_certificates: Optional[RequestedCertificateSet] = None,
        session_manager: Optional[DefaultSessionManager] = None,
    ):
        """Initialize AuthFetch.

        Args:
            wallet: Wallet instance implementing BRC-100 WalletInterface.
                    Must have get_public_key(), create_signature(), and create_action() methods.
            requested_certificates: Optional certificate requirements for mutual auth.
            session_manager: Optional session manager for auth sessions (defaults to DefaultSessionManager).
        """
        self._impl = _AuthFetch(
            wallet=wallet,
            requested_certs=requested_certificates,
            session_manager=session_manager,
        )

    def fetch(
        self,
        url: str,
        config: Optional[SimplifiedFetchRequestOptions] = None,
    ):
        """Make authenticated HTTP request.

        Handles BRC-104 mutual authentication and 402 Payment Required responses
        automatically when the wallet supports create_action().

        Args:
            url: Request URL
            config: Request options (method, headers, body)

        Returns:
            requests.Response object

        Raises:
            Exception: On request failure or authentication error
        """
        return self._impl.fetch(url, config)

    def send_certificate_request(
        self,
        base_url: str,
        certificates_to_request: Any,
    ):
        """Request certificates from a peer.

        Args:
            base_url: Base URL of the peer
            certificates_to_request: Certificate requirements

        Returns:
            List of received certificates
        """
        return self._impl.send_certificate_request(base_url, certificates_to_request)

    def consume_received_certificates(self):
        """Consume and return certificates received during fetch operations.

        Returns:
            List of VerifiableCertificate objects received since last call
        """
        return self._impl.consume_received_certificates()

    @property
    def certificates_received(self):
        """Access list of received certificates."""
        return self._impl.certificates_received

    @property
    def peers(self):
        """Access peer connections."""
        return self._impl.peers


# Re-export for convenience
__all__ = [
    "AuthFetch",
    "AuthPeer",
    "SimplifiedFetchRequestOptions",
    "RequestedCertificateSet",
    "DefaultSessionManager",
    "p2pkh_locking_script_from_pubkey",
]
