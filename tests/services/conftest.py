"""Test fixtures for services module.

Provides mocked implementations of abstract classes and complex dependencies
to enable testing of service functionality.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from bsv_wallet_toolbox.services.wallet_services import WalletServices


class MockWalletServices(WalletServices):
    """Mock implementation of WalletServices for testing."""

    def __init__(self, chain: str = "main"):
        super().__init__(chain)
        self.mock_chain_tracker = AsyncMock()
        self.mock_height = 850000
        self.mock_header = b'\x00' * 80  # Mock 80-byte header

    async def get_chain_tracker(self):
        """Return mock chain tracker."""
        return self.mock_chain_tracker

    async def get_height(self) -> int:
        """Return mock height."""
        return self.mock_height

    async def get_header_for_height(self, height: int) -> bytes:
        """Return mock header."""
        if height < 0:
            raise ValueError("Height must be non-negative")
        return self.mock_header


@pytest.fixture
def mock_wallet_services():
    """Create mock WalletServices instance for testing."""
    return MockWalletServices("main")


class MockWhatsOnChain:
    """Mock implementation of WhatsOnChain provider for testing."""

    def __init__(self):
        self.mock_response = {"height": 850000, "hash": "mock_hash"}

    async def get_info(self):
        """Mock get_info method."""
        return self.mock_response

    async def get_height(self):
        """Mock get_height method."""
        return self.mock_response["height"]

    async def get_header(self, height):
        """Mock get_header method."""
        return b'\x00' * 80  # Mock header

    async def start_listening(self):
        """Mock start_listening (raises NotImplementedError in real implementation)."""
        pass

    async def listening(self):
        """Mock listening (raises NotImplementedError in real implementation)."""
        pass

    async def add_header(self, header):
        """Mock add_header (raises NotImplementedError in real implementation)."""
        pass


@pytest.fixture
def mock_whats_on_chain():
    """Create mock WhatsOnChain instance for testing."""
    return MockWhatsOnChain()
