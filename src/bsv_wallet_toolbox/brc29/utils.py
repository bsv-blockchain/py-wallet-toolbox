"""BRC-29 utility functions for key handling and derivation.

This module provides utility functions for converting various key representations
and performing BRC-42 key derivation operations for BRC-29.

Reference: go-wallet-toolbox/pkg/brc29/brc29_utils.go
"""

from bsv.keys import PrivateKey, PublicKey
from bsv.wallet import Counterparty, CounterpartyType, KeyDeriver

from .types import PROTOCOL, CounterpartyPrivateKey, CounterpartyPublicKey, KeyID


def to_identity_key(key_source: CounterpartyPublicKey) -> PublicKey:
    """Convert a counterparty public key source to a PublicKey.

    Accepts various representations of public keys:
    - PubHex: hex string of public key
    - KeyDeriver: uses identity key
    - PublicKey: passes through
    - bytes: raw public key bytes

    Args:
        key_source: Public key in various supported formats

    Returns:
        PublicKey object

    Raises:
        ValueError: If key source type is unsupported or parsing fails
    """
    if isinstance(key_source, str):
        # Assume hex string
        try:
            return PublicKey(key_source)
        except Exception as e:
            raise ValueError(f"failed to parse public key from hex string: {e}") from e
    elif isinstance(key_source, bytes):
        # Raw public key bytes
        try:
            return PublicKey.from_bytes(key_source)
        except Exception as e:
            raise ValueError(f"failed to parse public key from bytes: {e}") from e
    elif hasattr(key_source, "identity_key"):
        # KeyDeriver - use identity key
        if key_source is None:
            raise ValueError("key deriver cannot be None")
        return key_source.identity_key()
    elif isinstance(key_source, PublicKey):
        # Already a PublicKey
        if key_source is None:
            raise ValueError("public key cannot be None")
        return key_source
    else:
        raise ValueError(
            f"unexpected key source type: {type(key_source)}, ensure that all subtypes of key source are handled"
        )


def to_key_deriver(key_source: CounterpartyPrivateKey) -> KeyDeriver:
    """Convert a counterparty private key source to a KeyDeriver.

    Accepts various representations of private keys:
    - PrivHex: hex string of private key
    - WIF: WIF-encoded string
    - PrivateKey: creates KeyDeriver from it
    - KeyDeriver: passes through
    - bytes: raw private key bytes

    Args:
        key_source: Private key in various supported formats

    Returns:
        KeyDeriver object

    Raises:
        ValueError: If key source type is unsupported or parsing fails
    """
    if isinstance(key_source, str):
        # Check if it's WIF (starts with specific prefixes) or hex
        if key_source.startswith(("5", "9", "c", "K", "L")):
            # WIF format
            try:
                priv_key = PrivateKey(key_source)
                return KeyDeriver(priv_key)
            except Exception as e:
                raise ValueError(f"failed to parse private key from WIF: {e}") from e
        else:
            # Hex format
            try:
                priv_key = PrivateKey.from_hex(key_source)
                return KeyDeriver(priv_key)
            except Exception as e:
                raise ValueError(f"failed to parse private key from hex: {e}") from e
    elif isinstance(key_source, bytes):
        # Raw private key bytes
        try:
            priv_key = PrivateKey.from_bytes(key_source)
            return KeyDeriver(priv_key)
        except Exception as e:
            raise ValueError(f"failed to parse private key from bytes: {e}") from e
    elif isinstance(key_source, PrivateKey):
        # Already a PrivateKey
        if key_source is None:
            raise ValueError("private key cannot be None")
        return KeyDeriver(key_source)
    elif hasattr(key_source, "_root_private_key"):
        # KeyDeriver (has the attribute)
        if key_source is None:
            raise ValueError("key deriver cannot be None")
        return key_source
    else:
        raise ValueError(
            f"unexpected key source type: {type(key_source)}, ensure that all subtypes of key source are handled"
        )


def derive_recipient_private_key(
    sender_public_key_source: CounterpartyPublicKey, key_id: KeyID, recipient_private_key_source: CounterpartyPrivateKey
) -> PrivateKey:
    """Derive the recipient's private key using BRC-42 derivation.

    This is the core operation of BRC-29: the recipient derives the private key
    that corresponds to the public key the sender used to create the P2PKH output.

    Args:
        sender_public_key_source: Sender's public key (identity key)
        key_id: KeyID with derivation prefix and suffix
        recipient_private_key_source: Recipient's private key deriver

    Returns:
        PrivateKey: The derived private key that can unlock the output

    Raises:
        ValueError: If key derivation fails or validation fails
    """
    # Convert sender's public key to identity key
    sender_identity_key = to_identity_key(sender_public_key_source)

    # Convert recipient's private key source to key deriver
    recipient_key_deriver = to_key_deriver(recipient_private_key_source)

    # Validate key ID
    key_id.validate()

    # Derive private key using BRC-29 protocol
    try:
        derived_private_key = recipient_key_deriver.derive_private_key(
            protocol=PROTOCOL,
            key_id=str(key_id),
            counterparty=Counterparty(type=CounterpartyType.OTHER, counterparty_key=sender_identity_key),
        )
        return derived_private_key
    except Exception as e:
        raise ValueError(f"failed to derive BRC29 private key: {e}") from e
