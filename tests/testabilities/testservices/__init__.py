"""Mock services for cross-implementation testing.

This module provides mock services with enhanced verification capabilities,
particularly script verification in MockARC to catch signing bugs.

Reference: go-wallet-toolbox/pkg/internal/testabilities/testservices/
"""

from .mock_arc import (
    MockARC,
    MockARCQueryFixture,
    MockBroadcastResult,
)
from .mock_bhs import (
    BHSMerkleRootConfirmed,
    BHSMerkleRootNotFound,
    MockBHS,
)
from .mock_storage import (
    StorageFixture,
    TestRandomizer,
    create_in_memory_storage_provider,
    given_storage,
)

__all__ = [
    "BHSMerkleRootConfirmed",
    "BHSMerkleRootNotFound",
    # MockARC
    "MockARC",
    "MockARCQueryFixture",
    # MockBHS
    "MockBHS",
    "MockBroadcastResult",
    # MockStorage
    "StorageFixture",
    "TestRandomizer",
    "create_in_memory_storage_provider",
    "given_storage",
]
