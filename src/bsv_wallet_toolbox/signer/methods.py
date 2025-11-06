"""Signer methods implementation (TypeScript parity).

Implements high-level transaction signing operations that combine KeyDeriver
and WalletStorage to provide the full Wallet interface signing capabilities.

Reference:
    - toolbox/ts-wallet-toolbox/src/signer/methods/createAction.ts
    - toolbox/ts-wallet-toolbox/src/signer/methods/buildSignableTransaction.ts
    - toolbox/ts-wallet-toolbox/src/signer/methods/completeSignedTransaction.ts
    - toolbox/ts-wallet-toolbox/src/signer/methods/signAction.ts
    - toolbox/ts-wallet-toolbox/src/signer/methods/internalizeAction.ts
    - toolbox/ts-wallet-toolbox/src/signer/methods/acquireDirectCertificate.ts
    - toolbox/ts-wallet-toolbox/src/signer/methods/proveCertificate.ts
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from bsv.script import Script
from bsv.transaction import Beef, Transaction, TransactionInput, TransactionOutput

from bsv_wallet_toolbox.errors import WalletError
from bsv_wallet_toolbox.utils.validation import validate_satoshis

# ============================================================================
# Type Definitions (TS Parity)
# ============================================================================


@dataclass
class PendingSignAction:
    """Pending transaction awaiting signature (TS parity)."""

    reference: str
    dcr: Any  # StorageCreateActionResult
    args: Any  # ValidCreateActionArgs
    amount: int
    tx: Transaction
    pdi: list[PendingStorageInput] = field(default_factory=list)


@dataclass
class PendingStorageInput:
    """Pending storage input awaiting signature (TS parity)."""

    vin: int
    derivation_prefix: str
    derivation_suffix: str
    unlocker_pub_key: str
    source_satoshis: int
    locking_script: str


@dataclass
class CreateActionResultX:
    """Create action result (TS parity - extended)."""

    txid: str | None = None
    tx: bytes | None = None
    no_send_change: list[str] | None = None
    send_with_results: list[Any] | None = None
    signable_transaction: dict[str, Any] | None = None
    not_delayed_results: list[Any] | None = None


# ============================================================================
# Core Methods
# ============================================================================


def create_action(wallet: Any, auth: Any, vargs: dict[str, Any]) -> CreateActionResultX:
    """Create action with optional signing (TS parity).

    Reference:
        - toolbox/ts-wallet-toolbox/src/signer/methods/createAction.ts

    Args:
        wallet: Wallet instance
        auth: Authentication context
        vargs: Validated create action arguments

    Returns:
        CreateActionResultX with transaction and results
    """
    result = CreateActionResultX()
    prior: PendingSignAction | None = None

    if vargs.get("is_new_tx"):
        prior = _create_new_tx(wallet, vargs)

        if vargs.get("is_sign_action"):
            return _make_signable_transaction_result(prior, wallet, vargs)

        prior.tx = complete_signed_transaction(prior, {}, wallet)

        result.txid = prior.tx.id("hex")
        beef = Beef()
        if prior.dcr.get("input_beef"):
            beef.merge_beef(Beef.from_binary(prior.dcr["input_beef"]))
        beef.merge_transaction(prior.tx)

        _verify_unlock_scripts(result.txid, beef)

        result.no_send_change = (
            [f"{result.txid}.{vout}" for vout in prior.dcr.get("no_send_change_output_vouts", [])]
            if prior.dcr.get("no_send_change_output_vouts")
            else None
        )
        if not vargs.get("options", {}).get("return_txid_only"):
            result.tx = beef.to_binary_atomic(result.txid)

    process_result = process_action(prior, wallet, auth, vargs)
    result.send_with_results = process_result.get("send_with_results")
    result.not_delayed_results = process_result.get("not_delayed_results")

    return result


def build_signable_transaction(
    dctr: dict[str, Any], args: dict[str, Any], wallet: Any
) -> tuple[Transaction, int, list[PendingStorageInput], str]:
    """Build signable transaction from storage result (TS parity).

    Reference:
        - toolbox/ts-wallet-toolbox/src/signer/methods/buildSignableTransaction.ts

    Args:
        dctr: Storage create transaction result
        args: Validated create action arguments
        wallet: Wallet instance

    Returns:
        Tuple of (transaction, amount, pending_inputs, log)
    """
    change_keys = wallet.get_client_change_key_pair()

    input_beef = Beef.from_binary(args["input_beef"]) if args.get("input_beef") else None

    storage_inputs = dctr.get("inputs", [])
    storage_outputs = dctr.get("outputs", [])

    tx = Transaction(version=args.get("version", 2), inputs=[], outputs=[], lock_time=args.get("lock_time", 0))

    # Map output vout to index
    vout_to_index: dict[int, int] = {}
    for vout in range(len(storage_outputs)):
        found_index = None
        for i, output in enumerate(storage_outputs):
            if output.get("vout") == vout:
                found_index = i
                break
        if found_index is None:
            raise WalletError(f"output.vout must be sequential. {vout} is missing")
        vout_to_index[vout] = found_index

    # Add outputs
    for vout in range(len(storage_outputs)):
        i = vout_to_index[vout]
        out = storage_outputs[i]

        if vout != out.get("vout"):
            raise WalletError(f"output.vout must equal array index. {out.get('vout')} !== {vout}")

        is_change = out.get("provided_by") == "storage" and out.get("purpose") == "change"

        locking_script = (
            _make_change_lock(out, dctr, args, change_keys, wallet)
            if is_change
            else Script.from_hex(out.get("locking_script", ""))
        )

        tx.add_output(
            TransactionOutput(satoshis=out.get("satoshis", 0), locking_script=locking_script, change=is_change)
        )

    if len(storage_outputs) == 0:
        # Add dummy output to avoid empty transaction rejection
        tx.add_output(
            TransactionOutput(satoshis=0, locking_script=Script.from_asm("OP_FALSE OP_RETURN 42"), change=False)
        )

    # Sort inputs by vin order
    inputs: list[dict[str, Any]] = []
    for storage_input in storage_inputs:
        vin = storage_input.get("vin")
        args_input = args.get("inputs", [])[vin] if vin is not None and vin < len(args.get("inputs", [])) else None
        inputs.append({"args_input": args_input, "storage_input": storage_input})

    inputs.sort(key=lambda x: x["storage_input"].get("vin", 0))

    pending_storage_inputs: list[PendingStorageInput] = []
    total_change_inputs = 0

    # Add inputs
    for input_data in inputs:
        storage_input = input_data["storage_input"]
        args_input = input_data["args_input"]

        if args_input:
            # Type 1: User supplied input
            has_unlock = args_input.get("unlocking_script") is not None
            unlock = Script.from_hex(args_input.get("unlocking_script", "")) if has_unlock else Script()

            source_transaction = None
            if args.get("is_sign_action") and input_beef:
                txid = args_input.get("outpoint", {}).get("txid")
                if txid:
                    tx_data = input_beef.find_txid(txid)
                    if tx_data:
                        source_transaction = tx_data.get("tx")

            tx.add_input(
                TransactionInput(
                    source_txid=args_input.get("outpoint", {}).get("txid", ""),
                    source_output_index=args_input.get("outpoint", {}).get("vout", 0),
                    source_transaction=source_transaction,
                    unlocking_script=unlock,
                    sequence=args_input.get("sequence_number", 0xFFFFFFFF),
                )
            )
        else:
            # Type 2: SABPPP protocol inputs
            if storage_input.get("type") != "P2PKH":
                raise WalletError(f'vin {storage_input.get("vin")}, ' f'"{storage_input.get("type")}" is not supported')

            pending_storage_inputs.append(
                PendingStorageInput(
                    vin=len(tx.inputs),
                    derivation_prefix=storage_input.get("derivation_prefix", ""),
                    derivation_suffix=storage_input.get("derivation_suffix", ""),
                    unlocker_pub_key=storage_input.get("sender_identity_key", ""),
                    source_satoshis=storage_input.get("source_satoshis", 0),
                    locking_script=storage_input.get("source_locking_script", ""),
                )
            )

            source_tx_binary = storage_input.get("source_transaction")
            source_tx = Transaction.from_binary(source_tx_binary) if source_tx_binary else None

            tx.add_input(
                TransactionInput(
                    source_txid=storage_input.get("source_txid", ""),
                    source_output_index=storage_input.get("source_vout", 0),
                    source_transaction=source_tx,
                    unlocking_script=Script(),
                    sequence=0xFFFFFFFF,
                )
            )
            total_change_inputs += validate_satoshis(
                storage_input.get("source_satoshis", 0), "storage_input.source_satoshis"
            )

    # Calculate amount (total non-foreign inputs minus change outputs)
    total_change_outputs = sum(
        output.get("satoshis", 0) for output in storage_outputs if output.get("purpose") == "change"
    )
    amount = total_change_inputs - total_change_outputs

    return tx, amount, pending_storage_inputs, ""


def complete_signed_transaction(prior: PendingSignAction, spends: dict[int, Any], wallet: Any) -> Transaction:
    """Complete signed transaction (TS parity).

    Inserts user-provided unlocking scripts and SABPPP unlock templates,
    then signs the transaction.

    Reference:
        - toolbox/ts-wallet-toolbox/src/signer/methods/completeSignedTransaction.ts

    Args:
        prior: Pending sign action
        spends: Dict mapping vin to spend data (unlocking script, sequence)
        wallet: Wallet instance

    Returns:
        Completed and signed transaction
    """
    # Insert user-provided unlocking scripts from spends
    for vin_str, spend in spends.items():
        vin = int(vin_str)
        create_input = prior.args.get("inputs", [])[vin] if vin < len(prior.args.get("inputs", [])) else None
        input_data = prior.tx.inputs[vin] if vin < len(prior.tx.inputs) else None

        if (
            not create_input
            or not input_data
            or create_input.get("unlocking_script") is not None
            or "unlocking_script_length" not in create_input
            or not isinstance(create_input["unlocking_script_length"], int)
        ):
            raise WalletError("spend does not correspond to prior input with valid unlockingScriptLength.")

        unlock_script_hex = spend.get("unlocking_script", "")
        unlock_script_len_bytes = len(unlock_script_hex) // 2

        if unlock_script_len_bytes > create_input["unlocking_script_length"]:
            raise WalletError(
                f"spend unlockingScript length {unlock_script_len_bytes} "
                f"exceeds expected length {create_input['unlocking_script_length']}"
            )

        input_data["unlocking_script"] = Script.from_hex(unlock_script_hex)
        if "sequence_number" in spend:
            input_data["sequence"] = spend["sequence_number"]

    # Insert SABPPP unlock templates for wallet-signed inputs
    for _pdi in prior.pdi:
        # TODO: Implement ScriptTemplateBRC29 unlock template generation
        # For now, this is a placeholder
        pass

    # Sign wallet-signed inputs
    # TODO: Implement full transaction signing with KeyDeriver
    # prior.tx.sign()

    return prior.tx


def process_action(prior: PendingSignAction | None, wallet: Any, auth: Any, vargs: dict[str, Any]) -> dict[str, Any]:
    """Process action (TS parity).

    Reference:
        - toolbox/ts-wallet-toolbox/src/signer/methods/createAction.ts

    Args:
        prior: Optional pending sign action
        wallet: Wallet instance
        auth: Authentication context
        vargs: Validated process action arguments

    Returns:
        Process action results
    """
    storage_args = {
        "is_new_tx": vargs.get("is_new_tx"),
        "is_send_with": vargs.get("is_send_with"),
        "is_no_send": vargs.get("is_no_send"),
        "is_delayed": vargs.get("is_delayed"),
        "reference": prior.reference if prior else None,
        "txid": prior.tx.id("hex") if prior else None,
        "raw_tx": prior.tx.to_binary() if prior else None,
        "send_with": vargs.get("options", {}).get("send_with", []) if vargs.get("is_send_with") else [],
    }

    result = wallet.storage.process_action(storage_args)
    return result


def sign_action(wallet: Any, auth: Any, args: dict[str, Any]) -> dict[str, Any]:
    """Sign action (TS parity).

    Reference:
        - toolbox/ts-wallet-toolbox/src/signer/methods/signAction.ts

    Args:
        wallet: Wallet instance
        auth: Authentication context
        args: Sign action arguments

    Returns:
        Sign action result dict with txid, tx, sendWithResults, notDelayedResults
    """
    # Get prior pending sign action from wallet
    reference = args.get("reference")
    if not reference:
        raise WalletError("reference is required in sign_action args")

    prior = wallet.pending_sign_actions.get(reference)
    if not prior:
        raise WalletError("recovery of out-of-session signAction reference data is not yet implemented.")

    if not prior.dcr.get("input_beef"):
        raise WalletError("prior.dcr.input_beef must be valid")

    # Merge prior options with new sign action options
    vargs = _merge_prior_options(prior.args, args)

    # Complete transaction with signatures
    prior.tx = complete_signed_transaction(prior, vargs.get("spends", {}), wallet)

    # Process the action
    process_result = process_action(prior, wallet, auth, vargs)

    # Build result
    txid = prior.tx.id("hex")
    beef = Beef.from_binary(prior.dcr.get("input_beef", b""))
    beef.merge_transaction(prior.tx)

    _verify_unlock_scripts(txid, beef)

    result = {
        "txid": txid,
        "tx": (None if vargs.get("options", {}).get("return_txid_only") else beef.to_binary_atomic(txid)),
        "send_with_results": process_result.get("send_with_results"),
        "not_delayed_results": process_result.get("not_delayed_results"),
    }

    return result


def internalize_action(wallet: Any, auth: Any, args: dict[str, Any]) -> dict[str, Any]:
    """Internalize action (TS parity).

    Allows wallet to take ownership of outputs in pre-existing transaction.
    Handles "wallet payments" and "basket insertions".

    Reference:
        - toolbox/ts-wallet-toolbox/src/signer/methods/internalizeAction.ts

    Args:
        wallet: Wallet instance
        auth: Authentication context
        args: Internalize action arguments

    Returns:
        Internalize action result from storage layer
    """
    # Validate arguments
    vargs = args  # TODO: Call validateInternalizeActionArgs when available

    # Validate and extract atomic BEEF
    ab = Beef.from_binary(vargs.get("tx", b""))

    # TODO: Add support for known txids...
    # For now, verify the beef
    txid = ab.atomic_txid
    if not txid:
        raise WalletError(f"tx is not valid AtomicBEEF: {ab.to_log_string()}")

    btx = ab.find_txid(txid)
    if not btx:
        raise WalletError(f"tx is not valid AtomicBEEF with newest txid of {txid}")

    tx = btx.get("tx")
    if not tx:
        raise WalletError("Could not extract transaction from BEEF")

    # BRC-29 protocol ID
    brc29_protocol_id = [2, "3241645161d8"]

    # Process each output
    for output_spec in vargs.get("outputs", []):
        output_index = output_spec.get("output_index")

        if output_index < 0 or output_index >= len(tx.outputs):
            raise WalletError(f"outputIndex must be valid output index in range 0 to {len(tx.outputs) - 1}")

        protocol = output_spec.get("protocol")

        if protocol == "wallet payment":
            _setup_wallet_payment_for_output(output_spec, tx, wallet, brc29_protocol_id)
        elif protocol == "basket insertion":
            # No additional validations for basket insertion
            pass
        else:
            raise WalletError(f"unexpected protocol {protocol}")

    # Pass to storage layer
    result = wallet.storage.internalize_action(vargs)
    return result


def acquire_direct_certificate(wallet: Any, auth: Any, vargs: dict[str, Any]) -> dict[str, Any]:
    """Acquire direct certificate (TS parity).

    Reference:
        - toolbox/ts-wallet-toolbox/src/signer/methods/acquireDirectCertificate.ts

    Args:
        wallet: Wallet instance
        auth: Authentication context
        vargs: Validated certificate arguments

    Returns:
        Certificate result dict
    """
    now = datetime.utcnow()
    user_id = auth.get("user_id") if isinstance(auth, dict) else getattr(auth, "user_id", "")

    # Create certificate record
    new_cert = {
        "certificate_id": 0,  # Will be replaced by storage insert
        "created_at": now,
        "updated_at": now,
        "user_id": user_id,
        "type": vargs.get("type"),
        "subject": vargs.get("subject"),
        "verifier": (
            vargs.get("certifier") if vargs.get("keyring_revealer") == "certifier" else vargs.get("keyring_revealer")
        ),
        "serial_number": vargs.get("serial_number"),
        "certifier": vargs.get("certifier"),
        "revocation_outpoint": vargs.get("revocation_outpoint"),
        "signature": vargs.get("signature"),
        "fields": [],
        "is_deleted": False,
    }

    # Add certificate fields
    keyring_for_subject = vargs.get("keyring_for_subject", {})
    for field_name, field_value in vargs.get("fields", {}).items():
        new_cert["fields"].append(
            {
                "certificate_id": 0,  # Will be replaced by storage insert
                "created_at": now,
                "updated_at": now,
                "user_id": user_id,
                "field_name": field_name,
                "field_value": field_value,
                "master_key": keyring_for_subject.get(field_name, ""),
            }
        )

    # Insert certificate into storage
    wallet.storage.insert_certificate(new_cert)

    # Return result
    result = {
        "type": vargs.get("type"),
        "subject": vargs.get("subject"),
        "serial_number": vargs.get("serial_number"),
        "certifier": vargs.get("certifier"),
        "revocation_outpoint": vargs.get("revocation_outpoint"),
        "signature": vargs.get("signature"),
        "fields": vargs.get("fields", {}),
    }

    return result


def prove_certificate(wallet: Any, auth: Any, vargs: dict[str, Any]) -> dict[str, Any]:
    """Prove certificate (TS parity).

    Reference:
        - toolbox/ts-wallet-toolbox/src/signer/methods/proveCertificate.ts

    Args:
        wallet: Wallet instance
        auth: Authentication context
        vargs: Validated prove arguments

    Returns:
        Proof result dict
    """
    # TODO: Implement full certificate proof logic with KeyDeriver integration
    # For now, return a minimal result structure
    result = {
        "certificate_id": vargs.get("certificate_id"),
        "subject": vargs.get("subject"),
        "field_values": vargs.get("field_values", {}),
    }
    return result


# ============================================================================
# Helper Functions
# ============================================================================


def _create_new_tx(wallet: Any, args: dict[str, Any]) -> PendingSignAction:
    """Create new transaction (TS parity - internal).

    Reference:
        - toolbox/ts-wallet-toolbox/src/signer/methods/createAction.ts
    """
    storage_args = _remove_unlock_scripts(args)
    dcr = wallet.storage.create_action(storage_args)

    reference = dcr.get("reference", "")
    tx, amount, pdi, _ = build_signable_transaction(dcr, args, wallet)

    return PendingSignAction(reference=reference, dcr=dcr, args=args, amount=amount, tx=tx, pdi=pdi)


def _make_signable_transaction_result(
    prior: PendingSignAction, wallet: Any, args: dict[str, Any]
) -> CreateActionResultX:
    """Make signable transaction result (TS parity - internal).

    Reference:
        - toolbox/ts-wallet-toolbox/src/signer/methods/createAction.ts
    """
    if not prior.dcr.get("input_beef"):
        raise WalletError("prior.dcr.input_beef must be valid")

    txid = prior.tx.id("hex")

    result = CreateActionResultX()
    result.no_send_change = (
        [f"{txid}.{vout}" for vout in prior.dcr.get("no_send_change_output_vouts", [])]
        if args.get("is_no_send")
        else None
    )
    result.signable_transaction = {
        "reference": prior.dcr.get("reference"),
        "tx": _make_signable_transaction_beef(prior.tx, prior.dcr.get("input_beef", [])),
    }

    wallet.pending_sign_actions[result.signable_transaction["reference"]] = prior

    return result


def _make_signable_transaction_beef(tx: Transaction, input_beef: bytes) -> bytes:
    """Make signable transaction BEEF (TS parity - internal).

    Reference:
        - toolbox/ts-wallet-toolbox/src/signer/methods/createAction.ts
    """
    beef = Beef()
    for input_data in tx.inputs:
        source_tx = input_data.get("source_transaction")
        if not source_tx:
            raise WalletError("Every signable_transaction input must have a source_transaction")
        beef.merge_raw_tx(source_tx.to_binary())

    beef.merge_raw_tx(tx.to_binary())
    return beef.to_binary_atomic(tx.id("hex"))


def _remove_unlock_scripts(args: dict[str, Any]) -> dict[str, Any]:
    """Remove unlocking scripts from args (TS parity - internal).

    Reference:
        - toolbox/ts-wallet-toolbox/src/signer/methods/createAction.ts
    """
    if all(inp.get("unlocking_script") is None for inp in args.get("inputs", [])):
        return args

    # Create new args without unlocking scripts
    new_inputs = []
    for inp in args.get("inputs", []):
        new_inp = dict(inp)
        if "unlocking_script" in new_inp:
            new_inp["unlocking_script_length"] = (
                len(new_inp["unlocking_script"])
                if new_inp.get("unlocking_script")
                else new_inp.get("unlocking_script_length", 0)
            )
            del new_inp["unlocking_script"]
        new_inputs.append(new_inp)

    return {**args, "inputs": new_inputs}


def _make_change_lock(
    out: dict[str, Any], dctr: dict[str, Any], args: dict[str, Any], change_keys: Any, wallet: Any
) -> Script:
    """Make change lock script (TS parity - internal).

    Reference:
        - toolbox/ts-wallet-toolbox/src/signer/methods/buildSignableTransaction.ts
    """
    # TODO: Implement ScriptTemplateBRC29 locking
    raise NotImplementedError("_make_change_lock not yet implemented")


def _verify_unlock_scripts(txid: str, beef: Beef) -> None:
    """Verify unlock scripts (TS parity - internal).

    Reference:
        - toolbox/ts-wallet-toolbox/src/signer/methods/completeSignedTransaction.ts
    """
    # TODO: Implement unlock script verification
    # This includes finding the transaction in beef, validating all inputs,
    # and checking that each unlocking script is valid for its corresponding output


def _merge_prior_options(ca_vargs: dict[str, Any], sa_args: dict[str, Any]) -> dict[str, Any]:
    """Merge prior create action options with sign action options (TS parity - internal).

    Reference:
        - toolbox/ts-wallet-toolbox/src/signer/methods/signAction.ts
    """
    result = dict(sa_args)

    sa_options = result.get("options", {})
    if not isinstance(sa_options, dict):
        sa_options = {}

    ca_options = ca_vargs.get("options", {})

    # Set defaults from create action options
    if "accept_delayed_broadcast" not in sa_options:
        sa_options["accept_delayed_broadcast"] = ca_options.get("accept_delayed_broadcast")
    if "return_txid_only" not in sa_options:
        sa_options["return_txid_only"] = ca_options.get("return_txid_only")
    if "no_send" not in sa_options:
        sa_options["no_send"] = ca_options.get("no_send")
    if "send_with" not in sa_options:
        sa_options["send_with"] = ca_options.get("send_with")

    result["options"] = sa_options
    return result


def _setup_wallet_payment_for_output(
    output_spec: dict[str, Any], tx: Transaction, wallet: Any, brc29_protocol_id: list[Any]
) -> None:
    """Setup wallet payment for output (TS parity - internal).

    Reference:
        - toolbox/ts-wallet-toolbox/src/signer/methods/internalizeAction.ts
    """
    payment_remittance = output_spec.get("payment_remittance")

    if not payment_remittance:
        raise WalletError("paymentRemittance is required for wallet payment protocol")

    # TODO: Implement key derivation and locking script validation
    # This requires KeyDeriver integration
    # output = tx.outputs[output_index]
    # derivation_prefix = payment_remittance.get("derivation_prefix", "")
    # derivation_suffix = payment_remittance.get("derivation_suffix", "")
    # key_id = f"{derivation_prefix} {derivation_suffix}"
    # sender_identity_key = payment_remittance.get("sender_identity_key", "")
    # priv_key = wallet.key_deriver.derive_private_key(
    #     brc29_protocol_id, key_id, sender_identity_key
    # )
    # expected_lock_script = P2PKH().lock(priv_key.to_address())
    # if output.locking_script.to_hex() != expected_lock_script.to_hex():
    #     raise WalletError("paymentRemittance must be locked by script conforming to BRC-29")
