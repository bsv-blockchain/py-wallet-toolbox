"""Validation utility functions for BRC-100 parameters.

Reference: toolbox/ts-wallet-toolbox/src/utility/utilityHelpers.ts
Reference: toolbox/go-wallet-toolbox/pkg/internal/validate/
"""

import base64
from typing import Any

from bsv_wallet_toolbox.errors import InvalidParameterError


def validate_originator(originator: str | None) -> None:
    """Validate originator parameter according to BRC-100 specifications.

    The originator parameter must be:
    - None (optional) or a string
    - At most 250 bytes in length when encoded as UTF-8

    Reference: toolbox/ts-wallet-toolbox/src/utility/utilityHelpers.ts
               function validateOriginator

    Args:
        originator: Originator domain name (optional)

    Raises:
        InvalidParameterError: If originator is invalid

    Example:
        >>> validate_originator(None)  # OK
        >>> validate_originator("example.com")  # OK
        >>> validate_originator("a" * 251)  # Raises InvalidParameterError
    """
    if originator is None:
        return

    if not isinstance(originator, str):
        raise InvalidParameterError("originator", "a string")

    # Check length in bytes (UTF-8 encoding)
    originator_bytes = originator.encode("utf-8")
    if len(originator_bytes) > 250:
        raise InvalidParameterError("originator", "at most 250 bytes in length")


def validate_basket_config(config: dict[str, Any]) -> None:
    """Validate BasketConfiguration according to BRC-100 specifications.

    BasketConfiguration must have:
    - name: non-empty string, at least 1 character and at most 300 bytes

    Reference: toolbox/go-wallet-toolbox/pkg/internal/validate/validate_basket_config.go
               ValidateBasketConfiguration

    Args:
        config: BasketConfiguration dict containing 'name' field

    Raises:
        InvalidParameterError: If basket configuration is invalid

    Example:
        >>> validate_basket_config({"name": "MyBasket"})  # OK
        >>> validate_basket_config({"name": ""})  # Raises InvalidParameterError
        >>> validate_basket_config({"name": "a" * 301})  # Raises InvalidParameterError
    """
    if "name" not in config:
        raise InvalidParameterError("name", "required in basket configuration")

    name = config["name"]

    if not isinstance(name, str):
        raise InvalidParameterError("name", "a string")

    # Check minimum length
    if len(name) < 1:
        raise InvalidParameterError("name", "at least 1 character in length")

    # Check maximum length in bytes (UTF-8 encoding)
    name_bytes = name.encode("utf-8")
    if len(name_bytes) > 300:
        raise InvalidParameterError("name", "no more than 300 bytes in length")


# ----------------------------------------------------------------------------
# ListOutputsArgs validation
# ----------------------------------------------------------------------------

_ALLOWED_TAG_QUERY_MODES = {"any", "all"}
_ALLOWED_LABEL_QUERY_MODES = {"any", "all", ""}

MAX_PAGINATION_LIMIT = 10_000
MAX_PAGINATION_OFFSET = 1_000_000


def _is_hex_string(value: str) -> bool:
    try:
        int(value, 16)
        return True
    except Exception:
        return False


def _is_base64_string(value: str) -> bool:
    try:
        # validate=True ensures character set and padding are checked
        base64.b64decode(value, validate=True)
        return True
    except Exception:
        return False


def validate_list_outputs_args(args: dict[str, Any]) -> None:
    """Validate ListOutputsArgs structure.

    Rules based on BRC-100 behavior and TS/Go toolboxes tests:
    - limit: optional; if present must be int and > 0
    - knownTxids: optional; if present must be a list of hex strings
    - tagQueryMode: optional; if present must be one of {"any", "all"}
    """
    if not isinstance(args, dict):
        raise InvalidParameterError("args", "a dict")

    # limit
    if "limit" in args:
        limit = args["limit"]
        if not isinstance(limit, int) or limit <= 0:
            raise InvalidParameterError("limit", "an integer greater than 0")

    # knownTxids
    if "knownTxids" in args:
        known_txids = args["knownTxids"]
        if not isinstance(known_txids, list):
            raise InvalidParameterError("knownTxids", "a list of hex txids")
        for txid in known_txids:
            if not isinstance(txid, str) or not _is_hex_string(txid):
                raise InvalidParameterError("txid", "a valid hexadecimal string")

    # tagQueryMode
    if "tagQueryMode" in args:
        mode = args["tagQueryMode"]
        if not isinstance(mode, str) or mode not in _ALLOWED_TAG_QUERY_MODES:
            raise InvalidParameterError("tagQueryMode", f"one of {_ALLOWED_TAG_QUERY_MODES}")


def validate_list_actions_args(args: dict[str, Any] | None) -> None:
    """Validate ListActionsArgs.

    - args must be dict
    - limit <= MAX_PAGINATION_LIMIT if present
    - offset <= MAX_PAGINATION_OFFSET if present
    - labelQueryMode in {"any","all",""} if present
    - seekPermission must not be False (default True)
    - labels: list[str], each label 1..300 chars
    """
    if args is None or not isinstance(args, dict):
        raise InvalidParameterError("args", "required and must be a dict")

    if "limit" in args:
        limit = args["limit"]
        if not isinstance(limit, int) or limit < 0 or limit > MAX_PAGINATION_LIMIT:
            raise InvalidParameterError("limit", f"must be 0..{MAX_PAGINATION_LIMIT}")

    if "offset" in args:
        offset = args["offset"]
        if not isinstance(offset, int) or offset < 0 or offset > MAX_PAGINATION_OFFSET:
            raise InvalidParameterError("offset", f"must be 0..{MAX_PAGINATION_OFFSET}")

    if "labelQueryMode" in args:
        lqm = args["labelQueryMode"]
        if not isinstance(lqm, str) or lqm not in _ALLOWED_LABEL_QUERY_MODES:
            raise InvalidParameterError("labelQueryMode", f"one of {_ALLOWED_LABEL_QUERY_MODES}")

    if args.get("seekPermission") is False:
        raise InvalidParameterError("seekPermission", "must be True")

    if "labels" in args:
        labels = args["labels"]
        if not isinstance(labels, list):
            raise InvalidParameterError("labels", "a list of strings")
        for label in labels:
            if not isinstance(label, str):
                raise InvalidParameterError("label", "a string")
            if len(label) == 0:
                raise InvalidParameterError("label", "must not be empty")
            if len(label) > 300:
                raise InvalidParameterError("label", "must be at most 300 characters")


def validate_list_certificates_args(args: dict[str, Any]) -> None:
    """Validate ListCertificatesArgs.

    - certifiers: optional list[str] of even-length hex strings
    - types: optional list[str] of base64 strings
    - limit: optional int <= MAX_PAGINATION_LIMIT
    - partial: optional object that may include certifier (hex), type (base64),
      serialNumber (base64), revocationOutpoint ("<txid>.<index>"), signature (base64), subject (string)
    """
    if not isinstance(args, dict):
        raise InvalidParameterError("args", "a dict")

    if "limit" in args:
        limit = args["limit"]
        if not isinstance(limit, int) or limit < 0 or limit > MAX_PAGINATION_LIMIT:
            raise InvalidParameterError("limit", f"must be 0..{MAX_PAGINATION_LIMIT}")

    if "certifiers" in args:
        certifiers = args["certifiers"]
        if not isinstance(certifiers, list):
            raise InvalidParameterError("certifiers", "a list of hex strings")
        for c in certifiers:
            if not isinstance(c, str) or (len(c) % 2 != 0) or not _is_hex_string(c):
                raise InvalidParameterError("certifier", "an even-length hexadecimal string")

    if "types" in args:
        types = args["types"]
        if not isinstance(types, list):
            raise InvalidParameterError("types", "a list of base64 strings")
        for t in types:
            if not isinstance(t, str) or not _is_base64_string(t):
                raise InvalidParameterError("type", "a base64 string")

    if "partial" in args and args["partial"] is not None:
        partial = args["partial"]
        if not isinstance(partial, dict):
            raise InvalidParameterError("partial", "a dict")
        if "certifier" in partial:
            c = partial["certifier"]
            if not isinstance(c, str) or not _is_hex_string(c):
                raise InvalidParameterError("certifier", "a hexadecimal string")
        if "type" in partial:
            t = partial["type"]
            if not isinstance(t, str) or not _is_base64_string(t):
                raise InvalidParameterError("type", "a base64 string")
        if "serialNumber" in partial:
            s = partial["serialNumber"]
            if not isinstance(s, str) or not _is_base64_string(s):
                raise InvalidParameterError("serialNumber", "a base64 string")
        if "revocationOutpoint" in partial:
            op = partial["revocationOutpoint"]
            if not isinstance(op, str) or "." not in op:
                raise InvalidParameterError("revocationOutpoint", "format '<txid>.<index>'")
            txid, _, index_str = op.partition(".")
            if not _is_hex_string(txid) or not index_str.isdigit():
                raise InvalidParameterError("revocationOutpoint", "format '<txid>.<index>'")


def validate_create_action_args(args: dict[str, Any]) -> dict[str, Any]:
    """Validate CreateActionArgs with full normalization.

    Reference: toolbox/ts-wallet-toolbox/src/sdk/validationHelpers.ts
               function validateCreateActionArgs

    Validates and normalizes CreateActionArgs with defaults:
    - description: 5-2000 bytes UTF-8
    - inputs: ValidCreateActionInput[] (each with outpoint, description, sequenceNumber)
    - outputs: ValidCreateActionOutput[] (each with lockingScript, satoshis, description)
    - lockTime: defaults to 0
    - version: defaults to 1
    - labels: optional string array
    - options: ValidCreateActionOptions with defaults
    - Computed flags: isSendWith, isRemixChange, isNewTx, isSignAction, isDelayed, isNoSend

    Args:
        args: CreateActionArgs dict

    Returns:
        Validated and normalized CreateActionArgs dict

    Raises:
        InvalidParameterError: If validation fails
    """
    if not isinstance(args, dict):
        raise InvalidParameterError("args", "a dict")

    # Validate description: 5-2000 bytes
    desc = args.get("description")
    if not isinstance(desc, str):
        raise InvalidParameterError("description", "a string")
    desc_bytes = desc.encode("utf-8")
    if len(desc_bytes) < 5 or len(desc_bytes) > 2000:
        raise InvalidParameterError("description", "5-2000 bytes UTF-8")

    # Validate outputs: non-empty list
    outputs = args.get("outputs", [])
    if not isinstance(outputs, list):
        raise InvalidParameterError("outputs", "a list")
    if len(outputs) == 0:
        raise InvalidParameterError("outputs", "at least one output required")

    for o in outputs:
        if not isinstance(o, dict):
            raise InvalidParameterError("outputs", "list of dicts")
        # lockingScript: even-length hex
        ls = o.get("lockingScript")
        if not isinstance(ls, str) or (len(ls) % 2 != 0) or not _is_hex_string(ls):
            raise InvalidParameterError("lockingScript", "an even-length hexadecimal string")
        # satoshis: integer >= 0
        sat = o.get("satoshis")
        if not isinstance(sat, int) or sat < 0:
            raise InvalidParameterError("satoshis", "an integer >= 0")
        # outputDescription: 5-2000 bytes
        out_desc = o.get("outputDescription", "")
        if isinstance(out_desc, str):
            out_desc_bytes = out_desc.encode("utf-8")
            if len(out_desc_bytes) < 5 or len(out_desc_bytes) > 2000:
                raise InvalidParameterError("outputDescription", "5-2000 bytes UTF-8")

    # Validate inputs if present
    inputs = args.get("inputs", [])
    if not isinstance(inputs, list):
        raise InvalidParameterError("inputs", "a list")

    # Normalize and compute flags
    vargs = {
        "description": desc,
        "inputBEEF": args.get("inputBEEF"),
        "inputs": inputs,
        "outputs": outputs,
        "lockTime": args.get("lockTime", 0),
        "version": args.get("version", 1),
        "labels": args.get("labels", []),
        "options": args.get("options", {}),
        "isSendWith": False,
        "isDelayed": False,
        "isNoSend": False,
        "isNewTx": False,
        "isRemixChange": False,
        "isSignAction": False,
    }

    # Compute flags
    opts = vargs.get("options", {})
    send_with = opts.get("sendWith", [])
    vargs["isSendWith"] = len(send_with) > 0 if isinstance(send_with, list) else False
    vargs["isRemixChange"] = not vargs["isSendWith"] and len(inputs) == 0 and len(outputs) == 0
    vargs["isNewTx"] = vargs["isRemixChange"] or len(inputs) > 0 or len(outputs) > 0
    vargs["isDelayed"] = opts.get("acceptDelayedBroadcast", True)
    vargs["isNoSend"] = opts.get("noSend", False)

    return vargs


def validate_abort_action_args(args: dict[str, Any] | None) -> dict[str, Any]:
    """Validate AbortActionArgs.

    Reference: toolbox/ts-wallet-toolbox/src/sdk/validationHelpers.ts
               function validateAbortActionArgs

    Args:
        args: AbortActionArgs dict with 'reference' (base64 string)

    Returns:
        Validated AbortActionArgs dict

    Raises:
        InvalidParameterError: If validation fails
    """
    if args is None or not isinstance(args, dict):
        raise InvalidParameterError("args", "required")
    ref = args.get("reference")
    if not isinstance(ref, str) or len(ref) == 0:
        raise InvalidParameterError("reference", "a non-empty base64 string")
    # Basic base64 validation: characters and length divisible by 4
    if len(ref) % 4 != 0 or not _is_base64_string(ref):
        raise InvalidParameterError("reference", "a valid base64 string (length divisible by 4)")

    return {"reference": ref}


def validate_internalize_action_args(args: dict[str, Any]) -> dict[str, Any]:
    """Validate InternalizeActionArgs.

    Reference: toolbox/ts-wallet-toolbox/src/sdk/validationHelpers.ts
               function validateInternalizeActionArgs

    Args:
        args: InternalizeActionArgs dict

    Returns:
        Validated InternalizeActionArgs dict

    Raises:
        InvalidParameterError: If validation fails
    """
    if not isinstance(args, dict):
        raise InvalidParameterError("args", "a dict")

    # Validate tx: BEEF binary data
    tx = args.get("tx")
    if not isinstance(tx, (bytes, bytearray)) or len(tx) == 0:
        raise InvalidParameterError("tx", "non-empty bytes")

    # Validate outputs: non-empty list
    outputs = args.get("outputs")
    if not isinstance(outputs, list) or len(outputs) == 0:
        raise InvalidParameterError("outputs", "a non-empty list")

    # Validate description: 5-2000 bytes
    desc = args.get("description")
    if not isinstance(desc, str):
        raise InvalidParameterError("description", "a string")
    desc_bytes = desc.encode("utf-8")
    if len(desc_bytes) < 5 or len(desc_bytes) > 2000:
        raise InvalidParameterError("description", "5-2000 bytes UTF-8")

    # Validate labels if present
    labels = args.get("labels", [])
    if labels is not None:
        if not isinstance(labels, list):
            raise InvalidParameterError("labels", "a list of strings")
        for label in labels:
            if not isinstance(label, str):
                raise InvalidParameterError("label", "a string")
            label_bytes = label.encode("utf-8")
            if len(label_bytes) > 300:
                raise InvalidParameterError("label", "must be <= 300 bytes")

    # Validate each output
    for o in outputs:
        if not isinstance(o, dict):
            raise InvalidParameterError("outputs", "list of dicts")

        # protocol: required, must be one of the known types
        protocol = o.get("protocol")
        if not isinstance(protocol, str) or len(protocol) == 0:
            raise InvalidParameterError("protocol", "a non-empty string")

        if protocol == "wallet payment":
            remit = o.get("paymentRemittance")
            if not isinstance(remit, dict):
                raise InvalidParameterError("paymentRemittance", "required for wallet payment")
            dp = remit.get("derivationPrefix")
            ds = remit.get("derivationSuffix")
            if not isinstance(dp, str) or not _is_base64_string(dp):
                raise InvalidParameterError("paymentRemittance", "derivationPrefix must be base64")
            if not isinstance(ds, str) or not _is_base64_string(ds):
                raise InvalidParameterError("paymentRemittance", "derivationSuffix must be base64")

    return {
        "tx": tx,
        "outputs": outputs,
        "description": desc,
        "labels": labels if labels else [],
        "seekPermission": args.get("seekPermission", True),
    }


def validate_relinquish_output_args(args: dict[str, Any]) -> dict[str, Any]:
    """Validate RelinquishOutputArgs.

    Reference: toolbox/ts-wallet-toolbox/src/sdk/validationHelpers.ts
               function validateRelinquishOutputArgs

    Args:
        args: RelinquishOutputArgs dict

    Returns:
        Validated RelinquishOutputArgs dict

    Raises:
        InvalidParameterError: If validation fails
    """
    if not isinstance(args, dict):
        raise InvalidParameterError("args", "a dict")

    # Validate outpoint format: "txid.index"
    out = args.get("output")
    if not isinstance(out, str) or len(out) == 0:
        raise InvalidParameterError("output", "required outpoint 'txid.index'")
    if "." not in out:
        raise InvalidParameterError("outpoint", "format '<txid>.<index>'")
    txid, _, idx = out.partition(".")
    if not _is_hex_string(txid) or not idx.isdigit():
        raise InvalidParameterError("outpoint", "format '<txid>.<index>'")

    # Validate basket: optional string, max 300 chars
    basket = args.get("basket", "")
    if not isinstance(basket, str):
        raise InvalidParameterError("basket", "a string")
    basket_bytes = basket.encode("utf-8")
    if len(basket_bytes) > 300:
        raise InvalidParameterError("basket", "must be <= 300 bytes")

    return {
        "basket": basket,
        "output": f"{txid}.{idx}",
    }


def validate_insert_certificate_auth_args(args: dict[str, Any]) -> dict[str, Any]:
    """Validate InsertCertificateAuthArgs.

    Reference: TableCertificateX certificate insertion validation

    Args:
        args: InsertCertificateAuthArgs dict

    Returns:
        Validated InsertCertificateAuthArgs dict

    Raises:
        InvalidParameterError: If validation fails
    """
    if not isinstance(args, dict):
        raise InvalidParameterError("args", "a dict")

    def _require_even_hex(field: str) -> str:
        v = args.get(field)
        if not isinstance(v, str) or (len(v) % 2 != 0) or not _is_hex_string(v):
            raise InvalidParameterError(field, "an even-length hexadecimal string")
        return v

    # Validate type: even-length hex
    cert_type = _require_even_hex("type")

    # Validate serialNumber: base64
    sn = args.get("serialNumber")
    if not isinstance(sn, str) or not _is_base64_string(sn):
        raise InvalidParameterError("serialNumber", "a base64 string")

    # Validate certifier: non-empty even-length hex, max 300 chars
    certifier = args.get("certifier")
    if (
        not isinstance(certifier, str)
        or len(certifier) == 0
        or len(certifier) > 300
        or (len(certifier) % 2 != 0)
        or not _is_hex_string(certifier)
    ):
        raise InvalidParameterError(
            "certifier",
            "a non-empty even-length hexadecimal string up to 300 chars",
        )

    # Validate subject: non-empty string
    subject = args.get("subject")
    if not isinstance(subject, str) or len(subject) == 0:
        raise InvalidParameterError("subject", "a non-empty string")

    # Validate signature: even-length hex
    signature = _require_even_hex("signature")

    # Validate fields: list of dicts with masterKey (even-length hex)
    fields = args.get("fields", [])
    if not isinstance(fields, list):
        raise InvalidParameterError("fields", "a list")
    for f in fields:
        if not isinstance(f, dict):
            raise InvalidParameterError("fields", "list of dicts")
        mk = f.get("masterKey")
        if not isinstance(mk, str) or (len(mk) % 2 != 0) or not _is_hex_string(mk):
            raise InvalidParameterError("masterKey", "an even-length hexadecimal string")

    # Validate revocationOutpoint: format "txid.index"
    ro = args.get("revocationOutpoint")
    if not isinstance(ro, str) or "." not in ro:
        raise InvalidParameterError("revocationOutpoint", "format '<txid>.<index>'")
    rtxid, _, ridx = ro.partition(".")
    if not _is_hex_string(rtxid) or not ridx.isdigit():
        raise InvalidParameterError("revocationOutpoint", "format '<txid>.<index>'")

    return {
        "type": cert_type,
        "serialNumber": sn,
        "certifier": certifier,
        "subject": subject,
        "signature": signature,
        "fields": fields,
        "revocationOutpoint": f"{rtxid}.{ridx}",
    }


def validate_relinquish_certificate_args(args: dict[str, Any]) -> dict[str, Any]:
    """Validate RelinquishCertificateArgs.

    Reference: toolbox/ts-wallet-toolbox/src/sdk/validationHelpers.ts
               function validateRelinquishCertificateArgs

    - type: base64
    - serialNumber: base64
    - certifier: non-empty even-length hex string

    Args:
        args: RelinquishCertificateArgs dict

    Returns:
        Validated RelinquishCertificateArgs dict

    Raises:
        InvalidParameterError: If validation fails
    """
    if not isinstance(args, dict):
        raise InvalidParameterError("args", "a dict")

    # Validate type: base64
    t = args.get("type")
    if not isinstance(t, str) or not _is_base64_string(t):
        raise InvalidParameterError("type", "a base64 string")

    # Validate serialNumber: base64
    s = args.get("serialNumber")
    if not isinstance(s, str) or not _is_base64_string(s):
        raise InvalidParameterError("serialNumber", "a base64 string")

    # Validate certifier: non-empty even-length hex
    c = args.get("certifier")
    if not isinstance(c, str) or len(c) == 0 or (len(c) % 2 != 0) or not _is_hex_string(c):
        raise InvalidParameterError("certifier", "a non-empty even-length hexadecimal string")

    return {
        "type": t,
        "serialNumber": s,
        "certifier": c,
    }


def validate_request_sync_chunk_args(args: dict[str, Any]) -> None:
    """Validate RequestSyncChunkArgs.

    Required non-empty strings: fromStorageIdentityKey, toStorageIdentityKey, identityKey
    Positive integers: maxRoughSize (>0), maxItems (>0)
    Optional: since (datetime), offsets (list of {name: str, offset: int>=0})
    """
    if not isinstance(args, dict):
        raise InvalidParameterError("args", "a dict")
    for key in ("fromStorageIdentityKey", "toStorageIdentityKey", "identityKey"):
        v = args.get(key)
        if not isinstance(v, str) or len(v) == 0:
            raise InvalidParameterError(key, "a non-empty string")
    for key in ("maxRoughSize", "maxItems"):
        v = args.get(key)
        if not isinstance(v, int) or v <= 0:
            raise InvalidParameterError(key, "an integer greater than 0")
    if "offsets" in args and args["offsets"] is not None:
        offsets = args["offsets"]
        if not isinstance(offsets, list):
            raise InvalidParameterError("offsets", "a list")
        for item in offsets:
            if not isinstance(item, dict):
                raise InvalidParameterError("offsets", "list of dicts")
            name = item.get("name")
            off = item.get("offset")
            if not isinstance(name, str) or not isinstance(off, int) or off < 0:
                raise InvalidParameterError("offsets", "each item requires name:str and offset:int>=0")


def validate_process_action_args(args: dict[str, Any]) -> None:
    """Validate ProcessActionArgs.

    - txid: if present, must be 64-char hex
    - if isNewTx is True: require reference (str), rawTx (bytes|bytearray), txid (str)
    - if isSendWith is True: require sendWith (not None)
    """
    if not isinstance(args, dict):
        raise InvalidParameterError("args", "a dict")
    if "txid" in args and args.get("txid") is not None:
        txid = args["txid"]
        if not isinstance(txid, str) or len(txid) != 64 or not _is_hex_string(txid):
            raise InvalidParameterError("txid", "a 64-character hexadecimal string")
    if args.get("isNewTx"):
        ref = args.get("reference")
        if not isinstance(ref, str) or len(ref) == 0:
            raise InvalidParameterError("reference", "required when isNewTx is True")
        raw_tx = args.get("rawTx")
        if raw_tx is None:
            raise InvalidParameterError("rawTx", "required when isNewTx is True")
        txid = args.get("txid")
        if not isinstance(txid, str) or len(txid) == 0:
            raise InvalidParameterError("txid", "required when isNewTx is True")
    if args.get("isSendWith"):
        if args.get("sendWith") is None:
            raise InvalidParameterError("sendWith", "required when isSendWith is True")


def validate_no_send_change_outputs(outputs: list[dict[str, Any]]) -> None:
    """Validate outputs used for no-send change selection.

    Rules per tests:
    - outputs may be empty (no error)
    - for each output: providedBy == 'storage', purpose == 'change', basketName == 'change basket' and not None
    """
    if not isinstance(outputs, list):
        raise InvalidParameterError("outputs", "a list of outputs")
    for o in outputs:
        if not isinstance(o, dict):
            raise InvalidParameterError("outputs", "a list of dicts")
        if o.get("providedBy") != "storage":
            raise InvalidParameterError("providedBy", "must equal 'storage'")
        if o.get("purpose") != "change":
            raise InvalidParameterError("purpose", "must equal 'change'")
        basket_name = o.get("basketName")
        if basket_name is None or basket_name != "change basket":
            raise InvalidParameterError("basketName", "must equal 'change basket'")


def validate_sign_action_args(args: dict[str, Any]) -> None:
    """Validate SignActionArgs for Wave 4 Transaction Operations.

    Required parameters:
        - reference: non-empty string (unique action reference from createAction)
        - rawTx: non-empty string (signed raw transaction in hex or binary)

    Optional parameters:
        - isNewTx: bool - whether transaction is new
        - isSendWith: bool - whether to send with other transactions
        - isNoSend: bool - whether to suppress network broadcast
        - isDelayed: bool - whether to accept delayed broadcast
        - sendWith: list of strings - transaction IDs to send with

    Reference: toolbox/ts-wallet-toolbox/src/Wallet.ts (signAction)
    """
    if not isinstance(args, dict):
        raise InvalidParameterError("args", "a dict")

    # Validate reference (required, non-empty string)
    reference = args.get("reference")
    if not isinstance(reference, str) or len(reference) == 0:
        raise InvalidParameterError("reference", "a non-empty string")

    # Validate rawTx (required, non-empty string)
    raw_tx = args.get("rawTx")
    if not isinstance(raw_tx, str) or len(raw_tx) == 0:
        raise InvalidParameterError("rawTx", "a non-empty string")

    # Optional boolean fields
    for key in ("isNewTx", "isSendWith", "isNoSend", "isDelayed"):
        if key in args and not isinstance(args[key], bool):
            raise InvalidParameterError(key, "a boolean value")
