"""Fixed test users for cross-implementation compatibility testing.

These users have fixed private keys that match Go/TS implementations,
ensuring deterministic test results across all implementations.

Reference: go-wallet-toolbox/pkg/internal/fixtures/testusers/test_users.go
"""

from .test_users import (
    User,
    ALICE,
    BOB,
    ALL_USERS,
    ANYONE_IDENTITY_KEY,
)

__all__ = [
    "User",
    "ALICE",
    "BOB",
    "ALL_USERS",
    "ANYONE_IDENTITY_KEY",
]

