from __future__ import annotations

from typing import Union

from bsv.hash import double_sha256


def transaction_id(raw: Union[bytes, str]) -> str:
    data = raw if isinstance(raw, (bytes, bytearray)) else bytes.fromhex(raw)
    digest = double_sha256(data)
    return bytes(reversed(digest)).hex()
