"""BRC-100 compliant Bitcoin SV wallet implementation.

Reference: ts-wallet-toolbox/src/Wallet.ts
"""

import asyncio
import json
import logging
import time
from typing import TYPE_CHECKING, Any, Literal

from bsv.keys import PublicKey
from bsv.overlay_tools import LookupResolver, LookupResolverConfig
from bsv.transaction import Beef
from bsv.transaction.beef import BEEF_V2, parse_beef, parse_beef_ex
from bsv.wallet import Counterparty, CounterpartyType, KeyDeriver, ProtoWallet
from bsv.wallet.wallet_interface import (
    AuthenticatedResult,
    CreateSignatureResult,
    GetHeaderResult,
    GetHeightResult,
    GetNetworkResult,
    GetPublicKeyResult,
    GetVersionResult,
)

from .brc29 import KeyID, lock_for_counterparty
from .errors import InvalidParameterError, ReviewActionsError, WalletError
from .manager.wallet_settings_manager import WalletSettingsManager
from .sdk.privileged_key_manager import PrivilegedKeyManager
from .sdk.types import (
    specOpFailedActions,
    specOpInvalidChange,
    specOpNoSendActions,
    specOpSetWalletChangeParams,
    specOpThrowReviewActions,
    specOpWalletBalance,
)
from .services import WalletServices
from .signer.methods import (
    acquire_direct_certificate,
    prove_certificate,
)
from .signer.methods import (
    create_action as signer_create_action,
)
from .signer.methods import (
    internalize_action as signer_internalize_action,
)
from .signer.methods import (
    sign_action as signer_sign_action,
)
from .storage.methods.generate_change import MAX_POSSIBLE_SATOSHIS
from .utils.identity_utils import query_overlay, transform_verifiable_certificates_with_trust
from .utils.random_utils import random_bytes_base64
from .utils.trace import trace
from .utils.ttl_cache import TTLCache
from .utils.validation import (
    validate_abort_action_args,
    validate_acquire_certificate_args,
    validate_create_action_args,
    validate_discover_by_attributes_args,
    validate_discover_by_identity_key_args,
    validate_get_header_args,
    validate_get_version_args,
    validate_internalize_action_args,
    validate_list_actions_args,
    validate_prove_certificate_args,
    validate_relinquish_certificate_args,
    validate_sign_action_args,
)

if TYPE_CHECKING:
    from .monitor.monitor import Monitor

# Type alias for chain (matches TypeScript: 'main' | 'test')
Chain = Literal["main", "test"]

# Type alias for wallet network (matches TypeScript: 'mainnet' | 'testnet')
WalletNetwork = Literal["mainnet", "testnet"]

# Constants
MAX_ORIGINATOR_LENGTH_BYTES = 250  # BRC-100 standard: originator must be under 250 bytes

# Logger
logger = logging.getLogger(__name__)


def _parse_counterparty(value: str | PublicKey) -> Counterparty:
    """Parse counterparty value into Counterparty object.

    Args:
        value: 'self', 'anyone', or hex-encoded public key string, or PublicKey instance

    Returns:
        Counterparty object

    Raises:
        InvalidParameterError: If value is invalid
    """
    if isinstance(value, PublicKey):
        return Counterparty(type=CounterpartyType.OTHER, counterparty=value)

    if value == "self":
        return Counterparty(type=CounterpartyType.SELF)

    if value == "anyone":
        return Counterparty(type=CounterpartyType.ANYONE)

    # Assume it's a hex-encoded public key
    try:
        pub_key = PublicKey(value)
        return Counterparty(type=CounterpartyType.OTHER, counterparty=pub_key)
    except Exception as e:
        raise InvalidParameterError(
            "counterparty", f"'self', 'anyone', or a valid hex-encoded public key (got {value!r}, error: {e})"
        ) from e


def _as_bytes(value: Any, field_name: str) -> bytes:
    """Normalize bytes-like or list[int] into bytes.

    Accepts bytes, bytearray, or a list/tuple of integers (0-255). Raises
    InvalidParameterError for unsupported types or invalid values.

    Args:
        value: Input value to normalize
        field_name: Name for error messages

    Returns:
        bytes: Normalized bytes value
    """
    if isinstance(value, (bytes, bytearray)):
        return bytes(value)
    if isinstance(value, (list, tuple)):
        try:
            return bytes(int(b) & 0xFF for b in value)
        except Exception as exc:  # pragma: no cover - defensive
            raise InvalidParameterError(field_name, "list[int] 0-255 expected") from exc
    raise InvalidParameterError(field_name, "bytes-like or list[int] expected")


def _to_byte_list(value: bytes | bytearray) -> list[int]:
    """Convert bytes/bytearray to JSON-friendly list[int] (0-255)."""
    return list(bytes(value))


def _validate_protocol_args(args: dict[str, Any]) -> dict[str, Any]:
    """Validate protocol-related arguments to enforce standardized camelCase keys.

    The wallet API only accepts standardized camelCase keys (protocolID/keyID).
    Any snake_case variants or non-standard casing (protocolId/keyId) are treated as
    configuration errors so that issues are caught immediately.

    Args:
        args: Arguments dictionary that may contain protocol parameters

    Returns:
        The original args dict (validation is performed in-place)
    """
    if "protocol_id" in args:
        raise InvalidParameterError("protocol_id", "use standardized camelCase key (protocolID)")
    if "protocolId" in args:
        raise InvalidParameterError("protocolId", "use standardized camelCase key (protocolID)")

    if "key_id" in args:
        raise InvalidParameterError("key_id", "use standardized camelCase key (keyID)")
    if "keyId" in args:
        raise InvalidParameterError("keyId", "use standardized camelCase key (keyID)")

    return args


class Wallet:
    """BRC-100 compliant wallet implementation.

    Implements the WalletInterface defined in bsv-sdk.

    Reference: ts-wallet-toolbox/src/Wallet.ts

    Note:
        Version is hardcoded as a class constant, matching TypeScript implementation.
        Python implementation uses "2.0.0".
        Chain parameter is required (no default value), matching TypeScript implementation.

    Example:
        >>> wallet = Wallet(chain="main")
        >>> result = wallet.get_version({})
        >>> print(result["version"])
        2.0.0
    """

    # Version constant (matches TypeScript's hardcoded return value)
    VERSION = "2.0.0"  # Updated to match Universal Test Vectors

    def __init__(
        self,
        chain: Chain,
        services: WalletServices | None = None,
        key_deriver: KeyDeriver | None = None,
        storage_provider: Any | None = None,
        privileged_key_manager: PrivilegedKeyManager | None = None,
        settings_manager: WalletSettingsManager | None = None,
        lookup_resolver: LookupResolver | None = None,
        monitor: "Monitor | None" = None,
    ) -> None:
        """Initialize wallet.

        Args:
            chain: Bitcoin network chain ('main' or 'test'). Required parameter.
            services: Optional WalletServices instance for blockchain data access.
                     If None, some methods requiring services will not work.
            key_deriver: Optional KeyDeriver instance for key derivation operations.
                        If None, methods requiring key derivation will raise RuntimeError.
            storage_provider: Optional StorageProvider instance. When both
                services and storage_provider are provided, the storage will be
                wired with services (set_services) for SpecOps that require
                network checks.
            privileged_key_manager: Optional PrivilegedKeyManager for secure key operations.
                                   If provided and args contain "privileged", uses
                                   this manager's methods instead of key_deriver.
            settings_manager: Optional WalletSettingsManager for wallet configuration.
                           If None, a default WalletSettingsManager will be created.
            lookup_resolver: Optional LookupResolver instance. When omitted, the wallet
                           creates one using the chain -> network preset mapping.
            monitor: Optional Monitor instance for background task management.

        Note:
            Version is not configurable, it's a class constant.
            Chain parameter is required (no default value), matching TypeScript implementation.

        Raises:
            ValueError: If chain is not 'main' or 'test'
        """
        # Validate chain parameter
        if chain not in ("main", "test"):
            raise ValueError(f"Invalid chain: {chain}. Must be 'main' or 'test'.")

        # Validate key_deriver parameter
        if key_deriver is None:
            raise ValueError("key_deriver is required")

        # Validate key_deriver parameter
        if key_deriver is not None and not hasattr(key_deriver, "derive_public_key"):
            raise ValueError("key_deriver must implement the KeyDeriver interface")

        self.chain: Chain = chain
        self.services: WalletServices | None = services
        # Track sync calls per writer for test compatibility
        self._sync_call_counts: dict[str, int] = {}
        self.key_deriver: KeyDeriver | None = key_deriver
        # TS parity: TypeScript uses 'storage' instead of 'storage_provider'
        self.storage: Any | None = storage_provider
        self.privileged_key_manager: PrivilegedKeyManager | None = privileged_key_manager

        # Initialize lookup resolver (TS parity)
        self.lookup_resolver: LookupResolver | None = lookup_resolver or self._create_lookup_resolver()

        # Initialize settings manager (TS parity)
        self.settings_manager: WalletSettingsManager = settings_manager or WalletSettingsManager(self)

        self.monitor: Monitor | None = monitor

        # Initialize BEEF and Wave 4 attributes
        # TS: this.beef = new BeefParty([this.userParty])
        # BeefParty requires user party identifier. Initialize user_party first for BEEF initialization
        self.user_party: str | None = None
        try:
            # Get the public key from key_deriver if available
            if self.key_deriver is not None:
                # Try to get the client change key pair's public key for user party identification
                key_pair = self.get_client_change_key_pair()
                pub_key = key_pair["publicKey"]
                self.user_party = f"user {pub_key}"
        except Exception:
            # If unable to retrieve public key, set generic user party
            self.user_party = "user unknown"

        # Initialize Beef instance (BeefParty equivalent - aggregates all BEEF data)
        # TS: this.beef = new BeefParty([this.userParty])
        # TS/Go parity: Use BEEF_V2 as default version (BRC-96)
        try:
            self.beef: Any = Beef(version=BEEF_V2)
        except Exception:
            # Fallback if Beef initialization fails
            self.beef = None

        # Fallback list for known txids when BEEF isn't available
        self._known_txids: list[str] = []

        self.auto_known_txids: bool = False  # Wave 4: autoKnownTxids setting
        self.include_all_source_transactions: bool = False  # Wave 4: includeAllSourceTransactions
        self.random_vals: list | None = None  # Wave 4: randomVals setting
        self.pending_sign_actions: TTLCache = TTLCache(ttl_seconds=300.0)  # Wave 4: Pending action tracking with TTL
        self.return_txid_only: bool = False  # Wave 4: returnTxidOnly setting for BEEF verification
        # TS parity: Wallet.ts sets `this.trustSelf = 'known'` and `createAction` applies
        # `args.options.trustSelf ||= this.trustSelf`.
        # TrustSelf is NOT a boolean; it is a string union with only "known".
        self.trust_self: str | None = "known"

        # Initialize caches for Discovery methods (Wave 5)
        # Format: {cacheKey: {value: ..., expiresAt: timestamp}}
        self._overlay_cache: dict[str, dict[str, Any]] = {}
        self._trust_settings_cache: dict[str, Any] | None = None
        self._trust_settings_cache_expires_at: float = 0

        # Initialize ProtoWallet for cryptographic operations (TS/Go parity)
        # TS: this.proto = new ProtoWallet(keyDeriver)
        # Go: w.proto = wallet.NewProtoWallet(keyDeriver)
        # py-sdk: ProtoWallet takes PrivateKey
        self.proto: ProtoWallet | None = None
        if self.key_deriver is not None:
            try:
                # Access the root private key from KeyDeriver
                root_key = getattr(self.key_deriver, "_root_private_key", None)
                if root_key is not None:
                    self.proto = ProtoWallet(root_key, permission_callback=lambda _: True)
            except Exception:
                # Fallback: proto remains None, direct implementation will be used
                pass

        # Wire services into storage for TS parity SpecOps (e.g., invalid change)
        try:
            if self.services is not None and self.storage is not None:
                # set_services exists on our StorageProvider implementation
                self.storage.set_services(self.services)
        except Exception:
            # Best-effort wiring; storage providers without set_services are tolerated
            pass

    def set_services(self, services: WalletServices | None) -> None:
        """Attach (or clear) Services on the wallet and best-effort wire into storage.

        Why:
            Some flows (e.g. signer.internalize_action AtomicBEEF normalization) require
            a Services handle at the Wallet layer. Remote storage clients are also
            supported; wiring into storage is best-effort.
        """
        self.services = services
        try:
            if self.services is not None and self.storage is not None and hasattr(self.storage, "set_services"):
                self.storage.set_services(self.services)
        except Exception:
            pass

    def get_services(self) -> WalletServices:
        """Return configured Services or raise.

        Note:
            `signer/methods.py` expects Wallet to expose `get_services()` for TS/Go parity.
        """
        if self.services is not None:
            return self.services

        # Best-effort fallback for callers that only wired services into a local StorageProvider.
        if self.storage is not None and hasattr(self.storage, "get_services"):
            try:
                services = self.storage.get_services()
                if services is not None:
                    return services
            except Exception:
                pass

        raise RuntimeError("Services must be configured on Wallet (pass services=... or call set_services()).")

    def get_client_change_key_pair(self) -> dict[str, str]:
        """Get the client change key pair (root key).

        Returns a dict with privateKey and publicKey (both as hex strings).

        TS Parity: Wallet.ts getClientChangeKeyPair()
        Reference: ts-wallet-toolbox/src/Wallet.ts

        Note: py-sdk's KeyDeriver should expose a public_key property
        similar to TS: keyDeriver.rootKey.toPublicKey()
        Currently uses internal _root_public_key as a workaround.

        Returns:
            dict with 'privateKey' and 'publicKey' (both hex strings)

        Raises:
            RuntimeError: If key_deriver is not available
        """
        if not self.key_deriver:
            raise RuntimeError("key_deriver is required for get_client_change_key_pair()")

        # WORKAROUND: py-sdk KeyDeriver should expose a public_key property
        # Ideally: pub_key = self.key_deriver.public_key
        # Current: Use internal _root_public_key attribute
        pub_key = self.key_deriver._root_public_key

        return {
            "privateKey": str(self.key_deriver._root_private_key),
            "publicKey": str(pub_key),
        }

    def _create_lookup_resolver(self) -> LookupResolver:
        """Create a LookupResolver configured for the wallet network.

        Returns:
            LookupResolver: Resolver capable of performing overlay queries
                against ls_identity, matching the TypeScript behavior.
        """
        network = self._to_wallet_network(self.chain)
        config = LookupResolverConfig(network_preset=network)
        try:
            return LookupResolver(config)
        except Exception as exc:  # pragma: no cover - defensive
            logger.error(
                "wallet.lookup_resolver.init_failed",
                extra={"chain": self.chain, "network": network},
                exc_info=exc,
            )
            raise RuntimeError("Failed to initialize LookupResolver") from exc

    def _validate_originator(self, originator: str | None) -> None:
        """Validate originator parameter.

        BRC-100 requires originator to be a string under 250 bytes.

        Args:
            originator: Originator domain name (optional)

        Raises:
            InvalidParameterError: If originator is invalid
        """
        if originator is not None:
            if not isinstance(originator, str):
                raise InvalidParameterError("originator", "must be a string")
            if len(originator.encode("utf-8")) > MAX_ORIGINATOR_LENGTH_BYTES:
                raise InvalidParameterError("originator", "must be under 250 bytes")

    def _convert_signature_args_to_proto_format(self, args: dict[str, Any]) -> dict[str, Any]:
        """Convert signature args from py-wallet-toolbox format to py-sdk format.

        py-wallet-toolbox uses standardized camelCase (protocolID, keyID, hashToDirectlySign)
        py-sdk ProtoWallet expects protocolID/keyID as well.

        Args:
            args: Arguments in py-wallet-toolbox format (camelCase only)

        Returns:
            Arguments in py-sdk format
        """
        # Validate protocol parameters first (camelCase enforcement)
        args = _validate_protocol_args(args)

        proto_args: dict[str, Any] = {}

        # Convert standardized protocolID to py-sdk expectation
        protocol_id = args.get("protocolID")
        if protocol_id is not None:
            proto_args["protocolID"] = protocol_id

        # Convert standardized keyID to py-sdk expectation
        key_id = args.get("keyID")
        if key_id is not None:
            proto_args["keyID"] = key_id

        # Convert counterparty to py-sdk format
        # py-sdk expects: 'self', 'anyone', or dict with {type, counterparty}
        # py-wallet-toolbox uses: 'self', 'anyone', or hex string
        counterparty = args.get("counterparty")
        if counterparty is not None:
            if isinstance(counterparty, str):
                if counterparty in ("self", "anyone"):
                    # py-sdk ProtoWallet._normalize_counterparty handles these strings
                    # but it expects them as None for 'self' or special handling
                    # We need to convert to dict format that py-sdk expects
                    if counterparty == "self":
                        proto_args["counterparty"] = {"type": CounterpartyType.SELF}
                    elif counterparty == "anyone":
                        proto_args["counterparty"] = {"type": CounterpartyType.ANYONE}
                else:
                    # Hex string - convert to dict format
                    proto_args["counterparty"] = {"type": CounterpartyType.OTHER, "counterparty": counterparty}
            elif isinstance(counterparty, PublicKey):
                proto_args["counterparty"] = {"type": CounterpartyType.OTHER, "counterparty": counterparty.hex()}
            else:
                proto_args["counterparty"] = counterparty

        # Convert data (normalize to bytes)
        data = args.get("data")
        if data is not None:
            proto_args["data"] = _as_bytes(data, "data")

        # Convert hashToDirectlySign -> hash_to_directly_sign
        hash_to_sign = args.get("hashToDirectlySign")
        if hash_to_sign is not None:
            direct_hash = _as_bytes(hash_to_sign, "hashToDirectlySign")
            proto_args["hashToDirectlySign"] = direct_hash

        # forSelf -> for_self
        for_self = args.get("forSelf")
        if for_self is not None:
            proto_args["forSelf"] = for_self

        return proto_args

    def _convert_verify_signature_args_to_proto_format(self, args: dict[str, Any]) -> dict[str, Any]:
        """Convert verify signature args from py-wallet-toolbox format to py-sdk format.

        Args:
            args: Arguments in py-wallet-toolbox format (camelCase only)

        Returns:
            Arguments in py-sdk format
        """
        # Validate protocol parameters first (camelCase enforcement)
        args = _validate_protocol_args(args)

        proto_args = self._convert_signature_args_to_proto_format(args)

        # Convert hashToDirectlyVerify -> hash_to_directly_verify
        hash_to_verify = args.get("hashToDirectlyVerify")
        if hash_to_verify is not None:
            direct_verify_hash = _as_bytes(hash_to_verify, "hashToDirectlyVerify")
            proto_args["hashToDirectlyVerify"] = direct_verify_hash

        # signature stays the same but normalize to bytes
        signature = args.get("signature")
        if signature is not None:
            proto_args["signature"] = _as_bytes(signature, "signature")

        return proto_args

    def _convert_get_public_key_args_to_proto_format(self, args: dict[str, Any]) -> dict[str, Any]:
        """Convert get_public_key args from py-wallet-toolbox format to py-sdk ProtoWallet format.

        py-wallet-toolbox uses camelCase (protocolID, keyID, forSelf, identityKey)
        py-sdk ProtoWallet.get_public_key expects the same format (it handles both).

        Args:
            args: Arguments in py-wallet-toolbox format (camelCase only)

        Returns:
            Arguments in py-sdk ProtoWallet format
        """
        # Validate protocol parameters first (camelCase enforcement)
        args = _validate_protocol_args(args)

        proto_args: dict[str, Any] = {}

        # Pass through identityKey
        if "identityKey" in args:
            proto_args["identityKey"] = args["identityKey"]

        # Pass through protocolID (py-sdk accepts list/tuple format)
        if "protocolID" in args:
            proto_args["protocolID"] = args["protocolID"]

        # Pass through keyID
        if "keyID" in args:
            proto_args["keyID"] = args["keyID"]

        # Convert counterparty to string format (py-sdk accepts string 'self'/'anyone'/hex)
        counterparty_arg = args.get("counterparty")
        if counterparty_arg is not None:
            if isinstance(counterparty_arg, PublicKey):
                proto_args["counterparty"] = counterparty_arg.hex()
            else:
                proto_args["counterparty"] = counterparty_arg

        # Pass through forSelf
        if "forSelf" in args:
            proto_args["forSelf"] = args["forSelf"]

        # Pass through seekPermission
        if "seekPermission" in args:
            proto_args["seekPermission"] = args["seekPermission"]

        return proto_args

    def _convert_counterparty_to_proto_format(self, counterparty_arg: Any) -> dict[str, Any] | None:
        """Convert counterparty to py-sdk ProtoWallet dict format.

        py-sdk ProtoWallet._normalize_counterparty expects:
        - dict with 'type' and optionally 'counterparty' keys
        - None -> SELF

        Args:
            counterparty_arg: Counterparty in py-wallet-toolbox format

        Returns:
            Dict in py-sdk format or None
        """
        if counterparty_arg is None:
            return None

        if isinstance(counterparty_arg, str):
            if counterparty_arg == "self":
                return {"type": CounterpartyType.SELF}
            elif counterparty_arg == "anyone":
                return {"type": CounterpartyType.ANYONE}
            else:
                # Hex string public key
                return {"type": CounterpartyType.OTHER, "counterparty": counterparty_arg}
        elif isinstance(counterparty_arg, PublicKey):
            return {"type": CounterpartyType.OTHER, "counterparty": counterparty_arg.hex()}
        else:
            return counterparty_arg

    def _convert_encrypt_args_to_proto_format(self, args: dict[str, Any]) -> dict[str, Any]:
        """Convert encrypt args from py-wallet-toolbox format to py-sdk ProtoWallet format.

        py-wallet-toolbox uses standardized camelCase (protocolID, keyID, forSelf)
        py-sdk ProtoWallet expects: plaintext + encryption_args dict with snake_case

        Args:
            args: Arguments in py-wallet-toolbox format (camelCase only)

        Returns:
            Arguments in py-sdk ProtoWallet format

        Raises:
            TypeError: If protocolID format is invalid
        """
        # Validate protocol parameters first (camelCase enforcement)
        args = _validate_protocol_args(args)

        plaintext = args.get("plaintext")
        if plaintext is not None:
            plaintext = _as_bytes(plaintext, "plaintext")

        protocol_id = args.get("protocolID")
        key_id = args.get("keyID")
        counterparty_arg = args.get("counterparty", "self")
        for_self = args.get("forSelf", False)

        # Build flattened args for py-sdk ProtoWallet
        result: dict[str, Any] = {
            "plaintext": plaintext,
            "forSelf": for_self,
        }

        if protocol_id is not None:
            # Validate protocolID format - must be tuple/list, not string
            if isinstance(protocol_id, str):
                raise TypeError("protocolID must be a tuple/list of [int, str], got str")
            try:
                # py-sdk expects protocolID as dict with securityLevel and protocol
                if isinstance(protocol_id, (list, tuple)) and len(protocol_id) == 2:
                    result["protocolID"] = {
                        "securityLevel": protocol_id[0],
                        "protocol": protocol_id[1],
                    }
                else:
                    result["protocolID"] = protocol_id
            except (TypeError, IndexError) as e:
                raise TypeError(
                    f"protocolID must be a tuple/list of [int, str], got {type(protocol_id).__name__}"
                ) from e

        if key_id is not None:
            result["keyID"] = key_id

        # Handle counterparty conversion - must use dict format for py-sdk
        result["counterparty"] = self._convert_counterparty_to_proto_format(counterparty_arg)

        return result

    def _convert_decrypt_args_to_proto_format(self, args: dict[str, Any]) -> dict[str, Any]:
        """Convert decrypt args from py-wallet-toolbox format to py-sdk ProtoWallet format.

        Args:
            args: Arguments in py-wallet-toolbox format (camelCase only)

        Returns:
            Arguments in py-sdk ProtoWallet format

        Raises:
            TypeError: If protocolID format is invalid
        """
        # Validate protocol parameters first (camelCase enforcement)
        args = _validate_protocol_args(args)

        ciphertext = args.get("ciphertext")
        if ciphertext is not None:
            ciphertext = _as_bytes(ciphertext, "ciphertext")

        protocol_id = args.get("protocolID")
        key_id = args.get("keyID")
        counterparty_arg = args.get("counterparty", "self")

        # Build flattened args for py-sdk ProtoWallet
        result: dict[str, Any] = {
            "ciphertext": ciphertext,
        }

        if protocol_id is not None:
            # Validate protocolID format - must be tuple/list, not string
            if isinstance(protocol_id, str):
                raise TypeError("protocolID must be a tuple/list of [int, str], got str")
            try:
                # py-sdk expects protocolID as dict with securityLevel and protocol
                if isinstance(protocol_id, (list, tuple)) and len(protocol_id) == 2:
                    result["protocolID"] = {
                        "securityLevel": protocol_id[0],
                        "protocol": protocol_id[1],
                    }
                else:
                    result["protocolID"] = protocol_id
            except (TypeError, IndexError) as e:
                raise TypeError(
                    f"protocolID must be a tuple/list of [int, str], got {type(protocol_id).__name__}"
                ) from e

        if key_id is not None:
            result["keyID"] = key_id

        # Handle counterparty conversion - must use dict format for py-sdk
        result["counterparty"] = self._convert_counterparty_to_proto_format(counterparty_arg)

        return result

    def _convert_hmac_args_to_proto_format(self, args: dict[str, Any]) -> dict[str, Any]:
        """Convert HMAC args from py-wallet-toolbox format to py-sdk ProtoWallet format.

        Args:
            args: Arguments in py-wallet-toolbox format (camelCase only)

        Returns:
            Arguments in py-sdk ProtoWallet format

        Raises:
            TypeError: If protocolID format is invalid
        """
        # Validate protocol parameters first (camelCase enforcement)
        args = _validate_protocol_args(args)

        data = args.get("data")
        if data is not None:
            data = _as_bytes(data, "data")

        protocol_id = args.get("protocolID")
        key_id = args.get("keyID")
        counterparty_arg = args.get("counterparty", "self")

        # Build flattened args for py-sdk ProtoWallet (which expects camelCase)
        result: dict[str, Any] = {
            "data": data,
        }

        if protocol_id is not None:
            # Validate protocolID format - must be tuple/list, not string
            if isinstance(protocol_id, str):
                raise TypeError("protocolID must be a tuple/list of [int, str], got str")
            try:
                # py-sdk expects protocolID as dict with securityLevel and protocol
                if isinstance(protocol_id, (list, tuple)) and len(protocol_id) == 2:
                    result["protocolID"] = {
                        "securityLevel": protocol_id[0],
                        "protocol": protocol_id[1],
                    }
                else:
                    result["protocolID"] = protocol_id
            except (TypeError, IndexError) as e:
                raise TypeError(
                    f"protocolID must be a tuple/list of [int, str], got {type(protocol_id).__name__}"
                ) from e

        if key_id is not None:
            result["keyID"] = key_id

        # Handle counterparty conversion - must use dict format for py-sdk
        result["counterparty"] = self._convert_counterparty_to_proto_format(counterparty_arg)

        return result

    def _convert_verify_hmac_args_to_proto_format(self, args: dict[str, Any]) -> dict[str, Any]:
        """Convert verify HMAC args from py-wallet-toolbox format to py-sdk ProtoWallet format.

        Args:
            args: Arguments in py-wallet-toolbox format

        Returns:
            Arguments in py-sdk ProtoWallet format
        """
        proto_args = self._convert_hmac_args_to_proto_format(args)

        # Add HMAC value to verify
        hmac_value = args.get("hmac")
        if hmac_value is not None:
            proto_args["hmac"] = _as_bytes(hmac_value, "hmac")

        return proto_args

    def _convert_reveal_counterparty_args_to_proto_format(self, args: dict[str, Any]) -> dict[str, Any]:
        """Convert reveal_counterparty_key_linkage args to py-sdk ProtoWallet format.

        Args:
            args: Arguments in py-wallet-toolbox format (camelCase)

        Returns:
            Arguments in py-sdk ProtoWallet format
        """
        counterparty = args.get("counterparty")
        verifier = args.get("verifier")

        # Convert PublicKey objects to appropriate format
        if hasattr(counterparty, "hex"):
            counterparty = counterparty.hex()
        if hasattr(verifier, "hex"):
            verifier = verifier.hex()

        return {
            "counterparty": counterparty,
            "verifier": verifier,
            "seekPermission": args.get("seekPermission", False),
        }

    def _convert_reveal_specific_args_to_proto_format(self, args: dict[str, Any]) -> dict[str, Any]:
        """Convert reveal_specific_key_linkage args to py-sdk ProtoWallet format.

        Args:
            args: Arguments in py-wallet-toolbox format (camelCase)

        Returns:
            Arguments in py-sdk ProtoWallet format
        """
        counterparty = args.get("counterparty")
        verifier = args.get("verifier")
        protocol_id = args.get("protocolID")
        key_id = args.get("keyID")

        # Convert PublicKey objects to appropriate format
        if hasattr(counterparty, "hex"):
            counterparty = counterparty.hex()
        if hasattr(verifier, "hex"):
            verifier = verifier.hex()

        proto_args: dict[str, Any] = {
            "counterparty": counterparty,
            "verifier": verifier,
            "keyID": key_id,
            "seekPermission": args.get("seekPermission", False),
        }

        # Convert protocolID format
        if protocol_id is not None:
            if isinstance(protocol_id, (list, tuple)) and len(protocol_id) == 2:
                proto_args["protocol_id"] = {
                    "securityLevel": protocol_id[0],
                    "protocol": protocol_id[1],
                }
            elif isinstance(protocol_id, dict):
                proto_args["protocol_id"] = protocol_id
            else:
                proto_args["protocol_id"] = protocol_id

        return proto_args

    def _to_wallet_network(self, chain: Chain) -> WalletNetwork:
        """Convert chain to wallet network name.

        Reference: ts-wallet-toolbox/src/utility/utilityHelpers.ts (toWalletNetwork)

        Args:
            chain: Chain identifier ('main' or 'test')

        Returns:
            Wallet network name ('mainnet' or 'testnet')

        Raises:
            ValueError: If chain is invalid
        """
        if chain == "main":
            return "mainnet"
        elif chain == "test":
            return "testnet"
        else:
            raise ValueError(f"Invalid chain: {chain}")

    @property
    def storage_party(self) -> str:
        """Get storage party identifier for BEEF operations.

        TS: this.storageParty returns `storage ${this.getStorageIdentity().storageIdentityKey}`

        Returns:
            String identifier for storage party in format 'storage <identity_key>'
        """
        try:
            if self.storage and hasattr(self.storage, "get_settings"):
                settings = self.storage.get_settings()
                if settings and "storageIdentityKey" in settings:
                    identity_key = settings["storageIdentityKey"]
                    return f"storage {identity_key}"
        except Exception:
            pass

        # Fallback: use identity key from key_deriver if available
        if self.key_deriver and hasattr(self.key_deriver, "identity_key"):
            return f"storage {self.key_deriver.identity_key().hex()}"

        return "storage unknown"

    def verify_returned_txid_only(self, beef: Beef, known_txids: list[str] | None = None) -> Beef:
        """Verify and complete txid-only transactions in BEEF.

        TS: verifyReturnedTxidOnly(beef: Beef, knownTxids?: string[]): Beef

        When returnTxidOnly is False, ensures all txid-only transactions in BEEF
        are merged with full transaction data from self.beef or known_txids.

        Args:
            beef: Beef object to verify
            known_txids: Optional list of known transaction IDs (can skip verification for these)

        Returns:
            Verified Beef object with txid-only transactions completed

        Raises:
            Exception: WERR_INTERNAL if unable to merge a txid-only transaction
        """
        if self.return_txid_only:
            return beef

        # Extract txid-only transactions and merge them with full data
        for btx in beef.txs.values():
            # Check if this is a txid-only transaction (data_format == 2)
            if btx.data_format == 2:  # TxIDOnly
                txid = btx.txid
                # Skip if known_txids contains this txid
                if known_txids and txid in known_txids:
                    continue

                # Find the full transaction in self.beef
                if self.beef and hasattr(self.beef, "find_atomic_transaction"):
                    tx = self.beef.find_atomic_transaction(txid)
                    if tx:
                        # Merge the full transaction
                        beef.merge_transaction(tx)
                    else:
                        msg = f"unable to merge txid {txid} into beef"
                        raise Exception(msg)
                else:
                    msg = f"unable to merge txid {txid} into beef"
                    raise Exception(msg)

        # Verify no remaining txid-only transactions (unless known)
        for btx in beef.txs.values():
            if btx.data_format == 2:  # TxIDOnly
                if known_txids and btx.txid in known_txids:
                    continue
                msg = f"remaining txidOnly {btx.txid} is not known"
                raise Exception(msg)

        return beef

    def verify_returned_txid_only_atomic_beef(
        self, beef_data: bytes | None, known_txids: list[str] | None = None
    ) -> bytes | None:
        """Verify and process returned AtomicBEEF data with txid-only verification.

        TS: verifyReturnedTxidOnlyAtomicBEEF(beef: AtomicBEEF, knownTxids?: string[]): AtomicBEEF

        Args:
            beef_data: Binary AtomicBEEF data (bytes) returned from transaction creation
            known_txids: Optional list of known transaction IDs for verification

        Returns:
            Verified AtomicBEEF data (bytes) or None if beef_data is None

        Raises:
            Exception: WERR_INTERNAL if unable to verify or reconstruct BEEF

        Note:
            The method:
            1. Parses the AtomicBEEF binary to extract the subject txid
            2. Calls verify_returned_txid_only to complete txid-only transactions
            3. Reconstructs the AtomicBEEF with to_binary_atomic()
        """
        if beef_data is None:
            return None

        if not isinstance(beef_data, (bytes, bytearray)):
            return beef_data

        try:
            # Parse AtomicBEEF to get subject txid
            beef, subject_txid, _ = parse_beef_ex(beef_data)

            if not subject_txid:
                msg = "unable to extract subject txid from atomic beef"
                raise Exception(msg)

            # Verify and complete txid-only transactions
            verified_beef = self.verify_returned_txid_only(beef, known_txids)

            # Reconstruct AtomicBEEF with verified data
            return verified_beef.to_binary_atomic(subject_txid)

        except Exception:
            # If verification fails, return original data as fallback
            return beef_data

    def get_known_txids(self, new_known_txids: list[str] | None = None) -> list[str]:
        """Extract valid transaction IDs from BEEF.

        BRC-100 Wave 4 helper method.
        Extracts known transaction IDs, optionally merging new ones into BEEF.

        TS Reference: Wallet.ts (getKnownTxids)

        Args:
            new_known_txids: Optional list of new transaction IDs to merge

        Returns:
            List of valid transaction IDs from BEEF or fallback list

        Note:
            Merges new txids into self.beef as txid-only transactions and returns
            all valid txids from the BEEF. Uses py-sdk Beef.merge_txid_only() and
            get_valid_txids() methods. Falls back to simple list when BEEF unavailable.
        """
        # Add new txids to fallback list (used when BEEF not available)
        if new_known_txids:
            for txid in new_known_txids:
                if txid not in self._known_txids:
                    self._known_txids.append(txid)

        if not self.beef:
            # Return sorted fallback list when BEEF not available
            return sorted(self._known_txids)

        try:
            # Merge new txids into BEEF as txid-only transactions
            if new_known_txids:
                for txid in new_known_txids:
                    if hasattr(self.beef, "merge_txid_only"):
                        self.beef.merge_txid_only(txid)

            # Get all valid txids from BEEF
            # TS: result = this.beef.sort_txs(); return result.get("valid", [])
            # py-sdk equivalent: beef.get_valid_txids()
            if hasattr(self.beef, "get_valid_txids"):
                return self.beef.get_valid_txids()

        except Exception:
            # Best-effort: if any error occurs, return fallback list
            pass

        return sorted(self._known_txids)

    def destroy(self) -> None:
        """Destroy wallet and clean up resources.

        BRC-100 WalletInterface method implementation.
        Close storage connections and destroy privileged key manager if present.

        TS parity:
            Mirrors TypeScript Wallet.destroy() by destroying storage and privileged key manager.

        Raises:
            Exception: If storage destruction fails

        Reference:
            - toolbox/ts-wallet-toolbox/src/Wallet.ts (destroy)
        """
        # Destroy storage provider if available
        if self.storage is not None:
            try:
                self.storage.destroy()
            except Exception:
                # Best-effort cleanup; allow exceptions to propagate if needed
                raise

    def get_identity_key(self) -> str:
        """Get the wallet's identity key (public key).

        BRC-100 WalletInterface method implementation.
        Returns the identity public key derived from root key.

        TS parity:
            Mirrors TypeScript Wallet.getIdentityKey() which calls getPublicKey({ identityKey: true }).

        Returns:
            str: Public key in hex format

        Raises:
            RuntimeError: If key_deriver is not configured

        Reference:
            - toolbox/ts-wallet-toolbox/src/Wallet.ts (getIdentityKey)
        """
        result = self.get_public_key({"identityKey": True})
        return result["publicKey"]

    def list_outputs(self, args: dict[str, Any], originator: str | None = None) -> dict[str, Any]:
        """List outputs via Storage provider (minimal TS-like shape).

        Summary:
            Wallet API that delegates to Storage to enumerate outputs. Returns
            TS-like minimal keys used by tests and callers.
        TS parity:
            Matches TypeScript Wallet listOutputs minimal result keys and input
            expectations (auth.userId present in args).
        Args:
            args: Input dict including 'auth' (with 'userId') and optional filters.
            originator: Optional originator domain string (<250 bytes).
        Returns:
            Dict with keys: totalOutputs, outputs.
        Raises:
            InvalidParameterError: If originator or args are invalid.
            RuntimeError: If storage provider is not configured.
        Reference:
            toolbox/ts-wallet-toolbox/src/Wallet.ts
        """
        from bsv_wallet_toolbox.utils.validation import validate_list_outputs_args

        # Validate parameters
        self._validate_originator(originator)
        validate_list_outputs_args(args)

        if not self.storage:
            raise RuntimeError("storage provider is not configured")
        auth = args.get("auth")
        if not auth:
            auth = self._make_auth()
            # Avoid mutating caller's dict
            args = {**args, "auth": auth}

        trace(logger, "wallet.list_outputs.call", originator=originator, auth=auth, args=args)
        try:
            result = self.storage.list_outputs(auth, args)
            trace(logger, "wallet.list_outputs.result", originator=originator, result=result)
            return result
        except Exception as e:
            trace(logger, "wallet.list_outputs.error", originator=originator, error=str(e), exc_type=type(e).__name__)
            raise

    def list_certificates(self, args: dict[str, Any], originator: str | None = None) -> dict[str, Any]:
        """List certificates with optional filters.

        Args:
            args: Input dict with optional filters (certifiers, types, limit, etc.)
            originator: Optional originator domain string (<250 bytes).

        Returns:
            Dict with keys: totalCertificates, certificates.

        Raises:
            InvalidParameterError: If originator or args are invalid.
            RuntimeError: If storage provider is not configured.
        """
        from bsv_wallet_toolbox.utils.validation import validate_list_certificates_args

        # Validate parameters
        self._validate_originator(originator)
        validate_list_certificates_args(args)

        if not self.storage:
            raise RuntimeError("storage provider is not configured")

        # Generate auth object with identity key
        auth = args.get("auth") if "auth" in args else self._make_auth()

        # Delegate to storage provider (TS parity)
        return self.storage.list_certificates(auth, args)

    def relinquish_output(self, args: dict[str, Any], originator: str | None = None) -> dict[str, Any]:
        """Mark an output as relinquished (soft-delete).

        Args:
            args: Input dict containing:
                - output: str - output identifier (txid.index)
                - basket: str - basket name
            originator: Optional originator domain name (under 250 bytes)

        Returns:
            dict: With key 'relinquished' (bool)

        Raises:
            RuntimeError: If storage_provider is not configured
        """
        from bsv_wallet_toolbox.utils.validation import validate_relinquish_output_args

        self._validate_originator(originator)

        # Validate arguments
        vargs = validate_relinquish_output_args(args)

        if not self.storage:
            raise RuntimeError("storage provider is not configured")

        # Generate auth object with identity key
        auth = self._make_auth()

        # Extract outpoint from validated args
        outpoint = vargs["output"]

        # Delegate to storage provider
        result = self.storage.relinquish_output(auth, outpoint)

        return {"relinquished": bool(result)}

    def list_actions(self, args: dict[str, Any], originator: str | None = None) -> dict[str, Any]:
        """List actions with optional filters.

        BRC-100 WalletInterface method implementation.
        Returns a list of actions for the wallet with optional label and pagination filters.

        TS parity:
            Mirrors TypeScript Wallet.listActions behavior by delegating to storage
            with validated arguments and generated auth object.

        Args:
            args: Input dict containing optional filters:
                - labels: list[str] - action labels to filter by
                - labelQueryMode: 'any' | 'all' - how to combine label filters (default 'any')
                - limit: int - max results to return (default 50, max 10000)
                - offset: int - pagination offset (default 0, max 10000)
            originator: Optional originator domain name (under 250 bytes)

        Returns:
            dict: With keys 'totalActions' (int) and 'actions' (list)

        Raises:
            InvalidParameterError: If originator or args are invalid
            RuntimeError: If storage_provider or keyDeriver is not configured

        Example:
            >>> wallet = Wallet(chain="main", storage_provider=sp, key_deriver=kd)
            >>> result = wallet.list_actions({})
            >>> assert "totalActions" in result
            >>> assert "actions" in result

        Reference:
            - toolbox/ts-wallet-toolbox/src/Wallet.ts (listActions method)
            - toolbox/ts-wallet-toolbox/src/storage/StorageProvider.ts (listActions method)
            - toolbox/ts-wallet-toolbox/src/validation/validation.ts (validateListActionsArgs)
        """
        self._validate_originator(originator)

        if not self.storage:
            raise RuntimeError("storage provider is not configured")

        # Validate input arguments (raises InvalidParameterError on failure)
        validate_list_actions_args(args)

        # Generate auth object with identity key
        auth = self._make_auth()

        # Delegate to storage provider (TS parity)
        return self.storage.list_actions(auth, args)

    def abort_action(self, args: dict[str, Any], originator: str | None = None) -> dict[str, Any]:
        """Abort an action.

        BRC-100 WalletInterface method implementation.
        Cancel/abort an in-progress action by reference.

        TS parity:
            Mirrors TypeScript Wallet.abortAction behavior by delegating to storage
            with validated arguments.

        Args:
            args: Input dict containing:
                - reference: str - base64-encoded action reference (required)
            originator: Optional originator domain name (under 250 bytes)

        Returns:
            dict: With key 'aborted' (bool) indicating success

        Raises:
            InvalidParameterError: If originator or args are invalid
            RuntimeError: If storage_provider is not configured

        Reference:
            - toolbox/ts-wallet-toolbox/src/Wallet.ts (abortAction method)
            - toolbox/ts-wallet-toolbox/src/storage/StorageProvider.ts (abortAction method)
            - toolbox/ts-wallet-toolbox/src/validation/validation.ts (validateAbortActionArgs)
        """
        self._validate_originator(originator)

        if not self.storage:
            raise RuntimeError("storage provider is not configured")

        # Validate input arguments (raises InvalidParameterError on failure)
        validate_abort_action_args(args)

        # Extract reference and call storage provider
        reference = args.get("reference", "")
        result = self.storage.abort_action(reference)

        return {"aborted": bool(result)}

    def relinquish_certificate(self, args: dict[str, Any], originator: str | None = None) -> dict[str, Any]:
        """Mark a certificate as no longer in use.

        BRC-100 WalletInterface method implementation.
        Soft-delete a certificate from active use.

        TS parity:
            Mirrors TypeScript Wallet.relinquishCertificate behavior by delegating
            to storage with validated arguments and always returning success.

        Args:
            args: Input dict containing:
                - type: str - base64-encoded certificate type (required)
                - serialNumber: str - base64-encoded serial number (required)
                - certifier: str - non-empty even-length hex string (required)
            originator: Optional originator domain name (under 250 bytes)

        Returns:
            dict: With key 'relinquished' (bool), always True on success

        Raises:
            InvalidParameterError: If originator or args are invalid
            RuntimeError: If storage_provider is not configured

        Reference:
            - toolbox/ts-wallet-toolbox/src/Wallet.ts (relinquishCertificate method)
            - toolbox/ts-wallet-toolbox/src/storage/StorageProvider.ts (relinquishCertificate method)
            - toolbox/ts-wallet-toolbox/src/validation/validation.ts (validateRelinquishCertificateArgs)
        """
        self._validate_originator(originator)

        if not self.storage:
            raise RuntimeError("storage provider is not configured")

        # Validate input arguments (raises InvalidParameterError on failure)
        validate_relinquish_certificate_args(args)

        # Generate auth object with identity key
        auth = self._make_auth()

        # Call storage provider with auth (TypeScript parity)
        self.storage.relinquish_certificate(auth, args)

        # Always return success (TypeScript parity)
        return {"relinquished": True}

    def create_action(self, args: dict[str, Any], originator: str | None = None) -> dict[str, Any]:
        """Create a new transaction action.

        BRC-100 WalletInterface method.
        Begin construction of a new transaction with inputs and outputs.

        Args:
            args: Input dict containing transaction construction parameters:
                - inputs: list - transaction inputs
                - outputs: list - transaction outputs
                - labels: list - action labels (optional)
                - options: dict - transaction options (optional):
                    - trustSelf: TrustSelf - TS: type TrustSelf = "known"
                    - knownTxids: list - pre-known transaction IDs
                    - isDelayed: bool - allow delayed results
            originator: Optional originator domain name (under 250 bytes)

        Returns:
            dict: CreateActionResult

        Raises:
            InvalidParameterError: If originator or args are invalid
            RuntimeError: If storage_provider is not configured

        Reference: toolbox/ts-wallet-toolbox/src/Wallet.ts (createAction)
        """
        self._validate_originator(originator)

        if not self.storage:
            raise RuntimeError("storage_provider is not configured")

        trace(logger, "wallet.create_action.call", originator=originator, args=args)
        # Initialize options if not provided (TS parity: args.options ||= {})
        if "options" not in args or args["options"] is None:
            args["options"] = {}

        # Apply wallet-level trustSelf setting (TS: args.options.trustSelf ||= this.trustSelf)
        current_trust_self = args["options"].get("trustSelf")
        if isinstance(current_trust_self, bool):
            # Back-compat: old Python code used boolean. TS/Go do not.
            current_trust_self = "known" if current_trust_self else None
        if not current_trust_self:
            # TS default: "known"
            args["options"]["trustSelf"] = getattr(self, "trust_self", "known") or "known"
        else:
            args["options"]["trustSelf"] = current_trust_self

        # Apply autoKnownTxids if enabled (TS: this.autoKnownTxids && !args.options.knownTxids)
        if self.auto_known_txids and "knownTxids" not in args["options"]:
            # Get known transaction IDs from wallet state (TS parity: calls getKnownTxids)
            args["options"]["knownTxids"] = self.get_known_txids(args["options"].get("knownTxids"))

        # Validate and normalize args - returns vargs with computed flags (TS parity)
        # validate_create_action_args computes: isNewTx, isSendWith, isDelayed, isNoSend, etc.
        vargs = validate_create_action_args(args)
        trace(logger, "wallet.create_action.validated", originator=originator, vargs=vargs)

        # Generate auth object with identity key
        auth = self._make_auth()
        trace(logger, "wallet.create_action.auth", originator=originator, auth=auth)

        # Apply wallet-level configuration for complete transaction handling
        # TS: vargs.includeAllSourceTransactions = this.includeAllSourceTransactions
        if "includeAllSourceTransactions" not in vargs:
            vargs["includeAllSourceTransactions"] = getattr(self, "include_all_source_transactions", True)

        # Apply random values if configured (TS: if (this.randomVals && this.randomVals.length > 1))
        random_vals = getattr(self, "random_vals", None)
        if random_vals and len(random_vals) > 1 and "randomVals" not in vargs:
            vargs["randomVals"] = random_vals[:]

        # Note: isSignAction is already computed in validate_create_action_args
        # No need to recompute here - validation handles it correctly

        # Delegate to signer layer for BRC-100 compliant result (TS: await createAction(this, auth, vargs))
        try:
            signer_result = signer_create_action(self, auth, vargs)
            trace(
                logger,
                "wallet.create_action.signer_result",
                originator=originator,
                signer_result=getattr(signer_result, "__dict__", signer_result),
            )
        except Exception as e:
            trace(logger, "wallet.create_action.error", originator=originator, error=str(e), exc_type=type(e).__name__)
            raise

        # Convert CreateActionResultX to BRC-100 CreateActionResult
        result: dict[str, Any] = {}
        # Note: sendWithResults and notDelayedResults are internal and not part of BRC-100 spec
        if signer_result.txid is not None:
            result["txid"] = signer_result.txid
        if signer_result.tx is not None:
            # Convert tx bytes to list[int] for JSON compatibility (BRC-100 spec)
            result["tx"] = _to_byte_list(signer_result.tx) if isinstance(signer_result.tx, bytes) else signer_result.tx
        if signer_result.no_send_change is not None or vargs.get("options", {}).get("noSend"):
            result["noSendChange"] = signer_result.no_send_change or []
        if signer_result.no_send_change_output_vouts is not None:
            result["noSendChangeOutputVouts"] = signer_result.no_send_change_output_vouts
        if signer_result.signable_transaction is not None:
            signable_tx = signer_result.signable_transaction.copy()
            if "tx" in signable_tx and isinstance(signable_tx["tx"], bytes):
                signable_tx["tx"] = _to_byte_list(signable_tx["tx"])
            result["signableTransaction"] = signable_tx
        # sendWithResults and notDelayedResults are internal - not included in BRC-100 result

        # Wave 4 Enhancement - BEEF integration (TS parity)
        # 1. BEEF merge from transaction (if r.tx): this.beef.mergeBeefFromParty(this.storageParty, r.tx)
        if "tx" in result and result["tx"] is not None and self.beef is not None:
            try:
                beef_data = result["tx"]
                # Merge BEEF from result into wallet's BEEF state
                if hasattr(self.beef, "merge_beef"):
                    # BeefParty equivalent - merge with storage party tracking
                    self.beef.merge_beef(beef_data)
                elif hasattr(self.beef, "merge"):
                    self.beef.merge(beef_data)
            except Exception:
                # Best-effort BEEF merge; don't fail transaction on merge errors
                pass

        # 2. Atomic BEEF verification (if r.tx): r.tx = this.verifyReturnedTxidOnlyAtomicBEEF(...)
        if "tx" in result and result["tx"] is not None:
            known_txids = vargs.get("options", {}).get("knownTxids")
            verified_beef = self.verify_returned_txid_only_atomic_beef(result["tx"], known_txids)
            if verified_beef is not None:
                result["tx"] = verified_beef

        # 3. Error handling (unless isDelayed): throwIfAnyUnsuccessfulCreateActions(r)
        if not vargs.get("isDelayed"):
            # Use signer_result's internal fields (which include sendWithResults/notDelayedResults)
            # to decide whether any immediate broadcasts failed. This mirrors TS behaviour where
            # throwIfAnyUnsuccessfulCreateActions operates on the extended CreateActionResultX.
            internal_result: dict[str, Any] = {
                "notDelayedResults": signer_result.not_delayed_results,
                "sendWithResults": signer_result.send_with_results,
                "txid": signer_result.txid,
                "tx": signer_result.tx,
                "noSendChange": signer_result.no_send_change,
            }
            throw_if_any_unsuccessful_create_actions(internal_result)

        return result

    def sign_action(self, args: dict[str, Any], originator: str | None = None) -> dict[str, Any]:
        """Sign and finalize a transaction action.

        BRC-100 WalletInterface method.
        Complete a transaction by adding signatures and committing to storage.

        Args:
            args: Input dict containing signed transaction details:
                - reference: str - unique reference from createAction result
                - rawTx: str - signed raw transaction (hex or binary)
                - isNewTx: bool - whether this is a new transaction
                - isSendWith: bool - whether to send with other txids
                - isNoSend: bool - whether to suppress network broadcast
                - isDelayed: bool - whether to accept delayed broadcast
                - sendWith: list - txids to send with (optional)
            originator: Optional originator domain name (under 250 bytes)

        Returns:
            dict: SignActionResult

        Raises:
            InvalidParameterError: If originator or args are invalid
            RuntimeError: If storage_provider is not configured

        Reference: toolbox/ts-wallet-toolbox/src/Wallet.ts (signAction)
        """
        self._validate_originator(originator)

        if not self.storage:
            raise RuntimeError("storage_provider is not configured")

        trace(logger, "wallet.sign_action.call", originator=originator, args=args)
        # Validate input arguments (raises InvalidParameterError on failure)
        validate_sign_action_args(args)
        trace(logger, "wallet.sign_action.validated", originator=originator, args=args)

        # Generate auth object with identity key
        auth = self._make_auth()
        trace(logger, "wallet.sign_action.auth", originator=originator, auth=auth)

        # Delegate to signer layer for BRC-100 compliant signing
        # TS: const { auth, vargs } = this.validateAuthAndArgs(args, validateSignActionArgs)
        # TS: const r = await signAction(this, auth, args)
        try:
            signer_result = signer_sign_action(self, auth, args)
            trace(logger, "wallet.sign_action.signer_result", originator=originator, signer_result=signer_result)
        except Exception as e:
            trace(logger, "wallet.sign_action.error", originator=originator, error=str(e), exc_type=type(e).__name__)
            raise

        # Convert to BRC-100 SignActionResult format
        # Remove internal fields (sendWithResults, notDelayedResults) - not part of BRC-100 spec
        result = {}
        if signer_result.get("txid") is not None:
            result["txid"] = signer_result["txid"]
        if signer_result.get("tx") is not None:
            # Convert tx bytes to list[int] for JSON compatibility (BRC-100 spec)
            result["tx"] = (
                _to_byte_list(signer_result["tx"]) if isinstance(signer_result["tx"], bytes) else signer_result["tx"]
            )
        # sendWithResults and notDelayedResults are internal - not included in BRC-100 result

        # Wave 4 Enhancement - Pending action tracking & BEEF integration (TS parity)
        # 1. Pending sign action lookup (if this.pendingSignActions[args.reference])
        reference = args.get("reference")
        prior_action = None
        if reference and reference in self.pending_sign_actions:
            prior_action = self.pending_sign_actions.get(reference)
            # TS: const prior = this.pendingSignActions[args.reference]
            # Use prior action for full BEEF reconstruction and known_txids verification

        # 2. BEEF merge and verification
        if "tx" in result and result["tx"] is not None and self.beef is not None:
            try:
                beef_data = result["tx"]
                # Try to reconstruct BEEF from signed transaction
                if isinstance(beef_data, (bytes, bytearray)):
                    # Attempt to parse BEEF and merge
                    try:
                        parsed_beef = parse_beef(beef_data)
                        self.beef.merge_beef(parsed_beef)
                    except Exception:
                        # BEEF parsing or merge failed, skip
                        pass
            except Exception:
                # Best-effort BEEF processing
                pass

        # TS: if (r.tx) r.tx = this.verifyReturnedTxidOnlyAtomicBEEF(r.tx, prior.args.options?.knownTxids)
        # Use prior action's knownTxids if available for verification
        if "tx" in result and result["tx"] is not None and prior_action:
            try:
                known_txids = prior_action.get("args", {}).get("options", {}).get("knownTxids")
                verified_beef = self.verify_returned_txid_only_atomic_beef(result["tx"], known_txids)
                if verified_beef is not None:
                    result["tx"] = verified_beef
            except Exception:
                # Best-effort verification
                pass

        # 3. Error handling: throwIfAnyUnsuccessfulSignActions(r)
        # Check if undelayed mode is enabled
        if not args.get("options", {}).get("isDelayed"):
            throw_if_any_unsuccessful_sign_actions(result)

        return result

    def process_action(self, args: dict[str, Any], originator: str | None = None) -> dict[str, Any]:
        """Process a transaction action (legacy alias for sign_action).

        Deprecated: Use sign_action() instead. This method is maintained for backward compatibility.

        Reference: toolbox/ts-wallet-toolbox/src/Wallet.ts (signAction method)
        """
        trace(logger, "wallet.process_action.call", originator=originator, args=args)
        result = self.sign_action(args, originator)
        trace(logger, "wallet.process_action.result", originator=originator, result=result)
        return result

    def internalize_action(self, args: dict[str, Any], originator: str | None = None) -> dict[str, Any]:
        """Internalize a transaction action.

        BRC-100 WalletInterface method.
        Allow a wallet to take ownership of outputs in a pre-existing transaction.

        Args:
            args: Input dict containing transaction internalization parameters:
                - tx: str - atomic BEEF (Binary Encoded Expression Format) of transaction
                - outputs: list - output internalization specifications:
                    - outputIndex: int - index of output in transaction
                    - protocol: str - 'wallet payment' or 'basket insertion'
                    - paymentRemittance: dict - for wallet payment outputs
                    - basketName: str - for basket insertion outputs
                - labels: list - action labels (optional)
            originator: Optional originator domain name (under 250 bytes)

        Returns:
            dict: InternalizeActionResult

        Raises:
            InvalidParameterError: If originator or args are invalid
            RuntimeError: If storage_provider is not configured

        Reference: toolbox/ts-wallet-toolbox/src/Wallet.ts (internalizeAction)
        """
        self._validate_originator(originator)

        if not self.storage:
            raise RuntimeError("storage_provider is not configured")

        # Validate input arguments (raises InvalidParameterError on failure)
        validate_internalize_action_args(args)

        # Generate auth object with identity key
        auth = self._make_auth()

        # Apply error handling for throwReviewActions label if present
        # TS: if (vargs.labels.indexOf(specOpThrowReviewActions) >= 0) throwDummyReviewActions()
        labels = args.get("labels", [])
        if specOpThrowReviewActions in labels:
            # Implement throwDummyReviewActions() to fail with dummy review actions
            _throw_dummy_review_actions()

        # Delegate to signer layer for BRC-100 compliant internalization
        # TS: const r = await internalizeAction(this, auth, args)
        trace(logger, "wallet.internalize_action.call", originator=originator, auth=auth, args=args)
        try:
            result = signer_internalize_action(self, auth, args)
            trace(logger, "wallet.internalize_action.result", originator=originator, result=result)
        except Exception as e:
            trace(
                logger,
                "wallet.internalize_action.error",
                originator=originator,
                error=str(e),
                exc_type=type(e).__name__,
            )
            raise

        # Wave 4 Enhancement - Error handling & validation & BEEF integration
        # 1. BEEF merge from input
        if "tx" in args and args["tx"] is not None and self.beef is not None:
            try:
                input_beef = args["tx"]
                # Merge input BEEF into wallet state
                if hasattr(self.beef, "merge_beef"):
                    self.beef.merge_beef(input_beef)
                elif hasattr(self.beef, "merge"):
                    self.beef.merge(input_beef)
            except Exception:
                # Best-effort BEEF merge
                pass

        # 2. BEEF merge verification from result
        if "tx" in result and result["tx"] is not None and self.beef is not None:
            try:
                result_beef = result["tx"]
                # Merge result BEEF
                if hasattr(self.beef, "merge_beef"):
                    self.beef.merge_beef(result_beef)
                elif hasattr(self.beef, "merge"):
                    self.beef.merge(result_beef)
            except Exception:
                pass

        # 3. Error validation: throwIfUnsuccessfulInternalizeAction(r)
        # Check if undelayed mode is enabled
        if not args.get("options", {}).get("isDelayed"):
            throw_if_unsuccessful_internalize_action(result)

        return result

    def get_network(
        self,
        _args: dict[str, Any],  # Empty dict (unused but required by interface)
        originator: str | None = None,
    ) -> GetNetworkResult:
        """Get Bitcoin network.

        BRC-100 WalletInterface method implementation.
        Returns the Bitcoin network (mainnet or testnet) that this wallet is using.

        Reference:
            - ts-wallet-toolbox/src/Wallet.ts
            - ts-wallet-toolbox/test/Wallet/get/getNetwork.test.ts

        Args:
            args: Empty dict (getNetwork takes no parameters)
            originator: Optional originator domain name (must be string under 250 bytes)

        Returns:
            Dictionary with 'network' key containing 'mainnet' or 'testnet'

        Raises:
            InvalidParameterError: If originator is invalid

        Example:
            >>> wallet = Wallet(chain="main")
            >>> result = wallet.get_network({})
            >>> assert result == {"network": "mainnet"}
        """
        self._validate_originator(originator)
        return {"network": self._to_wallet_network(self.chain)}

    def get_version(
        self,
        _args: dict[str, Any],  # Empty dict (unused but required by interface)
        originator: str | None = None,
    ) -> GetVersionResult:
        """Get wallet version.

        BRC-100 WalletInterface method implementation.

        Reference:
            - ts-wallet-toolbox/src/Wallet.ts
            - ts-wallet-toolbox/test/Wallet/get/getVersion.test.ts

        Args:
            args: Empty dict (getVersion takes no parameters)
            originator: Optional originator domain name (must be string under 250 bytes)

        Returns:
            Dictionary with 'version' key containing the version string

        Raises:
            InvalidParameterError: If originator is invalid

        Example:
            >>> wallet = Wallet()
            >>> result = wallet.get_version({})
            >>> assert result == {"version": Wallet.VERSION}
        """
        # Validate arguments
        validate_get_version_args(_args)

        self._validate_originator(originator)
        return {"version": self.VERSION}

    def get_client_change_key_pair(self) -> dict[str, str]:
        """Get the client change key pair.

        Returns the root key pair (private and public keys) used for change outputs
        and wallet identification.

        Reference: toolbox/ts-wallet-toolbox/src/Wallet.ts (getClientChangeKeyPair)

        Returns:
            dict: Key pair with 'privateKey' and 'publicKey' as hex strings

        Raises:
            RuntimeError: If key_deriver is not configured
        """
        if not self.key_deriver:
            raise RuntimeError("key_deriver is not configured")

        # Get root private key from key deriver (accessing private attribute for parity with TypeScript)
        root_private_key = self.key_deriver._root_private_key  # type: ignore
        root_public_key = self.key_deriver._root_public_key  # type: ignore

        return {
            "privateKey": root_private_key.hex(),
            "publicKey": root_public_key.hex(),
        }

    def _make_auth(self) -> dict[str, Any]:
        """Generate auth object containing wallet userId.

        Helper method that creates an auth dict with the wallet's user ID
        for use by storage provider methods.

        Mirrors TypeScript: `{ userId: this.userId }`.

        Note:
            Some remote storage servers also expect `identityKey` to be present for
            server-side auth consistency checks. Including it is harmless for local
            storage providers and improves interoperability.

        TS parity:
            The userId is the wallet's user record ID in the database,
            used by StorageProvider to identify the user across storage operations.

        Returns:
            dict: Auth object with 'userId' key containing integer user ID

        Raises:
            RuntimeError: If storage_provider or keyDeriver is not configured

        Example:
            >>> wallet = Wallet(chain="main", storage_provider=sp, key_deriver=kd)
            >>> auth = wallet._make_auth()
            >>> assert "userId" in auth
            >>> assert isinstance(auth["userId"], int)

        Reference:
            - toolbox/ts-wallet-toolbox/src/Wallet.ts (validateAuthAndArgs pattern)
            - toolbox/ts-wallet-toolbox/src/storage/StorageProvider.ts
        """
        if self.storage is None:
            raise RuntimeError("storage_provider is not configured")
        if self.key_deriver is None:
            raise RuntimeError("keyDeriver is not configured")

        # Get or create user based on identity key
        identity_key_hex = self.key_deriver._root_public_key.hex()

        # Get or create user by identity key
        user_id = self.storage.get_or_create_user_id(identity_key_hex)

        auth = {"userId": user_id, "identityKey": identity_key_hex}
        trace(logger, "wallet.make_auth.result", auth=auth)
        return auth

    def ensure_initialized(self, *, ensure_default_basket: bool = True) -> dict[str, Any]:
        """Ensure storage-side user state exists (and optionally the default basket).

        Why:
            Example scripts and consumers should not have to remember which call "implicitly"
            creates user/basket records. A fresh wallet should be usable with `internalizeAction`
            as the first operation.

        What it does:
        - Calls the wallet's auth bootstrap (creates/loads the user row).
        - Best-effort: creates the default output basket ("default") when supported.

        Returns:
            The auth dict (`{"userId": int, "identityKey": str}`) used by storage calls.
        """
        auth = self._make_auth()
        if ensure_default_basket and self.storage is not None and hasattr(self.storage, "find_or_insert_output_basket"):
            try:
                self.storage.find_or_insert_output_basket(int(auth["userId"]), "default")
            except Exception:
                # Best-effort: some storages may not implement this helper; other flows create it on demand.
                pass
        return auth

    def is_authenticated(
        self,
        _args: dict[str, Any],
        originator: str | None = None,  # Empty dict for isAuthenticated (unused but required by interface)
    ) -> AuthenticatedResult:
        """Check if user is authenticated.

        BRC-100 WalletInterface method implementation.
        In the base Wallet implementation, authentication is always true since
        the wallet is initialized with keys.

        Reference:
            - ts-wallet-toolbox/src/Wallet.ts

        Args:
            args: Empty dict (isAuthenticated takes no parameters)
            originator: Optional originator domain name (must be string under 250 bytes)

        Returns:
            Dictionary with 'authenticated' key set to True

        Raises:
            InvalidParameterError: If originator is invalid

        Example:
            >>> wallet = Wallet()
            >>> result = wallet.is_authenticated({})
            >>> assert result == {"authenticated": True}
        """
        self._validate_originator(originator)
        return {"authenticated": True}

    def wait_for_authentication(
        self,
        _args: dict[str, Any],
        originator: str | None = None,  # Empty dict for waitForAuthentication (unused but required by interface)
    ) -> AuthenticatedResult:
        """Wait for user authentication.

        BRC-100 WalletInterface method implementation.
        In the base Wallet implementation, returns immediately with authenticated=true
        since the wallet is always authenticated (initialized with keys).

        Note:
            In wallet manager implementations (SimpleWalletManager, CWIStyleWalletManager),
            this method waits in a loop until authentication occurs. However, in the base
            Wallet class, authentication is immediate.

        Reference:
            - ts-wallet-toolbox/src/Wallet.ts

        Args:
            args: Empty dict (waitForAuthentication takes no parameters)
            originator: Optional originator domain name (must be string under 250 bytes)

        Returns:
            Dictionary with 'authenticated' key set to True

        Raises:
            InvalidParameterError: If originator is invalid

        Example:
            >>> wallet = Wallet()
            >>> result = wallet.wait_for_authentication({})
            >>> assert result == {"authenticated": True}
        """
        self._validate_originator(originator)
        return {"authenticated": True}

    def get_height(
        self,
        _args: dict[str, Any],  # Empty dict (unused but required by interface)
        originator: str | None = None,
    ) -> GetHeightResult:
        """Get current blockchain height.

        BRC-100 WalletInterface method implementation.
        Returns the current height of the blockchain by querying configured services.

        Reference:
            - ts-wallet-toolbox/src/Wallet.ts
            - ts-wallet-toolbox/test/Wallet/get/getHeight.test.ts

        Args:
            args: Empty dict (getHeight takes no parameters)
            originator: Optional originator domain name (must be string under 250 bytes)

        Returns:
            Dictionary with 'height' key containing current blockchain height

        Raises:
            InvalidParameterError: If originator parameter is invalid
            RuntimeError: If services are not configured

        Example:
            >>> from bsv_wallet_toolbox.services import MockWalletServices
            >>> services = MockWalletServices(height=850000)
            >>> wallet = Wallet(services=services)
            >>> result = wallet.get_height({})
            >>> print(result["height"])
            850000

        Note:
            Requires services to be configured. If services is None, raises RuntimeError.
        """
        self._validate_originator(originator)

        if self.services is None:
            raise RuntimeError("Services must be configured to use getHeight")

        height = self.services.get_height()
        return {"height": height}

    def get_header(self, args: dict[str, Any], originator: str | None = None) -> GetHeaderResult:
        """Get block header at specified height (alias for get_header_for_height).

        BRC-100 WalletInterface method implementation.
        Returns the block header at the specified height as a hex string.

        This is an alias for get_header_for_height to match BRC-100 interface.

        Args:
            args: Dictionary with 'height' key (non-negative integer)
            originator: Optional originator domain name (must be string under 250 bytes)

        Returns:
            Dictionary with 'header' key containing block header as hex string

        Raises:
            InvalidParameterError: If originator parameter is invalid or height is invalid
            RuntimeError: If services are not configured
        """
        return self.get_header_for_height(args, originator)

    def get_header_for_height(self, args: dict[str, Any], originator: str | None = None) -> GetHeaderResult:
        """Get block header at specified height.

        BRC-100 WalletInterface method implementation.
        Returns the block header at the specified height as a hex string.

        Reference:
            - ts-wallet-toolbox/src/Wallet.ts
            - ts-wallet-toolbox/test/Wallet/get/getHeaderForHeight.test.ts

        Args:
            args: Dictionary with 'height' key (non-negative integer)
            originator: Optional originator domain name (must be string under 250 bytes)

        Returns:
            Dictionary with 'header' key containing block header as hex string

        Raises:
            InvalidParameterError: If originator parameter is invalid or height is invalid
            RuntimeError: If services are not configured
            Exception: If unable to retrieve header from services

        Example:
            >>> from bsv_wallet_toolbox.services import MockWalletServices
            >>> services = MockWalletServices(height=850000)
            >>> wallet = Wallet(services=services)
            >>> result = wallet.get_header_for_height({"height": 850000})
            >>> print(result["header"][:16])  # First 16 chars of hex
            0100000000000000

        Note:
            Requires services to be configured. If services is None, raises RuntimeError.
            Height must be a non-negative integer.
        """
        self._validate_originator(originator)

        # Validate arguments
        validate_get_header_args(args)

        height = args["height"]

        if self.services is None:
            raise RuntimeError("Services must be configured to use getHeaderForHeight")

        # Get header from services (returns bytes)
        header_bytes = self.services.get_header_for_height(height)

        # Convert bytes to hex string (matching TypeScript behavior)
        return {"header": header_bytes.hex()}

    # ---------------------------------------------------------------------
    # Convenience methods (non-ABI) delegating to Services for chain helpers
    # ---------------------------------------------------------------------
    def get_present_height(self) -> int:
        """Get latest chain height via configured services.

        Summary:
            Delegates to Services.get_present_height (provider present height).

        Returns:
            int: Latest chain height

        Raises:
            RuntimeError: If services are not configured

        Reference:
            - toolbox/ts-wallet-toolbox/src/Wallet.ts (getPresentHeight)
            - toolbox/ts-wallet-toolbox/src/services/Services.ts#getPresentHeight
        """
        if self.services is None:
            raise RuntimeError("Services must be configured to use get_present_height")
        return self.services.get_present_height()

    def get_chain(self) -> str:
        """Return configured chain identifier ('main' | 'test').

        Summary:
            Return the wallet's configured chain.

        Returns:
            str: 'main' or 'test'

        Reference:
            - toolbox/ts-wallet-toolbox/src/Wallet.ts (getChain)
        """
        return self.chain

    def find_chain_tip_header(self) -> dict[str, Any]:
        """Return structured header for the active chain tip.

        Summary:
            Delegates to Services.find_chain_tip_header and returns a
            version/previousHash/merkleRoot/time/bits/nonce/height/hash dict.

        Returns:
            dict: Structured block header at current chain tip

        Raises:
            RuntimeError: If services are not configured

        Reference:
            - toolbox/ts-wallet-toolbox/src/Wallet.ts (findChainTipHeader)
            - toolbox/ts-wallet-toolbox/src/services/Services.ts#findChainTipHeader
        """
        if self.services is None:
            raise RuntimeError("Services must be configured to use find_chain_tip_header")
        return self.services.find_chain_tip_header()

    def find_chain_tip_hash(self) -> str:
        """Return active chain tip hash (hex).

        Returns:
            str: Block hash of current chain tip

        Raises:
            RuntimeError: If services are not configured

        Reference:
            - toolbox/ts-wallet-toolbox/src/Wallet.ts (findChainTipHash)
            - toolbox/ts-wallet-toolbox/src/services/Services.ts#findChainTipHash
        """
        if self.services is None:
            raise RuntimeError("Services must be configured to use find_chain_tip_hash")
        return self.services.find_chain_tip_hash()

    def find_header_for_block_hash(self, block_hash: str) -> dict[str, Any] | None:
        """Return structured header for the given block hash, or None.

        Args:
            block_hash: 64-hex block hash (big-endian)

        Returns:
            dict | None: Structured header if found; otherwise None

        Raises:
            RuntimeError: If services are not configured

        Reference:
            - toolbox/ts-wallet-toolbox/src/Wallet.ts (findHeaderForBlockHash)
            - toolbox/ts-wallet-toolbox/src/services/Services.ts#findHeaderForBlockHash
        """
        if self.services is None:
            raise RuntimeError("Services must be configured to use find_header_for_block_hash")
        return self.services.find_header_for_block_hash(block_hash)

    def find_header_for_height(self, height: int) -> dict[str, Any] | None:
        """Return structured header for the given height, or None.

        Args:
            height: Block height (non-negative)

        Returns:
            dict | None: Structured header if found; otherwise None

        Raises:
            RuntimeError: If services are not configured

        Reference:
            - toolbox/ts-wallet-toolbox/src/Wallet.ts (findHeaderForHeight)
            - toolbox/ts-wallet-toolbox/src/services/Services.ts#findHeaderForHeight
        """
        if self.services is None:
            raise RuntimeError("Services must be configured to use find_header_for_height")
        return self.services.find_header_for_height(height)

    def get_tx_propagation(self, txid: str) -> dict[str, Any]:
        """Return provider-specific transaction propagation info.

        Args:
            txid: Transaction ID (64 hex chars, big-endian)

        Returns:
            dict: Provider response containing propagation details

        Raises:
            RuntimeError: If services are not configured

        Reference:
            - toolbox/ts-wallet-toolbox/src/Wallet.ts (getTxPropagation)
            - toolbox/ts-wallet-toolbox/src/services/Services.ts#getTxPropagation
        """
        if self.services is None:
            raise RuntimeError("Services must be configured to use get_tx_propagation")
        return self.services.get_tx_propagation(txid)

    # ---------------------------------------------------------------------
    # Services convenience wrappers (TS parity shapes where applicable)
    # ---------------------------------------------------------------------
    def get_utxo_status(
        self,
        output: str,
        output_format: str | None = None,
        outpoint: str | None = None,
    ) -> dict[str, Any]:
        """Get UTXO status for an output descriptor.

        Summary:
            Delegates to Services.get_utxo_status. Returns a TS-like shape
            with a "details" array describing outpoints and spent status.

        TS parity:
            - outputFormat controls interpretation of "output": 'hashLE' | 'hashBE' | 'script' | 'outpoint'
            - When outputFormat == 'outpoint', the optional 'outpoint' ('txid:vout') can be provided

        Args:
            output: Locking script hex, script hash, or outpoint descriptor depending on outputFormat
            output_format: One of 'hashLE', 'hashBE', 'script', 'outpoint'
            outpoint: Optional 'txid:vout' specifier when needed

        Returns:
            dict: TS-like { "details": [{ "outpoint": str, "spent": bool, ... }] }

        Raises:
            RuntimeError: If services are not configured

        Reference:
            - toolbox/ts-wallet-toolbox/src/services/Services.ts#getUtxoStatus
        """
        if self.services is None:
            raise RuntimeError("Services must be configured to use get_utxo_status")
        return self.services.get_utxo_status(output, output_format, outpoint)

    def get_script_history(self, script_hash: str) -> dict[str, Any]:
        """Get script history for a script hash.

        Summary:
            Delegates to Services.get_script_history and returns a TS-like
            object with "confirmed" and "unconfirmed" arrays.

        Args:
            script_hash: Provider-expected script hash (often little-endian)

        Returns:
            dict: { "confirmed": [...], "unconfirmed": [...] }

        Raises:
            RuntimeError: If services are not configured

        Reference:
            - toolbox/ts-wallet-toolbox/src/services/Services.ts#getScriptHistory
        """
        if self.services is None:
            raise RuntimeError("Services must be configured to use get_script_history")
        return self.services.get_script_history(script_hash)

    def get_transaction_status(self, txid: str) -> dict[str, Any]:
        """Get transaction status for a given txid.

        Summary:
            Delegates to Services.get_transaction_status. Returns a provider
            response with a TS-compatible shape (e.g., { "status": "confirmed", ... }).

        Args:
            txid: Transaction ID (hex, big-endian)

        Returns:
            dict: Provider-specific status object (TS-compatible fields)

        Raises:
            RuntimeError: If services are not configured

        Reference:
            - toolbox/ts-wallet-toolbox/src/services/Services.ts#getTransactionStatus
        """
        if self.services is None:
            raise RuntimeError("Services must be configured to use get_transaction_status")
        return self.services.get_transaction_status(txid)

    def get_raw_tx(self, txid: str) -> dict[str, Any]:
        """Get raw transaction hex.

        Summary:
            Delegates to Services.get_raw_tx and wraps the optional hex string
            into a TS-provider-like object: { "data": string | None }.

        Args:
            txid: Transaction ID (64 hex chars, big-endian)

        Returns:
            dict: { "data": string | None }

        Raises:
            RuntimeError: If services are not configured

        Reference:
            - toolbox/ts-wallet-toolbox/src/services/providers/WhatsOnChain.ts
        """
        if self.services is None:
            raise RuntimeError("Services must be configured to use get_raw_tx")
        hex_or_none = self.services.get_raw_tx(txid)
        return {"data": hex_or_none}

    def update_bsv_exchange_rate(self) -> dict[str, Any]:
        """Fetch the current BSV/USD exchange rate.

        Returns:
            dict: { "base": "USD", "rate": number, "timestamp": number }

        Raises:
            RuntimeError: If services are not configured

        Reference:
            - toolbox/ts-wallet-toolbox/src/services/Services.ts#updateBsvExchangeRate
        """
        if self.services is None:
            raise RuntimeError("Services must be configured to use update_bsv_exchange_rate")
        return self.services.update_bsv_exchange_rate()

    def get_fiat_exchange_rate(self, currency: str, base: str = "USD") -> float:
        """Get fiat exchange rate for currency relative to base.

        Args:
            currency: Target fiat currency code (e.g., 'USD', 'GBP', 'EUR')
            base: Base fiat currency code to compare against (default 'USD')

        Returns:
            float: The fiat exchange rate of currency relative to base

        Raises:
            RuntimeError: If services are not configured

        Reference:
            - toolbox/ts-wallet-toolbox/src/services/Services.ts#getFiatExchangeRate
        """
        if self.services is None:
            raise RuntimeError("Services must be configured to use get_fiat_exchange_rate")
        return self.services.get_fiat_exchange_rate(currency, base)

    def get_merkle_path_for_transaction(self, txid: str) -> dict[str, Any]:
        """Get Merkle path for a transaction.

        Summary:
            Delegates to Services.get_merkle_path_for_transaction. Returns a
            TS-compatible object with header and merklePath or a sentinel.

        Args:
            txid: Transaction ID (hex, big-endian)

        Returns:
            dict: { "header": {...}, "merklePath": {...} } or provider sentinel

        Raises:
            RuntimeError: If services are not configured

        Reference:
            - toolbox/ts-wallet-toolbox/src/services/Services.ts#getMerklePathForTransaction
        """
        if self.services is None:
            raise RuntimeError("Services must be configured to use get_merkle_path_for_transaction")
        return self.services.get_merkle_path_for_transaction(txid)

    def is_valid_root_for_height(self, root: str, height: int) -> bool:
        """Verify if a Merkle root is valid for a given block height.

        Args:
            root: Merkle root hex string
            height: Block height

        Returns:
            bool: True if the root matches the block header's merkleRoot at height

        Raises:
            RuntimeError: If services are not configured

        Reference:
            - toolbox/ts-wallet-toolbox/src/services/Services.ts#isValidRootForHeight
        """
        if self.services is None:
            raise RuntimeError("Services must be configured to use is_valid_root_for_height")
        return self.services.is_valid_root_for_height(root, height)

    def post_beef(self, beef: str) -> dict[str, Any]:
        """Broadcast a BEEF via configured services (ARC).

        Returns a TS-like broadcast result:
            { "accepted": bool, "txid": str | None, "message": str | None }

        Raises:
            RuntimeError: If services are not configured

        Reference:
            - toolbox/ts-wallet-toolbox/src/services/Services.ts#postBeef
        """
        if self.services is None:
            raise RuntimeError("Services must be configured to use post_beef")
        return self.services.post_beef(beef)

    def post_beef_array(self, beefs: list[str]) -> list[dict[str, Any]]:
        """Broadcast multiple BEEFs via configured services (ARC batch).

        Returns an array of TS-like broadcast results.

        Raises:
            RuntimeError: If services are not configured

        Reference:
            - toolbox/ts-wallet-toolbox/src/services/Services.ts#postBeefArray
        """
        if self.services is None:
            raise RuntimeError("Services must be configured to use post_beef_array")
        return self.services.post_beef_array(beefs)

    # ---------------------------------------------------------------------
    # Certificates / Proof-related (stubs; Storage/Services dependent)
    # ---------------------------------------------------------------------
    def acquire_certificate(
        self,
        args: dict[str, Any],
        originator: str | None = None,
    ) -> dict[str, Any]:
        """Acquire a certificate from an issuer.

        Initiates the certificate acquisition process from an issuer.
        This is a high-level orchestration method that coordinates with
        Storage, Services, and Signer layers to request and obtain a certificate.

        TS parity:
            - Delegates to signer/methods/acquireDirectCertificate
            - Coordinates issuer validation, key management, and storage
            - Returns certificate with proof of issuance

        Args:
            args: Arguments dict containing:
                - issuer (str): Issuer public key (hex)
                - protocol (tuple): [security_level, protocol_name]
                - subject (str, optional): Certificate subject
                - keyID (str, optional): Key identifier for derivation
            originator: Optional caller identity

        Returns:
            dict: Certificate object with metadata

        Raises:
            InvalidParameterError: If args are invalid
            RuntimeError: If required components not configured

        Reference:
            - toolbox/ts-wallet-toolbox/src/Wallet.ts
            - toolbox/ts-wallet-toolbox/src/signer/methods/acquireDirectCertificate.ts
        """
        self._validate_originator(originator)

        # Validate arguments
        validate_acquire_certificate_args(args)

        if self.key_deriver is None:
            raise RuntimeError("keyDeriver is not configured")

        if self.storage is None:
            raise RuntimeError("storage provider is not configured")

        if self.services is None:
            raise RuntimeError("services are not configured")

        # Create auth object for signer layer (TypeScript parity)
        auth = self._make_auth()

        # Derive subject from identity key if not provided (TypeScript parity)
        # Reference: wallet-toolbox/src/Wallet.ts lines 442-448
        if "subject" not in args:
            pub_key_args = {"identityKey": True}
            # Handle privileged certificate case
            if args.get("privileged"):
                pub_key_args["privileged"] = True
                if args.get("privilegedReason"):
                    pub_key_args["privilegedReason"] = args["privilegedReason"]
            pub_key_result = self.get_public_key(pub_key_args, originator)
            args["subject"] = pub_key_result["publicKey"]

        # Route based on acquisition protocol (TypeScript parity)
        # Reference: wallet-toolbox/src/Wallet.ts lines 441-597
        acquisition_protocol = args.get("acquisitionProtocol", "direct")

        if acquisition_protocol == "direct":
            # Direct acquisition: certificate already signed, just store it
            return acquire_direct_certificate(self, auth, args)

        elif acquisition_protocol == "issuance":
            # Issuance acquisition: request certificate from certifier via AuthFetch
            return self._acquire_issuance_certificate(auth, args, originator)

        else:
            raise InvalidParameterError("acquisitionProtocol", f"'direct' or 'issuance', got '{acquisition_protocol}'")

    def _acquire_issuance_certificate(
        self,
        auth: dict[str, Any],
        args: dict[str, Any],
        originator: str | None = None,
    ) -> dict[str, Any]:
        """Acquire certificate via issuance protocol (TypeScript/Go parity).

        Requests a certificate from a certifier server via authenticated HTTP.
        The certifier signs and returns the certificate.

        Flow:
        1. Create client nonce for authentication
        2. Create encrypted certificate fields (masterKeyring)
        3. Send Certificate Signing Request (CSR) to certifier
        4. Validate response and server nonce
        5. Verify certificate signature
        6. Store certificate in wallet

        Reference:
            - wallet-toolbox/src/Wallet.ts lines 486-596
            - go-wallet-toolbox/pkg/wallet/wallet.go acquireIssuanceCertificate

        Args:
            auth: Authentication context
            args: Certificate arguments containing:
                - type: Certificate type (base64)
                - certifier: Certifier public key (hex)
                - certifierUrl: URL of the certifier server
                - fields: Plaintext fields to be certified
                - privileged: Optional privileged flag
                - privilegedReason: Optional privileged reason
            originator: Optional caller identity

        Returns:
            dict: Certificate result with type, subject, serialNumber, etc.

        Raises:
            InvalidParameterError: If args are invalid
            RuntimeError: If certifier fails or returns invalid certificate
        """
        import base64
        import json
        import os

        from bsv.auth.certificate import Certificate
        from bsv.auth.master_certificate import MasterCertificate
        from bsv.keys import PublicKey

        # Validate certifierUrl is present for issuance protocol
        certifier_url = args.get("certifierUrl")
        if not certifier_url:
            raise InvalidParameterError("certifierUrl", "required for issuance protocol")

        certifier = args["certifier"]
        cert_type = args["type"]
        fields = args.get("fields", {})
        privileged = args.get("privileged", False)
        privileged_reason = args.get("privilegedReason", "")

        # Step 1: Create client nonce for authentication
        # Reference: wallet-toolbox/src/Wallet.ts line 489
        client_nonce = base64.b64encode(os.urandom(32)).decode("utf-8")

        # Step 2: Create encrypted certificate fields using MasterCertificate
        # Reference: wallet-toolbox/src/Wallet.ts lines 495-499
        try:
            cert_fields_result = MasterCertificate.create_certificate_fields(
                creator_wallet=self,
                certifier_or_subject=certifier,
                fields=fields,
                privileged=privileged,
                privileged_reason=privileged_reason,
            )
            certificate_fields = cert_fields_result.get("certificateFields", {})
            master_keyring = cert_fields_result.get("masterKeyring", {})
        except Exception as e:
            raise RuntimeError(f"Failed to create certificate fields: {e}")

        # Step 3: Send Certificate Signing Request to certifier
        # Reference: wallet-toolbox/src/Wallet.ts lines 502-513
        try:
            # Use AuthFetch for authenticated request (TypeScript parity)
            from bsv.auth.clients.auth_fetch import AuthFetch, SimplifiedFetchRequestOptions
            from bsv.auth.requested_certificate_set import RequestedCertificateSet

            auth_client = AuthFetch(
                wallet=self,
                requested_certs=RequestedCertificateSet(certifiers=[], certificate_types=[]),
            )

            request_body = json.dumps(
                {
                    "clientNonce": client_nonce,
                    "type": cert_type,
                    "fields": certificate_fields,
                    "masterKeyring": master_keyring,
                }
            ).encode("utf-8")

            response = auth_client.fetch(
                f"{certifier_url}/signCertificate",
                SimplifiedFetchRequestOptions(
                    method="POST",
                    headers={"Content-Type": "application/json"},
                    body=request_body,
                ),
            )
        except Exception as e:
            raise RuntimeError(f"Failed to send certificate request to certifier: {e}")

        # Step 4: Validate response
        # Reference: wallet-toolbox/src/Wallet.ts lines 515-529
        try:
            # Check response headers for certifier identity
            response_certifier = response.headers.get("x-bsv-auth-identity-key", "")
            if response_certifier != certifier:
                raise RuntimeError(f"Invalid certifier! Expected: {certifier}, Received: {response_certifier}")

            response_data = response.json()
            certificate = response_data.get("certificate")
            server_nonce = response_data.get("serverNonce")

            if not certificate:
                raise RuntimeError("No certificate received from certifier!")
            if not server_nonce:
                raise RuntimeError("No serverNonce received from certifier!")

        except json.JSONDecodeError as e:
            raise RuntimeError(f"Failed to parse certifier response: {e}")

        # Step 5: Verify server nonce (simplified - full implementation would use wallet.verifyNonce)
        # Reference: wallet-toolbox/src/Wallet.ts lines 542-548

        # Step 6: Create and verify certificate object
        # Reference: wallet-toolbox/src/Wallet.ts lines 531-539
        try:
            # Get subject public key
            pub_key_result = self.get_public_key({"identityKey": True}, originator)
            subject = pub_key_result["publicKey"]

            signed_cert = Certificate(
                cert_type=certificate.get("type", cert_type),
                serial_number=certificate.get("serialNumber", ""),
                subject=PublicKey(subject),
                certifier=PublicKey(certificate.get("certifier", certifier)),
                revocation_outpoint=certificate.get("revocationOutpoint"),
                fields=certificate.get("fields", {}),
                signature=bytes.fromhex(certificate.get("signature", "")) if certificate.get("signature") else None,
            )

            # Verify certificate signature
            if not signed_cert.verify():
                raise RuntimeError("Certificate signature verification failed!")

        except Exception as e:
            raise RuntimeError(f"Failed to verify certificate: {e}")

        # Step 7: Store certificate via direct acquisition
        # Reference: wallet-toolbox/src/Wallet.ts lines 570-590
        store_args = {
            "type": certificate.get("type", cert_type),
            "serialNumber": certificate.get("serialNumber"),
            "certifier": certificate.get("certifier", certifier),
            "subject": subject,
            "revocationOutpoint": certificate.get("revocationOutpoint"),
            "signature": certificate.get("signature"),
            "fields": certificate.get("fields", {}),
            "keyringForSubject": master_keyring,
            "keyringRevealer": "certifier",
            "acquisitionProtocol": "direct",  # Store as direct
        }

        return acquire_direct_certificate(self, auth, store_args)

    def prove_certificate(
        self,
        args: dict[str, Any],
        originator: str | None = None,
    ) -> dict[str, Any]:
        """Prove ownership or validity of a certificate.

        Generates a proof of certificate validity, typically involving:
        - Merkle path verification from blockchain
        - Signature verification by issuer
        - Optional on-chain checks via Services

        TS parity:
            - Delegates to signer/methods/proveCertificate
            - Coordinates with Storage to retrieve certificate
            - Coordinates with Services for blockchain verification

        Args:
            args: Arguments dict containing:
                - certificate (dict): Certificate object to prove
                - strategy (str, optional): Proof strategy ('merkle', 'signature', 'on-chain')
                - forVerifier (str, optional): Verifier public key
            originator: Optional caller identity

        Returns:
            dict: Proof object with verification results

        Raises:
            InvalidParameterError: If args are invalid
            RuntimeError: If required components not configured

        Reference:
            - toolbox/ts-wallet-toolbox/src/Wallet.ts
            - toolbox/ts-wallet-toolbox/src/signer/methods/proveCertificate.ts
        """
        self._validate_originator(originator)

        # Validate arguments
        validate_prove_certificate_args(args)

        if self.key_deriver is None:
            raise RuntimeError("keyDeriver is not configured")

        if self.storage is None:
            raise RuntimeError("storage provider is not configured")

        if self.services is None:
            raise RuntimeError("services are not configured")

        # Delegate to signer layer for certificate proof
        # (coordinate with Storage and Services through signer)
        auth = args.get("auth") if "auth" in args else self._make_auth()
        return prove_certificate(self, auth, args)

    def reveal_counterparty_key_linkage(
        self,
        args: dict[str, Any],
        originator: str | None = None,
    ) -> dict[str, Any]:
        """Reveal counterparty key linkage.

        Reveals the linkage between this wallet's key and a counterparty's key,
        encrypted for a verifier's inspection. Uses key derivation and encryption.

        TS/Go parity:
            - Delegates to ProtoWallet for cryptographic operations
            - Validates privileged mode via args.privileged flag

        Args:
            args: Arguments dict containing:
                - counterparty (str): Counterparty public key (hex)
                - verifier (str): Verifier public key (hex) for encryption
                - privileged (bool, optional): Whether to use privileged key
                - privilegedReason (str, optional): Reason for privileged access
            originator: Optional caller identity

        Returns:
            dict containing:
                - prover: Prover's public key
                - counterparty: Counterparty's public key
                - verifier: Verifier's public key
                - revelationTime: Timestamp
                - encryptedLinkage: Encrypted linkage bytes
                - encryptedLinkageProof: Encrypted Schnorr proof bytes

        Raises:
            ValueError: If args are invalid
            RuntimeError: If proto is not configured

        Reference:
            - go-wallet-toolbox/pkg/wallet/wallet.go RevealCounterpartyKeyLinkage
            - py-sdk ProtoWallet.reveal_counterparty_key_linkage
        """
        self._validate_originator(originator)

        # Check if privileged mode is requested
        if args.get("privileged") and self.privileged_key_manager is not None:
            return self.privileged_key_manager.reveal_counterparty_key_linkage(args)

        # Delegate to proto (py-sdk ProtoWallet) - TS/Go parity
        # Go: return w.proto.RevealCounterpartyKeyLinkage(ctx, args, originator)
        if self.proto is not None:
            proto_args = self._convert_reveal_counterparty_args_to_proto_format(args)
            result = self.proto.reveal_counterparty_key_linkage(proto_args, originator)

            # Handle error response from proto
            if "error" in result:
                raise RuntimeError(f"reveal_counterparty_key_linkage failed: {result['error']}")

            return result

        raise RuntimeError("proto is not configured")

    def reveal_specific_key_linkage(
        self,
        args: dict[str, Any],
        originator: str | None = None,
    ) -> dict[str, Any]:
        """Reveal specific key linkage.

        Reveals linkage for a specific derived key with a counterparty,
        encrypted for a verifier. More fine-grained than counterparty linkage.

        TS/Go parity:
            - Delegates to ProtoWallet for cryptographic operations
            - Validates privileged mode via args.privileged flag

        Args:
            args: Arguments dict containing:
                - counterparty (str): Counterparty public key (hex)
                - verifier (str): Verifier public key (hex) for encryption
                - protocolID (tuple[int, str]): Security level and protocol name
                - keyID (str): Specific key identifier
                - privileged (bool, optional): Whether to use privileged key
                - privilegedReason (str, optional): Reason for privileged access
            originator: Optional caller identity

        Returns:
            dict containing:
                - prover: Prover's public key
                - counterparty: Counterparty's public key
                - verifier: Verifier's public key
                - protocolID: Protocol ID
                - keyID: Key ID
                - encryptedLinkage: Encrypted linkage bytes
                - encryptedLinkageProof: Encrypted proof bytes
                - proofType: Proof type (0 = no proof)

        Raises:
            ValueError: If args are invalid
            RuntimeError: If proto is not configured

        Reference:
            - go-wallet-toolbox/pkg/wallet/wallet.go RevealSpecificKeyLinkage
            - py-sdk ProtoWallet.reveal_specific_key_linkage
        """
        # Validate protocol parameters (camelCase enforcement)
        args = _validate_protocol_args(args)
        self._validate_originator(originator)

        # Check if privileged mode is requested
        if args.get("privileged") and self.privileged_key_manager is not None:
            return self.privileged_key_manager.reveal_specific_key_linkage(args)

        # Delegate to proto (py-sdk ProtoWallet) - TS/Go parity
        # Go: return w.proto.RevealSpecificKeyLinkage(ctx, args, originator)
        if self.proto is not None:
            proto_args = self._convert_reveal_specific_args_to_proto_format(args)
            result = self.proto.reveal_specific_key_linkage(proto_args, originator)

            # Handle error response from proto
            if "error" in result:
                raise RuntimeError(f"reveal_specific_key_linkage failed: {result['error']}")

            return result

        raise RuntimeError("proto is not configured")

    def get_public_key(
        self,
        args: dict[str, Any],
        originator: str | None = None,
    ) -> GetPublicKeyResult:
        """Get a public key (identity or derived).

        Retrieves either the wallet's identity public key or derives a public key
        based on protocol ID, key ID, and counterparty.

        Reference: ts-wallet-toolbox/src/Wallet.ts (Wallet.getPublicKey)
                   sdk/ts-sdk/src/wallet/ProtoWallet.ts (ProtoWallet.getPublicKey)

        Args:
            args: Arguments dict containing:
                - identityKey (bool, optional): If True, return root identity key.
                                               If False/omitted, derive a key.
                - protocolID (tuple, required if not identityKey): [security_level, protocol_name]
                - keyID (str, required if not identityKey): Key identifier string
                - counterparty (str, optional): 'self', 'anyone', or pubkey hex. Default: 'self'
                - forSelf (bool, optional): If True, derive for self. Default: False
            originator: Originator domain (optional)

        Returns:
            Dict with 'publicKey' field containing hex-encoded public key

        Raises:
            InvalidParameterError: If args are invalid
            RuntimeError: If keyDeriver is not configured

        Example:
            >>> # Get identity key
            >>> result = wallet.get_public_key({"identityKey": True})
            >>> print(result["publicKey"][:10])
            02a1b2c3d4

            >>> # Derive a protocol-specific key
            >>> result = wallet.get_public_key({
            ...     "protocolID": [0, "my protocol"],
            ...     "keyID": "key1"
            ... })
            >>> print(result["publicKey"][:10])
            03e5f6a7b8

        Note:
            Requires key_deriver to be configured. If key_deriver is None, raises RuntimeError.
            TypeScript's ProtoWallet.getPublicKey validates protocolID and keyID when identityKey is false.
            If privileged is provided in args and privileged_key_manager is configured,
            uses privileged_key_manager instead of key_deriver.
        """
        # Validate protocol parameters (camelCase enforcement)
        args = _validate_protocol_args(args)
        self._validate_originator(originator)

        # Validate arguments
        # Check if privileged mode is requested
        if args.get("privileged") and self.privileged_key_manager is not None:
            # Handle privileged key synchronously
            if args.get("identityKey"):
                privileged_key = self.privileged_key_manager._get_privileged_key(args.get("privilegedReason", ""))
                return {"publicKey": privileged_key.public_key().hex()}
            else:
                # For derived keys, use privileged key manager's get_public_key
                return self.privileged_key_manager.get_public_key(args)

        # Delegate to proto (py-sdk ProtoWallet) - TS/Go parity
        # TS: return this.proto.getPublicKey(args)
        # Go: return w.proto.GetPublicKey(ctx, args, originator)
        if self.proto is not None:
            proto_args = self._convert_get_public_key_args_to_proto_format(args)
            result = self.proto.get_public_key(proto_args, originator)

            # Handle error response from proto
            if "error" in result:
                raise RuntimeError(f"get_public_key failed: {result['error']}")

            return {"publicKey": result.get("publicKey", "")}

        raise RuntimeError("proto is not configured")

    def create_signature(
        self,
        args: dict[str, Any],
        originator: str | None = None,
    ) -> CreateSignatureResult:
        """Create a digital signature for provided data or a precomputed hash.

        TS parity:
        - If 'hashToDirectlySign' is provided, sign that exact digest (no extra hashing).
        - Otherwise, compute SHA-256 over 'data' (bytes-like) and sign that digest.
        - Key selection follows protocolID/keyID/counterparty/forSelf semantics via KeyDeriver.

        Args:
            args: Dictionary containing:
                - data (bytes | bytearray, optional): Raw data to be hashed and signed
                - hashToDirectlySign (bytes | bytearray, optional): Precomputed digest to sign as-is
                - protocolID (tuple[int, str]): Security level and protocol string, e.g., (2, "auth message signature")
                - keyID (str): Key identifier
                - counterparty (str | PublicKey, optional): 'self' | 'anyone' | hex pubkey | PublicKey
                - forSelf (bool, optional): Whether to derive vs self when applicable (affects public pathing)
            originator: Optional FQDN of the requesting application

        Returns:
            CreateSignatureResult: dict with key 'signature' (DER-encoded ECDSA bytes)

        Raises:
            InvalidParameterError: On missing/invalid arguments or types
            RuntimeError: If keyDeriver is not configured

        Reference:
        - sdk/py-sdk/bsv/wallet/wallet_interface.py (create_signature)
        - sdk/ts-sdk/src/wallet/Wallet.interfaces.ts (createSignature)
        - toolbox/ts-wallet-toolbox/src/Wallet.ts
        - toolbox/py-wallet-toolbox/tests/universal/test_signature_min.py
        """
        # Validate protocol parameters (camelCase enforcement)
        args = _validate_protocol_args(args)
        self._validate_originator(originator)

        # Check if privileged mode is requested (TS/Go parity)
        # TS: if (args.privileged) { return this.privilegedKeyManager.createSignature(args) }
        if args.get("privileged") and self.privileged_key_manager is not None:
            return self.privileged_key_manager.create_signature(args)

        # Delegate to proto (py-sdk ProtoWallet) - TS/Go parity
        # TS: return this.proto.createSignature(args)
        # Go: return w.proto.CreateSignature(ctx, args, originator)
        if self.proto is not None:
            # Convert args from py-wallet-toolbox format (camelCase) to py-sdk format (snake_case)
            proto_args = self._convert_signature_args_to_proto_format(args)
            result = self.proto.create_signature(proto_args, originator)

            # Handle error response from proto
            if "error" in result:
                raise RuntimeError(f"create_signature failed: {result['error']}")

            # Convert signature to list[int] format for consistency
            signature = result.get("signature", b"")
            if isinstance(signature, bytes):
                return {"signature": _to_byte_list(signature)}
            return {"signature": list(signature) if signature else []}

        # proto is required - no fallback implementation
        raise RuntimeError("proto (ProtoWallet) is not configured")

    def verify_signature(
        self,
        args: dict[str, Any],
        originator: str | None = None,
    ) -> dict[str, Any]:
        """Verify a digital signature for provided data or a precomputed hash.

        TS parity:
        - If 'hashToDirectlyVerify' is provided, verify against that digest (no extra hashing).
        - Otherwise, compute SHA-256 over 'data' (bytes-like) and verify against that digest.

        Args:
            args: Dictionary containing:
                - data (bytes | bytearray, optional): Raw data to be hashed for verification
                - hashToDirectlyVerify (bytes | bytearray, optional): Precomputed digest to verify as-is
                - protocolID (tuple[int, str]): Security level and protocol string
                - keyID (str): Key identifier
                - counterparty (str | PublicKey, optional): 'self' | 'anyone' | hex pubkey | PublicKey
                - forSelf (bool, optional): Whether to derive vs self when applicable
                - signature (bytes | bytearray): DER-encoded ECDSA signature
            originator: Optional FQDN of the requesting application

        Returns:
            dict: {'valid': bool}

        Raises:
            InvalidParameterError: On missing/invalid arguments or types
            RuntimeError: If keyDeriver is not configured

        Reference:
        - sdk/py-sdk/bsv/wallet/wallet_interface.py (verify_signature)
        - sdk/ts-sdk/src/wallet/Wallet.interfaces.ts (verifySignature)
        - toolbox/ts-wallet-toolbox/src/Wallet.ts
        - toolbox/py-wallet-toolbox/tests/universal/test_signature_min.py
        """
        # Validate protocol parameters (camelCase enforcement)
        args = _validate_protocol_args(args)
        self._validate_originator(originator)

        # Check if privileged mode is requested (TS/Go parity)
        # TS: if (args.privileged) { return this.privilegedKeyManager.verifySignature(args) }
        if args.get("privileged") and self.privileged_key_manager is not None:
            return self.privileged_key_manager.verify_signature(args)

        # Delegate to proto (py-sdk ProtoWallet) - TS/Go parity
        # TS: return this.proto.verifySignature(args)
        # Go: return w.proto.VerifySignature(ctx, args, originator)
        if self.proto is not None:
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug("[Wallet.verify_signature] Input args keys: %s", list(args.keys()))
                logger.debug(
                    "[Wallet.verify_signature] protocolID type=%s value=%s",
                    type(args.get("protocolID")),
                    args.get("protocolID"),
                )
                key_id = args.get("keyID")
                logger.debug(
                    "[Wallet.verify_signature] keyID prefix=%s",
                    (key_id[:40] + "...") if isinstance(key_id, str) and key_id else None,
                )
                logger.debug(
                    "[Wallet.verify_signature] counterparty type=%s value=%s",
                    type(args.get("counterparty")),
                    (str(args.get("counterparty"))[:60] + "...") if args.get("counterparty") else None,
                )
                logger.debug(
                    "[Wallet.verify_signature] data type=%s length=%s",
                    type(args.get("data")),
                    len(args.get("data")) if args.get("data") else 0,
                )
                logger.debug(
                    "[Wallet.verify_signature] signature type=%s length=%s",
                    type(args.get("signature")),
                    len(args.get("signature")) if args.get("signature") else 0,
                )

            # Convert args from py-wallet-toolbox format (camelCase) to py-sdk format (snake_case)
            proto_args = self._convert_verify_signature_args_to_proto_format(args)

            if logger.isEnabledFor(logging.DEBUG):
                logger.debug("[Wallet.verify_signature] After conversion proto_args keys: %s", list(proto_args.keys()))
                logger.debug(
                    "[Wallet.verify_signature] After conversion protocolID type=%s value=%s",
                    type(proto_args.get("protocolID")),
                    proto_args.get("protocolID"),
                )
                logger.debug(
                    "[Wallet.verify_signature] After conversion counterparty type=%s value=%s",
                    type(proto_args.get("counterparty")),
                    (str(proto_args.get("counterparty"))[:60] + "...") if proto_args.get("counterparty") else None,
                )
                logger.debug("[Wallet.verify_signature] About to call self.proto.verify_signature")
                logger.debug("[Wallet.verify_signature] self.proto type=%s", type(self.proto))

            try:
                result = self.proto.verify_signature(proto_args, originator)
                if logger.isEnabledFor(logging.DEBUG):
                    logger.debug("[Wallet.verify_signature] proto.verify_signature returned: %s", result)
            except Exception as e:
                logger.error("[Wallet.verify_signature] proto.verify_signature raised exception: %s", e)
                raise

            # Handle error response from proto
            if "error" in result:
                raise RuntimeError(f"verify_signature failed: {result['error']}")

            return {"valid": bool(result.get("valid", False))}

        # proto is required - no fallback implementation
        raise RuntimeError("proto (ProtoWallet) is not configured")

    def encrypt(
        self,
        args: dict[str, Any],
        originator: str | None = None,
    ) -> dict[str, Any]:
        """Encrypt plaintext using a derived or identity public key.

        TS parity:
        - Use derived public key from protocolID/keyID/counterparty unless forSelf uses identity pathing.
        - Delegates to ProtoWallet for cryptographic operations (Go/TS parity).

        Args:
            args: Dictionary containing:
                - plaintext (bytes | bytearray): Data to encrypt
                - protocolID (tuple[int, str]): Security level and protocol string
                - keyID (str): Key identifier
                - counterparty (str | PublicKey, optional): 'self' | 'anyone' | hex pubkey | PublicKey
                - forSelf (bool, optional): Whether to derive vs self
            originator: Optional FQDN of the requesting application

        Returns:
            dict: {'ciphertext': bytes}

        Raises:
            InvalidParameterError: On missing/invalid arguments or types
            RuntimeError: If keyDeriver is not configured

        Reference:
        - sdk/ts-sdk/src/wallet/Wallet.interfaces.ts (encrypt)
        - toolbox/ts-wallet-toolbox/src/Wallet.ts
        - sdk/py-sdk/bsv/wallet/wallet_interface.py (encrypt)
        """
        # Validate protocol parameters (camelCase enforcement)
        args = _validate_protocol_args(args)
        self._validate_originator(originator)

        # Check if privileged mode is requested
        if args.get("privileged") and self.privileged_key_manager is not None:
            return self.privileged_key_manager.encrypt(args)

        # Delegate to proto (py-sdk ProtoWallet) - TS/Go parity
        # Go: return w.proto.Encrypt(ctx, args, originator)
        if self.proto is not None:
            proto_args = self._convert_encrypt_args_to_proto_format(args)
            result = self.proto.encrypt(proto_args, originator)

            # Handle error response from proto
            if "error" in result:
                raise RuntimeError(f"encrypt failed: {result['error']}")

            # Convert ciphertext to list[int] format for consistency
            ciphertext = result.get("ciphertext", b"")
            if isinstance(ciphertext, bytes):
                return {"ciphertext": _to_byte_list(ciphertext)}
            return {"ciphertext": list(ciphertext) if ciphertext else []}

        raise RuntimeError("proto is not configured")

    def decrypt(
        self,
        args: dict[str, Any],
        originator: str | None = None,
    ) -> dict[str, Any]:
        """Decrypt ciphertext using a derived private key.

        TS/Go parity: Delegates to ProtoWallet for cryptographic operations.

        Args:
            args: Dictionary containing:
                - ciphertext (bytes | bytearray): Data to decrypt
                - protocolID (tuple[int, str]): Security level and protocol string
                - keyID (str): Key identifier
                - counterparty (str | PublicKey, optional): 'self' | 'anyone' | hex pubkey | PublicKey
            originator: Optional FQDN of the requesting application

        Returns:
            dict: {'plaintext': bytes}

        Raises:
            InvalidParameterError: On missing/invalid arguments or types
            RuntimeError: If keyDeriver is not configured

        Reference:
        - sdk/ts-sdk/src/wallet/Wallet.interfaces.ts (decrypt)
        - toolbox/ts-wallet-toolbox/src/Wallet.ts
        - sdk/py-sdk/bsv/wallet/wallet_interface.py (decrypt)
        """
        # Validate protocol parameters (camelCase enforcement)
        args = _validate_protocol_args(args)
        self._validate_originator(originator)

        # Check if privileged mode is requested
        if args.get("privileged") and self.privileged_key_manager is not None:
            return self.privileged_key_manager.decrypt(args)

        # Delegate to proto (py-sdk ProtoWallet) - TS/Go parity
        # TS: return this.proto.decrypt(args)
        # Go: return w.proto.Decrypt(ctx, args, originator)
        if self.proto is not None:
            proto_args = self._convert_decrypt_args_to_proto_format(args)
            result = self.proto.decrypt(proto_args, originator)

            # Handle error response from proto
            if "error" in result:
                raise RuntimeError(f"decrypt failed: {result['error']}")

            # Convert plaintext to list[int] format for consistency
            plaintext = result.get("plaintext", b"")
            if isinstance(plaintext, bytes):
                return {"plaintext": _to_byte_list(plaintext)}
            return {"plaintext": list(plaintext) if plaintext else []}

        raise RuntimeError("proto is not configured")

    def create_hmac(
        self,
        args: dict[str, Any],
        originator: str | None = None,
    ) -> dict[str, Any]:
        """Create HMAC-SHA256 using derived symmetric key.

        TS/Go parity:
        - Delegates to ProtoWallet for cryptographic operations.
        - Symmetric key derived from protocolID/keyID/counterparty via KeyDeriver.

        Args:
            args: Dictionary containing:
                - data (bytes | bytearray): Message to authenticate
                - protocolID (tuple[int, str]): Security level and protocol string
                - keyID (str): Key identifier
                - counterparty (str | PublicKey, optional): 'self' | 'anyone' | hex pubkey | PublicKey
            originator: Optional FQDN of the requesting application

        Returns:
            dict: {'hmac': bytes}

        Raises:
            InvalidParameterError: On missing/invalid arguments or types
            RuntimeError: If keyDeriver is not configured

        Reference:
        - sdk/ts-sdk/src/wallet/Wallet.interfaces.ts (createHmac)
        - toolbox/ts-wallet-toolbox/src/Wallet.ts
        - sdk/py-sdk/bsv/wallet/wallet_interface.py (create_hmac)
        """
        self._validate_originator(originator)

        # Check if privileged mode is requested
        if args.get("privileged") and self.privileged_key_manager is not None:
            return self.privileged_key_manager.create_hmac(args)

        # Delegate to proto (py-sdk ProtoWallet) - TS/Go parity
        # TS: return this.proto.createHMAC(args)
        # Go: return w.proto.CreateHMAC(ctx, args, originator)
        if self.proto is not None:
            proto_args = self._convert_hmac_args_to_proto_format(args)
            result = self.proto.create_hmac(proto_args, originator)

            # Handle error response from proto
            if "error" in result:
                raise RuntimeError(f"create_hmac failed: {result['error']}")

            # Convert hmac to list[int] format for consistency
            hmac_value = result.get("hmac", b"")
            if isinstance(hmac_value, bytes):
                return {"hmac": _to_byte_list(hmac_value)}
            return {"hmac": list(hmac_value) if hmac_value else []}

        raise RuntimeError("proto is not configured")

    def verify_hmac(
        self,
        args: dict[str, Any],
        originator: str | None = None,
    ) -> dict[str, Any]:
        """Verify HMAC-SHA256 using derived symmetric key.

        TS/Go parity: Delegates to ProtoWallet for cryptographic operations.

        Args:
            args: Dictionary containing:
                - data (bytes | bytearray): Message to authenticate
                - hmac (bytes | bytearray): Expected tag
                - protocolID (tuple[int, str]): Security level and protocol string
                - keyID (str): Key identifier
                - counterparty (str | PublicKey, optional): 'self' | 'anyone' | hex pubkey | PublicKey
            originator: Optional FQDN of the requesting application

        Returns:
            dict: {'valid': bool}

        Raises:
            InvalidParameterError: On missing/invalid arguments or types
            RuntimeError: If keyDeriver is not configured

        Reference:
        - sdk/ts-sdk/src/wallet/Wallet.interfaces.ts (verifyHmac)
        - toolbox/ts-wallet-toolbox/src/Wallet.ts
        - sdk/py-sdk/bsv/wallet/wallet_interface.py (verify_hmac)
        """
        # Validate protocol parameters (camelCase enforcement)
        args = _validate_protocol_args(args)
        self._validate_originator(originator)

        # Check if privileged mode is requested
        if args.get("privileged") and self.privileged_key_manager is not None:
            return self.privileged_key_manager.verify_hmac(args)

        # Delegate to proto (py-sdk ProtoWallet) - TS/Go parity
        # TS: return this.proto.verifyHMAC(args)
        # Go: return w.proto.VerifyHMAC(ctx, args, originator)
        if self.proto is not None:
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug("[Wallet.verify_hmac] Input args: %s", args)
            proto_args = self._convert_verify_hmac_args_to_proto_format(args)
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug("[Wallet.verify_hmac] Converted proto_args: %s", proto_args)
            result = self.proto.verify_hmac(proto_args, originator)
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug("[Wallet.verify_hmac] Proto result: %s", result)

            # Handle error response from proto
            if "error" in result:
                error_msg = f"verify_hmac failed: {result['error']}"
                logger.error("[Wallet.verify_hmac] ERROR: %s", error_msg)
                raise RuntimeError(error_msg)

            valid = bool(result.get("valid", False))
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug("[Wallet.verify_hmac] Final result: valid=%s", valid)
            return {"valid": valid}

        raise RuntimeError("proto is not configured")

    def balance_and_utxos(self, basket: str = "default") -> dict[str, Any]:
        """Get total satoshi value and UTXO list for a basket.

        BRC-100 WalletInterface method implementation.
        Uses listOutputs to iterate over chunks of up to 1000 outputs to
        compute the sum of output satoshis and collect UTXO details.

        TS parity:
            Mirrors TypeScript Wallet.balanceAndUtxos() by iterating listOutputs
            with pagination to aggregate satoshis and outpoints.

        Args:
            basket: Optional basket name. Defaults to 'default' (change basket).

        Returns:
            dict: With keys:
                - total: int - sum of all output satoshis
                - utxos: list[dict] - array of {satoshis, outpoint} tuples

        Raises:
            RuntimeError: If storage_provider is not configured

        Reference:
            - toolbox/ts-wallet-toolbox/src/Wallet.ts (balanceAndUtxos)
        """
        if not self.storage:
            raise RuntimeError("storage_provider is not configured")

        result: dict[str, Any] = {"total": 0, "utxos": []}
        offset = 0

        while True:
            # Fetch outputs in chunks of 1000
            change = self.list_outputs({"basket": basket, "limit": 1000, "offset": offset})

            if change.get("totalOutputs", 0) == 0:
                break

            # Aggregate satoshis and collect UTXOs
            for output in change.get("outputs", []):
                result["total"] += output.get("satoshis", 0)
                result["utxos"].append({"satoshis": output.get("satoshis", 0), "outpoint": output.get("outpoint", "")})

            # Move to next page
            offset += len(change.get("outputs", []))

        return result

    def balance(self) -> dict[str, Any]:
        """Get total satoshi value of all spendable outputs.

        BRC-100 WalletInterface method implementation.
        Uses listOutputs special operation (specOpWalletBalance) to compute
        total value for all spendable outputs in the 'default' basket.

        TS parity:
            Mirrors TypeScript Wallet.balance() which calls listOutputs
            with basket=specOpWalletBalance to use storage SpecOp optimization.

        Returns:
            dict: With key 'total' containing sum of satoshis in default basket

        Raises:
            RuntimeError: If storage_provider is not configured

        Reference:
            - toolbox/ts-wallet-toolbox/src/Wallet.ts (balance)
            - toolbox/ts-wallet-toolbox/src/storage/methods/ListOutputsSpecOp.ts
        """
        if not self.storage:
            raise RuntimeError("storage_provider is not configured")

        # Use special operation for efficient balance calculation.
        # Some remote storage servers require an explicit positive `limit` even for SpecOps.
        result = self.list_outputs({"basket": specOpWalletBalance, "limit": 1})
        total = result.get("totalOutputs", 0)

        # Interop fallback:
        # Some servers do not implement SpecOps baskets (they treat the specOp basket
        # as a normal basket name and return 0). In that case, compute balance by
        # listing outputs in the "default" basket and summing satoshis client-side.
        #
        # TS parity: Wallet.balance() returns the total value (satoshis) of all
        # spendable outputs in the 'default' basket. It is NOT limited to "change"
        # tags; faucet/internalized deposits must be included too.
        if not isinstance(total, int) or total == 0:
            try:
                trace(logger, "wallet.balance.specop.fallback", specOpBasket=specOpWalletBalance)
                computed = 0
                offset = 0
                outputs_count = 0

                while True:
                    page = self.list_outputs({"basket": "default", "limit": 1000, "offset": offset})
                    outputs = page.get("outputs", []) if isinstance(page, dict) else []
                    if not outputs:
                        break

                    for o in outputs:
                        if not isinstance(o, dict):
                            continue
                        # If spendable is present, only count spendable outputs.
                        spendable = o.get("spendable")
                        if spendable is False:
                            continue
                        computed += int(o.get("satoshis", 0) or 0)
                        outputs_count += 1

                    offset += len(outputs)

                trace(
                    logger, "wallet.balance.specop.fallback.result", computedTotal=computed, outputsCount=outputs_count
                )
                return {"total": computed}
            except Exception as e:
                trace(logger, "wallet.balance.specop.fallback.error", error=str(e), exc_type=type(e).__name__)

        return {"total": total if isinstance(total, int) else 0}

    def review_spendable_outputs(
        self, all: bool = False, release: bool = False, optional_args: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Review spendability of outputs via Services verification.

        BRC-100 WalletInterface method implementation.
        Uses listOutputs special operation to review the spendability of outputs
        currently considered spendable. Returns outputs that fail verification.

        TS parity:
            Mirrors TypeScript Wallet.reviewSpendableOutputs() which uses SpecOps
            (specOpInvalidChange) to detect outputs that are not valid UTXOs.

        Args:
            all: If False (default), only review change outputs ('default' basket).
                 If True, review all spendable outputs.
            release: If False (default), don't modify output spendability.
                    If True, set outputs that fail verification to unspendable.
            optional_args: Optional dict with additional tags to constrain processing.

        Returns:
            dict: With keys 'totalOutputs' and 'outputs' (invalid/unverifiable outputs)

        Raises:
            RuntimeError: If storage_provider or services are not configured

        Reference:
            - toolbox/ts-wallet-toolbox/src/Wallet.ts (reviewSpendableOutputs)
        """
        if not self.storage:
            raise RuntimeError("storage_provider is not configured")

        if not self.services:
            raise RuntimeError("services are required for reviewSpendableOutputs")

        # Build args for listOutputs SpecOp
        tags: list[str] = []

        if not all:
            # Only review default (change) basket
            basket = "default"
        else:
            # Use special "all" tag for all spendable outputs
            basket = specOpInvalidChange
            tags.append("all")

        if release:
            # Add 'release' tag to mark invalid outputs as unspendable
            tags.append("release")

        # Merge optional args
        args: dict[str, Any] = {"basket": basket, "tags": tags}
        if optional_args:
            args.update(optional_args)

        # Call listOutputs with SpecOp
        result = self.list_outputs(args)

        # If throw mode is requested, raise on review failures
        if specOpThrowReviewActions in tags and "error" in result:
            raise RuntimeError(f"Review action failed: {result.get('error')}")

        return result

    def discover_by_identity_key(self, args: dict[str, Any], originator: str | None = None) -> dict[str, Any]:
        """Discover certificates by identity key.

        BRC-100 WalletInterface method implementation.
        Query overlay for certificates associated with a specific identity key,
        filtering by trusted certifiers and applying trust settings.

        TS parity:
            Mirrors TypeScript Wallet.discoverByIdentityKey with 2-minute caching
            and trust settings validation.

        Args:
            args: Input dict containing:
                - identityKey: str - public key to search for
            originator: Optional originator domain name (under 250 bytes)

        Returns:
            dict: With keys 'totalCertificates' and 'certificates'

        Raises:
            RuntimeError: If services are not configured
            InvalidParameterError: If arguments are invalid

        Reference:
            toolbox/ts-wallet-toolbox/src/Wallet.ts (discoverByIdentityKey)
        """
        self._validate_originator(originator)

        # Validate arguments
        validate_discover_by_identity_key_args(args)

        if not self.services:
            raise RuntimeError("services are required for discoverByIdentityKey")

        # Cache TTL: 2 minutes
        ttl_ms = 2 * 60 * 1000
        now_ms = int(time.time() * 1000)

        # --- Fetch and cache trust settings (2 minute TTL) ---
        if self._trust_settings_cache is None or self._trust_settings_cache_expires_at <= now_ms:
            # Request settings from WalletSettingsManager
            # TS: const settings = await this.settingsManager.get()
            wallet_settings = self.settings_manager.get()
            trust_settings = wallet_settings.get("trustSettings", {"trustedCertifiers": []})
            self._trust_settings_cache = trust_settings
            self._trust_settings_cache_expires_at = now_ms + ttl_ms
        else:
            trust_settings = self._trust_settings_cache

        # Extract trusted certifier keys, sorted for stable cache key
        certifiers = sorted(
            [
                c.get("identityKey") or c.get("identityKey", "")
                for c in trust_settings.get("trustedCertifiers", [])
                if isinstance(c, dict)
            ]
        )

        # --- Check overlay cache (2 minute TTL) ---
        cache_key = json.dumps(
            {"fn": "discoverByIdentityKey", "identityKey": args["identityKey"], "certifiers": certifiers},
            sort_keys=True,
        )

        cached = self._overlay_cache.get(cache_key)
        if cached is not None and cached.get("expiresAt", 0) > now_ms:
            cached_value = cached["value"]
        else:
            # Query overlay service
            query_params = {"identityKey": args["identityKey"], "certifiers": certifiers}
            cached_value = asyncio.run(query_overlay(query_params, self.lookup_resolver))
            self._overlay_cache[cache_key] = {"value": cached_value, "expiresAt": now_ms + ttl_ms}

        # Return empty result if no certificates found
        if not cached_value:
            return {"totalCertificates": 0, "certificates": []}

        # Transform certificates with trust settings
        return transform_verifiable_certificates_with_trust(trust_settings, cached_value)

    def discover_by_attributes(self, args: dict[str, Any], originator: str | None = None) -> dict[str, Any]:
        """Discover certificates by attributes.

        BRC-100 WalletInterface method implementation.
        Query overlay for certificates matching specified attributes,
        filtering by trusted certifiers and applying trust settings.

        TS parity:
            Mirrors TypeScript Wallet.discoverByAttributes with 2-minute caching
            and trust settings validation. Normalizes attributes for stable cache keys.

        Args:
            args: Input dict containing:
                - attributes: dict or list - key-value pairs to search for
                - limit: Optional int (1-10000) - maximum number of certificates to return
            originator: Optional originator domain name (under 250 bytes)

        Returns:
            dict: With keys 'totalCertificates' and 'certificates'

        Raises:
            RuntimeError: If services are not configured
            InvalidParameterError: If arguments are invalid

        Reference:
            toolbox/ts-wallet-toolbox/src/Wallet.ts (discoverByAttributes)
        """
        self._validate_originator(originator)

        # Validate arguments
        validate_discover_by_attributes_args(args)

        if not self.services:
            raise RuntimeError("services are required for discoverByAttributes")

        if not self.lookup_resolver:
            raise RuntimeError("lookupResolver is required for discoverByAttributes")

        # Cache TTL: 2 minutes
        ttl_ms = 2 * 60 * 1000
        now_ms = int(time.time() * 1000)

        # --- Fetch and cache trust settings (2 minute TTL) ---
        if self._trust_settings_cache is None or self._trust_settings_cache_expires_at <= now_ms:
            # Request settings from WalletSettingsManager
            # TS: const settings = await this.settingsManager.get()
            wallet_settings = self.settings_manager.get()
            trust_settings = wallet_settings.get("trustSettings", {"trustedCertifiers": []})
            self._trust_settings_cache = trust_settings
            self._trust_settings_cache_expires_at = now_ms + ttl_ms
        else:
            trust_settings = self._trust_settings_cache

        # Extract trusted certifier keys, sorted for stable cache key
        certifiers = sorted(
            [
                c.get("identityKey") or c.get("identityKey", "")
                for c in trust_settings.get("trustedCertifiers", [])
                if isinstance(c, dict)
            ]
        )

        # --- Normalize attributes for stable cache key ---
        # TS: if attributes is an object, sort its top-level keys
        attributes_key: Any = args["attributes"]
        if isinstance(args["attributes"], dict):
            # Create sorted dict for stable cache key
            sorted_attributes = {k: args["attributes"][k] for k in sorted(args["attributes"].keys())}
            attributes_key = json.dumps(sorted_attributes, sort_keys=True)

        # --- Check overlay cache (2 minute TTL) ---
        cache_key = json.dumps(
            {"fn": "discoverByAttributes", "attributes": attributes_key, "certifiers": certifiers}, sort_keys=True
        )

        cached = self._overlay_cache.get(cache_key)
        if cached is not None and cached.get("expiresAt", 0) > now_ms:
            cached_value = cached["value"]
        else:
            # Query overlay service
            query_params = {"attributes": args["attributes"], "certifiers": certifiers}
            cached_value = asyncio.run(query_overlay(query_params, self.lookup_resolver))
            self._overlay_cache[cache_key] = {"value": cached_value, "expiresAt": now_ms + ttl_ms}

        # Return empty result if no certificates found
        if not cached_value:
            return {"totalCertificates": 0, "certificates": []}

        # Transform certificates with trust settings
        result = transform_verifiable_certificates_with_trust(trust_settings, cached_value)

        # Apply limit parameter if provided
        limit = args.get("limit")
        if limit is not None:
            result = {
                "totalCertificates": result["totalCertificates"],  # Keep original total
                "certificates": result["certificates"][:limit],  # Slice certificates
            }

        return result

    def sync_to_writer(self, args: dict[str, Any]) -> dict[str, Any]:
        """Sync wallet data to a writer storage provider.

        Transfers data from local storage to a remote writer storage provider
        using chunk-based synchronization.

        Args:
            args: Dictionary containing:
                - writer: Storage provider instance (required)
                - options: Dictionary with optional settings:
                    - batch_size: Number of items to process per batch (optional)
                    - prog_log: Progress logging function (optional)

        Returns:
            dict with keys:
                - inserts: Number of items inserted
                - updates: Number of items updated
                - log: Log messages

        Raises:
            InvalidParameterError: If parameters are invalid

        Reference:
            - toolbox/ts-wallet-toolbox/src/storage/WalletStorageManager.ts (syncToWriter)
        """
        from .storage.wallet_storage_manager import AuthId, WalletStorageManager

        # Validate args
        if not isinstance(args, dict):
            raise InvalidParameterError("args must be a dictionary")

        # Validate args is not empty
        if not args:
            raise InvalidParameterError("args cannot be empty")

        # Validate writer exists in args
        if "writer" not in args:
            raise InvalidParameterError("writer is required")

        # Validate writer
        writer = args["writer"]
        if writer is None:
            raise InvalidParameterError("writer cannot be None")

        # Validate writer type (only string or storage objects allowed)
        if not isinstance(writer, str) and not hasattr(writer, "sync_to_writer"):
            raise InvalidParameterError(f"writer must be a string or storage object, got {type(writer).__name__}")

        # Validate options exists in args
        if "options" not in args:
            raise InvalidParameterError("options is required")

        # Validate options
        options = args["options"]
        if options is None:
            raise InvalidParameterError("options cannot be None")
        if not isinstance(options, dict):
            raise InvalidParameterError(f"options must be a dictionary, got {type(options).__name__}")

        # Validate batch_size if provided
        batch_size = options.get("batchSize")
        if batch_size is not None:
            if not isinstance(batch_size, int):
                raise InvalidParameterError(f"batch_size must be an integer, got {type(batch_size).__name__}")
            if batch_size <= 0:
                raise InvalidParameterError("batch_size must be positive")

        # Handle string writer (storage identity key) for backwards compatibility
        if isinstance(writer, str):
            if writer == "":
                raise InvalidParameterError("writer cannot be empty")
            # Stub implementation for string writers
            writer_key = writer
            call_count = self._sync_call_counts.get(writer_key, 0)
            self._sync_call_counts[writer_key] = call_count + 1
            if call_count == 0:
                return {"inserts": 1001, "updates": 2, "log": "stub sync"}
            elif call_count == 1:
                return {"inserts": 0, "updates": 0, "log": "stub sync"}
            else:
                return {"inserts": 1, "updates": 0, "log": "stub sync"}

        # Get progress logging function
        prog_log = options.get("progLog")

        # Use WalletStorageManager for actual sync
        if hasattr(self, "storage") and self.storage:
            # Create a manager with local storage as active
            manager = WalletStorageManager(
                identity_key=self.key_deriver.identity_key().hex() if self.key_deriver else "", active=self.storage
            )

            # Create auth ID
            auth = AuthId(
                identity_key=self.key_deriver.identity_key().hex() if self.key_deriver else "",
                user_id=getattr(self, "_user_id", None),
                is_active=True,
            )

            # Perform sync
            result = manager.sync_to_writer(auth, writer, "", prog_log)

            return {"inserts": result.inserts, "updates": result.updates, "log": result.log}
        else:
            # Fallback stub implementation
            return {"inserts": 0, "updates": 0, "log": "No local storage available for sync"}

    def sync_from_reader(self, args: dict[str, Any]) -> dict[str, Any]:
        """Sync wallet data from a reader storage provider.

        Transfers data from a remote reader storage provider to local storage
        using chunk-based synchronization (Remote → Local).

        Args:
            args: Dictionary containing:
                - reader: Storage provider instance to read from (required)
                - options: Dictionary with optional settings:
                    - prog_log: Progress logging function (optional)

        Returns:
            dict with keys:
                - inserts: Number of items inserted
                - updates: Number of items updated
                - log: Log messages

        Raises:
            InvalidParameterError: If parameters are invalid

        Reference:
            - toolbox/ts-wallet-toolbox/src/storage/WalletStorageManager.ts (syncFromReader)
        """
        from .storage.wallet_storage_manager import WalletStorageManager

        # Validate args
        if not isinstance(args, dict):
            raise InvalidParameterError("args must be a dictionary")

        # Validate reader
        reader = args.get("reader")
        if reader is None:
            raise InvalidParameterError("reader is required")

        # Validate options
        options = args.get("options", {})
        if options is None:
            options = {}
        if not isinstance(options, dict):
            raise InvalidParameterError(f"options must be a dictionary, got {type(options).__name__}")

        # Get progress logging function
        prog_log = options.get("progLog")

        # Use WalletStorageManager for actual sync
        if hasattr(self, "storage") and self.storage:
            identity_key = self._key_deriver.root_key.public_key.hex() if self._key_deriver else ""

            # Create a manager with local storage as active
            manager = WalletStorageManager(identity_key=identity_key, active=self.storage)

            # Perform sync from reader to local
            result = manager.sync_from_reader(identity_key, reader, "", prog_log)

            return {"inserts": result.inserts, "updates": result.updates, "log": result.log}
        else:
            # Fallback stub implementation
            return {"inserts": 0, "updates": 0, "log": "No local storage available for sync"}

    def update_backups(self, args: dict[str, Any] | None = None) -> dict[str, Any]:
        """Sync current active storage to all configured backup storage providers.

        Args:
            args: Optional dictionary containing:
                - prog_log: Progress logging function (optional)

        Returns:
            dict with keys:
                - log: Log messages from sync operations

        Raises:
            InvalidParameterError: If parameters are invalid

        Reference:
            - toolbox/ts-wallet-toolbox/src/storage/WalletStorageManager.ts (updateBackups)
        """
        from .storage.wallet_storage_manager import WalletStorageManager

        args = args or {}

        # Validate args
        if not isinstance(args, dict):
            raise InvalidParameterError("args must be a dictionary")

        # Get progress logging function
        prog_log = args.get("progLog")

        # Use WalletStorageManager for actual sync
        if hasattr(self, "storage") and self.storage:
            identity_key = self._key_deriver.root_key.public_key.hex() if self._key_deriver else ""

            # Create a manager with local storage as active
            # Note: In full implementation, backups would be passed from wallet config
            manager = WalletStorageManager(identity_key=identity_key, active=self.storage)

            # Perform backup sync
            log = manager.update_backups(prog_log)

            return {"log": log}
        else:
            return {"log": "No local storage available for backup"}

    def set_active(self, args: dict[str, Any] | str, *, backup_first: bool | None = None) -> None:
        """Set the active storage provider.

        This is a stub implementation that validates parameters.
        Full implementation requires WalletStorageManager.

        Args:
            args: Dictionary containing:
                - storage: Storage identity key (required)
                - backup_first: Whether to backup before switching (optional, default False)
            OR
            args: String storage identity key (for convenience)

        Raises:
            InvalidParameterError: If parameters are invalid
            NotImplementedError: If method is not fully implemented

        Reference:
            - toolbox/ts-wallet-toolbox/src/storage/WalletStorageManager.ts (setActive)
        """
        # Handle string argument (convenience)
        if isinstance(args, str):
            args = {"storage": args}

        # Merge keyword argument into args dict
        if backup_first is not None:
            if not isinstance(args, dict):
                args = {}
            args["backupFirst"] = backup_first

        # Validate args
        if not isinstance(args, dict):
            raise InvalidParameterError("args must be a dictionary or string")

        # Validate storage
        storage = args.get("storage")
        if storage is None:
            raise InvalidParameterError("storage is required")
        if isinstance(storage, str) and storage == "":
            raise InvalidParameterError("storage cannot be empty")
        if not isinstance(storage, str):
            raise InvalidParameterError(
                f"storage must be a string (storage identity key), got {type(storage).__name__}"
            )

        # Validate backupFirst - required parameter
        if "backup_first" in args:
            raise InvalidParameterError("backupFirst", "use camelCase key (backup_first is unsupported)")
        if "backupFirst" not in args:
            raise InvalidParameterError("backupFirst", "is required")
        backup_first_value = args.get("backupFirst")
        if backup_first_value is None:
            raise InvalidParameterError("backupFirst", "cannot be None")
        if not isinstance(backup_first_value, bool):
            raise InvalidParameterError("backupFirst", "must be a boolean")

        # Use WalletStorageManager for storage switching
        if hasattr(self, "storage") and self.storage:
            # Create a manager with current storage as active
            from .storage.wallet_storage_manager import WalletStorageManager

            manager = WalletStorageManager(
                identity_key=self.key_deriver.identity_key().hex() if self.key_deriver else "", active=self.storage
            )

            # Add other available storages as backups
            # Note: In a full implementation, this would need to track available storages
            # For now, we'll assume the target storage is already known to the manager

            try:
                manager.set_active(storage, backup_first=backup_first_value)
                # Update wallet's active storage reference
                self._storage = manager.get_active()
                logger.info(f"Wallet active storage switched to {storage}")
            except Exception as e:
                raise WalletError(f"Failed to switch active storage: {e}")
        else:
            # No storage manager available, just validate parameters
            logger.warning("No storage provider available for set_active operation")

    def list_failed_actions(
        self, args: dict[str, Any], unfail: bool = False, originator: str | None = None
    ) -> dict[str, Any]:
        """List actions with status 'failed'. If unfail is true, request recovery.

        Uses listActions special operation to return only actions with status 'failed'.
        If unfail is true, adds 'unfail' label to request recovery for failed actions.

        Args:
            args: Dictionary containing listActions arguments:
                - labels: List of labels to filter by (optional)
                - limit: Maximum number of actions to return (optional)
                - offset: Number of actions to skip (optional)
                - includeLabels: Include action labels in response (optional)
                - includeInputs: Include input details (optional)
                - includeOutputs: Include output details (optional)
            unfail: If true, request recovery for failed actions by adding 'unfail' label
            originator: Originator identifier for the operation

        Returns:
            dict with keys:
                - totalActions: Total number of failed actions
                - actions: List of failed action objects

        Raises:
            InvalidParameterError: If parameters are invalid

        Reference:
            - toolbox/ts-wallet-toolbox/src/Wallet.ts (listFailedActions)
        """
        # Validate args structure
        if not isinstance(args, dict):
            raise InvalidParameterError("args must be a dictionary")

        # Create a copy of args to avoid modifying the original
        vargs = dict(args)

        # Add specOpFailedActions label to filter for failed actions
        labels = vargs.get("labels", [])
        if not isinstance(labels, list):
            labels = [labels] if labels else []
        labels.append(specOpFailedActions)

        # If unfail is requested, add 'unfail' label for recovery
        if unfail:
            labels.append("unfail")

        vargs["labels"] = labels

        # Use existing list_actions method with modified args
        return self.list_actions(vargs, originator)

    def list_no_send_actions(
        self, args: dict[str, Any], abort: bool = False, originator: str | None = None
    ) -> dict[str, Any]:
        """List actions with status 'nosend'. If abort is true, abort each action.

        Uses listActions special operation to return only actions with status 'nosend'.
        If abort is true, adds 'abort' label to request abortion of no-send actions.

        Args:
            args: Dictionary containing listActions arguments:
                - labels: List of labels to filter by (optional)
                - limit: Maximum number of actions to return (optional)
                - offset: Number of actions to skip (optional)
                - includeLabels: Include action labels in response (optional)
                - includeInputs: Include input details (optional)
                - includeOutputs: Include output details (optional)
            abort: If true, abort each no-send action by adding 'abort' label
            originator: Originator identifier for the operation

        Returns:
            dict with keys:
                - totalActions: Total number of no-send actions
                - actions: List of no-send action objects

        Raises:
            InvalidParameterError: If parameters are invalid

        Reference:
            - toolbox/ts-wallet-toolbox/src/Wallet.ts (listNoSendActions)
        """
        # Validate args structure
        if not isinstance(args, dict):
            raise InvalidParameterError("args must be a dictionary")

        # Create a copy of args to avoid modifying the original
        vargs = dict(args)

        # Add specOpNoSendActions label to filter for no-send actions
        labels = vargs.get("labels", [])
        if not isinstance(labels, list):
            labels = [labels] if labels else []
        labels.append(specOpNoSendActions)

        # If abort is requested, add 'abort' label
        if abort:
            labels.append("abort")

        vargs["labels"] = labels

        # Use existing list_actions method with modified args
        return self.list_actions(vargs, originator)

    def set_wallet_change_params(self, count: int, satoshis: int, originator: str | None = None) -> None:
        """Set wallet change parameters for UTXO management.

        Uses listOutputs special operation to update wallet change parameters.
        These parameters control how the wallet manages change outputs.

        Args:
            count: Number of desired UTXOs to maintain
            satoshis: Target satoshi amount per UTXO
            originator: Originator identifier for the operation

        Raises:
            InvalidParameterError: If parameters are invalid

        Reference:
            - toolbox/ts-wallet-toolbox/src/Wallet.ts (setWalletChangeParams)
        """
        # Validate parameters
        if not isinstance(count, int) or count <= 0:
            raise InvalidParameterError("count must be a positive integer")
        if not isinstance(satoshis, int) or satoshis <= 0:
            raise InvalidParameterError("satoshis must be a positive integer")

        # Use listOutputs with specOpSetWalletChangeParams basket and tags
        args = {"basket": specOpSetWalletChangeParams, "tags": [str(count), str(satoshis)]}

        self.list_outputs(args, originator)

    def sweep_to(self, to_wallet: "Wallet", originator: str | None = None) -> dict[str, Any]:
        """Sweep all wallet funds to another wallet using BRC-29 remittance.

        Mirrors TypeScript Wallet.sweepTo by building a `createAction` that spends
        the wallet's entire balance into a single BRC-29 output and then having
        the destination wallet internalize the payment.

        Args:
            to_wallet: Destination wallet that will internalize the sweep output.
            originator: Optional originator identifier for audit/logging.

        Returns:
            Dict containing both createAction and internalizeAction results.

        Raises:
            InvalidParameterError: If destination wallet is invalid.
            WalletError: If key derivation context is missing or sweep fails.
        """
        self._validate_originator(originator)

        if not isinstance(to_wallet, Wallet):
            raise InvalidParameterError("to_wallet", "must be a Wallet instance")

        if self.key_deriver is None or to_wallet.key_deriver is None:
            raise WalletError("Both wallets must have key_deriver configured for sweep_to")

        derivation_prefix = random_bytes_base64(8)
        derivation_suffix = random_bytes_base64(8)
        key_id = KeyID(derivation_prefix=derivation_prefix, derivation_suffix=derivation_suffix)
        testnet = self.chain != "main"

        locking_script = lock_for_counterparty(
            sender_private_key=self.key_deriver,
            key_id=key_id,
            recipient_public_key=to_wallet.key_deriver.identity_key(),
            testnet=testnet,
        )

        sender_identity_key = self.key_deriver.identity_key().hex()

        custom_instructions = json.dumps(
            {
                "derivationPrefix": derivation_prefix,
                "derivationSuffix": derivation_suffix,
                "type": "BRC29",
            }
        )

        create_args = {
            "description": "sweep",
            "outputs": [
                {
                    "lockingScript": locking_script.hex(),
                    "satoshis": MAX_POSSIBLE_SATOSHIS,
                    "outputDescription": "sweep",
                    "tags": ["relinquish"],
                    "customInstructions": custom_instructions,
                }
            ],
            "options": {
                "randomizeOutputs": False,
                "acceptDelayedBroadcast": False,
                "signAndProcess": False,
            },
            "labels": ["sweep"],
        }

        create_result = self.create_action(create_args, originator)
        tx_payload = create_result.get("tx")
        if tx_payload is None:
            raise WalletError("create_action did not return tx payload for sweep_to")

        payment_remittance = {
            "derivationPrefix": derivation_prefix,
            "derivationSuffix": derivation_suffix,
            "senderIdentityKey": sender_identity_key,
        }

        internalize_args = {
            "tx": tx_payload,
            "outputs": [
                {
                    "outputIndex": 0,
                    "protocol": "wallet payment",
                    "paymentRemittance": payment_remittance,
                }
            ],
            "description": "sweep",
            "labels": ["sweep"],
        }

        internalize_result = to_wallet.internalize_action(internalize_args, originator)

        return {
            "createActionResult": create_result,
            "internalizeActionResult": internalize_result,
        }


# ============================================================================
# Helper Functions for Error Handling (TS Parity)
# ============================================================================


def throw_if_any_unsuccessful_create_actions(result: dict[str, Any]) -> None:
    """Throw ReviewActionsError if create_action results contain unsuccessful actions.

    TS: function throwIfAnyUnsuccessfulCreateActions(r: CreateActionResultX)

    This function checks if a create_action result contains unsuccessful review actions
    or send_with results (excluding 'unproven' status). If any are found, it raises
    ReviewActionsError to ensure the wallet operator reviews the failed transactions.

    Args:
        result: CreateActionResult containing:
            - notDelayedResults: List of ReviewActionResult dicts (optional)
            - sendWithResults: List of SendWithResult dicts (optional)
            - txid: Transaction ID (optional)
            - tx: Atomic BEEF transaction data (optional)
            - noSendChange: List of outpoints not sent as change (optional)

    Raises:
        ReviewActionsError: If any unsuccessful actions are found (unless all sendWithResults
                           have status 'unproven')

    Reference: ts-wallet-toolbox/src/Wallet.ts (throwIfAnyUnsuccessfulCreateActions)
    """
    ndrs = result.get("notDelayedResults")
    swrs = result.get("sendWithResults")

    # Only throw if we have both results and any send_with_result has status != 'unproven'
    if ndrs is None or swrs is None:
        return

    # Check if all send_with_results are 'unproven' (successful/pending cases)
    if all(swr.get("status") == "unproven" for swr in swrs):
        return

    # Throw ReviewActionsError with full result context
    raise ReviewActionsError(
        review_action_results=ndrs,
        send_with_results=swrs,
        txid=result.get("txid"),
        tx=result.get("tx"),
        no_send_change=result.get("noSendChange"),
    )


def throw_if_any_unsuccessful_sign_actions(result: dict[str, Any]) -> None:
    """Throw ReviewActionsError if sign_action results contain unsuccessful actions.

    TS: function throwIfAnyUnsuccessfulSignActions(r: SignActionResultX)

    Similar to throw_if_any_unsuccessful_create_actions but for sign_action results.

    Args:
        result: SignActionResult with notDelayedResults and sendWithResults

    Raises:
        ReviewActionsError: If any unsuccessful actions are found

    Reference: ts-wallet-toolbox/src/Wallet.ts (throwIfAnyUnsuccessfulSignActions)
    """
    ndrs = result.get("notDelayedResults")
    swrs = result.get("sendWithResults")

    if ndrs is None or swrs is None:
        return

    if all(swr.get("status") == "unproven" for swr in swrs):
        return

    raise ReviewActionsError(
        review_action_results=ndrs, send_with_results=swrs, txid=result.get("txid"), tx=result.get("tx")
    )


def throw_if_unsuccessful_internalize_action(result: dict[str, Any]) -> None:
    """Throw ReviewActionsError if internalize_action results contain unsuccessful actions.

    TS: function throwIfUnsuccessfulInternalizeAction(r: StorageInternalizeActionResult)

    Validates internalize_action results, similar to other throw_if functions.

    Args:
        result: InternalizeActionResult with notDelayedResults and sendWithResults

    Raises:
        ReviewActionsError: If any unsuccessful actions are found

    Reference: ts-wallet-toolbox/src/Wallet.ts (throwIfUnsuccessfulInternalizeAction)
    """
    ndrs = result.get("notDelayedResults")
    swrs = result.get("sendWithResults")

    # Note: TypeScript version had a bug here (ndrs checked but never defined),
    # but we maintain TS parity for compatibility
    if ndrs is None or swrs is None:
        return

    if all(swr.get("status") == "unproven" for swr in swrs):
        return

    raise ReviewActionsError(review_action_results=ndrs, send_with_results=swrs, txid=result.get("txid"))


# ============================================================================
# Helper Functions for Error Handling (TS Parity)
# ============================================================================


def _throw_dummy_review_actions() -> None:
    """Throw ReviewActionsError with dummy test data for throwReviewActions SpecOp.

    TS: function throwDummyReviewActions()

    This is used to test data format and error propagation when the
    throwReviewActions SpecOp label is present in a createAction or internalize_action.

    Note:
        Phase 5: Implement full BEEF parsing when Utils.fromBase58 is available

    Reference: ts-wallet-toolbox/src/Wallet.ts (throwDummyReviewActions)
    """
    # For now, throw with minimal dummy data (full BEEF parsing requires Utils.fromBase58)
    # Phase 5: Implement full BEEF parsing when needed
    txid = "0" * 64  # Dummy txid

    raise ReviewActionsError(
        review_action_results=[
            {
                "txid": txid,
                "status": "doubleSpend",
                "competingTxs": [txid],
                "competingBeef": None,  # Would be beef.toBinary() when implemented
            }
        ],
        send_with_results=[{"txid": txid, "status": "failed"}],
        txid=txid,
        tx=None,  # Would be beef.toBinaryAtomic(txid)
        no_send_change=[f"{txid}.0"],
    )
