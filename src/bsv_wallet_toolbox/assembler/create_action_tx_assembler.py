"""CreateAction Transaction Assembler.

This module provides the CreateActionTransactionAssembler class that builds
and signs transactions from StorageCreateActionResult.

Reference: go-wallet-toolbox/pkg/internal/assembler/create_action_tx_assembler.go
"""

from dataclasses import dataclass, field
from typing import Any

from bsv.script import P2PKH, Script
from bsv.transaction import Transaction, TransactionInput, TransactionOutput
from bsv.transaction.beef import Beef, new_beef_from_bytes

from bsv_wallet_toolbox.brc29 import KeyID, unlock


@dataclass
class StorageCreateTransactionSdkInput:
    """Input from StorageCreateActionResult.

    Reference: go-wallet-toolbox/pkg/wdk/wallet_storage_types.go
    """

    vin: int
    source_txid: str
    source_vout: int
    source_satoshis: int
    source_locking_script: str
    unlocking_script_length: int = 107  # Default P2PKH unlocking script length
    provided_by: str = "storage"
    sender_identity_key: str | None = None
    type: str = "P2PKH"
    derivation_prefix: str | None = None
    derivation_suffix: str | None = None
    source_transaction: bytes | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "StorageCreateTransactionSdkInput":
        """Create from dict (JSON deserialization)."""
        return cls(
            vin=data.get("vin", 0),
            source_txid=data.get("sourceTxid", ""),
            source_vout=data.get("sourceVout", 0),
            source_satoshis=data.get("sourceSatoshis", 0),
            source_locking_script=data.get("sourceLockingScript", ""),
            unlocking_script_length=data.get("unlockingScriptLength", 107),
            provided_by=data.get("providedBy", "storage"),
            sender_identity_key=data.get("senderIdentityKey"),
            type=data.get("type", "P2PKH"),
            derivation_prefix=data.get("derivationPrefix"),
            derivation_suffix=data.get("derivationSuffix"),
            source_transaction=bytes(data["sourceTransaction"]) if data.get("sourceTransaction") else None,
        )


@dataclass
class StorageCreateTransactionSdkOutput:
    """Output from StorageCreateActionResult.

    Reference: go-wallet-toolbox/pkg/wdk/wallet_storage_types.go
    """

    vout: int
    satoshis: int
    locking_script: str | None = None
    basket: str | None = None
    output_description: str | None = None
    custom_instructions: str | None = None
    provided_by: str = "you"
    purpose: str = ""
    derivation_suffix: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "StorageCreateTransactionSdkOutput":
        """Create from dict (JSON deserialization)."""
        return cls(
            vout=data.get("vout", 0),
            satoshis=data.get("satoshis", 0),
            locking_script=data.get("lockingScript"),
            basket=data.get("basket"),
            output_description=data.get("outputDescription"),
            custom_instructions=data.get("customInstructions"),
            provided_by=data.get("providedBy", "you"),
            purpose=data.get("purpose", ""),
            derivation_suffix=data.get("derivationSuffix"),
        )


@dataclass
class StorageCreateActionResult:
    """Result from storage.createAction.

    Reference: go-wallet-toolbox/pkg/wdk/wallet_storage_types.go
    """

    inputs: list[StorageCreateTransactionSdkInput] = field(default_factory=list)
    outputs: list[StorageCreateTransactionSdkOutput] = field(default_factory=list)
    input_beef: bytes = field(default_factory=bytes)
    version: int = 1
    lock_time: int = 0
    reference: str = ""
    derivation_prefix: str = ""
    no_send_change_output_vouts: list[int] | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "StorageCreateActionResult":
        """Create from dict (JSON deserialization)."""
        inputs = [StorageCreateTransactionSdkInput.from_dict(i) for i in data.get("inputs", [])]
        outputs = [StorageCreateTransactionSdkOutput.from_dict(o) for o in data.get("outputs", [])]

        # Handle inputBeef as list of integers (bytes)
        input_beef_data = data.get("inputBeef", [])
        if isinstance(input_beef_data, list):
            input_beef = bytes(input_beef_data)
        elif isinstance(input_beef_data, bytes):
            input_beef = input_beef_data
        elif isinstance(input_beef_data, str):
            input_beef = bytes.fromhex(input_beef_data)
        else:
            input_beef = b""

        return cls(
            inputs=inputs,
            outputs=outputs,
            input_beef=input_beef,
            version=data.get("version", 1),
            lock_time=data.get("lockTime", 0),
            reference=data.get("reference", ""),
            derivation_prefix=data.get("derivationPrefix", ""),
            no_send_change_output_vouts=data.get("noSendChangeOutputVouts"),
        )


class AssembledTransaction:
    """An assembled transaction ready for signing.

    Reference: go-wallet-toolbox/pkg/internal/assembler/assembled_transaction.go
    """

    def __init__(self, tx: Transaction, input_beef: Beef | None = None):
        """Initialize AssembledTransaction.

        Args:
            tx: The transaction
            input_beef: The BEEF containing input transactions
        """
        self.tx = tx
        self.input_beef = input_beef

    def sign(self) -> None:
        """Sign the transaction (all inputs).

        This signs all inputs that have unlocking script templates.
        """
        self.tx.sign()

    def hex(self) -> str:
        """Get the transaction as hex string.

        Returns:
            str: Transaction hex
        """
        return self.tx.hex()

    def to_hex(self) -> str:
        """Get the transaction as hex string (alias for hex()).

        Returns:
            str: Transaction hex
        """
        return self.hex()

    def txid(self) -> str:
        """Get the transaction ID.

        Returns:
            str: Transaction ID (32-byte hex)
        """
        return self.tx.txid()

    def atomic_beef(self, allow_partials: bool = False) -> bytes:
        """Get the transaction as AtomicBEEF bytes.

        Args:
            allow_partials: Whether to allow partial source transactions

        Returns:
            bytes: AtomicBEEF bytes
        """
        beef = Beef()

        # Merge input BEEF
        if self.input_beef:
            beef.merge_beef(self.input_beef)

        # Add source transactions from inputs
        for tx_input in self.tx.inputs:
            if tx_input.source_transaction:
                beef.merge_raw_tx(tx_input.source_transaction.serialize())

        # Add this transaction
        beef.merge_raw_tx(self.tx.serialize())

        return beef.to_atomic_bytes(self.txid())


class CreateActionTransactionAssembler:
    """Assembles a transaction from StorageCreateActionResult.

    This class takes the result from storage.createAction and builds a
    transaction ready for signing.

    Reference: go-wallet-toolbox/pkg/internal/assembler/create_action_tx_assembler.go

    Example:
        >>> from bsv_wallet_toolbox.assembler import CreateActionTransactionAssembler
        >>> assembler = CreateActionTransactionAssembler(key_deriver, None, create_action_result)
        >>> assembled = assembler.assemble()
        >>> assembled.sign()
        >>> print(assembled.hex())
    """

    def __init__(
        self,
        key_deriver: Any,
        provided_inputs: list[dict[str, Any]] | None,
        create_action_result: StorageCreateActionResult | dict[str, Any],
    ):
        """Initialize the assembler.

        Args:
            key_deriver: KeyDeriver for signing (with identity_key property)
            provided_inputs: Inputs provided by the caller (not from storage)
            create_action_result: Result from storage.createAction
        """
        self.key_deriver = key_deriver
        self.provided_inputs = provided_inputs or []

        # Parse create_action_result if it's a dict
        if isinstance(create_action_result, dict):
            self.create_action_result = StorageCreateActionResult.from_dict(create_action_result)
        else:
            self.create_action_result = create_action_result

        self.tx = Transaction()
        self.input_beef: Beef | None = None

    def assemble(self) -> AssembledTransaction:
        """Assemble the transaction from storage result.

        Returns:
            AssembledTransaction: The assembled transaction ready for signing

        Raises:
            ValueError: If assembly fails
        """
        self._parse_input_beef()
        self._fill_transaction_header()
        self._fill_inputs()
        self._fill_outputs()

        return AssembledTransaction(self.tx, self.input_beef)

    def _parse_input_beef(self) -> None:
        """Parse the inputBEEF from the result."""
        if self.create_action_result.input_beef:
            self.input_beef = new_beef_from_bytes(self.create_action_result.input_beef)

    def _fill_transaction_header(self) -> None:
        """Fill transaction version and locktime."""
        self.tx.version = self.create_action_result.version
        self.tx.locktime = self.create_action_result.lock_time

    def _fill_inputs(self) -> None:
        """Fill transaction inputs from storage result."""
        # Sort inputs by vin
        sorted_inputs = sorted(self.create_action_result.inputs, key=lambda x: x.vin)

        for storage_input in sorted_inputs:
            tx_input = self._to_tx_input(storage_input)
            self.tx.add_input(tx_input)

    def _fill_outputs(self) -> None:
        """Fill transaction outputs from storage result."""
        # Sort outputs by vout
        sorted_outputs = sorted(self.create_action_result.outputs, key=lambda x: x.vout)

        for storage_output in sorted_outputs:
            tx_output = self._to_tx_output(storage_output)
            self.tx.add_output(tx_output)

    def _is_input_from_args(self, storage_input: StorageCreateTransactionSdkInput) -> bool:
        """Check if this input was provided in args (not from storage)."""
        return len(self.provided_inputs) > storage_input.vin

    def _to_tx_input(self, storage_input: StorageCreateTransactionSdkInput) -> TransactionInput:
        """Convert a storage input to TransactionInput."""
        if self._is_input_from_args(storage_input):
            return self._to_tx_input_from_args(storage_input)
        return self._to_tx_input_from_managed(storage_input)

    def _to_tx_input_from_args(self, storage_input: StorageCreateTransactionSdkInput) -> TransactionInput:
        """Create input from provided args (not managed by storage)."""
        args_input = self.provided_inputs[storage_input.vin]

        # Verify outpoint matches
        expected_txid = args_input.get("outpoint", {}).get("txid", "")
        expected_vout = args_input.get("outpoint", {}).get("index", 0)

        if expected_txid != storage_input.source_txid or expected_vout != storage_input.source_vout:
            raise ValueError(
                f"Unexpected input (outpoint: {storage_input.source_txid}.{storage_input.source_vout}) "
                f"on index {storage_input.vin}"
            )

        # Find source transaction in BEEF
        source_tx = None
        if self.input_beef:
            beef_tx = self.input_beef.find_transaction(storage_input.source_txid)
            if beef_tx and beef_tx.tx_obj:
                source_tx = beef_tx.tx_obj

        tx_input = TransactionInput(
            source_txid=storage_input.source_txid,
            source_output_index=storage_input.source_vout,
            unlocking_script=Script.from_bytes(bytes(args_input.get("unlockingScript", []))),
            sequence=args_input.get("sequenceNumber", 0xFFFFFFFF),
            source_transaction=source_tx,
        )

        return tx_input

    def _to_tx_input_from_managed(self, storage_input: StorageCreateTransactionSdkInput) -> TransactionInput:
        """Create input from storage-managed UTXO."""
        if storage_input.type != "P2PKH":
            raise ValueError(
                f"Unexpected locking script type '{storage_input.type}' "
                f"on input {storage_input.vin} managed by storage"
            )

        # Get source transaction if available
        source_tx = None
        if storage_input.source_transaction:
            source_tx = Transaction.from_bytes(storage_input.source_transaction)

        # Get sender identity key
        sender_identity_key = storage_input.sender_identity_key
        if not sender_identity_key:
            # Use our own identity key
            sender_identity_key = self.key_deriver.identity_key

        # Create unlocking script template using BRC-29
        key_id = KeyID(
            derivation_prefix=storage_input.derivation_prefix or "",
            derivation_suffix=storage_input.derivation_suffix or "",
        )

        # Create BRC-29 unlock template
        unlock_template = unlock(
            sender_public_key=sender_identity_key,
            key_id=key_id,
            recipient_private_key=self.key_deriver,
        )

        # Create the input
        tx_input = TransactionInput(
            source_txid=storage_input.source_txid,
            source_output_index=storage_input.source_vout,
            sequence=0xFFFFFFFF,
            source_transaction=source_tx,
            unlocking_script_template=unlock_template,
        )

        # If no source transaction, set satoshis and locking script directly
        if not source_tx:
            locking_script = Script(storage_input.source_locking_script)
            tx_input.satoshis = storage_input.source_satoshis
            tx_input.locking_script = locking_script

        return tx_input

    def _to_tx_output(self, storage_output: StorageCreateTransactionSdkOutput) -> TransactionOutput:
        """Convert a storage output to TransactionOutput."""
        is_change = storage_output.provided_by == "storage" and storage_output.purpose == "change"

        if is_change:
            locking_script = self._change_locking_script(storage_output)
        else:
            if not storage_output.locking_script:
                raise ValueError(f"Output {storage_output.vout} has no locking script")
            locking_script = Script(storage_output.locking_script)

        return TransactionOutput(
            locking_script=locking_script,
            satoshis=storage_output.satoshis,
        )

    def _change_locking_script(self, storage_output: StorageCreateTransactionSdkOutput) -> Script:
        """Create a locking script for a change output.

        Change outputs are locked to ourselves using BRC-29 with SELF counterparty.
        """
        from bsv.wallet import Counterparty, CounterpartyType, Protocol

        # For change outputs, use transaction-level derivation_prefix (shared by all change outputs in this tx)
        # and output-level derivation_suffix (unique per change output)
        # Both are base64 strings used directly (not decoded) - matches Go/TS behavior
        derivation_prefix = self.create_action_result.derivation_prefix or ""
        derivation_suffix = storage_output.derivation_suffix or ""

        # Create KeyID with base64 strings (not decoded) - KeyID.__str__() will use them directly
        key_id = KeyID(
            derivation_prefix=derivation_prefix,
            derivation_suffix=derivation_suffix,
        )

        # Validate key_id
        key_id.validate()

        # For change outputs, use SELF counterparty (we are locking to ourselves)
        protocol = Protocol(security_level=2, protocol="3241645161d8")
        counterparty = Counterparty(type=CounterpartyType.SELF)

        # Derive the public key using SELF counterparty (matches signer logic)
        derived_pub_key = self.key_deriver.derive_public_key(
            protocol=protocol, key_id=str(key_id), counterparty=counterparty, for_self=True
        )

        # Create P2PKH locking script
        p2pkh = P2PKH()
        locking_script = p2pkh.lock(derived_pub_key.hash160())

        return locking_script
