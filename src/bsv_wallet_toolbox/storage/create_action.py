"""CreateAction storage helpers (TypeScript parity).

Summary:
    Implements the heavy lifting for `StorageProvider.create_action`, mirroring
    the behaviour of the TypeScript module at
    `toolbox/ts-wallet-toolbox/src/storage/methods/createAction.ts`. The
    helpers in this file normalise input arguments, derive intermediate
    structures (`XInput`, `XOutput`), and support commission/service-charge
    output generation.

Reference:
    - toolbox/ts-wallet-toolbox/src/storage/methods/createAction.ts
"""

from __future__ import annotations

import base64
import hashlib
import secrets
from dataclasses import dataclass, field
from typing import Any

from bsv.keys import PrivateKey, PublicKey, curve, curve_add, curve_multiply
from bsv.script.type import P2PKH
from bsv.transaction import Beef, parse_beef_ex

from bsv_wallet_toolbox.utils.validation import InvalidParameterError


@dataclass
class CreateActionOptions:
    """Normalised createAction options (TS parity).

    Summary:
        Mirrors `ValidCreateActionOptions` from the TypeScript validation layer,
        capturing option defaults after normalisation.

    Reference:
        - toolbox/ts-wallet-toolbox/src/sdk/validationHelpers.ts
    """

    randomize_outputs: bool = False
    sign_and_process: bool = False
    no_send: bool = False
    no_send_change: list[dict[str, Any]] = field(default_factory=list)
    known_txids: list[str] = field(default_factory=list)
    return_txid_only: bool = False
    trust_self: str = "unknown"
    accept_delayed_broadcast: bool = True
    send_with: list[str] = field(default_factory=list)
    include_all_source_transactions: bool = False


@dataclass
class NormalizedCreateActionArgs:
    """Container for validated createAction arguments.

    Summary:
        Synchronous equivalent of the TS `ValidCreateActionArgs` structure with
        additional convenience flags consumed by storage helpers.

    Reference:
        - toolbox/ts-wallet-toolbox/src/sdk/validationHelpers.ts
    """

    description: str
    inputs: list[dict[str, Any]]
    outputs: list[dict[str, Any]]
    labels: list[str]
    lock_time: int
    version: int
    options: CreateActionOptions
    random_vals: list[float]
    input_beef: Beef | None
    input_beef_bytes: bytes | None
    is_send_with: bool
    is_remix_change: bool
    is_new_tx: bool
    is_sign_action: bool
    is_delayed: bool
    is_no_send: bool


@dataclass
class XInput:
    """Extended input information after validation (TS `XValidCreateActionInput`).

    Reference:
        - toolbox/ts-wallet-toolbox/src/storage/methods/createAction.ts
    """

    vin: int
    satoshis: int
    locking_script: bytes
    output: dict[str, Any] | None
    unlocking_script_length: int | None
    input_description: str | None
    outpoint: dict[str, Any]


@dataclass
class XOutput:
    """Extended output information (TS `XValidCreateActionOutput`).

    Reference:
        - toolbox/ts-wallet-toolbox/src/storage/methods/createAction.ts
    """

    vout: int
    satoshis: int
    locking_script: bytes
    output_description: str | None
    basket: str | None
    tags: list[str]
    provided_by: str = "you"
    purpose: str | None = None
    derivation_suffix: str | None = None
    key_offset: str | None = None
    custom_instructions: str | None = None


def _ensure_even_hex(value: str, field: str) -> None:
    """Validate that a value is an even-length hexadecimal string."""
    if not isinstance(value, str) or len(value) % 2 != 0:
        raise InvalidParameterError(field, "an even-length hexadecimal string")
    try:
        bytes.fromhex(value)
    except ValueError as exc:
        raise InvalidParameterError(field, "an even-length hexadecimal string") from exc


def _ensure_base64(value: str, field: str) -> None:
    """Validate that a value is valid base64 (TS parity helper)."""
    try:
        base64.b64decode(value, validate=True)
    except Exception as exc:  # pragma: no cover
        raise InvalidParameterError(field, "a base64 string") from exc


def normalize_create_action_args(args: dict[str, Any]) -> NormalizedCreateActionArgs:
    """Validate and normalise createAction arguments (TS parity).

    Summary:
        Applies the same validation rules as TS `validateCreateActionArgs`,
        materialising defaults and derived boolean flags used by the storage
        pipeline.

    Args:
        args: Raw `create_action` payload from the wallet layer.

    Returns:
        `NormalizedCreateActionArgs` instance with parsed BEEF (if present).

    Raises:
        InvalidParameterError: If any field fails validation.

    Reference:
        - toolbox/ts-wallet-toolbox/src/sdk/validationHelpers.ts
        - toolbox/ts-wallet-toolbox/src/storage/methods/createAction.ts
    """
    if not isinstance(args, dict):
        raise InvalidParameterError("args", "a dict")

    description = args.get("description")
    if not isinstance(description, str) or len(description) < 1:
        raise InvalidParameterError("description", "a non-empty string")

    outputs = list(args.get("outputs") or [])
    if not outputs:
        raise InvalidParameterError("outputs", "a non-empty list")

    labels = list(args.get("labels") or [])
    inputs = list(args.get("inputs") or [])

    options_dict = dict(args.get("options") or {})
    trust_self_raw = options_dict.get("trustSelf")
    # TS parity: TrustSelf is "known" or undefined. (Never boolean.)
    if isinstance(trust_self_raw, bool):
        trust_self_raw = "known" if trust_self_raw else None
    options = CreateActionOptions(
        randomize_outputs=bool(options_dict.get("randomizeOutputs", False)),
        sign_and_process=bool(options_dict.get("signAndProcess", False)),
        no_send=bool(options_dict.get("noSend", False)),
        no_send_change=_normalize_no_send_change(options_dict.get("noSendChange")),
        known_txids=list(options_dict.get("knownTxids") or []),
        return_txid_only=bool(options_dict.get("returnTXIDOnly", False)),
        trust_self="known" if trust_self_raw == "known" else "",
        accept_delayed_broadcast=bool(options_dict.get("acceptDelayedBroadcast", True)),
        send_with=list(options_dict.get("sendWith") or []),
        include_all_source_transactions=bool(options_dict.get("includeAllSourceTransactions", False)),
    )

    normalized_outputs: list[dict[str, Any]] = []
    for output in outputs:
        if not isinstance(output, dict):
            raise InvalidParameterError("outputs", "list of dicts")
        locking_script = output.get("lockingScript")
        if not isinstance(locking_script, str) or len(locking_script) % 2 != 0:
            raise InvalidParameterError("lockingScript", "an even-length hexadecimal string")
        try:
            bytes.fromhex(locking_script)
        except ValueError as exc:
            raise InvalidParameterError("lockingScript", "an even-length hexadecimal string") from exc
        satoshis = output.get("satoshis")
        if not isinstance(satoshis, int) or satoshis < 0:
            raise InvalidParameterError("satoshis", "an integer >= 0")

        normalized_outputs.append(output)

    random_vals = list(args.get("randomVals") or [])
    lock_time = int(args.get("lockTime", 0) or 0)
    version = int(args.get("version", 2) or 2)

    input_beef_bytes: bytes | None = None
    input_beef_obj: Beef | None = None
    raw_input_beef = args.get("inputBEEF")
    if raw_input_beef is not None:
        if isinstance(raw_input_beef, (bytes, bytearray)):
            input_beef_bytes = bytes(raw_input_beef)
        elif isinstance(raw_input_beef, str):
            try:
                input_beef_bytes = base64.b64decode(raw_input_beef, validate=True)
            except Exception as exc:  # pragma: no cover
                raise InvalidParameterError("inputBEEF", "bytes or base64 string") from exc
        elif isinstance(raw_input_beef, list):
            try:
                input_beef_bytes = bytes(int(x) & 0xFF for x in raw_input_beef)
            except Exception as exc:
                raise InvalidParameterError("inputBEEF", "list of integers") from exc
        else:
            raise InvalidParameterError("inputBEEF", "bytes-compatible value")

        try:
            input_beef_obj, _, _ = parse_beef_ex(input_beef_bytes)
        except Exception as exc:
            raise InvalidParameterError("inputBEEF", "valid Beef encoding") from exc

    is_send_with = len(options.send_with) > 0
    is_remix_change = (not is_send_with) and len(inputs) == 0 and len(outputs) == 0
    is_new_tx = is_remix_change or len(inputs) > 0 or len(outputs) > 0

    any_missing_unlock = any(
        isinstance(inp, dict) and (inp.get("unlockingScript") is None and inp.get("unlockingScript") is None)
        for inp in inputs
    )
    is_sign_action = is_new_tx and (not options.sign_and_process or any_missing_unlock)
    is_delayed = options.accept_delayed_broadcast
    is_no_send = options.no_send

    return NormalizedCreateActionArgs(
        description=description,
        inputs=inputs,
        outputs=normalized_outputs,
        labels=labels,
        lock_time=lock_time,
        version=version,
        options=options,
        random_vals=random_vals,
        input_beef=input_beef_obj,
        input_beef_bytes=input_beef_bytes,
        is_send_with=is_send_with,
        is_remix_change=is_remix_change,
        is_new_tx=is_new_tx,
        is_sign_action=is_sign_action,
        is_delayed=is_delayed,
        is_no_send=is_no_send,
    )


def _normalize_no_send_change(value: Any) -> list[dict[str, Any]]:
    """Convert noSendChange option to canonical list of dicts.

    Summary:
        Accepts string outpoints or dict structures and produces the uniform
        representation used downstream.

    Args:
        value: Raw `noSendChange` option value.

    Returns:
        List of dicts with keys `txid`/`vout`.

    Raises:
        InvalidParameterError: If entries are malformed.

    Reference:
        - toolbox/ts-wallet-toolbox/src/storage/methods/createAction.ts
    """
    if value is None:
        return []
    if isinstance(value, list):
        result = []
        for item in value:
            if isinstance(item, str):
                txid, _, vout = item.partition(".")
                _ensure_even_hex(txid, "noSendChange")
                if not vout.isdigit():
                    raise InvalidParameterError("noSendChange", "format '<txid>.<index>'")
                result.append({"txid": txid, "vout": int(vout)})
            elif isinstance(item, dict):
                txid = item.get("txid")
                vout = item.get("vout")
                if not isinstance(txid, str) or not isinstance(vout, int):
                    raise InvalidParameterError("noSendChange", "dict with txid/vout")
                _ensure_even_hex(txid, "noSendChange")
                result.append({"txid": txid, "vout": vout})
            else:
                raise InvalidParameterError("noSendChange", "list of outpoints")

        # Check for duplicates (TS/Go parity)
        seen_outpoints = set()
        for item in result:
            outpoint = f"{item['txid']}.{item['vout']}"
            if outpoint in seen_outpoints:
                raise InvalidParameterError("noSendChange", "contains duplicate outpoints")
            seen_outpoints.add(outpoint)

        return result
    raise InvalidParameterError("noSendChange", "list")


def generate_reference() -> str:
    """Generate random reference string (TS parity randomBytesBase64).

    Reference:
        - toolbox/ts-wallet-toolbox/src/utility/utilityHelpers.ts (randomBytesBase64)
    """
    return base64.b64encode(secrets.token_bytes(9)).decode("ascii")


def deterministic_txid(reference: str, outputs: list[dict[str, Any]]) -> str:
    """Derive deterministic txid placeholder for repeatable testing.

    Summary:
        Emulates the TS helper used for deterministic `createAction`
        integration tests when real signing is absent.

    Args:
        reference: Reference string.
        outputs: Output list used to derive a hash.

    Returns:
        Hex string representing a pseudo txid.

    Reference:
        - toolbox/ts-wallet-toolbox/src/storage/methods/createAction.ts (test utility)
    """
    digest = hashlib.sha256()
    digest.update(reference.encode("utf-8"))
    for output in outputs:
        locking = output.get("lockingScript", "")
        satoshis = output.get("satoshis", 0)
        digest.update(locking.encode("utf-8"))
        digest.update(str(satoshis).encode("utf-8"))
    return digest.hexdigest()


def validate_required_outputs(
    storage: Any,
    user_id: int,
    vargs: NormalizedCreateActionArgs,
) -> list[XOutput]:
    """Validate outputs and append storage commission output when required.

    Summary:
        Converts normalised outputs into `XOutput` instances and, if the storage
        provider is configured with a commission, appends the service-charge
        output using the same logic as TS.

    Args:
        storage: Storage provider instance (used for commission settings).
        user_id: Current user id (unused placeholder for future parity).
        vargs: Normalised createAction arguments.

    Returns:
        List of `XOutput` structures ready for funding logic.

    Reference:
        - toolbox/ts-wallet-toolbox/src/storage/methods/createAction.ts
    """
    xoutputs: list[XOutput] = []
    for idx, output in enumerate(vargs.outputs):
        locking_script_hex = output.get("lockingScript")
        satoshis = int(output.get("satoshis", 0))
        output_description = output.get("outputDescription")
        basket = output.get("basket")
        custom_instructions = output.get("customInstructions")
        tags = list(output.get("tags") or [])

        xoutputs.append(
            XOutput(
                vout=idx,
                satoshis=satoshis,
                locking_script=bytes.fromhex(locking_script_hex),
                output_description=output_description,
                basket=basket,
                tags=tags,
                provided_by="you",
                purpose=None,
                derivation_suffix=None,
                key_offset=None,
                custom_instructions=custom_instructions,
            )
        )

    commission_satoshis = int(getattr(storage, "commission_satoshis", getattr(storage, "commissionSatoshis", 0)) or 0)
    commission_pub_key_hex = getattr(
        storage,
        "commission_pub_key_hex",
        getattr(storage, "commissionPubKeyHex", None),
    )

    if commission_satoshis > 0 and commission_pub_key_hex:
        script_hex, key_offset = create_storage_service_charge_script(commission_pub_key_hex)
        xoutputs.append(
            XOutput(
                vout=len(xoutputs),
                satoshis=commission_satoshis,
                locking_script=bytes.fromhex(script_hex),
                output_description="Storage Service Charge",
                basket=None,
                tags=[],
                provided_by="storage",
                purpose="service-charge",
                derivation_suffix=None,
                key_offset=key_offset,
                custom_instructions=None,
            )
        )

    return xoutputs


def key_offset_to_hashed_secret(pub: PublicKey, key_offset: str | None = None) -> tuple[int, str]:
    """Derive hashed secret scalar used for commission key offsetting.

    Summary:
        Matches TS logic which produces a deterministic scalar and optional
        offset key for service charge outputs.

    Args:
        pub: Recipient public key.
        key_offset: Optional existing offset (WIF or hex).

    Returns:
        Tuple of (hashed secret scalar, key offset string).

    Reference:
        - toolbox/ts-wallet-toolbox/src/storage/methods/createAction.ts
    """
    if key_offset is not None:
        offset: PrivateKey
        if len(key_offset) == 64:
            offset = PrivateKey.from_hex(key_offset)
        else:
            offset = PrivateKey(key_offset)
    else:
        offset = PrivateKey()
        key_offset = offset.wif()

    shared_secret = pub.derive_shared_secret(offset)
    hashed_secret = hashlib.sha256(shared_secret).digest()
    hashed_int = int.from_bytes(hashed_secret, "big") % curve.n
    if hashed_int == 0:
        hashed_int = 1
    return hashed_int, key_offset


def offset_pub_key(pub_key_hex: str, key_offset: str | None = None) -> tuple[str, str]:
    """Offset a public key using hashed secret (TS parity helper).

    Args:
        pub_key_hex: Recipient public key hex.
        key_offset: Optional pre-selected offset.

    Returns:
        Tuple of (offset public key hex, key offset string).

    Reference:
        - toolbox/ts-wallet-toolbox/src/storage/methods/createAction.ts
    """
    pub = PublicKey(pub_key_hex)
    hashed_int, derived_key_offset = key_offset_to_hashed_secret(pub, key_offset)
    point = curve_add(pub.point(), curve_multiply(hashed_int, curve.g))
    offset_pub = PublicKey(point)
    return offset_pub.hex(), derived_key_offset


def create_storage_service_charge_script(pub_key_hex: str) -> tuple[str, str]:
    """Create service charge locking script and key offset (TS parity).

    Args:
        pub_key_hex: Commission public key hex.

    Returns:
        Tuple of (locking script hex, key offset string).

    Reference:
        - toolbox/ts-wallet-toolbox/src/storage/methods/createAction.ts
    """
    offset_hex, key_offset = offset_pub_key(pub_key_hex)
    offset_pub = PublicKey(offset_hex)
    script_obj = P2PKH().lock(offset_pub.address())
    return script_obj.hex(), key_offset
