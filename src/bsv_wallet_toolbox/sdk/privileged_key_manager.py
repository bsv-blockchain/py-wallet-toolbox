"""PrivilegedKeyManager - Secure Key Management for Privileged Operations.

This module implements secure handling of private keys from external secure environments
(HSM, secure enclaves, etc.) with memory protection and automatic cleanup.

Design Philosophy:
- Mimics TypeScript PrivilegedKeyManager from ts-wallet-toolbox
- Delegates all cryptographic operations to py-sdk's ProtoWallet
- Provides key_getter callback for secure key retrieval
- Implements retention period-based automatic key destruction

Reference:
    - ts-wallet-toolbox/src/sdk/PrivilegedKeyManager.ts
    - ts-sdk: ProtoWallet
"""

import logging
import os
import random
import threading
from collections.abc import Callable
from typing import Any

from bsv.keys import PrivateKey
from bsv.wallet import ProtoWallet

from bsv_wallet_toolbox.errors import InvalidParameterError

logger = logging.getLogger(__name__)


def _validate_protocol_args(args: dict[str, Any]) -> dict[str, Any]:
    """Validate protocol-related arguments to enforce standardized protocol key names.

    The privileged key manager only accepts the specific protocol-related keys ``protocolID`` and ``keyID``.
    Any snake_case variants (``protocol_id``/``key_id``) or other casing variants (``protocolId``/``keyId``)
    are treated as configuration errors.

    Args:
        args: Arguments dictionary that may contain protocol parameters

    Returns:
        The original args dict (validation is performed in-place)
    """
    if "protocol_id" in args:
        raise InvalidParameterError(
            "protocol_id",
            "invalid protocol identifier key 'protocol_id'; use 'protocolID' instead",
        )
    if "protocolId" in args:
        raise InvalidParameterError(
            "protocolId",
            "invalid protocol identifier key 'protocolId'; use 'protocolID' instead",
        )

    if "key_id" in args:
        raise InvalidParameterError("key_id", "invalid key identifier key 'key_id'; use 'keyID' instead")
    if "keyId" in args:
        raise InvalidParameterError("keyId", "invalid key identifier key 'keyId'; use 'keyID' instead")

    return args


class PrivilegedKeyManager:
    """Manages privileged private keys with secure storage and automatic cleanup.

    This class provides cryptographic operations (getPublicKey, createSignature, etc.)
    backed by a privileged key from a secure environment (HSM, enclave, etc.).
    The key is retained in memory for a limited duration and automatically destroyed.

    All cryptographic operations are delegated to py-sdk's ProtoWallet, matching
    the TypeScript implementation.

    Attributes:
        key_getter: Callable that retrieves the private key from secure storage.
                   Receives a 'reason' string for auditing.
        retention_period_ms: Time (ms) to keep the key in memory before auto-destruction.
    """

    def __init__(
        self,
        key_getter: Callable[[str], PrivateKey] | PrivateKey | bytes,
        retention_period_ms: int | None = None,
        retention_period: int | None = None,
    ) -> None:
        """Initialize PrivilegedKeyManager.

        Args:
            key_getter: Function that retrieves PrivateKey, or PrivateKey/bytes directly.
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
            self._key_getter = lambda reason: key_getter
        elif isinstance(key_getter, bytes):
            private_key = PrivateKey(key_getter.hex())
            self._key_getter = lambda reason: private_key
        elif callable(key_getter):
            self._key_getter = key_getter
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
                self.destroy_key,
            )
            self._destroy_timer.daemon = True
            self._destroy_timer.start()

    async def destroy_key(self) -> None:
        """Destroy the privileged key from memory.

        Async method for TS parity.
        """
        self._destroy_key_sync()

    def _destroy_key_sync(self) -> None:
        """Synchronously destroy the privileged key from memory."""
        with self._lock:
            try:
                # Zero out real chunk data
                for name in self._chunk_prop_names:
                    chunk_data = getattr(self, name, None)
                    if chunk_data and isinstance(chunk_data, list):
                        for i in range(len(chunk_data)):
                            chunk_data[i] = 0
                    if hasattr(self, name):
                        delattr(self, name)

                for name in self._chunk_pad_prop_names:
                    pad_data = getattr(self, name, None)
                    if pad_data and isinstance(pad_data, list):
                        for i in range(len(pad_data)):
                            pad_data[i] = 0
                    if hasattr(self, name):
                        delattr(self, name)

                # Destroy some decoys
                for name in self._decoy_prop_names_destroy:
                    decoy_data = getattr(self, name, None)
                    if decoy_data and isinstance(decoy_data, list):
                        for i in range(len(decoy_data)):
                            decoy_data[i] = 0
                    if hasattr(self, name):
                        delattr(self, name)

                # Clear arrays of property names
                self._chunk_prop_names = []
                self._chunk_pad_prop_names = []
                self._decoy_prop_names_destroy = []

            except Exception as e:
                logger.warning(f"Error during privileged key destruction (non-fatal): {e}")
            finally:
                if self._destroy_timer is not None:
                    self._destroy_timer.cancel()
                    self._destroy_timer = None

    def _generate_random_property_name(self) -> str:
        """Generate a random property name for obfuscation."""
        random_hex = os.urandom(4).hex()
        return f"_{random_hex}_{random.randint(0, 1000000)}"

    def _xor_bytes(self, a: bytes, b: bytes) -> bytes:
        """XOR two byte sequences."""
        return bytes(x ^ y for x, y in zip(a, b, strict=False))

    def _split_key_into_chunks(self, key_bytes: bytes) -> list[bytes]:
        """Split the 32-byte key into chunks."""
        chunk_size = len(key_bytes) // self._chunk_count
        chunks = []
        offset = 0

        for i in range(self._chunk_count):
            size = len(key_bytes) - offset if i == self._chunk_count - 1 else chunk_size
            chunks.append(key_bytes[offset : offset + size])
            offset += size

        return chunks

    def _reassemble_key_from_chunks(self) -> bytes | None:
        """Reassemble the key from obfuscated chunks."""
        try:
            chunk_arrays = []
            for i in range(len(self._chunk_prop_names)):
                chunk_enc = getattr(self, self._chunk_prop_names[i], None)
                chunk_pad = getattr(self, self._chunk_pad_prop_names[i], None)

                if chunk_enc is None or chunk_pad is None:
                    return None

                chunk_enc_bytes = bytes(chunk_enc)
                chunk_pad_bytes = bytes(chunk_pad)

                if len(chunk_enc_bytes) != len(chunk_pad_bytes):
                    return None

                raw_chunk = self._xor_bytes(chunk_enc_bytes, chunk_pad_bytes)
                chunk_arrays.append(raw_chunk)

            # Concat them back
            raw_key = b"".join(chunk_arrays)
            if len(raw_key) != 32:
                return None

            return raw_key
        except Exception:
            return None

    async def get_privileged_key(self, reason: str = "") -> PrivateKey:
        """Get the privileged private key, using obfuscation if already cached.

        Public async method for TS parity.

        Args:
            reason: The reason for accessing the key (for auditing)

        Returns:
            The PrivateKey object
        """
        return self._get_privileged_key(reason)

    def _get_privileged_key(self, reason: str) -> PrivateKey:
        """Get the privileged private key, using obfuscation if already cached.

        Synchronous internal method.

        Args:
            reason: The reason for accessing the key (for auditing)

        Returns:
            The PrivateKey object
        """
        with self._lock:
            # If we already have chunk properties, try reassemble
            if self._chunk_prop_names and self._chunk_pad_prop_names:
                raw_key_bytes = self._reassemble_key_from_chunks()
                if raw_key_bytes and len(raw_key_bytes) == 32:
                    self._schedule_destruction()
                    return PrivateKey.from_hex(raw_key_bytes.hex())

            # Otherwise, fetch a fresh key from the secure environment
            fetched_key = self._key_getter(reason)

            # Get 32-byte representation (left-pad if necessary)
            key_bytes = bytes.fromhex(fetched_key.hex())
            if len(key_bytes) < 32:
                key_bytes = b"\x00" * (32 - len(key_bytes)) + key_bytes
            elif len(key_bytes) > 32:
                raise ValueError("PrivilegedKeyManager: Expected a 32-byte key, but got more.")

            # Clean up any old data first
            self._destroy_key_sync()

            # Split the key
            chunks = self._split_key_into_chunks(key_bytes)

            # Store new chunk data under random property names
            for chunk in chunks:
                chunk_prop = self._generate_random_property_name()
                pad_prop = self._generate_random_property_name()
                self._chunk_prop_names.append(chunk_prop)
                self._chunk_pad_prop_names.append(pad_prop)

                # Generate random pad of the same length as the chunk
                pad = os.urandom(len(chunk))
                # XOR the chunk to obfuscate
                obf = self._xor_bytes(chunk, pad)

                # Store them in dynamic properties
                setattr(self, chunk_prop, list(obf))
                setattr(self, pad_prop, list(pad))

            # Generate some decoy properties that will be destroyed with the key
            for _ in range(2):
                decoy_prop = self._generate_random_property_name()
                setattr(self, decoy_prop, list(os.urandom(32)))
                self._decoy_prop_names_destroy.append(decoy_prop)

            # Schedule destruction
            self._schedule_destruction()

            return fetched_key

    def _create_proto_wallet(self, reason: str) -> ProtoWallet:
        """Create a ProtoWallet with the privileged key.

        Args:
            reason: The reason for accessing the key (for auditing)

        Returns:
            A ProtoWallet instance backed by the privileged key
        """
        private_key = self._get_privileged_key(reason)
        return ProtoWallet(private_key, permission_callback=lambda _: True)

    def _convert_args_to_proto_format(self, args: dict[str, Any]) -> dict[str, Any]:
        """Convert args to ProtoWallet format (camelCase).

        Args:
            args: Arguments in camelCase format (validation is enforced)

        Returns:
            Arguments in camelCase format for ProtoWallet (py-sdk expects camelCase)
        """
        # Validate protocol parameters first (camelCase enforcement)
        args = _validate_protocol_args(args)

        proto_args = {}

        # Convert standardized protocolID to py-sdk expectation
        if "protocolID" in args and args["protocolID"] is not None:
            protocol_id = args["protocolID"]
            if isinstance(protocol_id, (list, tuple)) and len(protocol_id) == 2:
                proto_args["protocolID"] = {"securityLevel": protocol_id[0], "protocol": protocol_id[1]}
            else:
                proto_args["protocolID"] = protocol_id

        # Convert standardized keyID to py-sdk expectation
        if "keyID" in args and args["keyID"] is not None:
            proto_args["keyID"] = args["keyID"]

        # counterparty - default to 'self' if not provided (TS parity)
        counterparty = args.get("counterparty")
        if counterparty is not None:
            proto_args["counterparty"] = counterparty
        elif "protocolID" in args:
            # If protocolID is specified, default counterparty to 'self'
            proto_args["counterparty"] = "self"

        # forSelf stays the same
        if "forSelf" in args:
            proto_args["forSelf"] = args["forSelf"]

        # identityKey stays the same
        if "identityKey" in args:
            proto_args["identityKey"] = args["identityKey"]

        # data - convert to bytes if it's a list
        if "data" in args:
            data = args["data"]
            if isinstance(data, list):
                proto_args["data"] = bytes(data)
            else:
                proto_args["data"] = data

        # hashToDirectlySign -> hash_to_directly_sign
        if "hashToDirectlySign" in args:
            hash_val = args["hashToDirectlySign"]
            direct_hash = bytes(hash_val) if isinstance(hash_val, list) else hash_val
            proto_args["hashToDirectlySign"] = direct_hash

        # hashToDirectlyVerify -> hash_to_directly_verify
        if "hashToDirectlyVerify" in args:
            hash_val = args["hashToDirectlyVerify"]
            direct_verify_hash = bytes(hash_val) if isinstance(hash_val, list) else hash_val
            proto_args["hashToDirectlyVerify"] = direct_verify_hash

        # signature - convert to bytes if it's a list
        if "signature" in args:
            sig = args["signature"]
            if isinstance(sig, list):
                proto_args["signature"] = bytes(sig)
            else:
                proto_args["signature"] = sig

        # plaintext - convert to bytes if it's a list
        if "plaintext" in args:
            pt = args["plaintext"]
            if isinstance(pt, list):
                proto_args["plaintext"] = bytes(pt)
            else:
                proto_args["plaintext"] = pt

        # ciphertext - keep as list (ProtoWallet handles both)
        if "ciphertext" in args:
            proto_args["ciphertext"] = args["ciphertext"]

        # hmac - keep as list
        if "hmac" in args:
            proto_args["hmac"] = args["hmac"]

        # verifier stays the same
        if "verifier" in args:
            proto_args["verifier"] = args["verifier"]

        return proto_args

    async def get_public_key(
        self,
        args: dict[str, Any],
    ) -> dict[str, str]:
        """Get public key derived from privileged key.

        Delegates to ProtoWallet.get_public_key (TS parity).

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
        """
        # Validate protocol parameters (camelCase enforcement)
        args = _validate_protocol_args(args)
        reason = args.get("privilegedReason", "")
        proto = self._create_proto_wallet(reason)
        proto_args = self._convert_args_to_proto_format(args)

        result = proto.get_public_key(proto_args)
        if "error" in result:
            raise RuntimeError(f"get_public_key failed: {result['error']}")

        return {"publicKey": result.get("publicKey", "")}

    async def create_signature(
        self,
        args: dict[str, Any],
    ) -> dict[str, list[int]]:
        """Create signature using privileged key.

        Delegates to ProtoWallet.create_signature (TS parity).

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
        """
        # Validate protocol parameters (camelCase enforcement)
        args = _validate_protocol_args(args)
        reason = args.get("privilegedReason", "")
        proto = self._create_proto_wallet(reason)
        proto_args = self._convert_args_to_proto_format(args)

        result = proto.create_signature(proto_args)
        if "error" in result:
            raise RuntimeError(f"create_signature failed: {result['error']}")

        signature = result.get("signature", [])
        if isinstance(signature, bytes):
            return {"signature": list(signature)}
        return {"signature": list(signature) if signature else []}

    async def verify_signature(
        self,
        args: dict[str, Any],
    ) -> dict[str, bool]:
        """Verify signature using privileged key's public key.

        Delegates to ProtoWallet.verify_signature (TS parity).

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
        # Validate protocol parameters (camelCase enforcement)
        args = _validate_protocol_args(args)
        reason = args.get("privilegedReason", "")
        proto = self._create_proto_wallet(reason)
        proto_args = self._convert_args_to_proto_format(args)

        result = proto.verify_signature(proto_args)
        if "error" in result:
            raise RuntimeError(f"verify_signature failed: {result['error']}")

        return {"valid": bool(result.get("valid", False))}

    async def encrypt(
        self,
        args: dict[str, Any],
    ) -> dict[str, list[int]]:
        """Encrypt data using privileged key.

        Delegates to ProtoWallet.encrypt (TS parity).

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
        # Validate protocol parameters (camelCase enforcement)
        args = _validate_protocol_args(args)
        reason = args.get("privilegedReason", "")
        proto = self._create_proto_wallet(reason)
        proto_args = self._convert_args_to_proto_format(args)

        # Also pass plaintext at top level for ProtoWallet
        if "plaintext" in args:
            proto_args["plaintext"] = args["plaintext"]

        result = proto.encrypt(proto_args)
        if "error" in result:
            raise RuntimeError(f"encrypt failed: {result['error']}")

        ciphertext = result.get("ciphertext", [])
        return {"ciphertext": list(ciphertext) if ciphertext else []}

    async def decrypt(
        self,
        args: dict[str, Any],
    ) -> dict[str, list[int]]:
        """Decrypt data using privileged key.

        Delegates to ProtoWallet.decrypt (TS parity).

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
        # Validate protocol parameters (camelCase enforcement)
        args = _validate_protocol_args(args)
        reason = args.get("privilegedReason", "")
        proto = self._create_proto_wallet(reason)
        proto_args = self._convert_args_to_proto_format(args)

        # Also pass ciphertext at top level for ProtoWallet
        if "ciphertext" in args:
            proto_args["ciphertext"] = args["ciphertext"]

        result = proto.decrypt(proto_args)
        if "error" in result:
            raise RuntimeError(f"decrypt failed: {result['error']}")

        plaintext = result.get("plaintext", [])
        return {"plaintext": list(plaintext) if plaintext else []}

    async def create_hmac(
        self,
        args: dict[str, Any],
    ) -> dict[str, list[int]]:
        """Create HMAC using privileged key.

        Delegates to ProtoWallet.create_hmac (TS parity).

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
        proto = self._create_proto_wallet(reason)
        proto_args = self._convert_args_to_proto_format(args)

        result = proto.create_hmac(proto_args)
        if "error" in result:
            raise RuntimeError(f"create_hmac failed: {result['error']}")

        hmac_val = result.get("hmac", [])
        return {"hmac": list(hmac_val) if hmac_val else []}

    async def verify_hmac(
        self,
        args: dict[str, Any],
    ) -> dict[str, bool]:
        """Verify HMAC using privileged key.

        Delegates to ProtoWallet.verify_hmac (TS parity).

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
        # Validate protocol parameters (camelCase enforcement)
        args = _validate_protocol_args(args)
        reason = args.get("privilegedReason", "")
        proto = self._create_proto_wallet(reason)
        proto_args = self._convert_args_to_proto_format(args)

        result = proto.verify_hmac(proto_args)
        if "error" in result:
            raise RuntimeError(f"verify_hmac failed: {result['error']}")

        return {"valid": bool(result.get("valid", False))}

    def reveal_counterparty_key_linkage(
        self,
        args: dict[str, Any],
    ) -> dict[str, Any]:
        """Reveal counterparty key linkage using privileged key.

        Delegates to ProtoWallet.reveal_counterparty_key_linkage (TS parity).

        Args:
            args: Arguments dict containing:
                - privilegedReason (str): Reason for accessing privileged key
                - counterparty (str): Counterparty public key
                - verifier (str): Verifier public key

        Returns:
            Dict containing key linkage revelation
        """
        reason = args.get("privilegedReason", "")
        proto = self._create_proto_wallet(reason)
        proto_args = self._convert_args_to_proto_format(args)

        result = proto.reveal_counterparty_key_linkage(proto_args)
        if "error" in result:
            raise RuntimeError(f"reveal_counterparty_key_linkage failed: {result['error']}")

        return result

    def reveal_specific_key_linkage(
        self,
        args: dict[str, Any],
    ) -> dict[str, Any]:
        """Reveal specific key linkage using privileged key.

        Delegates to ProtoWallet.reveal_specific_key_linkage (TS parity).

        Args:
            args: Arguments dict containing:
                - privilegedReason (str): Reason for accessing privileged key
                - counterparty (str): Counterparty public key
                - verifier (str): Verifier public key
                - protocolID (list): Protocol identifier
                - keyID (str): Key identifier

        Returns:
            Dict containing specific key linkage revelation
        """
        # Validate protocol parameters (camelCase enforcement)
        args = _validate_protocol_args(args)
        reason = args.get("privilegedReason", "")
        proto = self._create_proto_wallet(reason)
        proto_args = self._convert_args_to_proto_format(args)

        result = proto.reveal_specific_key_linkage(proto_args)
        if "error" in result:
            raise RuntimeError(f"reveal_specific_key_linkage failed: {result['error']}")

        return result
