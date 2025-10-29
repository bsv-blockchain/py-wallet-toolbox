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
        >>> result = await wallet.get_version({})
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
    ) -> None:
        """Initialize wallet.

        Args:
            chain: Bitcoin network chain ('main' or 'test'). Required parameter.
            services: Optional WalletServices instance for blockchain data access.
                     If None, some methods requiring services will not work.
            key_deriver: Optional KeyDeriver instance for key derivation operations.
                        If None, methods requiring key derivation will raise RuntimeError.

        Note:
            Version is not configurable, it's a class constant.
            Chain parameter is required (no default value), matching TypeScript implementation.
        """
        self.chain: Chain = chain
        self.services: WalletServices | None = services
        self.key_deriver: KeyDeriver | None = key_deriver

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

    async def get_network(
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
            >>> result = await wallet.get_network({})
            >>> assert result == {"network": "mainnet"}
        """
        self._validate_originator(originator)
        return {"network": self._to_wallet_network(self.chain)}

    async def get_version(
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
            >>> result = await wallet.get_version({})
            >>> assert result == {"version": Wallet.VERSION}
        """
        self._validate_originator(originator)
        return {"version": self.VERSION}

    async def is_authenticated(
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
            >>> result = await wallet.is_authenticated({})
            >>> assert result == {"authenticated": True}
        """
        self._validate_originator(originator)
        return {"authenticated": True}

    async def wait_for_authentication(
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
            >>> result = await wallet.wait_for_authentication({})
            >>> assert result == {"authenticated": True}
        """
        self._validate_originator(originator)
        return {"authenticated": True}

    async def get_height(
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
            >>> result = await wallet.get_height({})
            >>> print(result["height"])
            850000

        Note:
            Requires services to be configured. If services is None, raises RuntimeError.
        """
        self._validate_originator(originator)

        if self.services is None:
            raise RuntimeError("Services must be configured to use getHeight")

        height = await self.services.get_height()
        return {"height": height}

    async def get_header_for_height(self, args: dict[str, Any], originator: str | None = None) -> GetHeaderResult:
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
            >>> result = await wallet.get_header_for_height({"height": 850000})
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
        header_bytes = await self.services.get_header_for_height(height)

        # Convert bytes to hex string (matching TypeScript behavior)
        return {"header": header_bytes.hex()}

    async def get_public_key(
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
            >>> result = await wallet.get_public_key({"identityKey": True})
            >>> print(result["publicKey"][:10])
            02a1b2c3d4
            
            >>> # Derive a protocol-specific key
            >>> result = await wallet.get_public_key({
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

    async def create_signature(
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
            if isinstance(h_direct, (bytes, bytearray)):
                to_sign = bytes(h_direct)
            else:
                raise InvalidParameterError("hashToDirectlySign", "bytes-like expected")
        else:
            data = args.get("data", b"")
            if not isinstance(data, (bytes, bytearray)):
                raise InvalidParameterError("data", "bytes-like expected when hash not provided")
            import hashlib

            to_sign = hashlib.sha256(bytes(data)).digest()

        # Sign without extra hashing (TS parity)
        signature: bytes = priv.sign(to_sign, hasher=lambda m: m)
        return {"signature": signature}

    async def verify_signature(
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

        if not isinstance(signature, (bytes, bytearray)):
            raise InvalidParameterError("signature", "bytes-like expected")

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
            if isinstance(h_direct, (bytes, bytearray)):
                digest = bytes(h_direct)
            else:
                raise InvalidParameterError("hashToDirectlyVerify", "bytes-like expected")
        else:
            data = args.get("data", b"")
            if not isinstance(data, (bytes, bytearray)):
                raise InvalidParameterError("data", "bytes-like expected when hash not provided")
            import hashlib

            digest = hashlib.sha256(bytes(data)).digest()

        # Verify without extra hashing (TS parity)
        valid = pub.verify(signature, digest, hasher=lambda m: m)
        return {"valid": bool(valid)}

    async def encrypt(
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

        plaintext = args.get("plaintext")
        if not isinstance(plaintext, (bytes, bytearray)):
            raise InvalidParameterError("plaintext", "bytes-like expected")

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
        ciphertext: bytes = pub.encrypt(bytes(plaintext))
        return {"ciphertext": ciphertext}

    async def decrypt(
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

        ciphertext = args.get("ciphertext")
        if not isinstance(ciphertext, (bytes, bytearray)):
            raise InvalidParameterError("ciphertext", "bytes-like expected")

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
        plaintext: bytes = priv.decrypt(bytes(ciphertext))
        return {"plaintext": plaintext}
