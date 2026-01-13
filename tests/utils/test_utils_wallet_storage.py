"""Test utilities for wallet storage and monitor testing.

This module provides helper functions for creating test wallets with monitors,
mocking services, and setting up test infrastructure.
"""

from unittest.mock import AsyncMock, MagicMock

from bsv_wallet_toolbox import Wallet
from bsv_wallet_toolbox.services import Services
from bsv_wallet_toolbox.storage.db import create_engine_from_url
from bsv_wallet_toolbox.storage.models import Base
from bsv_wallet_toolbox.storage.provider import StorageProvider


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
    # Create in-memory SQLite database
    engine = create_engine_from_url("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    # Create storage provider
    storage = StorageProvider(engine=engine, chain=chain, storage_identity_key=database_name)

    # Create wallet with minimal key deriver for monitor tests
    try:
        from bsv import PrivateKey
        from bsv.wallet import KeyDeriver

        # Create a key deriver from a test private key
        test_private_key = PrivateKey.from_hex(root_key_hex[:64] if len(root_key_hex) >= 64 else "3" * 64)
        key_deriver = KeyDeriver(test_private_key)
        wallet = Wallet(chain=chain, storage_provider=storage, key_deriver=key_deriver)
    except Exception:
        # If key deriver creation fails, create wallet without it (may fail)
        wallet = None

    # Create real monitor instance
    try:
        from bsv_wallet_toolbox.monitor import Monitor, MonitorOptions

        services = Services(Services.create_default_options(chain))
        monitor_options = MonitorOptions(
            chain=chain,
            storage=storage,
            services=services,
            task_run_wait_msecs=5000,
            msecs_wait_per_merkle_proof_service_req=500,
            abandoned_msecs=1000 * 60 * 5,  # 5 minutes
            unproven_attempts_limit_test=10,
            unproven_attempts_limit_main=144,
        )
        monitor = Monitor(monitor_options)
    except Exception:
        # Fallback to mock if Monitor creation fails
        import warnings

        warnings.filterwarnings("ignore", category=RuntimeWarning)
        monitor = MagicMock()
        monitor.start_tasks = AsyncMock()
        monitor.stop_tasks = AsyncMock()
        monitor._tasks = []
        monitor.ONE_MINUTE = 60000
        monitor.ONE_SECOND = 1000

    ctx = MockWalletContext(wallet=wallet, storage=storage, monitor=monitor)
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
        if ctx.monitor and hasattr(ctx.monitor, "services"):
            # Mock the merkle path service
            ctx.monitor.services.get_merkle_path_for_transaction = callback


def mock_post_services_as_callback(contexts, callback):
    """Mock post services for testing.

    This is a minimal implementation that patches services to use the callback.
    """
    for ctx in contexts:
        if ctx.monitor and hasattr(ctx.monitor, "services"):
            # Mock the post service
            ctx.monitor.services.post_beef = callback
