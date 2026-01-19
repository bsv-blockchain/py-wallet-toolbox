"""Test fixtures for manager module.

Provides mocked implementations of wallet managers for testing.
"""

from unittest.mock import MagicMock

import pytest


class MockSimpleWalletManager:
    """Mock implementation of SimpleWalletManager for testing."""

    def __init__(self):
        super().__init__()
        self.mock_storage = MagicMock()
        self.mock_services = MagicMock()

    def create_action(self, args, originator=None):
        """Mock create_action implementation."""
        return {"txid": "mock_txid", "status": "created"}

    def sign_action(self, args, originator=None):
        """Mock sign_action implementation."""
        return {"txid": "mock_txid", "status": "signed"}

    def broadcast_action(self, args, originator=None):
        """Mock broadcast_action implementation."""
        return {"txid": "mock_txid", "status": "broadcast"}

    def abort_action(self, args, originator=None):
        """Mock abort_action implementation."""
        return {"status": "aborted"}

    def internalize_action(self, args, originator=None):
        """Mock internalize_action implementation."""
        return {"status": "internalized"}


class MockCWIStyleWalletManager:
    """Mock implementation of CWIStyleWalletManager for testing."""

    def __init__(self):
        super().__init__()
        self.mock_cwi_client = MagicMock()
        self.mock_storage = MagicMock()

    def create_action(self, args, originator=None):
        """Mock create_action implementation."""
        return {"txid": "cwi_mock_txid", "status": "created"}

    def sign_action(self, args, originator=None):
        """Mock sign_action implementation."""
        return {"txid": "cwi_mock_txid", "status": "signed"}

    def broadcast_action(self, args, originator=None):
        """Mock broadcast_action implementation."""
        return {"txid": "cwi_mock_txid", "status": "broadcast"}

    def abort_action(self, args, originator=None):
        """Mock abort_action implementation."""
        return {"status": "aborted"}

    def internalize_action(self, args, originator=None):
        """Mock internalize_action implementation."""
        return {"status": "internalized"}


@pytest.fixture
def mock_simple_wallet_manager():
    """Create mock SimpleWalletManager instance for testing."""
    return MockSimpleWalletManager()


@pytest.fixture
def mock_cwi_style_wallet_manager():
    """Create mock CWIStyleWalletManager instance for testing."""
    return MockCWIStyleWalletManager()
