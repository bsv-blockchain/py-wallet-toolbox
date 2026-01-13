"""BRC-29 locking and unlocking script templates.

This module provides functions for generating locking and unlocking scripts
according to the BRC-29 specification.

Reference: go-wallet-toolbox/pkg/brc29/brc29_template.go
"""

from bsv.script import P2PKH, Script
from bsv.transaction import Transaction

from .types import CounterpartyPrivateKey, CounterpartyPublicKey, KeyID
from .utils import derive_recipient_private_key


def lock_for_counterparty(
    sender_private_key: CounterpartyPrivateKey,
    key_id: KeyID,
    recipient_public_key: CounterpartyPublicKey,
    testnet: bool = False,
) -> Script:
    """Generate a locking script for a BRC-29 address derived from sender and recipient keys.

    This creates a P2PKH locking script where the address is derived using BRC-29 protocol.

    Args:
        sender_private_key: The sender's private key
        key_id: The key ID for derivation
        recipient_public_key: The recipient's public key (identity key)
        testnet: Whether to generate testnet addresses (default: False)

    Returns:
        Script: P2PKH locking script

    Raises:
        ValueError: If address generation or script creation fails

    Example:
        >>> from bsv_wallet_toolbox.brc29 import lock_for_counterparty, KeyID
        >>> key_id = KeyID(derivation_prefix="payment123", derivation_suffix="output1")
        >>> script = lock_for_counterparty(
        ...     sender_private_key="0000000000000000000000000000000000000000000000000000000000000001",
        ...     key_id=key_id,
        ...     recipient_public_key="0279be667ef9dcbbac55a06295ce870b07029bfcdb2dce28d959f2815b16f81798"
        ... )
        >>> print(script.hex())  # P2PKH locking script
    """
    from .address import address_for_counterparty

    address_result = address_for_counterparty(sender_private_key, key_id, recipient_public_key, testnet)

    try:
        p2pkh = P2PKH()
        locking_script = p2pkh.lock(address_result["addressString"])
        return locking_script
    except Exception as e:
        raise ValueError(f"failed to lock the output with BRC29: {e}") from e


def lock_for_self(
    sender_public_key: CounterpartyPublicKey,
    key_id: KeyID,
    recipient_private_key: CounterpartyPrivateKey,
    testnet: bool = False,
) -> Script:
    """Generate a locking script for a BRC-29 address derived from sender public key and recipient private key.

    This is the self-locking variant that uses address_for_self under the hood.

    Args:
        sender_public_key: The sender's public key (identity key)
        key_id: The key ID for derivation
        recipient_private_key: The recipient's private key
        testnet: Whether to generate testnet addresses (default: False)

    Returns:
        Script: P2PKH locking script

    Raises:
        ValueError: If address generation or script creation fails

    Example:
        >>> from bsv_wallet_toolbox.brc29 import lock_for_self, KeyID
        >>> key_id = KeyID(derivation_prefix="payment123", derivation_suffix="output1")
        >>> script = lock_for_self(
        ...     sender_public_key="0279be667ef9dcbbac55a06295ce870b07029bfcdb2dce28d959f2815b16f81798",
        ...     key_id=key_id,
        ...     recipient_private_key="0000000000000000000000000000000000000000000000000000000000000001"
        ... )
        >>> print(script.hex())  # P2PKH locking script
    """
    from .address import address_for_self

    address_result = address_for_self(sender_public_key, key_id, recipient_private_key, testnet)

    try:
        p2pkh = P2PKH()
        locking_script = p2pkh.lock(address_result["addressString"])
        return locking_script
    except Exception as e:
        raise ValueError(f"failed to lock the output with BRC29: {e}") from e


class UnlockingScriptTemplate:
    """Transaction unlocking script template implementation for BRC-29.

    This class implements the unlocking script generation for BRC-29 outputs.
    It can sign transactions and estimate the length of the unlocking script.
    """

    def __init__(self, unlocker: P2PKH):
        """Initialize the unlocking script template.

        Args:
            unlocker: P2PKH unlocker instance
        """
        self.unlocker = unlocker

    def sign(self, tx: Transaction, input_index: int) -> Script:
        """Sign the transaction input with BRC-29.

        Args:
            tx: The transaction to sign
            input_index: Index of the input to sign

        Returns:
            Script: The unlocking script

        Raises:
            ValueError: If signing fails
        """
        try:
            unlocking_script = self.unlocker.sign(tx, input_index)
            return unlocking_script
        except Exception as e:
            raise ValueError(f"failed to sign input {input_index} with BRC29: {e}") from e

    def estimate_length(self, tx: Transaction, input_index: int) -> int:
        """Estimate the length of the BRC-29 unlocking script.

        For P2PKH, this is always 108 bytes (DER signature + pubkey + script overhead).

        Args:
            tx: The transaction (unused for P2PKH)
            input_index: Input index (unused for P2PKH)

        Returns:
            int: Estimated length in bytes (always 108 for P2PKH)
        """
        return self.unlocker.estimate_length(tx, input_index)


def unlock(
    sender_public_key: CounterpartyPublicKey, key_id: KeyID, recipient_private_key: CounterpartyPrivateKey
) -> UnlockingScriptTemplate:
    """Generate an unlocking script template for a BRC-29 address.

    This creates a template that can be used to sign transactions spending BRC-29 outputs.

    Args:
        sender_public_key: The sender's public key (identity key)
        key_id: The key ID used for derivation
        recipient_private_key: The recipient's private key

    Returns:
        UnlockingScriptTemplate: Template for creating unlocking scripts

    Raises:
        ValueError: If key derivation or template creation fails

    Example:
        >>> from bsv_wallet_toolbox.brc29 import unlock, KeyID
        >>> key_id = KeyID(derivation_prefix="payment123", derivation_suffix="output1")
        >>> template = unlock(
        ...     sender_public_key="0279be667ef9dcbbac55a06295ce870b07029bfcdb2dce28d959f2815b16f81798",
        ...     key_id=key_id,
        ...     recipient_private_key="0000000000000000000000000000000000000000000000000000000000000001"
        ... )
        >>> print(template.estimate_length(tx, 0))  # 108
    """
    # Derive the recipient's private key
    derived_key = derive_recipient_private_key(sender_public_key, key_id, recipient_private_key)

    try:
        # Create P2PKH unlocker
        p2pkh = P2PKH()
        unlocker = p2pkh.unlock(derived_key)

        return UnlockingScriptTemplate(unlocker)
    except Exception as e:
        raise ValueError(f"failed to create BRC29 unlocker: {e}") from e
