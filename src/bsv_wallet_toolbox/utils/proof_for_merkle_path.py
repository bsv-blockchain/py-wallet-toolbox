from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from bsv.merkle_path import MerklePath


def _ensure_hex32_lower(hex_str: str) -> str:
    if not isinstance(hex_str, str):
        raise ValueError("expected hex string")
    try:
        raw = bytes.fromhex(hex_str)
    except Exception as exc:
        raise ValueError("invalid hex string") from exc
    if len(raw) != 32:
        raise ValueError("hex string must be 32 bytes (64 chars)")
    return hex_str.lower()


def convert_tsc_proof_to_merkle_path(
    txid: str, index: int | str, nodes: Sequence[str], block_height: int | str
) -> dict[str, Any]:
    # Coerce numeric inputs
    current_index = int(index)
    height = int(block_height)

    if not isinstance(nodes, (list, tuple)) or len(nodes) == 0:
        raise ValueError("nodes must be a non-empty list")

    # Build path levels: for each level, add sibling at (index ^ 1)
    path: list[list[dict[str, Any]]] = []
    for _i, n in enumerate(nodes):
        sibling_offset = current_index ^ 1
        if n == "*":
            level = [{"offset": sibling_offset, "duplicate": True}]
        else:
            level = [{"offset": sibling_offset, "hash_str": _ensure_hex32_lower(n)}]
        path.append(level)
        current_index >>= 1

    # Add txid leaf at level 0 with its own offset
    if len(path) == 0:
        raise ValueError("nodes must not be empty")
    path[0].append({"offset": int(index), "hash_str": _ensure_hex32_lower(txid), "txid": True})

    mp = MerklePath(block_height=height, path=path)
    return {"blockHeight": mp.block_height, "path": mp.path}
