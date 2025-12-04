import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

"""Token definition for PushDrop example."""

from dataclasses import dataclass
from typing import List

from bsv.keys import PublicKey


@dataclass
class Token:
    tx_id: str
    beef: bytes
    key_id: str
    from_identity_key: PublicKey
    satoshis: int


class Tokens(list):
    def append(self, item: Token) -> None:
        if not isinstance(item, Token):
            raise TypeError("item must be Token")
        super().append(item)

    def tx_ids(self) -> List[str]:
        return [t.tx_id for t in self]

