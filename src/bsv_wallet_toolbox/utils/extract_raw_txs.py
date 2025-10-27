from __future__ import annotations

from collections.abc import Iterable


def extract_raw_txs(items: Iterable[str | bytes | dict]) -> list[str]:
    raws: list[str] = []
    for it in items:
        if isinstance(it, (bytes, bytearray)):
            raws.append(bytes(it).hex())
        elif isinstance(it, str):
            # assume hex
            bytes.fromhex(it)  # validate
            raws.append(it.lower())
        elif isinstance(it, dict):
            raw = it.get("raw") or it.get("rawTx") or it.get("hex")
            if not isinstance(raw, str):
                raise ValueError("missing raw tx hex in dict")
            bytes.fromhex(raw)  # validate
            raws.append(raw.lower())
        else:
            raise TypeError("unsupported item type for raw tx extraction")
    return raws
