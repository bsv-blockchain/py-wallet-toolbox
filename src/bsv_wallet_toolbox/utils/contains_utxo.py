"""UTXO containment utility (GO port)."""

from __future__ import annotations

from collections.abc import Iterable


def contains_utxo(details: Iterable[dict], outpoint: dict) -> bool:
    target_txid = outpoint.get("txid")
    target_vout = outpoint.get("vout") or outpoint.get("index")
    for d in details:
        if d.get("txid") == target_txid and (d.get("vout") == target_vout or d.get("index") == target_vout):
            return True
    return False
