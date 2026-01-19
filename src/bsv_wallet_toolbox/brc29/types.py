"""BRC-29 types and protocol constants.

This module defines core types and constants for the BRC-29 Simple Authenticated
BSV P2PKH Payment Protocol implementation.

Reference: go-wallet-toolbox/pkg/brc29/brc29_types.go
"""

from dataclasses import dataclass
from typing import Any

from bsv.wallet import KeyDeriver, Protocol

# BRC-29 Protocol ID - magic number that identifies BRC-29 compliance
PROTOCOL_ID = "3241645161d8"

# BRC-29 Protocol - security level 2 (counterparty access restrictions per BRC-43)
PROTOCOL = Protocol(security_level=2, protocol=PROTOCOL_ID)

# Type aliases for flexible key input handling
# These match the Go implementation's type constraints
CounterpartyPrivateKey = str | bytes | KeyDeriver | Any  # PrivHex | WIF | PrivateKey | KeyDeriver
CounterpartyPublicKey = str | bytes | KeyDeriver | Any  # PubHex | KeyDeriver | PublicKey


@dataclass
class KeyID:
    """KeyID represents a key ID for BRC-29.

    Key ID is a combination of derivation prefix and derivation suffix.
    Used to derive unique keys for each payment and output within a payment.

    Reference: go-wallet-toolbox/pkg/brc29/brc29_types.go
    """

    derivation_prefix: str
    derivation_suffix: str

    def validate(self) -> None:
        """Validate the key ID.

        The key ID must have a derivation prefix and derivation suffix.

        Raises:
            ValueError: If derivation_prefix or derivation_suffix is empty
        """
        if not self.derivation_prefix:
            raise ValueError("invalid key id: derivation prefix is required")
        if not self.derivation_suffix:
            raise ValueError("invalid key id: derivation suffix is required")

    def __str__(self) -> str:
        """Return the string representation used for derivation."""
        return f"{self.derivation_prefix} {self.derivation_suffix}"
