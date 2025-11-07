"""Utility functions for BSV Wallet Toolbox.

This package contains utility functions for validation, conversion, and other common operations.

Reference: toolbox/ts-wallet-toolbox/src/utility/
"""

import os
from types import SimpleNamespace

from dotenv import load_dotenv

from bsv_wallet_toolbox.utils.config import (
    configure_logger,
    create_action_tx_assembler,
    load_config,
)
from bsv_wallet_toolbox.utils.generate_change_sdk import generate_change_sdk
from bsv_wallet_toolbox.utils.identity_utils import (
    query_overlay_certificates,
    transform_verifiable_certificates_with_trust,
)
from bsv_wallet_toolbox.utils.random_utils import (
    double_sha256_be,
    double_sha256_le,
    random_bytes,
    random_bytes_base64,
    random_bytes_hex,
    sha256_hash,
    validate_seconds_since_epoch,
    wait_async,
)
from bsv_wallet_toolbox.utils.satoshi import (
    MAX_SATOSHIS,
    satoshi_add,
    satoshi_equal,
    satoshi_from,
    satoshi_multiply,
    satoshi_must_equal,
    satoshi_must_multiply,
    satoshi_must_uint64,
    satoshi_subtract,
    satoshi_sum,
    satoshi_to_uint64,
)
from bsv_wallet_toolbox.utils.validation import (
    validate_basket_config,
    validate_originator,
)


class Setup:
    """TS Setup util compat layer - mirrors TypeScript Setup.getEnv() behavior.

    Reference: toolbox/ts-wallet-toolbox/src/Setup.ts (getEnv method)
    """

    @staticmethod
    def get_env(chain: str) -> SimpleNamespace:
        """Get environment configuration from .env file and environment variables.

        Mirrors TypeScript Setup.getEnv() by loading .env and returning environment config.

        Args:
            chain: Blockchain network ('main' or 'test')

        Returns:
            SimpleNamespace with attributes: chain, taal_api_key, dev_keys, identity_key, mysql_connection

        Reference:
            - toolbox/ts-wallet-toolbox/src/Setup.ts (getEnv method)
        """
        # Load .env file (matches TS Setup.ts behavior)
        load_dotenv()

        # Get environment variables (TS parity)
        taal_api_key = os.getenv(f"{chain.upper()}_TAAL_API_KEY", "")

        return SimpleNamespace(
            chain=chain,
            taal_api_key=taal_api_key,
            dev_keys={},  # Device keys from .env if needed
            identity_key="",  # Identity key from .env if needed
            mysql_connection="",  # MySQL connection string if needed
        )


class TestUtils:
    """Test utility functions (compat with TS test helpers)."""

    @staticmethod
    def get_env(chain: str) -> dict[str, str]:
        return Setup.get_env(chain)


def arrays_equal(arr1: list | None, arr2: list | None) -> bool:
    """Compare two arrays for equality."""
    if arr1 is None or arr2 is None:
        return arr1 == arr2
    return arr1 == arr2


def optional_arrays_equal(arr1: list | None, arr2: list | None) -> bool:
    """Compare two optional arrays for equality."""
    return arrays_equal(arr1, arr2)


def max_date(d1: object | None, d2: object | None) -> object | None:
    """Return the maximum of two dates."""
    if d1 is None:
        return d2
    if d2 is None:
        return d1
    return max(d1, d2)


def to_wallet_network(chain: str) -> str:
    """Convert chain to wallet network."""
    chain_map = {
        "mainnet": "mainnet",
        "testnet": "testnet",
        "regtest": "regtest",
    }
    return chain_map.get(chain, chain)


def verify_truthy(value: object, description: str | None = None) -> None:
    """Verify that a value is truthy, raising an error if not."""
    if not value:
        msg = description or f"Value {value} is not truthy"
        raise AssertionError(msg)


def verify_hex_string(value: str, description: str | None = None) -> None:
    """Verify that a value is a valid hex string."""
    if not isinstance(value, str):
        msg = description or f"Value {value} is not a string"
        raise AssertionError(msg)
    try:
        int(value, 16)
    except ValueError as e:
        msg = description or f"Value {value} is not a valid hex string"
        raise AssertionError(msg) from e


def verify_id(value: object, description: str | None = None) -> None:
    """Verify that a value is a valid ID."""
    verify_truthy(value, description or f"Value {value} is not a valid ID")


def verify_integer(value: object, description: str | None = None) -> None:
    """Verify that a value is an integer."""
    if not isinstance(value, int) or isinstance(value, bool):
        msg = description or f"Value {value} is not an integer"
        raise AssertionError(msg)


def verify_number(value: object, description: str | None = None) -> None:
    """Verify that a value is a number."""
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        msg = description or f"Value {value} is not a number"
        raise AssertionError(msg)


def verify_one(value: object, description: str | None = None) -> None:
    """Verify that a value is truthy (similar to verify_truthy)."""
    verify_truthy(value, description)


def verify_one_or_none(value: object, description: str | None = None) -> None:
    """Verify that a value is truthy or None."""
    if value is not None:
        verify_truthy(value, description)


__all__ = [
    "MAX_SATOSHIS",
    "Setup",
    "TestUtils",
    "arrays_equal",
    "configure_logger",
    "create_action_tx_assembler",
    "double_sha256_be",
    "double_sha256_le",
    "generate_change_sdk",
    "load_config",
    "max_date",
    "optional_arrays_equal",
    "query_overlay_certificates",
    "random_bytes",
    "random_bytes_base64",
    "random_bytes_hex",
    "satoshi_add",
    "satoshi_equal",
    "satoshi_from",
    "satoshi_multiply",
    "satoshi_must_equal",
    "satoshi_must_multiply",
    "satoshi_must_uint64",
    "satoshi_subtract",
    "satoshi_sum",
    "satoshi_to_uint64",
    "sha256_hash",
    "to_wallet_network",
    "transform_verifiable_certificates_with_trust",
    "validate_basket_config",
    "validate_originator",
    "validate_seconds_since_epoch",
    "verify_hex_string",
    "verify_id",
    "verify_integer",
    "verify_number",
    "verify_one",
    "verify_one_or_none",
    "verify_truthy",
    "wait_async",
]
