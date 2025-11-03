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


def validate_create_action_args(args: dict[str, Any]) -> None:
    """Validate CreateActionArgs.

    - description: non-empty string
    - outputs: non-empty list of outputs; each output requires lockingScript (even-length hex) and satoshis:int>=0
    """
    if not isinstance(args, dict):
        raise InvalidParameterError("args", "a dict")
    desc = args.get("description")
    if not isinstance(desc, str) or len(desc) < 1:
        raise InvalidParameterError("description", "a non-empty string")
    outputs = args.get("outputs")
    if not isinstance(outputs, list) or len(outputs) == 0:
        raise InvalidParameterError("outputs", "a non-empty list")
    for o in outputs:
        if not isinstance(o, dict):
            raise InvalidParameterError("outputs", "list of dicts")
        ls = o.get("lockingScript")
        if not isinstance(ls, str) or (len(ls) % 2 != 0) or not _is_hex_string(ls):
            raise InvalidParameterError("lockingScript", "an even-length hexadecimal string")
        sat = o.get("satoshis")
        if not isinstance(sat, int) or sat < 0:
            raise InvalidParameterError("satoshis", "an integer >= 0")


def validate_abort_action_args(args: dict[str, Any] | None) -> None:
    """Validate AbortActionArgs with base64 reference."""
    if args is None or not isinstance(args, dict):
        raise InvalidParameterError("args", "required")
    ref = args.get("reference")
    if not isinstance(ref, str) or len(ref) == 0:
        raise InvalidParameterError("reference", "a non-empty base64 string")
    # Basic base64 validation: characters and length divisible by 4
    if len(ref) % 4 != 0 or not _is_base64_string(ref):
        raise InvalidParameterError("reference", "a valid base64 string (length divisible by 4)")


def validate_internalize_action_args(args: dict[str, Any]) -> None:
    """Validate InternalizeActionArgs."""
    if not isinstance(args, dict):
        raise InvalidParameterError("args", "a dict")
    tx = args.get("tx")
    if not isinstance(tx, (bytes, bytearray)) or len(tx) == 0:
        raise InvalidParameterError("tx", "non-empty bytes")
    outputs = args.get("outputs")
    if not isinstance(outputs, list) or len(outputs) == 0:
        raise InvalidParameterError("outputs", "a non-empty list")
    desc = args.get("description")
    if not isinstance(desc, str) or len(desc) < 3:
        raise InvalidParameterError("description", "at least 3 characters")
    if "labels" in args and args["labels"] is not None:
        labels = args["labels"]
        if not isinstance(labels, list):
            raise InvalidParameterError("labels", "a list of strings")
        for label in labels:
            if not isinstance(label, str) or len(label) > 300:
                raise InvalidParameterError("label", "each label must be <= 300 chars")
    for o in outputs:
        if not isinstance(o, dict):
            raise InvalidParameterError("outputs", "list of dicts")
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


def validate_relinquish_output_args(args: dict[str, Any]) -> None:
    """Validate RelinquishOutputArgs."""
    if not isinstance(args, dict):
        raise InvalidParameterError("args", "a dict")
    out = args.get("output")
    if not isinstance(out, str) or len(out) == 0:
        raise InvalidParameterError("output", "required outpoint 'txid.index'")
    if "." not in out:
        raise InvalidParameterError("outpoint", "format '<txid>.<index>'")
    txid, _, idx = out.partition(".")
    if not _is_hex_string(txid) or not idx.isdigit():
        raise InvalidParameterError("outpoint", "format '<txid>.<index>'")
    basket = args.get("basket", "")
    if not isinstance(basket, str):
        raise InvalidParameterError("basket", "a string")
    if len(basket) > 300:
        raise InvalidParameterError("basket", "must be <= 300 characters")


def validate_insert_certificate_auth_args(args: dict[str, Any]) -> None:
    """Validate insertCertificateAuth (TableCertificateX) arguments."""
    if not isinstance(args, dict):
        raise InvalidParameterError("args", "a dict")

    def _require_even_hex(field: str) -> None:
        v = args.get(field)
        if not isinstance(v, str) or (len(v) % 2 != 0) or not _is_hex_string(v):
            raise InvalidParameterError(field, "an even-length hexadecimal string")

    _require_even_hex("type")
    sn = args.get("serialNumber")
    if not isinstance(sn, str) or not _is_base64_string(sn):
        raise InvalidParameterError("serialNumber", "a base64 string")
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
    subject = args.get("subject")
    if not isinstance(subject, str) or len(subject) == 0:
        raise InvalidParameterError("subject", "a non-empty string")
    _require_even_hex("signature")
    fields = args.get("fields", [])
    if not isinstance(fields, list):
        raise InvalidParameterError("fields", "a list")
    for f in fields:
        if not isinstance(f, dict):
            raise InvalidParameterError("fields", "list of dicts")
        mk = f.get("masterKey")
        if not isinstance(mk, str) or (len(mk) % 2 != 0) or not _is_hex_string(mk):
            raise InvalidParameterError("masterKey", "an even-length hexadecimal string")
    ro = args.get("revocationOutpoint")
    if not isinstance(ro, str) or "." not in ro:
        raise InvalidParameterError("revocationOutpoint", "format '<txid>.<index>'")
    rtxid, _, ridx = ro.partition(".")
    if not _is_hex_string(rtxid) or not ridx.isdigit():
        raise InvalidParameterError("revocationOutpoint", "format '<txid>.<index>'")


def validate_relinquish_certificate_args(args: dict[str, Any]) -> None:
    """Validate RelinquishCertificateArgs.

    - type: base64
    - serialNumber: base64
    - certifier: non-empty even-length hex string
    """
    if not isinstance(args, dict):
        raise InvalidParameterError("args", "a dict")
    t = args.get("type")
    if not isinstance(t, str) or not _is_base64_string(t):
        raise InvalidParameterError("type", "a base64 string")
    s = args.get("serialNumber")
    if not isinstance(s, str) or not _is_base64_string(s):
        raise InvalidParameterError("serialNumber", "a base64 string")
    c = args.get("certifier")
    if not isinstance(c, str) or len(c) == 0 or (len(c) % 2 != 0) or not _is_hex_string(c):
        raise InvalidParameterError("certifier", "a non-empty even-length hexadecimal string")


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
