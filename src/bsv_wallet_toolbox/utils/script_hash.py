"""Output script hashing utilities (GO port).

Computes hash of a locking script and returns little-endian hex string,
matching toolbox expectations and GO tests.
"""

from __future__ import annotations

from bsv.hash import sha256


def hash_output_script(script_hex: str) -> str:
    if len(script_hex) % 2 != 0:
        raise ValueError("locking script hex must have even length")
    try:
        data = bytes.fromhex(script_hex)
    except ValueError as e:
        raise ValueError("locking script must be hexadecimal") from e
    digest = sha256(data)  # returns bytes in big-endian
    # Return as little-endian hex to match expected fixtures
    return bytes(reversed(digest)).hex()
