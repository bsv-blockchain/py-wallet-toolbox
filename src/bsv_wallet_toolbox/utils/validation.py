"""Validation utility functions for BRC-100 parameters.

Reference: toolbox/ts-wallet-toolbox/src/utility/utilityHelpers.ts
Reference: toolbox/go-wallet-toolbox/pkg/internal/validate/
"""

import base64
from typing import Any

from bsv_wallet_toolbox.errors import InvalidParameterError
from bsv_wallet_toolbox.utils.satoshi import satoshi_from


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
    - basket: optional; if present must be non-empty string (1-300 chars)
    - tags: optional; if present must be list of non-empty strings (each 1-300 chars)
    - limit: optional; if present must be int 1-10000, default 10
    - offset: optional; can be any integer (negative = newest first)
    - knownTxids: optional; if present must be a list of hex strings
    - tagQueryMode: optional; if present must be one of {"any", "all"}

    Reference: wallet-toolbox/src/sdk/validationHelpers.ts - validateListOutputsArgs
    """
    if not isinstance(args, dict):
        raise InvalidParameterError("args", "a dict")

    # basket - must be non-empty, non-whitespace if present
    if "basket" in args:
        basket = args["basket"]
        if not isinstance(basket, str):
            raise InvalidParameterError("basket", "a string")
        if len(basket.strip()) == 0:
            raise InvalidParameterError("basket", "a non-empty string (1-300 characters)")
        if len(basket) > 300:
            raise InvalidParameterError("basket", "at most 300 characters")

    # tags - each must be non-empty, non-whitespace if present
    if "tags" in args:
        tags = args["tags"]
        if not isinstance(tags, list):
            raise InvalidParameterError("tags", "a list of strings")
        for i, tag in enumerate(tags):
            if not isinstance(tag, str):
                raise InvalidParameterError(f"tags[{i}]", "a string")
            if len(tag.strip()) == 0:
                raise InvalidParameterError(f"tags[{i}]", "a non-empty string (1-300 characters)")
            if len(tag) > 300:
                raise InvalidParameterError(f"tags[{i}]", "at most 300 characters")

    # limit - must be 1-10000 if present
    if "limit" in args:
        limit = args["limit"]
        if not isinstance(limit, int) or isinstance(limit, bool):
            raise InvalidParameterError("limit", "an integer")
        if limit <= 0:
            raise InvalidParameterError("limit", "greater than 0")
        if limit > 10000:
            raise InvalidParameterError("limit", "at most 10000")

    # offset - must be non-negative integer if present
    if "offset" in args:
        offset = args["offset"]
        if not isinstance(offset, int) or isinstance(offset, bool):
            raise InvalidParameterError("offset", "an integer")
        # Negative offsets are allowed (negative = newest first), per docstring.

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
    - labels: list[str], each label 1..300 chars, not whitespace-only
    - includeLabels: boolean if present
    """
    if args is None or not isinstance(args, dict):
        raise InvalidParameterError("args", "required and must be a dict")

    if "limit" in args:
        limit = args["limit"]
        if not isinstance(limit, int) or limit < 0 or limit > MAX_PAGINATION_LIMIT:
            raise InvalidParameterError("limit", f"must be 0..{MAX_PAGINATION_LIMIT}")

    if "offset" in args:
        offset = args["offset"]
        if not isinstance(offset, int) or isinstance(offset, bool):
            raise InvalidParameterError("offset", "an integer")
        # Negative offsets are allowed (negative = newest first)
        if offset > MAX_PAGINATION_OFFSET:
            raise InvalidParameterError("offset", f"must be <= {MAX_PAGINATION_OFFSET}")

    if "labelQueryMode" in args:
        lqm = args["labelQueryMode"]
        if not isinstance(lqm, str) or lqm not in _ALLOWED_LABEL_QUERY_MODES:
            raise InvalidParameterError("labelQueryMode", f"one of {_ALLOWED_LABEL_QUERY_MODES}")

    if args.get("seekPermission") is False:
        raise InvalidParameterError("seekPermission", "must be True")

    if "includeLabels" in args:
        include_labels = args["includeLabels"]
        if not isinstance(include_labels, bool):
            raise InvalidParameterError("includeLabels", "a boolean")

    if "labels" in args:
        labels = args["labels"]
        if not isinstance(labels, list):
            raise InvalidParameterError("labels", "a list of strings")
        for label in labels:
            if not isinstance(label, str):
                raise InvalidParameterError("label", "a string")
            if len(label.strip()) == 0:
                raise InvalidParameterError("label", "must not be empty or whitespace-only")
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

    if "offset" in args:
        offset = args["offset"]
        if not isinstance(offset, int):
            raise InvalidParameterError("offset", "must be an integer")

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
            if not isinstance(t, str) or len(t.strip()) == 0 or not _is_base64_string(t):
                raise InvalidParameterError("type", "a non-empty base64 string")

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
        raise TypeError("description must be a string")
    desc_bytes = desc.encode("utf-8")
    if len(desc_bytes) < 5 or len(desc_bytes) > 2000:
        raise InvalidParameterError("description", "5-2000 bytes UTF-8")

    # Validate outputs: list (can be empty when using sendWith)
    if "outputs" not in args:
        raise InvalidParameterError("outputs", "required field")
    outputs = args["outputs"]
    if not isinstance(outputs, list):
        raise InvalidParameterError("outputs", "a list")

    # Check if sendWith is being used - allows empty outputs
    opts = args.get("options", {})
    send_with = opts.get("sendWith", [])
    is_send_with = len(send_with) > 0 if isinstance(send_with, list) else False

    # Require at least one output unless using sendWith (TS parity)
    if len(outputs) == 0 and not is_send_with:
        raise InvalidParameterError("outputs", "at least one output required")

    for o in outputs:
        if not isinstance(o, dict):
            raise InvalidParameterError("outputs", "list of dicts")
        # lockingScript: even-length hex
        ls = o.get("lockingScript")
        if not isinstance(ls, str) or (len(ls) % 2 != 0) or not _is_hex_string(ls):
            raise InvalidParameterError("lockingScript", "an even-length hexadecimal string")
        # satoshis: integer >= 0 and <= max supply
        sat = o.get("satoshis")
        if not isinstance(sat, int) or sat < 0:
            raise InvalidParameterError("satoshis", "an integer >= 0")
        # Check maximum Bitcoin supply (21M BTC = ~2.1 quadrillion satoshis)
        if sat > 2_100_000_000_000_000:
            raise InvalidParameterError("satoshis", "must not exceed maximum Bitcoin supply")
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
    # --- Validate options (TS parity) ---
    if "options" in args and args["options"] is not None:
        if not isinstance(args["options"], dict):
            raise InvalidParameterError("options", "a dict")
        trust_self = args["options"].get("trustSelf")
        # TS: type TrustSelf = "known"; unset means undefined/absent.
        if trust_self is not None:
            if isinstance(trust_self, bool):
                raise InvalidParameterError("trustSelf", 'TrustSelf type ("known") (not boolean)')
            if not isinstance(trust_self, str):
                raise InvalidParameterError("trustSelf", 'TrustSelf type ("known")')
            if trust_self != "known":
                raise InvalidParameterError("trustSelf", 'TrustSelf must be "known" when provided')
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
    # isSignAction matches TypeScript: vargs.isNewTx && (!vargs.options.signAndProcess || vargs.inputs.some(i => i.unlockingScript === undefined))
    sign_and_process = opts.get("signAndProcess", True)  # Default is True in TypeScript
    has_undefined_unlocking_script = any(inp.get("unlockingScript") is None for inp in inputs)
    vargs["isSignAction"] = vargs["isNewTx"] and (not sign_and_process or has_undefined_unlocking_script)

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

    # Validate tx: BEEF binary data (can be bytes or list[int] from JSON)
    tx = args.get("tx")
    if isinstance(tx, list):
        # Convert list[int] to bytes (from JSON representation)
        try:
            args["tx"] = bytes(tx)
            tx = args["tx"]
        except (ValueError, TypeError):
            raise InvalidParameterError("tx", "valid byte array (list of integers 0-255)")

    if not isinstance(tx, (bytes, bytearray)) or len(tx) == 0:
        raise InvalidParameterError("tx", "non-empty bytes or list of integers")

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

        output_index = o.get("outputIndex")
        if output_index is None:
            output_index = o.get("outputIndex")
        if not isinstance(output_index, int):
            raise InvalidParameterError("outputIndex", "an integer")
        if output_index < 0:
            raise InvalidParameterError("outputIndex", "must be >= 0")
        o["outputIndex"] = output_index

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
        raise ValueError("output is required outpoint 'txid.index'")
    if "." not in out:
        raise ValueError("outpoint must be format '<txid>.<index>'")
    txid, _, idx = out.partition(".")
    if len(txid) != 64 or not _is_hex_string(txid) or not idx.isdigit():
        raise ValueError("outpoint must be format '<txid>.<index>'")
    # Check vout is reasonable (not too large)
    vout = int(idx)
    if vout > 100000:  # Arbitrary reasonable limit
        raise ValueError("outpoint vout index too large")

    # Validate basket: required string, max 300 chars
    if "basket" not in args:
        raise ValueError("basket is required")
    basket = args["basket"]
    if not isinstance(basket, str):
        raise TypeError("basket must be a string")
    basket_bytes = basket.encode("utf-8")
    if len(basket_bytes) > 300:
        raise ValueError("basket must be <= 300 bytes")

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

    # Validate type: non-empty base64
    t = args.get("type")
    if not isinstance(t, str) or len(t) == 0 or not _is_base64_string(t):
        raise InvalidParameterError("type", "a non-empty base64 string")

    # Validate serialNumber: non-empty base64
    s = args.get("serialNumber")
    if not isinstance(s, str) or len(s) == 0 or not _is_base64_string(s):
        raise InvalidParameterError("serialNumber", "a non-empty base64 string")

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
    """Validate SignActionArgs for BRC-100 Transaction Operations.

    Required parameters:
        - reference: non-empty string (unique action reference from createAction)

    Optional parameters:
        - spends: dict mapping input index (str) to spend data with unlockingScript
        - options: dict with signAndProcess options

    Reference: BRC-100 SignActionArgs specification
    """
    if not isinstance(args, dict):
        raise InvalidParameterError("args", "a dict")

    # Validate reference (required, non-empty string)
    reference = args.get("reference")
    if not isinstance(reference, str) or len(reference) == 0:
        raise InvalidParameterError("reference", "a non-empty string")

    # Validate spends if present (dict of input index -> spend data)
    if "spends" in args:
        spends = args["spends"]
        if not isinstance(spends, dict):
            raise InvalidParameterError("spends", "a dict mapping input index to spend data")


def validate_satoshis(value: Any, field_name: str = "satoshis") -> int:
    """Validate and return a Satoshi value.

    Validates that the value is an integer and within valid Satoshi bounds.
    Returns the validated value if valid.

    Args:
        value: The value to validate (should be an integer)
        field_name: The name of the field for error messages

    Returns:
        The validated Satoshi value

    Raises:
        InvalidParameterError: If value is not an integer or exceeds bounds

    Reference:
        - toolbox/ts-wallet-toolbox/src/utility/satoshiUtils.ts
        - toolbox/go-wallet-toolbox/pkg/internal/satoshi/
    """
    if not isinstance(value, int) or isinstance(value, bool):
        raise InvalidParameterError(field_name, "an integer")
    return satoshi_from(value)


# ----------------------------------------------------------------------------
# Certificate validation functions
# ----------------------------------------------------------------------------


def validate_acquire_certificate_args(args: dict[str, Any]) -> None:
    """Validate AcquireCertificateArgs structure.

    Reference: wallet-toolbox/test/Wallet/certificate/acquireCertificate.test.ts
    """
    if not isinstance(args, dict):
        raise InvalidParameterError("args", "a dict")

    # Validate type: non-empty string
    if "type" not in args:
        raise InvalidParameterError("type", "required")
    cert_type = args["type"]
    if not isinstance(cert_type, str) or len(cert_type) == 0:
        raise InvalidParameterError("type", "a non-empty string")

    # Validate certifier: non-empty even-length hex string
    if "certifier" not in args:
        raise InvalidParameterError("certifier", "required")
    certifier = args["certifier"]
    if not isinstance(certifier, str) or len(certifier) == 0:
        raise InvalidParameterError("certifier", "a non-empty string")
    if len(certifier) % 2 != 0 or not _is_hex_string(certifier):
        raise InvalidParameterError("certifier", "a non-empty even-length hexadecimal string")

    # Validate acquisitionProtocol: non-empty string with valid values
    if "acquisitionProtocol" not in args:
        raise InvalidParameterError("acquisitionProtocol", "required")
    protocol = args["acquisitionProtocol"]
    if not isinstance(protocol, str) or len(protocol) == 0:
        raise InvalidParameterError("acquisitionProtocol", "a non-empty string")
    # Check for valid protocol values (based on failing tests)
    if protocol not in ["direct", "issuance"]:
        raise InvalidParameterError("acquisitionProtocol", "'direct' or 'issuance'")

    # Validate fields: dict if present
    if "fields" in args:
        fields = args["fields"]
        if not isinstance(fields, dict):
            raise InvalidParameterError("fields", "a dict")

    # Validate privileged/privilegedReason
    if args.get("privileged") is True:
        reason = args.get("privilegedReason")
        if not isinstance(reason, str) or len(reason) == 0:
            raise InvalidParameterError("privilegedReason", "a non-empty string when privileged is True")


def validate_prove_certificate_args(args: dict[str, Any]) -> None:
    """Validate ProveCertificateArgs structure.

    Reference: wallet-toolbox/test/Wallet/certificate/proveCertificate.test.ts
    """
    if not isinstance(args, dict):
        raise InvalidParameterError("args", "a dict")

    # Validate certificate: required non-empty dict
    if "certificate" not in args:
        raise InvalidParameterError("certificate", "required")
    certificate = args["certificate"]
    if not isinstance(certificate, dict) or len(certificate) == 0:
        raise InvalidParameterError("certificate", "a non-empty dict")

    # Validate verifier: required hex string (even length for pubkey)
    if "verifier" not in args:
        raise InvalidParameterError("verifier", "required")
    verifier = args["verifier"]
    if not isinstance(verifier, str) or len(verifier) == 0:
        raise InvalidParameterError("verifier", "a non-empty string")
    if len(verifier) % 2 != 0 or not _is_hex_string(verifier):
        raise InvalidParameterError("verifier", "a non-empty even-length hexadecimal string")

    # Validate fieldsToReveal: required list of strings
    if "fieldsToReveal" not in args:
        raise InvalidParameterError("fieldsToReveal", "required")
    fields = args["fieldsToReveal"]
    if not isinstance(fields, list):
        raise InvalidParameterError("fieldsToReveal", "a list")
    if len(fields) == 0:
        raise InvalidParameterError("fieldsToReveal", "a non-empty list")
    for field in fields:
        if not isinstance(field, str):
            raise InvalidParameterError("fieldsToReveal", "list of strings")


def validate_discover_by_identity_key_args(args: dict[str, Any]) -> None:
    """Validate DiscoverByIdentityKeyArgs structure.

    Reference: wallet-toolbox/test/Wallet/certificate/discoverByIdentityKey.test.ts
    """
    if not isinstance(args, dict):
        raise InvalidParameterError("args", "a dict")

    # Validate identityKey: required non-empty even-length hex string
    if "identityKey" not in args:
        raise InvalidParameterError("identityKey", "required")
    identity_key = args["identityKey"]
    if not isinstance(identity_key, str) or len(identity_key.strip()) == 0:
        raise InvalidParameterError("identityKey", "a non-empty string")
    if len(identity_key) % 2 != 0 or not _is_hex_string(identity_key):
        raise InvalidParameterError("identityKey", "a non-empty even-length hexadecimal string")


def validate_discover_by_attributes_args(args: dict[str, Any]) -> None:
    """Validate discover_by_attributes arguments.

    Raises:
        InvalidParameterError: If arguments are invalid
    """
    """Validate DiscoverByAttributesArgs structure.

    Reference: wallet-toolbox/test/Wallet/certificate/discoverByAttributes.test.ts
    """
    if not isinstance(args, dict):
        raise InvalidParameterError("args", "a dict")

    # Validate attributes: required non-empty dict
    if "attributes" not in args:
        raise InvalidParameterError("attributes", "required")
    attributes = args["attributes"]
    if not isinstance(attributes, dict):
        raise InvalidParameterError("attributes", "a dict")
    if len(attributes) == 0:
        raise InvalidParameterError("attributes", "a non-empty dict")

    # Validate limit: optional int 1-MAX_PAGINATION_LIMIT
    if "limit" in args:
        limit = args["limit"]
        if not isinstance(limit, int) or isinstance(limit, bool):
            raise InvalidParameterError("limit", "must be an integer")
        if limit <= 0 or limit > MAX_PAGINATION_LIMIT:
            raise InvalidParameterError("limit", f"must be 1..{MAX_PAGINATION_LIMIT}")


# ----------------------------------------------------------------------------
# Misc validation functions
# ----------------------------------------------------------------------------


def validate_get_header_args(args: dict[str, Any]) -> None:
    """Validate GetHeaderArgs structure.

    Reference: wallet-toolbox/test/wallet/misc/getHeader.test.ts
    """
    if not isinstance(args, dict):
        raise InvalidParameterError("args", "a dict")

    # Validate height: required int >= 0
    if "height" not in args:
        raise InvalidParameterError("height", "required")
    height = args["height"]
    if not isinstance(height, int):
        raise InvalidParameterError("height", "an integer")
    if height < 0:
        raise InvalidParameterError("height", "an integer >= 0")

    # Validate extremely large height
    if height > 10000000:  # Arbitrary large number for "extremely large"
        raise InvalidParameterError("height", "not extremely large")


def validate_get_version_args(args: dict[str, Any]) -> None:
    """Validate GetVersionArgs structure.

    Reference: wallet-toolbox/test/wallet/misc/getVersion.test.ts
    """
    if args is None:
        raise InvalidParameterError("args", "a dict")

    if not isinstance(args, dict):
        raise InvalidParameterError("args", "a dict")

    # Validate originator: optional string, but if present must be valid
    if "originator" in args:
        originator = args["originator"]
        if originator is None:
            raise InvalidParameterError("originator", "a string")
        if not isinstance(originator, str):
            raise InvalidParameterError("originator", "a string")
        if len(originator.strip()) == 0:
            raise InvalidParameterError("originator", "a non-empty string")
        # Check domain format (basic validation)
        if "." not in originator:
            raise InvalidParameterError("originator", "a valid domain format")


def validate_wallet_constructor_args(chain: str) -> None:
    """Validate Wallet constructor arguments.

    Reference: wallet-toolbox/test/wallet/misc/WalletConstructor.test.ts
    """
    if not isinstance(chain, str):
        raise InvalidParameterError("chain", "a string")

    if chain not in ("main", "test"):
        raise InvalidParameterError("chain", "'main' or 'test'")

    # Validate key_deriver: optional KeyDeriver
    # Note: This would be checked in the constructor, but we can add validation here if needed
