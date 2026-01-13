"""Configuration and logging utilities for BSV Wallet Toolbox.

Reference: toolbox/ts-wallet-toolbox/src/utility/ (config/logger utilities)
"""

import logging
from collections.abc import Mapping
from os import environ
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

SENTINEL_ENV_VARS: tuple[str, ...] = ("HOME", "PATH", "SHELL")


def _is_sanitized_environment(env: Mapping[str, str]) -> bool:
    """Return True when common OS env vars are missing (patch.dict clear=True, etc.)."""
    return not any(var in env for var in SENTINEL_ENV_VARS)


def load_config(env_file: str | None = None) -> dict[str, Any]:
    """Load configuration from environment variables and optional .env file.

    Reference: toolbox/ts-wallet-toolbox/src/utility/configUtils.ts
               function loadConfig

    Loads configuration from:
    1. Optional .env file (if env_file is provided)
    2. Environment variables (os.environ)

    Args:
        env_file: Optional path to .env file. If None, uses default .env in current directory

    Returns:
        Dictionary containing loaded configuration

    Example:
        >>> config = load_config()  # Loads from default .env
        >>> config = load_config('/path/to/.env')  # Loads from specific file
    """
    # Load .env file if provided or if default .env exists
    if env_file is not None:
        load_dotenv(env_file)
    # Skip implicit .env loading when the environment was intentionally sanitized
    # by tests (e.g., patch.dict(..., clear=True)) to avoid leaking local secrets.
    elif not _is_sanitized_environment(environ):
        if Path(".env").exists():
            load_dotenv(".env")
        else:
            load_dotenv()

    # Extract all environment variables as configuration
    config = dict(environ)
    return config


def configure_logger(
    name: str | None = None,
    level: int | str = logging.INFO,
    log_format: str | None = None,
) -> logging.Logger:
    """Configure and return a logger instance.

    Reference: toolbox/ts-wallet-toolbox/src/utility/loggerUtils.ts
               function configureLogger

    Sets up a logger with specified name, level, and format.

    Args:
        name: Logger name (defaults to root logger if None)
        level: Logging level (logging.INFO, logging.DEBUG, etc. or string like 'INFO')
        log_format: Custom log format string. If None, uses default format

    Returns:
        Configured logger instance

    Example:
        >>> logger = configure_logger('my_app', level=logging.DEBUG)
        >>> logger.info('Application started')
    """
    # Convert string level to int if needed
    if isinstance(level, str):
        level = getattr(logging, level.upper(), logging.INFO)

    # Get or create logger
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Create console handler if not already present
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setLevel(level)

        # Set format
        if log_format is None:
            # Default format: timestamp, logger name, level, message
            log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

        formatter = logging.Formatter(log_format)
        handler.setFormatter(formatter)

        logger.addHandler(handler)

    return logger


def create_action_tx_assembler() -> dict[str, Any]:
    """Create a transaction assembler configuration for action transactions.

    Reference: toolbox/ts-wallet-toolbox/src/utility/assembler.ts
               function createActionTxAssembler

    Initializes configuration for assembling action transactions with default settings.

    Returns:
        Dictionary containing transaction assembler configuration

    Example:
        >>> assembler_config = create_action_tx_assembler()
        >>> # Use config for transaction assembly operations
    """
    # Default assembler configuration for action transactions
    assembler_config: dict[str, Any] = {
        "version": 1,
        "inputs": [],
        "outputs": [],
        "lockTime": 0,
        "changeDerivationPath": None,
        "feeRate": 1,  # satoshis per byte
        "dustLimit": 0,  # minimum output value
        "randomizeOutputs": True,
        "useAllInputs": False,
    }

    return assembler_config


def get_config_value(config: dict[str, Any] | None, key: str, default: Any = None) -> Any:
    """Get a configuration value by key with optional default.

    Supports dot notation for nested keys (e.g., "database.host").
    If the key exists as-is (including dots), returns that value first.

    Args:
        config: Configuration dictionary, can be None
        key: Configuration key (supports dot notation for nesting)
        default: Default value if key not found

    Returns:
        Configuration value or default

    Example:
        >>> config = {"database": {"host": "localhost"}, "key.with.dots": "value"}
        >>> get_config_value(config, "database.host")  # "localhost"
        >>> get_config_value(config, "key.with.dots")  # "value"
        >>> get_config_value(config, "missing.key", "default")  # "default"
    """
    if config is None:
        return default

    # First try the key as-is (handles keys with dots in their names)
    if key in config:
        return config[key]

    # Then try dot notation for nested access
    keys = key.split(".")
    value = config

    for k in keys:
        if isinstance(value, dict) and k in value:
            value = value[k]
        else:
            return default

    return value


def set_config_value(config: dict[str, Any] | None, key: str, value: Any) -> dict[str, Any]:
    """Set a configuration value by key.

    Supports dot notation for nested keys (e.g., "database.host").
    Creates nested dictionaries as needed.

    Args:
        config: Configuration dictionary (can be None, will create new dict)
        key: Configuration key (supports dot notation)
        value: Value to set

    Returns:
        Modified configuration dictionary

    Example:
        >>> config = {}
        >>> set_config_value(config, "database.host", "localhost")
        >>> config  # {"database": {"host": "localhost"}}
    """
    if config is None:
        config = {}

    keys = key.split(".")
    current = config

    # Navigate to the parent of the final key
    for k in keys[:-1]:
        if k not in current or not isinstance(current[k], dict):
            current[k] = {}
        current = current[k]

    # Set the final value
    current[keys[-1]] = value

    return config


def validate_config(config: dict[str, Any] | None, schema: dict[str, Any] | None = None) -> bool:
    """Validate configuration dictionary structure.

    Args:
        config: Configuration dictionary to validate
        schema: Optional schema for validation (currently unused, for future extension)

    Returns:
        True if config is valid (non-empty dict), False otherwise

    Example:
        >>> validate_config({"key": "value"})  # True
        >>> validate_config({})  # True (empty dict is valid)
        >>> validate_config(None)  # False
    """
    if config is None:
        return False

    if not isinstance(config, dict):
        return False

    # For now, just check that it's a dictionary
    # Future: implement schema validation if schema is provided
    return True
