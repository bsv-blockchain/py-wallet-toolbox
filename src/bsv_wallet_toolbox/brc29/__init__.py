"""BRC-29 Simple Authenticated BSV P2PKH Payment Protocol implementation.

This module provides a complete implementation of the BRC-29 protocol for
secure, authenticated P2PKH payments using BRC-42 key derivation.

Key Features:
- Address generation for both sender and recipient roles
- Locking and unlocking script templates
- Compatible with BRC-42 key derivation
- Support for mainnet and testnet

Reference: https://brc.dev/29
"""

from .address import address_for_counterparty, address_for_self
from .template import UnlockingScriptTemplate, lock_for_counterparty, lock_for_self, unlock
from .types import KeyID, PROTOCOL, PROTOCOL_ID

__all__ = [
    # Types
    "KeyID",
    "PROTOCOL",
    "PROTOCOL_ID",

    # Address functions
    "address_for_self",
    "address_for_counterparty",

    # Template functions
    "lock_for_self",
    "lock_for_counterparty",
    "unlock",
    "UnlockingScriptTemplate",
]
