"""Test fixtures for services module.

Provides mocked implementations of abstract classes and complex dependencies
to enable testing of service functionality.
"""

from unittest.mock import AsyncMock

import pytest

from bsv_wallet_toolbox.services.wallet_services import WalletServices


class MockWalletServices(WalletServices):
    """Mock implementation of WalletServices for testing."""

    def __init__(self, chain: str = "main"):
        super().__init__(chain)
        self.mock_chain_tracker = AsyncMock()
        self.mock_height = 850000
        self.mock_header = b"\x00" * 80  # Mock 80-byte header

    async def get_chain_tracker(self):
        """Return mock chain tracker."""
        return self.mock_chain_tracker

    def get_height(self) -> int:
        """Return mock height."""
        return self.mock_height

    def get_header_for_height(self, height: int) -> bytes:
        """Return mock header."""
        if height < 0:
            raise ValueError("Height must be non-negative")
        return self.mock_header

    # Additional methods expected by expanded coverage tests
    def post_transaction(self, raw_tx):
        return {"txid": "mock_txid", "status": "success"}

    def get_transaction_status(self, txid):
        return {"txid": "mock_txid", "status": "confirmed"}

    def get_raw_transaction(self, txid):
        return "mock_raw_tx_hex"

    def post_beef_transaction(self, beef_data):
        return {"txid": "mock_txid", "status": "success"}

    def post_multiple_transactions(self, txs):
        return [{"txid": "mock_txid1"}, {"txid": "mock_txid2"}]

    def get_utxo_status(self, outpoint):
        return {"utxo": "mock_utxo", "status": "confirmed"}

    def get_utxos_for_script(self, script_hash):
        return {"utxos": ["mock_utxo1", "mock_utxo2"]}

    def get_script_history(self, script_hash):
        return {"history": ["tx1", "tx2"]}

    def get_merkle_path(self, txid):
        return {"merklePath": "mock_path"}

    def get_block_header(self, height):
        return {"hash": "mock_hash", "height": 850000}

    def get_chain_tip(self):
        return {"hash": "mock_tip_hash", "height": self.mock_height}

    def add_provider(self, provider):
        return True

    def remove_provider(self, provider_name):
        return True

    def get_providers(self):
        return ["whatsOnChain", "arc"]

    def cached_height_retrieval(self):
        return self.mock_height


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
        return b"\x00" * 80  # Mock header

    async def start_listening(self):
        """Mock start_listening (raises NotImplementedError in real implementation)."""

    async def listening(self):
        """Mock listening (raises NotImplementedError in real implementation)."""

    async def add_header(self, header):
        """Mock add_header (raises NotImplementedError in real implementation)."""


@pytest.fixture
def mock_whats_on_chain():
    """Create mock WhatsOnChain instance for testing."""
    return MockWhatsOnChain()
