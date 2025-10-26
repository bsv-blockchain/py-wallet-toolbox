"""Utility functions for BSV Wallet Toolbox.

This package contains utility functions for validation, conversion, and other common operations.

Reference: toolbox/ts-wallet-toolbox/src/utility/
"""

from bsv_wallet_toolbox.utils.validation import (
    validate_basket_config,
    validate_originator,
)
from bsv_wallet_toolbox.utils.satoshi import (
    MAX_SATOSHIS,
    satoshi_add,
    satoshi_equal,
    satoshi_from,
    satoshi_multiply,
    satoshi_subtract,
    satoshi_sum,
    satoshi_to_uint64,
)
from bsv_wallet_toolbox.utils.generate_change_sdk import generate_change_sdk
from types import SimpleNamespace


class Setup:
    """Placeholder for TS Setup util (compat layer for tests)."""

    @staticmethod
    def get_env(chain: str) -> dict[str, str]:  # minimal shape used by tests
        # Return object with attribute access to match TS tests (env.chain, env.taal_api_key)
        return SimpleNamespace(chain=chain, taal_api_key="")


class TestUtils:
    """Test utility functions (compat with TS test helpers)."""

    @staticmethod
    def get_env(chain: str) -> dict[str, str]:
        return Setup.get_env(chain)

__all__ = [
    "validate_basket_config",
    "validate_originator",
    "MAX_SATOSHIS",
    "satoshi_add",
    "satoshi_equal",
    "satoshi_from",
    "satoshi_multiply",
    "satoshi_subtract",
    "satoshi_sum",
    "satoshi_to_uint64",
    "generate_change_sdk",
    "Setup",
    "TestUtils",
]
