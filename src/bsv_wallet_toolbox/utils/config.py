"""Configuration and logging utilities for BSV Wallet Toolbox.

Reference: toolbox/ts-wallet-toolbox/src/utility/ (config/logger utilities)
"""

import logging
import os
from typing import Any

from dotenv import load_dotenv


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
    else:
        # Try to load default .env file
        if os.path.exists(".env"):
            load_dotenv(".env")
        else:
            load_dotenv()

    # Extract all environment variables as configuration
    config = dict(os.environ)
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
        "change_derivation_path": None,
        "fee_rate": 1,  # satoshis per byte
        "dust_limit": 0,  # minimum output value
        "randomize_outputs": True,
        "use_all_inputs": False,
    }

    return assembler_config

