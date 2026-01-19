"""Fixed test users (Alice, Bob) for cross-implementation compatibility testing.

These users have fixed private keys matching Go/TS implementations.

Reference: go-wallet-toolbox/pkg/internal/fixtures/testusers/test_users.go
"""

from dataclasses import dataclass
from typing import Any


@dataclass
class User:
    """Test user with fixed keys matching Go/TS implementations.

    NOTE: Testabilities can modify user IDs to match database
    """

    name: str
    id: int
    priv_key: str

    def auth_id(self) -> dict[str, Any]:
        """Get AuthID dict for this user.

        Returns:
            dict: AuthID with identity_key, user_id, is_active
        """
        return {
            "identityKey": self.identity_key(),
            "userId": self.id,
            "isActive": True,
        }

    def identity_key(self) -> str:
        """Get the public key (identity key) as hex string.

        Returns:
            str: The compressed public key hex (33 bytes)
        """
        from bsv.keys import PrivateKey

        private_key = PrivateKey.from_hex(self.priv_key)
        return private_key.public_key().hex()

    def key_deriver(self):
        """Get a KeyDeriver for this user.

        Returns:
            KeyDeriver: SDK KeyDeriver instance
        """
        from bsv.keys import PrivateKey
        from bsv.wallet import KeyDeriver

        private_key = PrivateKey.from_hex(self.priv_key)
        return KeyDeriver(private_key)

    def private_key(self):
        """Get the PrivateKey object.

        Returns:
            PrivateKey: The private key
        """
        from bsv.keys import PrivateKey

        return PrivateKey.from_hex(self.priv_key)

    def public_key(self):
        """Get the PublicKey object.

        Returns:
            PublicKey: The public key
        """
        return self.private_key().public_key()

    def pub_key_hex(self) -> str:
        """Get the public key as hex string.

        Returns:
            str: The compressed public key hex
        """
        return self.identity_key()

    def address(self) -> str:
        """Get the P2PKH address for this user.

        Returns:
            str: The base58check address
        """
        return self.public_key().address()


# Fixed test users (matching Go/TS implementations)
ALICE = User(
    name="Alice",
    id=1,
    priv_key="143ab18a84d3b25e1a13cefa90038411e5d2014590a2a4a57263d1593c8dee1c",
)

BOB = User(
    name="Bob",
    id=2,
    priv_key="0881208859876fc227d71bfb8b91814462c5164b6fee27e614798f6e85d2547d",
)

# All test users
ALL_USERS = [ALICE, BOB]


# Common fixtures
ANYONE_IDENTITY_KEY = "0279be667ef9dcbbac55a06295ce870b07029bfcdb2dce28d959f2815b16f81798"
"""The "anyone" identity key (generator point G on secp256k1)"""
