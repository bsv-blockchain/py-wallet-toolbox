"""Common pytest fixtures for all tests.

These fixtures are automatically available to all test files.
"""

import json
from collections.abc import Callable
from pathlib import Path

import pytest
from bsv.chaintracker import ChainTracker

from bsv_wallet_toolbox import Wallet
from bsv_wallet_toolbox.services import WalletServices


@pytest.fixture
def test_vectors_dir() -> Path:
    """Get path to Universal Test Vectors directory.

    Returns:
        Path to BRC-100 test vectors directory
    """
    return Path(__file__).parent / "data" / "universal-test-vectors" / "generated" / "brc100"


@pytest.fixture
def load_test_vectors(test_vectors_dir: Path) -> Callable[[str], tuple[dict, dict]]:
    """Factory fixture to load Universal Test Vectors for any method.

    Returns:
        Function that takes method name and returns (args_data, result_data)

    Example:
        >>> args_data, result_data = load_test_vectors("getVersion-simple")
    """

    def _load(test_name: str) -> tuple[dict, dict]:
        """Load test vectors for given test name.

        Args:
            test_name: Test name (e.g., "getVersion-simple", "getNetwork-simple")

        Returns:
            Tuple of (args_data, result_data) dictionaries
        """
        args_path = test_vectors_dir / f"{test_name}-args.json"
        with args_path.open() as f:
            args_data = json.load(f)

        result_path = test_vectors_dir / f"{test_name}-result.json"
        with result_path.open() as f:
            result_data = json.load(f)

        return args_data, result_data

    return _load


@pytest.fixture
def wallet() -> Wallet:
    """Create a test wallet instance (mainnet by default).

    Returns:
        Wallet instance configured for mainnet
    """
    return Wallet(chain="main")


@pytest.fixture
def testnet_wallet() -> Wallet:
    """Create a test wallet instance for testnet.

    Returns:
        Wallet instance configured for testnet
    """
    return Wallet(chain="test")


# ========================================================================
# MockWalletServices - Test Implementation
# ========================================================================


class MockWalletServices(WalletServices):
    """Mock implementation of WalletServices for testing.

    This mock allows tests to verify Wallet interface behavior without
    requiring actual blockchain API calls.

    Attributes:
        height: Mock blockchain height (default: 850000)
        header: Mock block header bytes (default: genesis block)
    """

    def __init__(
        self,
        chain: str = "main",
        height: int = 850000,
        header: bytes | None = None,
    ) -> None:
        """Initialize mock services.

        Args:
            chain: Blockchain network ('main' or 'test')
            height: Mock blockchain height
            header: Mock block header (80 bytes). If None, uses genesis block header.
        """
        super().__init__(chain)
        self._height = height

        # Default to genesis block header if not provided
        if header is None:
            genesis_hex = (
                "0100000000000000000000000000000000000000000000000000000000000000"
                "000000003ba3edfd7a7b12b27ac72c3e67768f617fc81bc3888a51323a9fb8aa"
                "4b1e5e4a29ab5f49ffff001d1dac2b7c"
            )
            self._header = bytes.fromhex(genesis_hex)
        else:
            self._header = header

    async def get_chain_tracker(self) -> ChainTracker:
        """Get mock ChainTracker (not implemented for basic tests).

        Raises:
            NotImplementedError: ChainTracker not needed for basic Wallet interface tests
        """
        raise NotImplementedError("MockWalletServices does not provide ChainTracker")

    async def get_height(self) -> int:
        """Get mock blockchain height.

        Returns:
            Mock height value
        """
        return self._height

    async def get_header_for_height(self, height: int) -> bytes:
        """Get mock block header.

        Args:
            height: Block height (ignored in mock)

        Returns:
            Mock header bytes (80 bytes)
        """
        return self._header


# ========================================================================
# Fixtures using MockWalletServices
# ========================================================================


@pytest.fixture
def mock_services() -> MockWalletServices:
    """Create mock wallet services for testing.

    Returns:
        MockWalletServices instance with default height 850000
    """
    return MockWalletServices(chain="main", height=850000)


@pytest.fixture
def wallet_with_services(mock_services: MockWalletServices) -> Wallet:
    """Create a test wallet instance with mock services.

    Returns:
        Wallet instance configured with MockWalletServices
    """
    return Wallet(chain="main", services=mock_services)
