"""Test utilities for wallet storage and monitor testing.

This module provides helper functions for creating test wallets with monitors,
mocking services, and setting up test infrastructure.
"""

import pytest
from unittest.mock import MagicMock, AsyncMock

from bsv_wallet_toolbox import Wallet
from bsv_wallet_toolbox.services import Services
from bsv_wallet_toolbox.storage.provider import StorageProvider
from bsv_wallet_toolbox.storage.db import create_engine_from_url
from bsv_wallet_toolbox.storage.models import Base


class MockWalletContext:
    """Mock context object for wallet tests."""

    def __init__(self, wallet=None, storage=None, monitor=None):
        self.wallet = wallet
        self.active_storage = storage
        self.storage = storage
        self.monitor = monitor


def create_sqlite_test_setup_1_wallet(database_name="test_wallet", chain="main", root_key_hex="3" * 64):
    """Create a test wallet setup with SQLite storage.

    This is a minimal implementation for monitor tests.
    """
    try:
        # Create in-memory SQLite database
        engine = create_engine_from_url("sqlite:///:memory:")
        Base.metadata.create_all(engine)

        # Create storage provider
        storage = StorageProvider(engine=engine, chain=chain, storage_identity_key=database_name)

        # Create wallet (minimal - without key deriver for monitor tests)
        wallet = Wallet(chain=chain, storage_provider=storage)

        # Mock monitor - create a minimal monitor object
        monitor = MagicMock()
        monitor.start_tasks = AsyncMock()
        monitor.stop_tasks = AsyncMock()

        ctx = MockWalletContext(wallet=wallet, storage=storage, monitor=monitor)
        return ctx

    except Exception:
        # If setup fails, return minimal context
        ctx = MockWalletContext()
        return ctx


def create_legacy_wallet_sqlite_copy(database_name="test_wallet"):
    """Create a legacy wallet copy for testing.

    This is a minimal implementation for monitor tests.
    """
    # Return the same as create_sqlite_test_setup_1_wallet for now
    return create_sqlite_test_setup_1_wallet(database_name)


def mock_merkle_path_services_as_callback(contexts, callback):
    """Mock merkle path services for testing.

    This is a minimal implementation that patches services to use the callback.
    """
    for ctx in contexts:
        if ctx.monitor and hasattr(ctx.monitor, 'services'):
            # Mock the merkle path service
            ctx.monitor.services.get_merkle_path_for_transaction = callback


def mock_post_services_as_callback(contexts, callback):
    """Mock post services for testing.

    This is a minimal implementation that patches services to use the callback.
    """
    for ctx in contexts:
        if ctx.monitor and hasattr(ctx.monitor, 'services'):
            # Mock the post service
            ctx.monitor.services.post_beef = callback
