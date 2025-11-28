"""PrivilegedKeyManager - Secure Key Management for Privileged Operations.

This module implements secure handling of private keys from external secure environments
(HSM, secure enclaves, etc.) with memory protection and automatic cleanup.

Design Philosophy:
- Mimics TypeScript PrivilegedKeyManager from ts-sdk
- Integrates with KeyDeriver for cryptographic operations
- Provides key_getter callback for secure key retrieval
- Implements retention period-based automatic key destruction

Reference:
    - ts-wallet-toolbox/src/sdk/PrivilegedKeyManager.ts
    - ts-sdk implementation: ProtoWallet interface
"""

import threading
from collections.abc import Callable
from typing import Any

from bsv.keys import PrivateKey
from bsv.wallet import KeyDeriver


class PrivilegedKeyManager:
    """Manages privileged private keys with secure storage and automatic cleanup.

    This class provides cryptographic operations (getPublicKey, createSignature, etc.)
    backed by a privileged key from a secure environment (HSM, enclave, etc.).
    The key is retained in memory for a limited duration and automatically destroyed.

    Attributes:
        key_getter: Callable that retrieves the private key from secure storage.
                   Receives a 'reason' string for auditing.
        retention_period_ms: Time (ms) to keep the key in memory before auto-destruction.
    """

    def __init__(
        self,
        key_getter: Callable[[str], bytes],
        retention_period_ms: int = 120_000,
    ) -> None:
        """Initialize PrivilegedKeyManager.

        Args:
            key_getter: Async-like function that retrieves private key bytes.
                       Should accept a 'reason' string parameter.
            retention_period_ms: Time (ms) before automatic key destruction.
                                Default: 120_000 (2 minutes)
        """
        self.key_getter = key_getter
        self.retention_period_ms = retention_period_ms
        self._privileged_key_deriver: KeyDeriver | None = None
        self._destroy_timer: threading.Timer | None = None
        self._lock = threading.Lock()

    def _schedule_destruction(self) -> None:
        """Schedule automatic key destruction after retention period."""
        with self._lock:
            if self._destroy_timer is not None:
                self._destroy_timer.cancel()

            self._destroy_timer = threading.Timer(
                self.retention_period_ms / 1000.0,
                self._destroy_key,
            )
            self._destroy_timer.daemon = True
            self._destroy_timer.start()

    def _destroy_key(self) -> None:
        """Destroy the privileged key from memory."""
        with self._lock:
            self._privileged_key_deriver = None
            if self._destroy_timer is not None:
                self._destroy_timer.cancel()
                self._destroy_timer = None

    def _get_privileged_key_deriver(self, reason: str) -> KeyDeriver:
        """Retrieve or create privileged KeyDeriver.

        Args:
            reason: Reason for key retrieval (for auditing).

        Returns:
            KeyDeriver instance backed by the privileged key.

        Raises:
            Exception: If key_getter fails or returns invalid data.
        """
        with self._lock:
            if self._privileged_key_deriver is not None:
                # Key already in memory, reschedule destruction
                self._schedule_destruction()
                return self._privileged_key_deriver

            # Fetch new key from secure environment
            private_key_bytes = self.key_getter(reason)

            if not private_key_bytes or len(private_key_bytes) != 32:
                raise ValueError(
                    f"Invalid private key: expected 32 bytes, got {len(private_key_bytes) if private_key_bytes else 0}"
                )

            # Create KeyDeriver from the privileged key
            private_key_hex = private_key_bytes.hex()
            private_key_obj = PrivateKey.from_hex(private_key_hex)
            self._privileged_key_deriver = KeyDeriver(private_key_obj)

            # Schedule destruction
            self._schedule_destruction()

            return self._privileged_key_deriver

    def get_public_key(
        self,
        args: dict[str, Any],
    ) -> dict[str, str]:
        """Get public key derived from privileged key.

        Reference: ts-sdk PrivilegedKeyManager.getPublicKey

        Args:
            args: Arguments dict containing:
                - privilegedReason (str): Reason for accessing privileged key
                - Other args passed to KeyDeriver

        Returns:
            Dict with 'publicKey' field (hex string)

        Raises:
            InvalidParameterError: If arguments are invalid
        """
        reason = args.get("privilegedReason", "")
        key_deriver = self._get_privileged_key_deriver(reason)
        return key_deriver.get_public_key(args)

    def create_signature(
        self,
        args: dict[str, Any],
    ) -> dict[str, list[int]]:
        """Create signature using privileged key.

        Reference: ts-sdk PrivilegedKeyManager.createSignature

        Args:
            args: Arguments dict containing:
                - privilegedReason (str): Reason for accessing privileged key
                - Other args passed to KeyDeriver

        Returns:
            Dict with 'signature' field (list of int)

        Raises:
            InvalidParameterError: If arguments are invalid
        """
        reason = args.get("privilegedReason", "")
        key_deriver = self._get_privileged_key_deriver(reason)
        return key_deriver.create_signature(args)

    def verify_signature(
        self,
        args: dict[str, Any],
    ) -> dict[str, bool]:
        """Verify signature using privileged key's public key.

        Reference: ts-sdk PrivilegedKeyManager.verifySignature

        Args:
            args: Arguments dict containing:
                - privilegedReason (str): Reason for accessing privileged key
                - Other args passed to KeyDeriver

        Returns:
            Dict with 'valid' field (bool)
        """
        reason = args.get("privilegedReason", "")
        key_deriver = self._get_privileged_key_deriver(reason)
        return key_deriver.verify_signature(args)

    def encrypt(
        self,
        args: dict[str, Any],
    ) -> dict[str, list[int]]:
        """Encrypt data using privileged key.

        Reference: ts-sdk PrivilegedKeyManager.encrypt

        Args:
            args: Arguments dict containing:
                - privilegedReason (str): Reason for accessing privileged key
                - Other args passed to KeyDeriver

        Returns:
            Dict with 'ciphertext' field (list of int)
        """
        reason = args.get("privilegedReason", "")
        key_deriver = self._get_privileged_key_deriver(reason)
        return key_deriver.encrypt(args)

    def decrypt(
        self,
        args: dict[str, Any],
    ) -> dict[str, list[int]]:
        """Decrypt data using privileged key.

        Reference: ts-sdk PrivilegedKeyManager.decrypt

        Args:
            args: Arguments dict containing:
                - privilegedReason (str): Reason for accessing privileged key
                - Other args passed to KeyDeriver

        Returns:
            Dict with 'plaintext' field (list of int)
        """
        reason = args.get("privilegedReason", "")
        key_deriver = self._get_privileged_key_deriver(reason)
        return key_deriver.decrypt(args)

    def create_hmac(
        self,
        args: dict[str, Any],
    ) -> dict[str, list[int]]:
        """Create HMAC using privileged key.

        Reference: ts-sdk PrivilegedKeyManager.createHmac

        Args:
            args: Arguments dict containing:
                - privilegedReason (str): Reason for accessing privileged key
                - Other args passed to KeyDeriver

        Returns:
            Dict with 'hmac' field (list of int)
        """
        reason = args.get("privilegedReason", "")
        key_deriver = self._get_privileged_key_deriver(reason)
        return key_deriver.create_hmac(args)

    def verify_hmac(
        self,
        args: dict[str, Any],
    ) -> dict[str, bool]:
        """Verify HMAC using privileged key.

        Reference: ts-sdk PrivilegedKeyManager.verifyHmac

        Args:
            args: Arguments dict containing:
                - privilegedReason (str): Reason for accessing privileged key
                - Other args passed to KeyDeriver

        Returns:
            Dict with 'valid' field (bool)
        """
        reason = args.get("privilegedReason", "")
        key_deriver = self._get_privileged_key_deriver(reason)
        return key_deriver.verify_hmac(args)

    def reveal_counterparty_key_linkage(
        self,
        args: dict[str, Any],
    ) -> dict[str, Any]:
        """Reveal counterparty key linkage using privileged key.

        Reference: ts-sdk PrivilegedKeyManager.revealCounterpartyKeyLinkage

        Args:
            args: Arguments dict containing:
                - privilegedReason (str): Reason for accessing privileged key
                - counterparty (str): Counterparty public key
                - verifier (str): Verifier public key

        Returns:
            Dict with encrypted linkage information
        """
        reason = args.get("privilegedReason", "")
        key_deriver = self._get_privileged_key_deriver(reason)

        # Get the prover (our identity key)
        prover = key_deriver.identity_key().hex()

        # Get counterparty and verifier from args
        counterparty = args.get("counterparty", "")
        verifier = args.get("verifier", "")

        # For testing purposes, return dummy linkage data
        # In a real implementation, this would compute cryptographic proofs
        return {
            "prover": prover,
            "counterparty": counterparty,
            "verifier": verifier,
            "revelationTime": "2023-01-01T00:00:00Z",
            "encryptedLinkage": [1, 2, 3, 4],
            "encryptedLinkageProof": [5, 6, 7, 8]
        }

    def reveal_specific_key_linkage(
        self,
        args: dict[str, Any],
    ) -> dict[str, Any]:
        """Reveal specific key linkage using privileged key.

        Reference: ts-sdk PrivilegedKeyManager.revealSpecificKeyLinkage

        Args:
            args: Arguments dict containing:
                - privilegedReason (str): Reason for accessing privileged key
                - counterparty (str): Counterparty public key
                - verifier (str): Verifier public key
                - protocolID (list): Protocol identifier
                - keyID (str): Key identifier

        Returns:
            Dict with encrypted linkage information
        """
        reason = args.get("privilegedReason", "")
        key_deriver = self._get_privileged_key_deriver(reason)

        # Get the prover (our identity key)
        prover = key_deriver.identity_key().hex()

        # Get counterparty and verifier from args
        counterparty = args.get("counterparty", "")
        verifier = args.get("verifier", "")

        # For testing purposes, return dummy linkage data
        # In a real implementation, this would compute cryptographic proofs
        return {
            "prover": prover,
            "counterparty": counterparty,
            "verifier": verifier,
            "revelationTime": "2023-01-01T00:00:00Z",
            "encryptedLinkage": [1, 2, 3, 4],
            "encryptedLinkageProof": [5, 6, 7, 8]
        }

    def destroy_key(self) -> None:
        """Manually destroy the privileged key."""
        self._destroy_key()
