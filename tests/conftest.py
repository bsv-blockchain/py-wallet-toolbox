"""Common pytest fixtures for all tests.

These fixtures are automatically available to all test files.
"""

import json
from collections.abc import Callable
from pathlib import Path

import pytest

from bsv_wallet_toolbox import Wallet


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
