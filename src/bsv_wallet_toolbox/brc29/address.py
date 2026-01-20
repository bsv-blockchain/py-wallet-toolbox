"""BRC-29 address generation functions.

This module provides functions for generating blockchain addresses according to
the BRC-29 specification.

Reference: go-wallet-toolbox/pkg/brc29/brc29_address.go
"""

from bsv.constants import Network

from .types import PROTOCOL, CounterpartyPrivateKey, CounterpartyPublicKey, KeyID
from .utils import derive_recipient_private_key, to_identity_key, to_key_deriver


def address_for_self(
    sender_public_key: CounterpartyPublicKey,
    key_id: KeyID,
    recipient_private_key: CounterpartyPrivateKey,
    testnet: bool = False,
) -> dict[str, str]:
    """Generate a blockchain address according to BRC-29 specification (recipient side).

    This function is meant to be used by the recipient to generate a BRC-29 address for himself.
    If you are a sender, and you want to generate an address to send funds for a recipient,
    use address_for_counterparty instead.

    The sender key can be a public key hex, a key deriver, or a PublicKey object.
    The recipient key can be a private key hex string, WIF, a key deriver, or a PrivateKey object.

    Args:
        sender_public_key: The sender's public key (identity key)
        key_id: The key ID for derivation
        recipient_private_key: The recipient's private key
        testnet: Whether to generate a testnet address (default: False for mainnet)

    Returns:
        Dict with 'address_string' key containing the generated address

    Raises:
        ValueError: If key derivation or address generation fails

    Example:
        >>> from bsv_wallet_toolbox.brc29 import address_for_self, KeyID
        >>> key_id = KeyID(derivation_prefix="payment123", derivation_suffix="output1")
        >>> result = address_for_self(
        ...     sender_public_key="0279be667ef9dcbbac55a06295ce870b07029bfcdb2dce28d959f2815b16f81798",
        ...     key_id=key_id,
        ...     recipient_private_key="0000000000000000000000000000000000000000000000000000000000000001"
        ... )
        >>> print(result["address_string"])  # Bitcoin address
    """
    # Derive the private key for the recipient
    derived_key = derive_recipient_private_key(sender_public_key, key_id, recipient_private_key)

    # Get the public key from the derived private key
    public_key = derived_key.public_key()

    # Generate address from public key
    try:
        network = Network.TESTNET if testnet else Network.MAINNET
        address = public_key.address(network=network)
        return {"addressString": address}
    except Exception as e:
        raise ValueError(f"failed to create brc29 address from public key: {e}") from e


def address_for_counterparty(
    sender_private_key: CounterpartyPrivateKey,
    key_id: KeyID,
    recipient_public_key: CounterpartyPublicKey,
    testnet: bool = False,
) -> dict[str, str]:
    """Generate a blockchain address according to BRC-29 specification (sender side).

    This function is meant to be used by the sender to generate a BRC-29 address for a recipient.
    If you are a recipient, and you want to generate an address to pass it to a sender,
    use address_for_self instead.

    The sender key can be a private key hex string, WIF, a key deriver, or a PrivateKey object.
    The recipient key can be a public key hex, a key deriver, or a PublicKey object.

    Args:
        sender_private_key: The sender's private key
        key_id: The key ID for derivation
        recipient_public_key: The recipient's public key (identity key)
        testnet: Whether to generate a testnet address (default: False for mainnet)

    Returns:
        Dict with 'address_string' key containing the generated address

    Raises:
        ValueError: If key derivation or address generation fails

    Example:
        >>> from bsv_wallet_toolbox.brc29 import address_for_counterparty, KeyID
        >>> key_id = KeyID(derivation_prefix="payment123", derivation_suffix="output1")
        >>> result = address_for_counterparty(
        ...     sender_private_key="0000000000000000000000000000000000000000000000000000000000000001",
        ...     key_id=key_id,
        ...     recipient_public_key="0279be667ef9dcbbac55a06295ce870b07029bfcdb2dce28d959f2815b16f81798"
        ... )
        >>> print(result["address_string"])  # Bitcoin address
    """
    # Validate key ID
    key_id.validate()

    # Convert sender private key to key deriver
    sender_key_deriver = to_key_deriver(sender_private_key)

    # Convert recipient public key to identity key
    recipient_identity_key = to_identity_key(recipient_public_key)

    # Derive public key for the recipient using sender's key deriver
    try:
        from bsv.wallet import Counterparty, CounterpartyType

        counterparty = Counterparty(type=CounterpartyType.OTHER, counterparty_key=recipient_identity_key)

        derived_pub_key = sender_key_deriver.derive_public_key(
            protocol=PROTOCOL, key_id=str(key_id), counterparty=counterparty, for_self=False
        )

        # Generate address from the derived public key
        network = Network.TESTNET if testnet else Network.MAINNET
        address = derived_pub_key.address(network=network)
        return {"addressString": address}

    except Exception as e:
        raise ValueError(f"failed to create brc29 address for recipient from public key: {e}") from e
