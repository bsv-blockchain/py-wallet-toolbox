"""Test fixtures for permissions module.

Provides mocked implementations of permissions managers for testing.
"""

from unittest.mock import MagicMock

import pytest

from bsv_wallet_toolbox.manager.wallet_permissions_manager import WalletPermissionsManager


class MockPermissionsWalletManager(WalletPermissionsManager):
    """Mock implementation of PermissionsWalletManager for testing."""

    def __init__(self):
        super().__init__(MagicMock(), "admin")  # Mock underlying wallet and admin originator
        self.mock_permissions = {}

    def create_action(self, args, originator=None):
        """Mock create_action with permission checks."""
        return {"txid": "perm_mock_txid", "status": "created"}

    def sign_action(self, args, originator=None):
        """Mock sign_action with permission checks."""
        return {"txid": "perm_mock_txid", "status": "signed"}

    def broadcast_action(self, args, originator=None):
        """Mock broadcast_action with permission checks."""
        return {"txid": "perm_mock_txid", "status": "broadcast"}

    def abort_action(self, args, originator=None):
        """Mock abort_action with permission checks."""
        return {"status": "aborted"}

    def internalize_action(self, args, originator=None):
        """Mock internalize_action with permission checks."""
        return {"status": "internalized"}


@pytest.fixture
def mock_permissions_wallet_manager():
    """Create mock PermissionsWalletManager instance for testing."""
    return MockPermissionsWalletManager()
