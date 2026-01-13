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
    # MockARC
    "MockARC",
    "MockARCQueryFixture",
    "MockBroadcastResult",
    # MockBHS
    "MockBHS",
    "BHSMerkleRootConfirmed",
    "BHSMerkleRootNotFound",
    # MockStorage
    "StorageFixture",
    "create_in_memory_storage_provider",
    "given_storage",
    "TestRandomizer",
]
