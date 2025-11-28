"""Utility functions for BSV Wallet Toolbox.

This package contains utility functions for validation, conversion, and other common operations.

Reference: toolbox/ts-wallet-toolbox/src/utility/
"""

import os
from types import SimpleNamespace

from dotenv import load_dotenv

from bsv_wallet_toolbox.utils.aggregate_results import (
    aggregate_action_results,
    aggregate_results,
    combine_results,
    merge_result_arrays,
)
from bsv_wallet_toolbox.utils.buffer_utils import (
    as_array,
    as_buffer,
    as_string,
    as_uint8array,
)
from bsv_wallet_toolbox.utils.config import (
    configure_logger,
    create_action_tx_assembler,
    get_config_value,
    load_config,
    set_config_value,
    validate_config,
)
from bsv_wallet_toolbox.utils.format_utils import Format
from bsv_wallet_toolbox.utils.generate_change_sdk import generate_change_sdk
from bsv_wallet_toolbox.utils.identity_utils import (
    parse_results,
    query_overlay,
    query_overlay_certificates,
    transform_verifiable_certificates_with_trust,
)
from bsv_wallet_toolbox.utils.merkle_path_utils import convert_proof_to_merkle_path
from bsv_wallet_toolbox.utils.parse_tx_script_offsets import parse_tx_script_offsets
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
from bsv_wallet_toolbox.utils.reader_uint8array import ReaderUint8Array
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
    validate_create_action_args,
    validate_internalize_action_args,
    validate_originator,
    validate_process_action_args,
    validate_satoshis,
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
    """Convert chain to wallet network.
    
    Args:
        chain: Chain identifier ('main', 'test', 'mainnet', 'testnet', 'regtest')
        
    Returns:
        Network name ('mainnet', 'testnet', 'regtest')
        
    Reference: wallet-toolbox/src/utility/utilityHelpers.ts - toWalletNetwork
    """
    chain_map = {
        "main": "mainnet",
        "test": "testnet",
        "mainnet": "mainnet",
        "testnet": "testnet",
        "regtest": "regtest",
    }
    return chain_map.get(chain, chain)


def verify_truthy(value: object, description: str | None = None) -> object:
    """Verify that a value is truthy, raising an error if not.
    
    Args:
        value: Value to verify
        description: Optional error description
        
    Returns:
        The value if truthy
        
    Raises:
        ValueError: If value is falsy
        
    Reference: wallet-toolbox/src/utility/utilityHelpers.ts - verifyTruthy
    """
    if not value:
        msg = description or f"Value must be truthy"
        raise ValueError(msg)
    return value


def verify_hex_string(value: str, description: str | None = None) -> str:
    """Verify that a value is a valid hex string, trim and lowercase it.
    
    Args:
        value: String to verify and normalize
        description: Optional error description
        
    Returns:
        Trimmed and lowercased hex string
        
    Raises:
        ValueError: If value is not a valid hex string
        
    Reference: wallet-toolbox/src/utility/utilityHelpers.ts - verifyHexString
    """
    if not isinstance(value, str):
        msg = description or f"Value must be a string"
        raise ValueError(msg)
    # Trim whitespace and lowercase
    normalized = value.strip().lower()
    # Verify it's valid hex
    try:
        int(normalized, 16)
    except ValueError as e:
        msg = description or f"Value is not a valid hex string"
        raise ValueError(msg) from e
    return normalized


def verify_id(value: int, description: str | None = None) -> int:
    """Verify that a value is a valid ID (positive integer).
    
    Args:
        value: Value to verify
        description: Optional error description
        
    Returns:
        The ID value
        
    Raises:
        ValueError: If value is not a positive integer
        
    Reference: wallet-toolbox/src/utility/utilityHelpers.ts - verifyId
    """
    verify_integer(value, description)
    if value <= 0:
        msg = description or f"ID must be positive (> 0), got {value}"
        raise ValueError(msg)
    return value


def verify_integer(value: int, description: str | None = None) -> int:
    """Verify that a value is an integer.
    
    Args:
        value: Value to verify
        description: Optional error description
        
    Returns:
        The integer value
        
    Raises:
        ValueError: If value is not an integer
        
    Reference: wallet-toolbox/src/utility/utilityHelpers.ts - verifyInteger
    """
    if not isinstance(value, int) or isinstance(value, bool):
        msg = description or f"Value must be an integer, got {type(value).__name__}"
        raise ValueError(msg)
    return value


def verify_number(value: int | float, description: str | None = None) -> int | float:
    """Verify that a value is a number.
    
    Args:
        value: Value to verify
        description: Optional error description
        
    Returns:
        The number value
        
    Raises:
        ValueError: If value is not a number
        
    Reference: wallet-toolbox/src/utility/utilityHelpers.ts - verifyNumber
    """
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        msg = description or f"Value must be a number, got {type(value).__name__}"
        raise ValueError(msg)
    return value


def verify_one(results: list, description: str | None = None) -> object:
    """Verify that a list contains exactly one element and return it.
    
    Args:
        results: List to verify
        description: Optional error description
        
    Returns:
        The single element in the list
        
    Raises:
        ValueError: If list is empty or has multiple elements
        
    Reference: wallet-toolbox/src/utility/utilityHelpers.ts - verifyOne
    """
    if len(results) == 0:
        msg = description or "Expected exactly one result to exist, found none"
        raise ValueError(msg)
    if len(results) > 1:
        msg = description or f"Expected unique result, found {len(results)}"
        raise ValueError(msg)
    return results[0]


def verify_one_or_none(results: list, description: str | None = None) -> object | None:
    """Verify that a list contains at most one element and return it or None.
    
    Args:
        results: List to verify
        description: Optional error description
        
    Returns:
        The single element in the list, or None if list is empty
        
    Raises:
        ValueError: If list has multiple elements
        
    Reference: wallet-toolbox/src/utility/utilityHelpers.ts - verifyOneOrNone
    """
    if len(results) == 0:
        return None
    if len(results) > 1:
        msg = description or f"Expected unique result, found {len(results)}"
        raise ValueError(msg)
    return results[0]


__all__ = [
    "MAX_SATOSHIS",
    "Format",
    "ReaderUint8Array",
    "Setup",
    "TestUtils",
    "aggregate_action_results",
    "aggregate_results",
    "arrays_equal",
    "as_array",
    "as_buffer",
    "as_string",
    "as_uint8array",
    "combine_results",
    "configure_logger",
    "convert_proof_to_merkle_path",
    "create_action_tx_assembler",
    "double_sha256_be",
    "double_sha256_le",
    "generate_change_sdk",
    "get_config_value",
    "load_config",
    "max_date",
    "merge_result_arrays",
    "optional_arrays_equal",
    "parse_results",
    "parse_tx_script_offsets",
    "query_overlay",
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
    "set_config_value",
    "sha256_hash",
    "to_wallet_network",
    "transform_verifiable_certificates_with_trust",
    "validate_basket_config",
    "validate_config",
    "validate_create_action_args",
    "validate_internalize_action_args",
    "validate_originator",
    "validate_process_action_args",
    "validate_satoshis",
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
