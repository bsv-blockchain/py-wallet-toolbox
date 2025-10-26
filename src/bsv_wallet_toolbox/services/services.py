"""Services implementation.

Main implementation of WalletServices interface with provider support.

Reference: toolbox/ts-wallet-toolbox/src/services/Services.ts
"""


from bsv.chaintracker import ChainTracker
from time import time
from typing import Any

from .providers.whatsonchain import WhatsOnChain
from .wallet_services import Chain, WalletServices
from .wallet_services_options import WalletServicesOptions
from ..utils.script_hash import hash_output_script as utils_hash_output_script
from bsv.transaction import Transaction


def create_default_options(chain: Chain) -> WalletServicesOptions:
    """Create default WalletServicesOptions for a given chain.

    Equivalent to TypeScript's Services.createDefaultOptions()

    Args:
        chain: Blockchain network ('main' or 'test')

    Returns:
        WalletServicesOptions with default values

    Reference: toolbox/ts-wallet-toolbox/src/services/createDefaultWalletServicesOptions.ts
    """
    return WalletServicesOptions(chain=chain)


class Services(WalletServices):
    """Production-ready WalletServices implementation.

    This is the Python equivalent of TypeScript's Services class.
    Supports multiple providers (WhatsOnChain, ARC, Bitails, etc.).

    Current implementation status:
    - ✅ WhatsOnChain: Fully implemented
    - ❌ ARC (TAAL): Not yet implemented
    - ❌ ARC (GorillaPool): Not yet implemented
    - ❌ Bitails: Not yet implemented

    Reference: toolbox/ts-wallet-toolbox/src/services/Services.ts

    Example:
        >>> # Simple usage with chain
        >>> services = Services("main")
        >>>
        >>> # Advanced usage with options
        >>> options = WalletServicesOptions(
        ...     chain="main",
        ...     whatsOnChainApiKey="your-api-key"
        ... )
        >>> services = Services(options)
        >>>
        >>> # Get blockchain height
        >>> height = await services.get_height()
        >>> print(height)
        850123
    """

    # Provider instances (TypeScript structure)
    options: WalletServicesOptions
    whatsonchain: WhatsOnChain
    # Future providers (not yet implemented):
    # arc_taal: ARC
    # arc_gorillapool: Optional[ARC]
    # bitails: Bitails

    @staticmethod
    def create_default_options(chain: Chain) -> WalletServicesOptions:
        return create_default_options(chain)

    def __init__(self, options_or_chain: Chain | WalletServicesOptions) -> None:
        """Initialize wallet services.

        Equivalent to TypeScript's Services constructor which accepts either
        a Chain string or WalletServicesOptions object.

        Args:
            options_or_chain: Either a Chain ('main'/'test') or full WalletServicesOptions

        Example:
            >>> # Simple: Just pass chain
            >>> services = Services("main")
            >>>
            >>> # Advanced: Pass full options
            >>> options = WalletServicesOptions(
            ...     chain="main",
            ...     whatsOnChainApiKey="your-api-key"
            ... )
            >>> services = Services(options)

        Reference: toolbox/ts-wallet-toolbox/src/services/Services.ts constructor
        """
        # Determine chain and options (matching TypeScript logic)
        if isinstance(options_or_chain, str):
            # Simple case: chain string provided
            chain: Chain = options_or_chain
            self.options = create_default_options(chain)
        else:
            # Advanced case: full options provided
            chain = options_or_chain["chain"]
            self.options = options_or_chain

        # Call parent constructor
        super().__init__(chain)

        # Initialize WhatsOnChain provider (currently only implemented provider)
        api_key = self.options.get("whatsOnChainApiKey")
        self.whatsonchain = WhatsOnChain(network=chain, api_key=api_key, http_client=None)

        # Future providers (not yet implemented):
        # self.arc_taal = ARC(self.options["arcUrl"], self.options["arcConfig"], "arcTaal")
        # if self.options.get("arcGorillaPoolUrl"):
        #     self.arc_gorillapool = ARC(
        #         self.options["arcGorillaPoolUrl"],
        #         self.options.get("arcGorillaPoolConfig"),
        #         "arcGorillaPool"
        #     )
        # self.bitails = Bitails(chain, {"apiKey": self.options.get("bitailsApiKey")})

    async def get_chain_tracker(self) -> ChainTracker:
        """Get ChainTracker instance for Merkle proof verification.

        Returns the WhatsOnChain ChainTracker implementation.

        Returns:
            WhatsOnChain instance (implements ChaintracksClientApi)
        """
        return self.whatsonchain

    async def get_height(self) -> int:
        """Get current blockchain height from WhatsOnChain.

        Equivalent to TypeScript's Services.getHeight()
        Uses py-sdk's WhatsOnChainTracker.current_height() (SDK method)

        Returns:
            Current blockchain height

        Raises:
            RuntimeError: If unable to retrieve height
        """
        return await self.whatsonchain.current_height()

    async def get_header_for_height(self, height: int) -> bytes:
        """Get block header at specified height from WhatsOnChain.

        Equivalent to TypeScript's Services.getHeaderForHeight()
        Uses WhatsOnChain.get_header_bytes_for_height() helper method

        Args:
            height: Block height (must be non-negative)

        Returns:
            80-byte serialized block header

        Raises:
            ValueError: If height is negative
            RuntimeError: If unable to retrieve header
        """
        return await self.whatsonchain.get_header_bytes_for_height(height)

    #
    # WalletServices local-calculation methods (no external API calls)
    #

    def hashOutputScript(self, script_hex: str) -> str:
        """Hash a locking script in hex and return little-endian hex string.

        Reference: toolbox/ts-wallet-toolbox/src/services/Services.ts (hashOutputScript)
        Reference: toolbox/go-wallet-toolbox/pkg/internal/txutils/script_hash.go

        Args:
            script_hex: Locking script as hexadecimal string

        Returns:
            Little-endian hex string of SHA-256(script)
        """
        return utils_hash_output_script(script_hex)

    async def nLockTimeIsFinal(self, tx_or_locktime: Any) -> bool:
        """Determine if an nLockTime value (or transaction) is final.

        Logic matches TypeScript Services.nLockTimeIsFinal:
        - If given a transaction (hex/bytes/Transaction), return True if all sequences are MAXINT
          otherwise use the transaction's locktime
        - Threshold 500,000,000 separates height-based vs timestamp-based locktimes
        - Timestamp branch: compare strictly with current unix time (nLockTime < now)
        - Height branch: compare strictly with chain height (nLockTime < height)

        Reference: toolbox/ts-wallet-toolbox/src/services/Services.ts (nLockTimeIsFinal)
        Reference: toolbox/go-wallet-toolbox/pkg/wdk/locktime.go

        Args:
            tx_or_locktime: int locktime, tx hex string, bytes, or Transaction

        Returns:
            True if considered final
        """
        MAXINT = 0xFFFFFFFF
        BLOCK_LIMIT = 500_000_000

        n_lock_time: int | None = None
        tx: Transaction | None = None

        if isinstance(tx_or_locktime, int):
            n_lock_time = tx_or_locktime
        else:
            # Try to parse a Transaction from hex/bytes/Reader
            if isinstance(tx_or_locktime, Transaction):
                tx = tx_or_locktime
            elif isinstance(tx_or_locktime, (bytes, str)):
                tx = Transaction.from_hex(tx_or_locktime)
                if tx is None:
                    raise ValueError("Invalid transaction hex provided to nLockTimeIsFinal")
            else:
                raise TypeError("nLockTimeIsFinal expects int, hex str/bytes, or Transaction")

            # If all input sequences are MAXINT -> final (TS behavior)
            if tx.inputs and all(i.sequence == MAXINT for i in tx.inputs):
                return True
            n_lock_time = int(tx.locktime)

        if n_lock_time is None:
            raise ValueError("Unable to determine nLockTime")

        if n_lock_time >= BLOCK_LIMIT:
            # Timestamp-based: strict less-than vs current unix seconds
            now_sec = int(time())
            return n_lock_time < now_sec

        height = await self.get_height()
        return n_lock_time < int(height)

    #
    # WalletServices external service methods
    #

    async def get_raw_tx(self, txid: str) -> str | None:
        """Get raw transaction hex for a given txid via WhatsOnChain.

        Reference: toolbox/ts-wallet-toolbox/src/services/Services.ts (getRawTx)

        Args:
            txid: Transaction ID (64-hex string)

        Returns:
            Raw transaction hex string if found, otherwise None
        """
        return await self.whatsonchain.get_raw_tx(txid)

    async def is_valid_root_for_height(self, root: str, height: int) -> bool:
        """Verify if a Merkle root is valid for a given block height.

        Delegates to provider's ChainTracker implementation (WhatsOnChainTracker).

        Reference: toolbox/ts-wallet-toolbox/src/services/Services.ts (isValidRootForHeight)

        Args:
            root: Merkle root hex string
            height: Block height

        Returns:
            True if the Merkle root matches the header's merkleRoot at the height
        """
        return await self.whatsonchain.is_valid_root_for_height(root, height)

    async def get_merkle_path_for_transaction(self, txid: str) -> dict[str, Any]:
        """Get the Merkle path for a transaction (TS-compatible response shape).

        Delegates to the provider implementation (WhatsOnChain).

        Args:
            txid: Transaction ID (hex, big-endian)

        Returns:
            dict: On success, an object with keys "header" and "merklePath". If no data exists,
                  returns the provider sentinel object (e.g., {"name": "WoCTsc", "notes": [...]})

        Raises:
            RuntimeError: If provider returns a non-OK status.

        Reference:
            - toolbox/ts-wallet-toolbox/src/services/Services.ts#getMerklePathForTransaction
        """
        return await self.whatsonchain.get_merkle_path(txid, self)

    async def update_bsv_exchange_rate(self) -> dict[str, Any]:
        """Get the current BSV/USD exchange rate via provider.

        Returns:
            dict: { "base": "USD", "rate": number, "timestamp": number }

        Raises:
            RuntimeError: If provider returns a non-OK status.

        Reference:
            - toolbox/ts-wallet-toolbox/src/services/Services.ts#updateBsvExchangeRate
        """
        return await self.whatsonchain.update_bsv_exchange_rate()

    async def get_fiat_exchange_rate(self, currency: str, base: str = "USD") -> float:
        """Get a fiat exchange rate for "currency" relative to "base".

        The provider returns a base and a rates map. If the provider base matches the requested base,
        this method returns rates[currency]. Otherwise it converts through the provider base.

        Args:
            currency: Target fiat currency code (e.g., 'USD', 'GBP', 'EUR')
            base: Base fiat currency code to compare against (default 'USD')

        Returns:
            float: The fiat exchange rate of currency relative to base.

        Raises:
            RuntimeError: If provider returns a non-OK status.
            ValueError: If currency/base cannot be resolved from provider rates.

        Reference:
            - toolbox/ts-wallet-toolbox/src/services/Services.ts#getFiatExchangeRate
        """
        return await self.whatsonchain.get_fiat_exchange_rate(currency, base)

    async def get_utxo_status(
        self,
        output: str,
        output_format: str | None = None,
        outpoint: str | None = None,
        use_next: bool | None = None,
    ) -> dict[str, Any]:
        """Get UTXO status via provider (TS-compatible response shape).

        Supports the same input conventions as the TS implementation:
        - output_format determines how "output" is interpreted: 'hashLE' | 'hashBE' | 'script' | 'outpoint'.
        - When output_format == 'outpoint', the optional 'outpoint' ('txid:vout') can be provided.
        - Provider selection (use_next) is accepted for parity but ignored here.

        Args:
            output: Locking script hex, script hash, or outpoint descriptor depending on output_format
            output_format: One of 'hashLE', 'hashBE', 'script', 'outpoint'
            outpoint: Optional 'txid:vout' specifier when needed
            use_next: Provider selection hint (ignored)

        Returns:
            dict: TS-like { "details": [{ "outpoint": str, "spent": bool, ... }] }.

        Raises:
            RuntimeError: If provider returns a non-OK status.

        Reference:
            - toolbox/ts-wallet-toolbox/src/services/Services.ts#getUtxoStatus
        """
        return await self.whatsonchain.get_utxo_status(output, output_format, outpoint, use_next)

    async def get_script_history(self, script_hash: str, use_next: bool | None = None) -> dict[str, Any]:
        """Get script history via provider (TS-compatible response shape).

        Returns two arrays, matching TS semantics:
        - confirmed: Transactions confirmed on-chain spending/creating outputs related to the script hash
        - unconfirmed: Transactions seen but not yet confirmed

        Args:
            script_hash: The script hash (usually little-endian for WoC) required by the provider
            use_next: Provider selection hint (ignored; kept for parity with TS)

        Returns:
            dict: { "confirmed": [...], "unconfirmed": [...] }

        Raises:
            RuntimeError: If provider returns a non-OK status.

        Reference:
            - toolbox/ts-wallet-toolbox/src/services/Services.ts#getScriptHistory
        """
        return await self.whatsonchain.get_script_history(script_hash, use_next)

    async def get_transaction_status(self, txid: str, use_next: bool | None = None) -> dict[str, Any]:
        """Get transaction status via provider (TS-compatible response shape).

        Args:
            txid: Transaction ID (hex, big-endian)
            use_next: Provider selection hint (ignored)

        Returns:
            dict: Provider-specific status object (TS-compatible shape expected by tests)
        """
        return await self.whatsonchain.get_transaction_status(txid, use_next)
