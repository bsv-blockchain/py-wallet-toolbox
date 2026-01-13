"""Single-line JSON debug tracing utilities.

Design goals:
- Enable root-cause diagnosis in a single run (LOGLEVEL=DEBUG)
- Emit one-line JSON for easy grepping/parsing
- Avoid logging secrets; summarize large binary payloads (len/sha256/hex prefix)
"""

from __future__ import annotations

import hashlib
import json
import logging
from typing import Any


def _bytes_summary(data: bytes, hex_prefix_bytes: int = 32) -> dict[str, Any]:
    hx = data.hex()
    prefix = hx[: hex_prefix_bytes * 2]
    return {
        "type": "bytes",
        "len": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
        "hexPrefix": prefix,
    }


def to_trace_value(value: Any) -> Any:
    """Best-effort JSON-safe conversion for debug tracing."""
    if value is None:
        return None
    if isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, (bytes, bytearray)):
        return _bytes_summary(bytes(value))
    if isinstance(value, list):
        # Truncate large lists to avoid massive log output
        MAX_LIST_ITEMS = 50
        if len(value) > MAX_LIST_ITEMS:
            # Check if it looks like a byte array (all integers 0-255)
            # Check first 100 items to determine if it's byte-like
            sample_size = min(100, len(value))
            is_byte_like = all(isinstance(v, int) and 0 <= v <= 255 for v in value[:sample_size])
            if is_byte_like and len(value) > 50:
                # Summarize as bytes
                try:
                    byte_data = bytes(value)
                    return _bytes_summary(byte_data)
                except (ValueError, OverflowError):
                    pass
            # Truncate large lists
            truncated = [to_trace_value(v) for v in value[:MAX_LIST_ITEMS]]
            return {
                "type": "list",
                "len": len(value),
                "items": truncated,
                "truncated": True,
            }
        return [to_trace_value(v) for v in value]
    if isinstance(value, dict):
        # Truncate large dicts too
        MAX_DICT_ITEMS = 20
        # Special handling for storage results: exclude sourceTransaction and inputBeef from nested inputs
        filtered_dict = {}
        for k, v in value.items():
            # Skip sourceTransaction and inputBeef fields entirely to avoid massive output
            if k in ("sourceTransaction", "inputBeef"):
                filtered_dict[str(k)] = {"type": "excluded", "reason": "large_binary_data"}
            elif k == "inputs" and isinstance(v, list):
                # For inputs list, filter out sourceTransaction from each input
                filtered_inputs = []
                for inp in v:
                    if isinstance(inp, dict):
                        filtered_inp = {ik: iv for ik, iv in inp.items() if ik != "sourceTransaction"}
                        if "sourceTransaction" in inp:
                            filtered_inp["sourceTransaction"] = {"type": "excluded", "reason": "large_binary_data"}
                        filtered_inputs.append(to_trace_value(filtered_inp))
                    else:
                        filtered_inputs.append(to_trace_value(inp))
                filtered_dict[str(k)] = filtered_inputs
            else:
                filtered_dict[str(k)] = to_trace_value(v)

        if len(filtered_dict) > MAX_DICT_ITEMS:
            items = dict(list(filtered_dict.items())[:MAX_DICT_ITEMS])
            return {
                "type": "dict",
                "len": len(value),
                "items": items,
                "truncated": True,
            }
        return filtered_dict
    # Common SDK objects: PublicKey has `.hex()`
    if hasattr(value, "hex") and callable(value.hex):
        try:
            return {"type": type(value).__name__, "hex": value.hex()}
        except Exception:
            pass
    # Fallback
    try:
        return {"type": type(value).__name__, "repr": repr(value)}
    except Exception:
        return {"type": type(value).__name__}


def trace(logger: logging.Logger, event: str, **fields: Any) -> None:
    """Emit a single-line JSON trace event at DEBUG level."""
    if not logger.isEnabledFor(logging.DEBUG):
        return
    payload = {"event": event, **{k: to_trace_value(v) for k, v in fields.items()}}
    logger.debug("AUTH_TRACE %s", json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True))
