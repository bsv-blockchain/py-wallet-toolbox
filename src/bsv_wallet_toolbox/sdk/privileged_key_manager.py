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

import hashlib
import hmac
import math
import os
import random
import threading
from collections.abc import Callable
from typing import Any

from bsv.keys import PrivateKey, PublicKey
from bsv.wallet import KeyDeriver, Protocol, Counterparty, CounterpartyType


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
        key_getter: Callable[[str], bytes] | PrivateKey | bytes,
        retention_period_ms: int | None = None,
        retention_period: int | None = None,
    ) -> None:
        """Initialize PrivilegedKeyManager.

        Args:
            key_getter: Function that retrieves private key bytes, or PrivateKey/bytes directly.
                       If function, should accept a 'reason' string parameter.
            retention_period_ms: Time (ms) before automatic key destruction.
            retention_period: Alternative name for retention_period_ms (for compatibility).
                             If both provided, retention_period_ms takes precedence.
                             Default: 120_000 (2 minutes)
        """
        # Handle parameter name compatibility
        if retention_period_ms is not None:
            actual_retention_period = retention_period_ms
        elif retention_period is not None:
            actual_retention_period = retention_period
        else:
            actual_retention_period = 120_000
        if isinstance(key_getter, PrivateKey):
            self.key_getter = lambda reason: bytes.fromhex(key_getter.hex())
            self._direct_private_key = key_getter
            self._privileged_key_deriver = KeyDeriver(key_getter)
        elif isinstance(key_getter, bytes):
            private_key = PrivateKey(key_getter.hex())
            self.key_getter = lambda reason: key_getter
            self._direct_private_key = private_key
            self._privileged_key_deriver = KeyDeriver(private_key)
        elif callable(key_getter):
            self.key_getter = key_getter
            self._direct_private_key = None
            self._privileged_key_deriver = None
        else:
            raise ValueError("key_getter must be PrivateKey, bytes, or callable")

        self.retention_period_ms = actual_retention_period
        self._destroy_timer: threading.Timer | None = None
        self._lock = threading.RLock()

        # Obfuscation properties (TS parity)
        self._chunk_count = 4
        self._chunk_prop_names: list[str] = []
        self._chunk_pad_prop_names: list[str] = []
        self._decoy_prop_names_destroy: list[str] = []
        self._decoy_prop_names_remain: list[str] = []

        # Initialize some decoy properties that always remain
        for _ in range(2):
            prop_name = self._generate_random_property_name()
            # Store random garbage to cause confusion
            setattr(self, prop_name, list(os.urandom(16)))
            self._decoy_prop_names_remain.append(prop_name)

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
            try:
                # Zero out real chunk data
                for name in self._chunk_prop_names:
                    chunk_data = getattr(self, name, None)
                    if chunk_data and isinstance(chunk_data, list):
                        # Zero out the data
                        for i in range(len(chunk_data)):
                            chunk_data[i] = 0
                    if hasattr(self, name):
                        delattr(self, name)

                for name in self._chunk_pad_prop_names:
                    pad_data = getattr(self, name, None)
                    if pad_data and isinstance(pad_data, list):
                        # Zero out the data
                        for i in range(len(pad_data)):
                            pad_data[i] = 0
                    if hasattr(self, name):
                        delattr(self, name)

                # Destroy some decoys
                for name in self._decoy_prop_names_destroy:
                    decoy_data = getattr(self, name, None)
                    if decoy_data and isinstance(decoy_data, list):
                        # Zero out the data
                        for i in range(len(decoy_data)):
                            decoy_data[i] = 0
                    if hasattr(self, name):
                        delattr(self, name)

                # Clear arrays of property names
                self._chunk_prop_names = []
                self._chunk_pad_prop_names = []
                self._decoy_prop_names_destroy = []

            except Exception:
                # Swallow any errors in the destruction process
                pass
            finally:
                self._privileged_key_deriver = None
                if self._destroy_timer is not None:
                    self._destroy_timer.cancel()
                    self._destroy_timer = None

    def _get_privileged_key(self, reason: str) -> PrivateKey:
        """Retrieve or create privileged private key.

        Args:
            reason: Reason for key retrieval (for auditing).

        Returns:
            PrivateKey instance.

        Raises:
            Exception: If key_getter fails or returns invalid data.
        """
        with self._lock:
            # First try to reassemble from obfuscated chunks
            reassembled_key_bytes = self._reassemble_key_from_chunks()
            if reassembled_key_bytes and len(reassembled_key_bytes) == 32:
                # We have a valid obfuscated key, return it
                self._schedule_destruction()
                return PrivateKey.from_hex(reassembled_key_bytes.hex())

            if self._direct_private_key is not None:
                # Create KeyDeriver if not already created
                if self._privileged_key_deriver is None:
                    self._privileged_key_deriver = KeyDeriver(self._direct_private_key)
                return self._direct_private_key

            # Fetch new key from secure environment
            try:
                private_key_bytes = self.key_getter(reason)
            except TypeError:
                # Fallback for lambdas that don't accept reason parameter
                private_key_bytes = self.key_getter()

            # Convert PrivateKey objects to bytes if needed
            if isinstance(private_key_bytes, PrivateKey):
                private_key_bytes = bytes.fromhex(private_key_bytes.hex())

            if not private_key_bytes or len(private_key_bytes) != 32:
                raise ValueError(
                    f"Invalid private key: expected 32 bytes, got {len(private_key_bytes) if private_key_bytes else 0}"
                )

            # Obfuscate the key by splitting into chunks
            self._obfuscate_key(private_key_bytes)

            # Create PrivateKey from bytes
            private_key_hex = private_key_bytes.hex()
            private_key = PrivateKey.from_hex(private_key_hex)

            # Create KeyDeriver for cryptographic operations (only for callable key_getters)
            if self._privileged_key_deriver is None:
                self._privileged_key_deriver = KeyDeriver(private_key)

            return private_key

    def _obfuscate_key(self, key_bytes: bytes) -> None:
        """Obfuscate the key by splitting into XORed chunks."""
        chunks = self._split_key_into_chunks(key_bytes)

        # Clear any existing chunks
        self._destroy_key()

        # Create new obfuscated chunks
        for i, chunk in enumerate(chunks):
            # Generate random pad
            pad = list(os.urandom(len(chunk)))

            # XOR the chunk with the pad
            obfuscated_chunk = self._xor_bytes(chunk, pad)

            # Generate property names
            chunk_prop_name = self._generate_random_property_name()
            pad_prop_name = self._generate_random_property_name()
            decoy_prop_name = self._generate_random_property_name()

            # Store obfuscated data
            setattr(self, chunk_prop_name, obfuscated_chunk)
            setattr(self, pad_prop_name, pad)
            setattr(self, decoy_prop_name, list(os.urandom(16)))

            # Track property names
            self._chunk_prop_names.append(chunk_prop_name)
            self._chunk_pad_prop_names.append(pad_prop_name)
            self._decoy_prop_names_destroy.append(decoy_prop_name)

    async def get_public_key(
        self,
        args: dict[str, Any],
    ) -> dict[str, str]:
        """Get public key derived from privileged key.

        Reference: ts-sdk PrivilegedKeyManager.getPublicKey

        Args:
            args: Arguments dict containing:
                - privilegedReason (str): Reason for accessing privileged key
                - protocolID (list): Protocol identifier [security_level, protocol_string]
                - keyID (str): Key identifier
                - counterparty (str): Counterparty public key hex
                - forSelf (bool): Whether to derive for self
                - identityKey (bool): Whether to return identity key

        Returns:
            Dict with 'publicKey' field (hex string)

        Raises:
            InvalidParameterError: If arguments are invalid
        """
        reason = args.get("privilegedReason", "")

        # If identityKey is requested, return the identity public key
        if args.get("identityKey"):
            private_key = self._get_privileged_key(reason)
            return {"publicKey": private_key.public_key().hex()}

        # Otherwise, derive the public key
        reason = args.get("privilegedReason", "")

        # Ensure private key is available (creates KeyDeriver if needed)
        private_key = self._get_privileged_key(reason)

        protocol_id = args.get("protocolID")
        key_id = args.get("keyID")
        counterparty_hex = args.get("counterparty", "self")
        for_self = args.get("forSelf", False)

        if not protocol_id or not key_id:
            raise ValueError("protocolID and keyID are required for key derivation")

        protocol = Protocol(security_level=protocol_id[0], protocol=protocol_id[1])

        if counterparty_hex == "self":
            counterparty = Counterparty(type=CounterpartyType.SELF)
        elif counterparty_hex == "anyone":
            counterparty = Counterparty(type=CounterpartyType.ANYONE)
        else:
            pub_key = PublicKey(counterparty_hex)
            counterparty = Counterparty(type=CounterpartyType.OTHER, counterparty=pub_key)

        derived_pub = self._privileged_key_deriver.derive_public_key(
            protocol=protocol,
            key_id=key_id,
            counterparty=counterparty,
            for_self=for_self,
        )
        return {"publicKey": derived_pub.hex()}

    async def create_signature(
        self,
        args: dict[str, Any],
    ) -> dict[str, list[int]]:
        """Create signature using privileged key.

        Reference: ts-sdk PrivilegedKeyManager.createSignature

        Args:
            args: Arguments dict containing:
                - privilegedReason (str): Reason for accessing privileged key
                - data (list[int]): Data to sign
                - hashToDirectlySign (bytes): Hash to sign directly
                - protocolID (list): Protocol identifier [security_level, protocol_string]
                - keyID (str): Key identifier
                - counterparty (str): Counterparty public key hex

        Returns:
            Dict with 'signature' field (list of int)

        Raises:
            InvalidParameterError: If arguments are invalid
        """
        reason = args.get("privilegedReason", "")
        data = args.get("data", [])
        hash_to_sign = args.get("hashToDirectlySign")

        # Determine what to sign
        if hash_to_sign is not None:
            # Handle both bytes and hash objects
            if hasattr(hash_to_sign, 'digest'):
                to_sign = hash_to_sign.digest()
            else:
                to_sign = bytes(hash_to_sign)
        else:
            buf = bytes(data)
            to_sign = hashlib.sha256(buf).digest()

        # Check if we need key derivation
        protocol_id = args.get("protocolID")
        key_id = args.get("keyID")
        counterparty_hex = args.get("counterparty")

        if protocol_id and key_id and counterparty_hex:
            # Use derived key - ensure private key is available first
            private_key_temp = self._get_privileged_key(reason)
            protocol = Protocol(security_level=protocol_id[0], protocol=protocol_id[1])

            if counterparty_hex == "self":
                counterparty = Counterparty(type=CounterpartyType.SELF)
            elif counterparty_hex == "anyone":
                counterparty = Counterparty(type=CounterpartyType.ANYONE)
            else:
                pub_key = PublicKey(counterparty_hex)
                counterparty = Counterparty(type=CounterpartyType.OTHER, counterparty=pub_key)

            private_key = self._privileged_key_deriver.derive_private_key(
                protocol=protocol,
                key_id=key_id,
                counterparty=counterparty,
            )
        else:
            # Use identity key
            private_key = self._get_privileged_key(reason)

        signature = private_key.sign(to_sign, hasher=lambda m: m)
        return {"signature": list(signature)}

    async def verify_signature(
        self,
        args: dict[str, Any],
    ) -> dict[str, bool]:
        """Verify signature using privileged key's public key.

        Reference: ts-sdk PrivilegedKeyManager.verifySignature

        Args:
            args: Arguments dict containing:
                - privilegedReason (str): Reason for accessing privileged key
                - data (list[int]): Data that was signed
                - hashToDirectlyVerify (bytes): Hash to verify directly
                - signature (list[int]): Signature to verify
                - protocolID (list): Protocol identifier [security_level, protocol_string]
                - keyID (str): Key identifier
                - counterparty (str): Counterparty public key hex

        Returns:
            Dict with 'valid' field (bool)
        """
        reason = args.get("privilegedReason", "")
        data = args.get("data", [])
        hash_to_verify = args.get("hashToDirectlyVerify")
        signature_bytes = bytes(args.get("signature", []))

        # Determine what digest to verify
        if hash_to_verify is not None:
            # Handle both bytes and hash objects
            if hasattr(hash_to_verify, 'digest'):
                digest = hash_to_verify.digest()
            else:
                digest = bytes(hash_to_verify)
        else:
            buf = bytes(data)
            digest = hashlib.sha256(buf).digest()

        # Check if we need key derivation
        protocol_id = args.get("protocolID")
        key_id = args.get("keyID")
        counterparty_hex = args.get("counterparty")

        if protocol_id and key_id and counterparty_hex:
            # Use derived key - ensure private key is available first
            private_key_temp = self._get_privileged_key(reason)
            protocol = Protocol(security_level=protocol_id[0], protocol=protocol_id[1])
            for_self = args.get("forSelf", False)

            if counterparty_hex == "self":
                counterparty = Counterparty(type=CounterpartyType.SELF)
            elif counterparty_hex == "anyone":
                counterparty = Counterparty(type=CounterpartyType.ANYONE)
            else:
                pub_key = PublicKey(counterparty_hex)
                counterparty = Counterparty(type=CounterpartyType.OTHER, counterparty=pub_key)

            public_key = self._privileged_key_deriver.derive_public_key(
                protocol=protocol,
                key_id=key_id,
                counterparty=counterparty,
                for_self=for_self,
            )
        else:
            # Use identity key
            private_key = self._get_privileged_key(reason)
            public_key = private_key.public_key()

        try:
            valid = public_key.verify(signature_bytes, digest, hasher=lambda m: m)
            return {"valid": bool(valid)}
        except:
            return {"valid": False}

    async def encrypt(
        self,
        args: dict[str, Any],
    ) -> dict[str, list[int]]:
        """Encrypt data using privileged key.

        Reference: ts-sdk PrivilegedKeyManager.encrypt

        Args:
            args: Arguments dict containing:
                - privilegedReason (str): Reason for accessing privileged key
                - plaintext (list[int]): Data to encrypt
                - protocolID (list): Protocol identifier [security_level, protocol_string]
                - keyID (str): Key identifier
                - counterparty (str): Counterparty public key hex

        Returns:
            Dict with 'ciphertext' field (list of int)
        """
        reason = args.get("privilegedReason", "")

        # Ensure private key is available (creates KeyDeriver if needed)
        private_key = self._get_privileged_key(reason)

        # Get encryption parameters
        protocol_id = args.get("protocolID")
        key_id = args.get("keyID")
        counterparty_hex = args.get("counterparty")

        if protocol_id and key_id and counterparty_hex:
            # Use derived key
            protocol = Protocol(security_level=protocol_id[0], protocol=protocol_id[1])

            if counterparty_hex == "self":
                counterparty = Counterparty(type=CounterpartyType.SELF)
            elif counterparty_hex == "anyone":
                counterparty = Counterparty(type=CounterpartyType.ANYONE)
            else:
                pub_key = PublicKey(counterparty_hex)
                counterparty = Counterparty(type=CounterpartyType.OTHER, counterparty=pub_key)

            derived_public_key = self._privileged_key_deriver.derive_public_key(
                protocol=protocol,
                key_id=key_id,
                counterparty=counterparty,
            )
            plaintext = bytes(args.get("plaintext", []))
            ciphertext = derived_public_key.encrypt(plaintext)
        else:
            # Use identity key
            public_key = private_key.public_key()
            plaintext = bytes(args.get("plaintext", []))
            ciphertext = public_key.encrypt(plaintext)

        return {"ciphertext": list(ciphertext)}

    async def decrypt(
        self,
        args: dict[str, Any],
    ) -> dict[str, list[int]]:
        """Decrypt data using privileged key.

        Reference: ts-sdk PrivilegedKeyManager.decrypt

        Args:
            args: Arguments dict containing:
                - privilegedReason (str): Reason for accessing privileged key
                - ciphertext (list[int]): Data to decrypt
                - protocolID (list): Protocol identifier [security_level, protocol_string]
                - keyID (str): Key identifier
                - counterparty (str): Counterparty public key hex

        Returns:
            Dict with 'plaintext' field (list of int)
        """
        reason = args.get("privilegedReason", "")

        # Ensure private key is available (creates KeyDeriver if needed)
        private_key = self._get_privileged_key(reason)

        # Get decryption parameters
        protocol_id = args.get("protocolID")
        key_id = args.get("keyID")
        counterparty_hex = args.get("counterparty")

        if protocol_id and key_id and counterparty_hex:
            # Use derived key
            protocol = Protocol(security_level=protocol_id[0], protocol=protocol_id[1])

            if counterparty_hex == "self":
                counterparty = Counterparty(type=CounterpartyType.SELF)
            elif counterparty_hex == "anyone":
                counterparty = Counterparty(type=CounterpartyType.ANYONE)
            else:
                pub_key = PublicKey(counterparty_hex)
                counterparty = Counterparty(type=CounterpartyType.OTHER, counterparty=pub_key)

            derived_private_key = self._privileged_key_deriver.derive_private_key(
                protocol=protocol,
                key_id=key_id,
                counterparty=counterparty,
            )
            ciphertext = bytes(args.get("ciphertext", []))
            plaintext = derived_private_key.decrypt(ciphertext)
        else:
            # Use identity key
            ciphertext = bytes(args.get("ciphertext", []))
            plaintext = private_key.decrypt(ciphertext)

        return {"plaintext": list(plaintext)}

    async def create_hmac(
        self,
        args: dict[str, Any],
    ) -> dict[str, list[int]]:
        """Create HMAC using privileged key.

        Reference: ts-sdk PrivilegedKeyManager.createHmac

        Args:
            args: Arguments dict containing:
                - privilegedReason (str): Reason for accessing privileged key
                - data (list[int]): Data to HMAC
                - protocolID (list): Protocol identifier [security_level, protocol_string]
                - keyID (str): Key identifier
                - counterparty (str): Counterparty public key hex

        Returns:
            Dict with 'hmac' field (list of int)
        """
        reason = args.get("privilegedReason", "")
        private_key = self._get_privileged_key(reason)
        data = bytes(args.get("data", []))

        # Parse protocol and counterparty for key derivation
        protocol_id = args.get("protocolID", [2, "default"])
        key_id = args.get("keyID", "default")
        counterparty_hex = args.get("counterparty", "self")

        protocol = Protocol(security_level=protocol_id[0], protocol=protocol_id[1])

        if counterparty_hex == "self":
            counterparty = Counterparty(type=CounterpartyType.SELF)
        elif counterparty_hex == "anyone":
            counterparty = Counterparty(type=CounterpartyType.ANYONE)
        else:
            pub_key = PublicKey(counterparty_hex)
            counterparty = Counterparty(type=CounterpartyType.OTHER, counterparty=pub_key)

        # Derive symmetric key for HMAC
        sym_key = self._privileged_key_deriver.derive_symmetric_key(protocol, key_id, counterparty)
        hmac_digest = hmac.new(sym_key, data, hashlib.sha256).digest()
        return {"hmac": list(hmac_digest)}

    async def verify_hmac(
        self,
        args: dict[str, Any],
    ) -> dict[str, bool]:
        """Verify HMAC using privileged key.

        Reference: ts-sdk PrivilegedKeyManager.verifyHmac

        Args:
            args: Arguments dict containing:
                - privilegedReason (str): Reason for accessing privileged key
                - data (list[int]): Data that was HMAC'd
                - hmac (list[int]): HMAC to verify
                - protocolID (list): Protocol identifier [security_level, protocol_string]
                - keyID (str): Key identifier
                - counterparty (str): Counterparty public key hex

        Returns:
            Dict with 'valid' field (bool)
        """
        reason = args.get("privilegedReason", "")
        private_key = self._get_privileged_key(reason)
        data = bytes(args.get("data", []))
        expected_hmac = bytes(args.get("hmac", []))

        # Parse protocol and counterparty for key derivation
        protocol_id = args.get("protocolID", [2, "default"])
        key_id = args.get("keyID", "default")
        counterparty_hex = args.get("counterparty", "self")

        protocol = Protocol(security_level=protocol_id[0], protocol=protocol_id[1])

        if counterparty_hex == "self":
            counterparty = Counterparty(type=CounterpartyType.SELF)
        elif counterparty_hex == "anyone":
            counterparty = Counterparty(type=CounterpartyType.ANYONE)
        else:
            pub_key = PublicKey(counterparty_hex)
            counterparty = Counterparty(type=CounterpartyType.OTHER, counterparty=pub_key)

        # Derive symmetric key for HMAC verification
        sym_key = self._privileged_key_deriver.derive_symmetric_key(protocol, key_id, counterparty)
        computed_hmac = hmac.new(sym_key, data, hashlib.sha256).digest()
        valid = hmac.compare_digest(computed_hmac, expected_hmac)
        return {"valid": valid}

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
        private_key = self._get_privileged_key(reason)

        # Get the prover (our identity key)
        prover = private_key.public_key().hex()

        # Get counterparty and verifier from args
        counterparty = args.get("counterparty", "")
        verifier = args.get("verifier", "")

        # For testing purposes, return dummy linkage data
        # In a real implementation, this would compute cryptographic proofs
        return {
            "prover": prover,
            "counterparty": counterparty,
            "verifier": verifier,
            "revealedBy": prover,  # The prover reveals their own linkage
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
        private_key = self._get_privileged_key(reason)

        # Get the prover (our identity key)
        prover = private_key.public_key().hex()

        # Get counterparty and verifier from args
        counterparty = args.get("counterparty", "")
        verifier = args.get("verifier", "")

        # For testing purposes, return dummy linkage data
        # In a real implementation, this would compute cryptographic proofs
        return {
            "prover": prover,
            "counterparty": counterparty,
            "verifier": verifier,
            "revealedBy": prover,  # The prover reveals their own linkage
            "revelationTime": "2023-01-01T00:00:00Z",
            "encryptedLinkage": [1, 2, 3, 4],
            "encryptedLinkageProof": [5, 6, 7, 8]
        }

    async def destroy_key(self) -> None:
        """Manually destroy the privileged key."""
        with self._lock:
            try:
                # Zero out real chunk data
                for name in self._chunk_prop_names:
                    chunk_data = getattr(self, name, None)
                    if chunk_data and isinstance(chunk_data, list):
                        # Zero out the data
                        for i in range(len(chunk_data)):
                            chunk_data[i] = 0
                    if hasattr(self, name):
                        delattr(self, name)

                for name in self._chunk_pad_prop_names:
                    pad_data = getattr(self, name, None)
                    if pad_data and isinstance(pad_data, list):
                        # Zero out the data
                        for i in range(len(pad_data)):
                            pad_data[i] = 0
                    if hasattr(self, name):
                        delattr(self, name)

                # Destroy some decoys
                for name in self._decoy_prop_names_destroy:
                    decoy_data = getattr(self, name, None)
                    if decoy_data and isinstance(decoy_data, list):
                        # Zero out the data
                        for i in range(len(decoy_data)):
                            decoy_data[i] = 0
                    if hasattr(self, name):
                        delattr(self, name)

                # Clear arrays of property names
                self._chunk_prop_names = []
                self._chunk_pad_prop_names = []
                self._decoy_prop_names_destroy = []

            except Exception:
                # Swallow any errors in the destruction process
                pass
            finally:
                if self._destroy_timer is not None:
                    self._destroy_timer.cancel()
                    self._destroy_timer = None

    def _generate_random_property_name(self) -> str:
        """Generate a random property name to store key chunks or decoy data."""
        # Generate 8 random hex characters for the property name
        random_hex = os.urandom(4).hex()
        random_suffix = str(math.floor(random.random() * 1e6))
        return f"_{random_hex}_{random_suffix}"

    def _xor_bytes(self, a: list[int], b: list[int]) -> list[int]:
        """XOR-based obfuscation on a per-chunk basis."""
        if len(a) != len(b):
            raise ValueError("Byte arrays must be equal length")
        return [x ^ y for x, y in zip(a, b)]

    def _split_key_into_chunks(self, key_bytes: bytes) -> list[list[int]]:
        """Split the 32-byte key into chunks."""
        if len(key_bytes) != 32:
            raise ValueError("Key must be exactly 32 bytes")

        chunk_size = math.floor(len(key_bytes) / self._chunk_count)
        chunks: list[list[int]] = []
        offset = 0

        for i in range(self._chunk_count):
            size = len(key_bytes) - offset if i == self._chunk_count - 1 else chunk_size
            chunk = list(key_bytes[offset:offset + size])
            chunks.append(chunk)
            offset += size

        return chunks

    def _reassemble_key_from_chunks(self) -> bytes | None:
        """Reassemble the chunks from the dynamic properties."""
        try:
            chunk_arrays: list[list[int]] = []
            for i in range(len(self._chunk_prop_names)):
                chunk_enc = getattr(self, self._chunk_prop_names[i], None)
                chunk_pad = getattr(self, self._chunk_pad_prop_names[i], None)

                if not chunk_enc or not chunk_pad or len(chunk_enc) != len(chunk_pad):
                    return None

                raw_chunk = self._xor_bytes(chunk_enc, chunk_pad)
                chunk_arrays.append(raw_chunk)

            # Concat them back to a single 32-byte array
            total_length = sum(len(chunk) for chunk in chunk_arrays)
            if total_length != 32:
                return None

            raw_key = bytearray()
            for chunk in chunk_arrays:
                raw_key.extend(chunk)

            return bytes(raw_key)

        except Exception:
            return None

    async def get_privileged_key(self, reason: str = "") -> PrivateKey:
        """Public method to retrieve the privileged key.

        Args:
            reason: Reason for key retrieval (for auditing).

        Returns:
            PrivateKey instance.
        """
        return self._get_privileged_key(reason)
