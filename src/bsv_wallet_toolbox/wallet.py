"""BRC-100 compliant Bitcoin SV wallet implementation.

Reference: ts-wallet-toolbox/src/Wallet.ts
"""

from typing import Any, Literal

from bsv.keys import PublicKey
from bsv.wallet import Counterparty, CounterpartyType, KeyDeriver, Protocol
from bsv.wallet.wallet_interface import (
    AuthenticatedResult,
    CreateSignatureResult,
    GetHeaderResult,
    GetHeightResult,
    GetNetworkResult,
    GetPublicKeyResult,
    GetVersionResult,
)

from .errors import InvalidParameterError
from .services import WalletServices

# Type alias for chain (matches TypeScript: 'main' | 'test')
Chain = Literal["main", "test"]

# Type alias for wallet network (matches TypeScript: 'mainnet' | 'testnet')
WalletNetwork = Literal["mainnet", "testnet"]

# Constants
MAX_ORIGINATOR_LENGTH_BYTES = 250  # BRC-100 standard: originator must be under 250 bytes


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
            "counterparty",
            f"'self', 'anyone', or a valid hex-encoded public key (got {value!r}, error: {e})"
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


class Wallet:
    """BRC-100 compliant wallet implementation.

    Implements the WalletInterface defined in bsv-sdk.

    Reference: ts-wallet-toolbox/src/Wallet.ts

    Note:
        Version is hardcoded as a class constant, matching TypeScript implementation.
        Python implementation uses "0.6.0" during development, will become "1.0.0"
        when all 28 methods are implemented.
        Chain parameter is required (no default value), matching TypeScript implementation.

    Example:
        >>> wallet = Wallet(chain="main")
        >>> result = wallet.get_version({})
        >>> print(result["version"])
        0.6.0
    """

    # Version constant (matches TypeScript's hardcoded return value)
    VERSION = "0.6.0"  # Will become "1.0.0" when all 28 methods are complete (7/28 done)

    def __init__(
        self,
        chain: Chain,
        services: WalletServices | None = None,
        key_deriver: KeyDeriver | None = None,
        storage_provider: Any | None = None,
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

        Note:
            Version is not configurable, it's a class constant.
            Chain parameter is required (no default value), matching TypeScript implementation.
        """
        self.chain: Chain = chain
        self.services: WalletServices | None = services
        self.key_deriver: KeyDeriver | None = key_deriver
        self.storage_provider: Any | None = storage_provider
        # Wire services into storage for TS parity SpecOps (e.g., invalid change)
        try:
            if self.services is not None and self.storage_provider is not None:
                # set_services exists on our StorageProvider implementation
                getattr(self.storage_provider, "set_services")(self.services)
        except Exception:
            # Best-effort wiring; storage providers without set_services are tolerated
            pass

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

    def _to_wallet_network(self, chain: Chain) -> WalletNetwork:
        """Convert chain to wallet network name.

        Reference: ts-wallet-toolbox/src/utility/utilityHelpers.ts (toWalletNetwork)

        Args:
            chain: Chain identifier ('main' or 'test')

        Returns:
            Wallet network name ('mainnet' or 'testnet')
        """
        return "mainnet" if chain == "main" else "testnet"

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
            InvalidParameterError: If originator is invalid.
            RuntimeError: If storage provider is not configured.
        Reference:
            toolbox/ts-wallet-toolbox/src/Wallet.ts
        """
        self._validate_originator(originator)
        if not self.storage_provider:
            raise RuntimeError("storage provider is not configured")
        auth = args.get("auth") or {}
        return self.storage_provider.list_outputs(auth, args)

    def list_certificates(self, args: dict[str, Any], originator: str | None = None) -> dict[str, Any]:
        """List certificates via Storage provider (minimal TS-like shape).

        Summary:
            Wallet API delegating to Storage to enumerate certificates with minimal
            TS-like shape.
        TS parity:
            Matches TypeScript Wallet listCertificates minimal result keys.
        Args:
            args: Input dict including 'auth' (with 'userId') and optional filters.
            originator: Optional originator domain string.
        Returns:
            Dict with keys: totalCertificates, certificates.
        Raises:
            InvalidParameterError: If originator is invalid.
            RuntimeError: If storage provider is not configured.
        Reference:
            toolbox/ts-wallet-toolbox/src/Wallet.ts
        """
        self._validate_originator(originator)
        if not self.storage_provider:
            raise RuntimeError("storage provider is not configured")
        auth = args.get("auth") or {}
        return self.storage_provider.list_certificates(auth, args)

    def list_actions(self, args: dict[str, Any], originator: str | None = None) -> dict[str, Any]:
        """List actions with optional filters.

        Summary:
            Return a list of actions for the wallet.
        Args:
            args: Optional action filters.
            originator: Optional caller identity (under 250 bytes).
        Returns:
            Dict with totalActions and actions list.
        Raises:
            NotImplementedError: Placeholder until full implementation.
        Reference:
            toolbox/ts-wallet-toolbox/src/Wallet.ts
        """
        self._validate_originator(originator)
        return self.storage_provider.list_actions(self._make_auth(), args)

    def abort_action(self, args: dict[str, Any], originator: str | None = None) -> dict[str, Any]:
        """Abort an action.

        Summary:
            Cancel/abort an in-progress action by reference.
        Args:
            args: Action reference (action_reference key).
            originator: Optional caller identity (under 250 bytes).
        Returns:
            Result dict indicating abort status.
        Raises:
            N/A
        Reference:
            toolbox/ts-wallet-toolbox/src/Wallet.ts
        """
        self._validate_originator(originator)
        if not self.storage_provider:
            raise RuntimeError("storage provider is not configured")
        reference = args.get("reference", "")
        
        result = self.storage_provider.abort_action(reference)
        return {"aborted": bool(result)}

    def relinquish_certificate(self, args: dict[str, Any], originator: str | None = None) -> dict[str, Any]:
        """Mark a certificate as no longer in use.

        Summary:
            Soft-delete a certificate from active use.
        Args:
            args: Certificate ID (certificateId key).
            originator: Optional caller identity (under 250 bytes).
        Returns:
            Result dict indicating relinquish status.
        Raises:
            N/A
        Reference:
            toolbox/ts-wallet-toolbox/src/Wallet.ts
        """
        self._validate_originator(originator)
        if not self.storage_provider:
            raise RuntimeError("storage provider is not configured")
        auth = args.get("auth") or {}
        cert_id = args.get("certificateId")
        
        result = self.storage_provider.relinquish_certificate(auth, cert_id)
        return {"relinquished": bool(result)}

    def create_action(self, args: dict[str, Any], originator: str | None = None) -> dict[str, Any]:
        """Create a new transaction action.

        Summary:
            Begin construction of a new transaction with inputs and outputs.
        Args:
            args: Transaction construction args (inputs, outputs, options, etc).
            originator: Optional caller identity (under 250 bytes).
        Returns:
            Result dict with reference, version, lockTime, inputs, outputs, derivationPrefix.
        Raises:
            ValueError: If validation fails.
        Reference:
            toolbox/ts-wallet-toolbox/src/Wallet.ts
        """
        self._validate_originator(originator)
        if not self.storage_provider:
            raise RuntimeError("storage provider is not configured")
        auth = args.get("auth") or {}
        
        return self.storage_provider.create_action(auth, args)

    def process_action(self, args: dict[str, Any], originator: str | None = None) -> dict[str, Any]:
        """Process a transaction action (finalize & sign).

        Summary:
            Finalize a transaction by committing it to storage with signed rawTx.
        Args:
            args: Contains reference, txid, rawTx, isNoSend, isDelayed, isSendWith.
            originator: Optional caller identity (under 250 bytes).
        Returns:
            Result dict with status and results.
        Raises:
            ValueError: If validation fails.
        Reference:
            toolbox/ts-wallet-toolbox/src/Wallet.ts
        """
        self._validate_originator(originator)
        if not self.storage_provider:
            raise RuntimeError("storage provider is not configured")
        auth = args.get("auth") or {}
        
        return self.storage_provider.process_action(auth, args)

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
        self._validate_originator(originator)
        return {"version": self.VERSION}

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

        if self.services is None:
            raise RuntimeError("Services must be configured to use getHeaderForHeight")

        # Validate height parameter
        if "height" not in args:
            raise InvalidParameterError("height", "required")

        height = args["height"]

        if not isinstance(height, int):
            raise InvalidParameterError("height", "an integer")

        if height < 0:
            raise InvalidParameterError("height", f"a non-negative integer (got {height})")

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
            If services are configured, defer to Services.get_chain; otherwise
            return the wallet's local chain.

        Returns:
            str: 'main' or 'test'

        Reference:
            - toolbox/ts-wallet-toolbox/src/Wallet.ts (getChain)
            - toolbox/ts-wallet-toolbox/src/services/Services.ts#getChain
        """
        if self.services is None:
            # Fallback to local chain if services not set
            return self.chain
        return self.services.get_chain()

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
    def acquire_certificate(self, args: dict[str, Any], originator: str | None = None) -> dict[str, Any]:
        """Acquire a certificate (stub).

        Summary:
            Placeholder for certificate issuance/acquisition flows. In the TS
            implementation, this operation depends on Storage + Services
            (issuer validation, persistence, and proof generation). The
            dependencies are not yet available in this codebase.

        TS parity:
            - High-level API involving signing, verification, and persistence.
            - Will expose the same I/O shape as TS once dependencies are ready.

        Args:
            args: Parameters required for certificate acquisition (TBD; TS parity later)
            originator: Optional caller identity (under 250 bytes)

        Returns:
            dict: TS-compatible certificate object (not implemented)

        Raises:
            NotImplementedError: Storage/Services are not implemented yet

        Reference:
            - toolbox/ts-wallet-toolbox/src/Wallet.ts#acquireCertificate
            - toolbox/ts-wallet-toolbox/src/signer/methods/acquireDirectCertificate.ts
        """
        self._validate_originator(originator)
        raise NotImplementedError("acquire_certificate is not implemented yet (Storage/Services required)")

    def prove_certificate(self, args: dict[str, Any], originator: str | None = None) -> dict[str, Any]:
        """Prove a certificate (stub).

        Summary:
            High-level API for generating and verifying proofs
            (Merkle/signing/on-chain checks). In TS it spans Storage/Services/Signer;
            not available here yet.

        TS parity:
            - Includes subject/protocol (BRC), verification strategy, persistence.
            - Will match TS I/O once dependencies are ready.

        Args:
            args: Parameters for proof generation/verification (TBD; TS parity later)
            originator: Optional caller identity (under 250 bytes)

        Returns:
            dict: TS-compatible verification result/proof object (not implemented)

        Raises:
            NotImplementedError: Storage/Services are not implemented yet

        Reference:
            - toolbox/ts-wallet-toolbox/src/Wallet.ts#proveCertificate
            - toolbox/ts-wallet-toolbox/src/signer/methods/proveCertificate.ts
        """
        self._validate_originator(originator)
        raise NotImplementedError("prove_certificate is not implemented yet (Storage/Services required)")

    def reveal_counterparty_key_linkage(self, args: dict[str, Any], originator: str | None = None) -> dict[str, Any]:
        """Reveal counterparty key linkage (stub).

        Summary:
            API to reveal counterparty key linkage. Depends on history/persistence
            and signing; not implemented here yet.

        TS parity:
            - Arguments/return shape will follow TS later.

        Args:
            args: Parameters required to reveal linkage (TBD)
            originator: Optional caller identity

        Returns:
            dict: Linkage reveal result (not implemented)

        Raises:
            NotImplementedError: Storage/Services are not implemented yet

        Reference:
            - toolbox/ts-wallet-toolbox/src/Wallet.ts#revealCounterpartyKeyLinkage
        """
        self._validate_originator(originator)
        raise NotImplementedError("reveal_counterparty_key_linkage is not implemented yet (Storage/Services required)")

    def reveal_specific_key_linkage(self, args: dict[str, Any], originator: str | None = None) -> dict[str, Any]:
        """Reveal specific key linkage (stub).

        Summary:
            Reveal linkage for a specific key. Depends on history/persistence
            and verification; not implemented here yet.

        TS parity:
            - Arguments/return shape will follow TS later.

        Args:
            args: Parameters required to reveal linkage (TBD)
            originator: Optional caller identity

        Returns:
            dict: Linkage reveal result (not implemented)

        Raises:
            NotImplementedError: Storage/Services are not implemented yet

        Reference:
            - toolbox/ts-wallet-toolbox/src/Wallet.ts#revealSpecificKeyLinkage
        """
        self._validate_originator(originator)
        raise NotImplementedError("reveal_specific_key_linkage is not implemented yet (Storage/Services required)")

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
        """
        self._validate_originator(originator)

        if self.key_deriver is None:
            raise RuntimeError("keyDeriver is not configured")

        # Case 1: Identity key requested
        if args.get("identityKey"):
            # Return root public key (matches TS: this.keyDeriver.rootKey.toPublicKey().toString())
            root_public_key = self.key_deriver._root_public_key
            return {"publicKey": root_public_key.hex()}

        # Case 2: Derive a key
        # Validate required parameters (matching TS ProtoWallet.getPublicKey)
        if "protocolID" not in args or "keyID" not in args:
            raise InvalidParameterError(
                "protocolID and keyID",
                "required if identityKey is false or undefined"
            )

        protocol_id = args["protocolID"]
        key_id = args["keyID"]

        # Validate keyID is not empty (matching TS check)
        if not key_id or key_id == "":
            raise InvalidParameterError(
                "keyID",
                "a non-empty string"
            )

        # Convert TypeScript protocolID format [security_level, protocol_name] to Protocol
        if not isinstance(protocol_id, (list, tuple)) or len(protocol_id) != 2:
            raise InvalidParameterError(
                "protocolID",
                "a tuple/list of [security_level, protocol_name]"
            )

        security_level, protocol_name = protocol_id
        protocol = Protocol(security_level=security_level, protocol=protocol_name)

        # Get counterparty (default: 'self', matching TS)
        counterparty_arg = args.get("counterparty", "self")
        counterparty = _parse_counterparty(counterparty_arg)

        # Get forSelf flag (default: False, matching TS)
        for_self = args.get("forSelf", False)

        # Derive public key
        derived_pub = self.key_deriver.derive_public_key(
            protocol=protocol,
            key_id=key_id,
            counterparty=counterparty,
            for_self=for_self,
        )

        return {"publicKey": derived_pub.hex()}

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
        self._validate_originator(originator)

        if self.key_deriver is None:
            raise RuntimeError("keyDeriver is not configured")

        # Inputs
        protocol_id = args.get("protocolID")
        key_id = args.get("keyID")
        counterparty_arg = args.get("counterparty", "self")
        for_self = args.get("forSelf", False)

        if not protocol_id or not key_id:
            raise InvalidParameterError("protocolID/keyID", "required")

        protocol = Protocol(security_level=protocol_id[0], protocol=protocol_id[1])
        counterparty = _parse_counterparty(counterparty_arg)

        # Derive private key for signing
        priv = self.key_deriver.derive_private_key(
            protocol=protocol,
            key_id=key_id,
            counterparty=counterparty,
        )

        # Decide message to sign
        h_direct = args.get("hashToDirectlySign")
        if h_direct is not None:
            to_sign = _as_bytes(h_direct, "hashToDirectlySign")
        else:
            data = args.get("data", b"")
            buf = _as_bytes(data, "data")
            import hashlib

            to_sign = hashlib.sha256(buf).digest()

        # Sign without extra hashing (TS parity)
        signature: bytes = priv.sign(to_sign, hasher=lambda m: m)
        return {"signature": _to_byte_list(signature)}

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
        self._validate_originator(originator)

        if self.key_deriver is None:
            raise RuntimeError("keyDeriver is not configured")

        protocol_id = args.get("protocolID")
        key_id = args.get("keyID")
        signature = args.get("signature")
        counterparty_arg = args.get("counterparty", "self")
        for_self = args.get("forSelf", False)

        if not protocol_id or not key_id or signature is None:
            raise InvalidParameterError("protocolID/keyID/signature", "required")

        signature_bytes = _as_bytes(signature, "signature")

        protocol = Protocol(security_level=protocol_id[0], protocol=protocol_id[1])
        counterparty = _parse_counterparty(counterparty_arg)

        # Derive public key for verification
        pub = self.key_deriver.derive_public_key(
            protocol=protocol,
            key_id=key_id,
            counterparty=counterparty,
            for_self=for_self,
        )

        h_direct = args.get("hashToDirectlyVerify")
        if h_direct is not None:
            digest = _as_bytes(h_direct, "hashToDirectlyVerify")
        else:
            data = args.get("data", b"")
            buf = _as_bytes(data, "data")
            import hashlib

            digest = hashlib.sha256(buf).digest()

        # Verify without extra hashing (TS parity)
        valid = pub.verify(signature_bytes, digest, hasher=lambda m: m)
        return {"valid": bool(valid)}

    def encrypt(
        self,
        args: dict[str, Any],
        originator: str | None = None,
    ) -> dict[str, Any]:
        """Encrypt plaintext using a derived or identity public key.

        TS parity:
        - Use derived public key from protocolID/keyID/counterparty unless forSelf uses identity pathing.

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
        self._validate_originator(originator)
        if self.key_deriver is None:
            raise RuntimeError("keyDeriver is not configured")

        plaintext = _as_bytes(args.get("plaintext"), "plaintext")

        protocol_id = args.get("protocolID")
        key_id = args.get("keyID")
        counterparty_arg = args.get("counterparty", "self")
        for_self = args.get("forSelf", False)
        if not protocol_id or not key_id:
            raise InvalidParameterError("protocolID/keyID", "required")

        protocol = Protocol(security_level=protocol_id[0], protocol=protocol_id[1])
        counterparty = _parse_counterparty(counterparty_arg)

        pub = self.key_deriver.derive_public_key(
            protocol=protocol,
            key_id=key_id,
            counterparty=counterparty,
            for_self=for_self,
        )
        ciphertext: bytes = pub.encrypt(plaintext)
        return {"ciphertext": _to_byte_list(ciphertext)}

    def decrypt(
        self,
        args: dict[str, Any],
        originator: str | None = None,
    ) -> dict[str, Any]:
        """Decrypt ciphertext using a derived private key.

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
        self._validate_originator(originator)
        if self.key_deriver is None:
            raise RuntimeError("keyDeriver is not configured")

        ciphertext = _as_bytes(args.get("ciphertext"), "ciphertext")

        protocol_id = args.get("protocolID")
        key_id = args.get("keyID")
        counterparty_arg = args.get("counterparty", "self")
        if not protocol_id or not key_id:
            raise InvalidParameterError("protocolID/keyID", "required")

        protocol = Protocol(security_level=protocol_id[0], protocol=protocol_id[1])
        counterparty = _parse_counterparty(counterparty_arg)

        priv = self.key_deriver.derive_private_key(
            protocol=protocol,
            key_id=key_id,
            counterparty=counterparty,
        )
        plaintext: bytes = priv.decrypt(ciphertext)
        return {"plaintext": _to_byte_list(plaintext)}

    def create_hmac(
        self,
        args: dict[str, Any],
        originator: str | None = None,
    ) -> dict[str, Any]:
        """Create HMAC-SHA256 using derived symmetric key.

        TS parity:
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
        if self.key_deriver is None:
            raise RuntimeError("keyDeriver is not configured")

        data = _as_bytes(args.get("data"), "data")

        protocol_id = args.get("protocolID")
        key_id = args.get("keyID")
        counterparty_arg = args.get("counterparty", "self")
        if not protocol_id or not key_id:
            raise InvalidParameterError("protocolID/keyID", "required")

        protocol = Protocol(security_level=protocol_id[0], protocol=protocol_id[1])
        counterparty = _parse_counterparty(counterparty_arg)

        sym_key = self.key_deriver.derive_symmetric_key(protocol, key_id, counterparty)
        import hmac as _hmac
        import hashlib as _hashlib

        tag = _hmac.new(sym_key, data, _hashlib.sha256).digest()
        return {"hmac": _to_byte_list(tag)}

    def verify_hmac(
        self,
        args: dict[str, Any],
        originator: str | None = None,
    ) -> dict[str, Any]:
        """Verify HMAC-SHA256 using derived symmetric key.

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
        self._validate_originator(originator)
        if self.key_deriver is None:
            raise RuntimeError("keyDeriver is not configured")

        data = _as_bytes(args.get("data"), "data")
        provided = _as_bytes(args.get("hmac"), "hmac")

        protocol_id = args.get("protocolID")
        key_id = args.get("keyID")
        counterparty_arg = args.get("counterparty", "self")
        if not protocol_id or not key_id:
            raise InvalidParameterError("protocolID/keyID", "required")

        protocol = Protocol(security_level=protocol_id[0], protocol=protocol_id[1])
        counterparty = _parse_counterparty(counterparty_arg)
        sym_key = self.key_deriver.derive_symmetric_key(protocol, key_id, counterparty)

        import hmac as _hmac
        import hashlib as _hashlib

        expected = _hmac.new(sym_key, data, _hashlib.sha256).digest()
        valid = _hmac.compare_digest(expected, provided)
        return {"valid": bool(valid)}
