
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
        "hex_prefix": prefix,
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
        return [to_trace_value(v) for v in value]
    if isinstance(value, dict):
        return {str(k): to_trace_value(v) for k, v in value.items()}
    # Common SDK objects: PublicKey has `.hex()`
    if hasattr(value, "hex") and callable(getattr(value, "hex")):
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
