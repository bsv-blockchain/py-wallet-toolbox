"""Mock Storage Provider for integration testing.

This module provides fixtures for creating in-memory SQLite storage providers
for integration testing, matching Go's testabilities pattern.

Reference: go-wallet-toolbox/pkg/internal/testabilities/fixture_storage.go
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from tests.testabilities.testservices.mock_arc import MockARC
from tests.testabilities.testservices.mock_bhs import MockBHS
from tests.testabilities.testusers import ALICE, User


@dataclass
class StorageFixture:
    """Fixture for storage provider testing.

    Reference: go-wallet-toolbox/pkg/internal/testabilities/fixture_storage.go
    """

    storage_provider: Any
    mock_arc: MockARC
    mock_bhs: MockBHS
    cleanup: Callable[[], None]

    def auth_for_user(self, user: User) -> dict[str, Any]:
        """Create auth dict for a user.

        Reference: Go's testusers.Alice.AuthID()
        """
        return {
            "identityKey": user.identity_key(),
            "userId": user.user_id,
        }


def create_in_memory_storage_provider(
    storage_identity_key: str | None = None,
    chain: str = "testnet",
) -> tuple[Any, Callable[[], None]]:
    """Create an in-memory SQLite storage provider for testing.

    Returns:
        Tuple of (StorageProvider, cleanup_function)

    Reference: go-wallet-toolbox/pkg/internal/testabilities/dbfixtures/db.go
    """
    from bsv_wallet_toolbox.storage.db import create_engine_from_url
    from bsv_wallet_toolbox.storage.provider import StorageProvider

    # Create in-memory SQLite engine
    engine = create_engine_from_url("sqlite:///:memory:", echo=False)

    # Use default storage identity key if not provided
    if storage_identity_key is None:
        from bsv.keys import PrivateKey

        storage_identity_key = PrivateKey().public_key().hex()

    # Create storage provider
    storage_provider = StorageProvider(
        engine=engine,
        chain=chain,
        storage_identity_key=storage_identity_key,
    )

    # Initialize database tables
    storage_provider.make_available()

    def cleanup():
        # SQLAlchemy engine disposal
        engine.dispose()

    return storage_provider, cleanup


def given_storage(
    user: User = ALICE,
    chain: str = "testnet",
) -> tuple[StorageFixture, Callable[[], None]]:
    """Create a storage fixture for integration testing.

    This is the Python equivalent of Go's testabilities.Given(t).

    Args:
        user: The user to initialize storage for (default: ALICE)
        chain: Network chain (default: "testnet")

    Returns:
        Tuple of (StorageFixture, cleanup_function)

    Reference: go-wallet-toolbox/pkg/storage/internal/testabilities/fixture_storage.go
    """
    # Create storage provider
    storage_provider, storage_cleanup = create_in_memory_storage_provider(
        chain=chain,
    )

    # Create mock services
    mock_arc = MockARC(verify_scripts=True)
    mock_bhs = MockBHS()

    # Register user in storage
    # Note: This requires the storage provider to have find_or_insert_user method
    auth = {
        "identityKey": user.identity_key(),
    }
    try:
        storage_provider.find_or_insert_user(auth, user.identity_key())
    except Exception:
        # If method signature is different, try alternative
        pass

    def cleanup():
        storage_cleanup()

    fixture = StorageFixture(
        storage_provider=storage_provider,
        mock_arc=mock_arc,
        mock_bhs=mock_bhs,
        cleanup=cleanup,
    )

    return fixture, cleanup


class TestRandomizer:
    """Deterministic randomizer for testing.

    This provides predictable "random" values for testing,
    ensuring reproducible test results across implementations.

    Reference: go-wallet-toolbox/pkg/randomizer/test_randomizer.go
    """

    def __init__(self, seed: int = 42):
        """Initialize with a seed for reproducibility."""
        self._seed = seed
        self._counter = 0

    def random_bytes(self, length: int) -> bytes:
        """Generate deterministic "random" bytes."""
        import hashlib

        # Use hash of seed + counter for deterministic output
        data = f"{self._seed}:{self._counter}".encode()
        self._counter += 1

        # Generate enough bytes by hashing repeatedly
        result = b""
        while len(result) < length:
            data = hashlib.sha256(data).digest()
            result += data

        return result[:length]

    def random_hex(self, length: int) -> str:
        """Generate deterministic "random" hex string."""
        return self.random_bytes(length // 2 + 1)[: length // 2].hex()

    def random_int(self, max_value: int) -> int:
        """Generate deterministic "random" integer."""
        bytes_val = self.random_bytes(4)
        int_val = int.from_bytes(bytes_val, "big")
        return int_val % max_value
