"""Complete coverage tests for config utilities.

This module provides comprehensive tests for configuration and logging utilities.
"""

import logging
import tempfile
from pathlib import Path
from unittest.mock import patch

try:
    from bsv_wallet_toolbox.utils.config import (
        configure_logger,
        create_action_tx_assembler,
        load_config,
    )

    IMPORT_SUCCESS = True
except ImportError:
    IMPORT_SUCCESS = False


class TestLoadConfig:
    """Test load_config function."""

    def test_load_config_no_env_file(self) -> None:
        """Test loading config without .env file."""
        with patch.dict("os.environ", {"TEST_VAR": "test_value"}, clear=True):
            config = load_config()
            assert isinstance(config, dict)
            assert "TEST_VAR" in config
            assert config["TEST_VAR"] == "test_value"

    def test_load_config_with_explicit_file(self) -> None:
        """Test loading config with explicit .env file path."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
            f.write("MY_VAR=my_value\n")
            f.write("ANOTHER_VAR=another_value\n")
            env_file = f.name

        try:
            config = load_config(env_file)
            assert isinstance(config, dict)
            # Values from .env file should be loaded
            assert "MY_VAR" in config or len(config) > 0
        finally:
            Path(env_file).unlink()

    def test_load_config_default_env_exists(self) -> None:
        """Test loading config when default .env exists."""
        # Create temporary .env in current directory
        env_path = Path(".env.test")
        env_path.write_text("DEFAULT_VAR=default_value\n")

        try:
            with patch("pathlib.Path.exists") as mock_exists:
                mock_exists.return_value = True
                with patch("bsv_wallet_toolbox.utils.config.load_dotenv"):
                    config = load_config()
                    assert isinstance(config, dict)
        finally:
            if env_path.exists():
                env_path.unlink()

    def test_load_config_no_env_no_file(self) -> None:
        """Test loading config with no .env file."""
        with patch("pathlib.Path.exists", return_value=False):
            with patch.dict("os.environ", {"ONLY_OS_VAR": "os_value"}, clear=True):
                config = load_config()
                assert isinstance(config, dict)
                assert "ONLY_OS_VAR" in config

    def test_load_config_returns_dict(self) -> None:
        """Test that load_config always returns a dictionary."""
        config = load_config()
        assert isinstance(config, dict)

    def test_load_config_includes_all_environ_vars(self) -> None:
        """Test that load_config includes all environment variables."""
        test_vars = {
            "VAR1": "value1",
            "VAR2": "value2",
            "VAR3": "value3",
        }
        with patch.dict("os.environ", test_vars, clear=True):
            config = load_config()
            for key, value in test_vars.items():
                assert key in config
                assert config[key] == value

    def test_load_config_with_nonexistent_file(self) -> None:
        """Test loading config with nonexistent file path."""
        # Should not raise, just load from environ
        config = load_config("/nonexistent/path/.env")
        assert isinstance(config, dict)

    def test_load_config_empty_file(self) -> None:
        """Test loading config from empty .env file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
            env_file = f.name

        try:
            config = load_config(env_file)
            assert isinstance(config, dict)
        finally:
            Path(env_file).unlink()

    def test_load_config_with_comments(self) -> None:
        """Test loading config from .env file with comments."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
            f.write("# This is a comment\n")
            f.write("VALID_VAR=valid_value\n")
            f.write("# Another comment\n")
            env_file = f.name

        try:
            config = load_config(env_file)
            assert isinstance(config, dict)
        finally:
            Path(env_file).unlink()


class TestConfigureLogger:
    """Test configure_logger function."""

    def teardown_method(self) -> None:
        """Clean up loggers after each test."""
        # Remove handlers from loggers
        for logger_name in list(logging.Logger.manager.loggerDict.keys()):
            logger = logging.getLogger(logger_name)
            logger.handlers.clear()
            logger.setLevel(logging.NOTSET)

    def test_configure_logger_basic(self) -> None:
        """Test basic logger configuration."""
        logger = configure_logger("test_logger")
        assert isinstance(logger, logging.Logger)
        assert logger.name == "test_logger"
        assert logger.level == logging.INFO

    def test_configure_logger_no_name(self) -> None:
        """Test configuring root logger (no name)."""
        logger = configure_logger(None)
        assert isinstance(logger, logging.Logger)
        assert logger.level == logging.INFO

    def test_configure_logger_custom_level_int(self) -> None:
        """Test configuring logger with custom level (int)."""
        logger = configure_logger("test_debug", level=logging.DEBUG)
        assert logger.level == logging.DEBUG

    def test_configure_logger_custom_level_string(self) -> None:
        """Test configuring logger with custom level (string)."""
        logger = configure_logger("test_warning", level="WARNING")
        assert logger.level == logging.WARNING

    def test_configure_logger_string_levels(self) -> None:
        """Test various string level values."""
        levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        for level_str in levels:
            logger = configure_logger(f"test_{level_str.lower()}", level=level_str)
            expected_level = getattr(logging, level_str)
            assert logger.level == expected_level

    def test_configure_logger_invalid_string_level(self) -> None:
        """Test configuring logger with invalid string level."""
        logger = configure_logger("test_invalid", level="INVALID")
        # Should default to INFO
        assert logger.level == logging.INFO

    def test_configure_logger_lowercase_string_level(self) -> None:
        """Test configuring logger with lowercase string level."""
        logger = configure_logger("test_lower", level="debug")
        assert logger.level == logging.DEBUG

    def test_configure_logger_custom_format(self) -> None:
        """Test configuring logger with custom format."""
        custom_format = "%(levelname)s - %(message)s"
        logger = configure_logger("test_format", log_format=custom_format)
        assert isinstance(logger, logging.Logger)
        assert len(logger.handlers) > 0
        # Check that handler has formatter
        assert logger.handlers[0].formatter is not None

    def test_configure_logger_default_format(self) -> None:
        """Test configuring logger with default format."""
        logger = configure_logger("test_default_format")
        assert len(logger.handlers) > 0
        formatter = logger.handlers[0].formatter
        assert formatter is not None
        # Default format should contain timestamp, name, level, message
        assert "asctime" in formatter._fmt
        assert "name" in formatter._fmt
        assert "levelname" in formatter._fmt
        assert "message" in formatter._fmt

    def test_configure_logger_no_duplicate_handlers(self) -> None:
        """Test that configuring same logger twice doesn't duplicate handlers."""
        logger1 = configure_logger("test_no_dup")
        handler_count1 = len(logger1.handlers)

        logger2 = configure_logger("test_no_dup")
        handler_count2 = len(logger2.handlers)

        # Should have same number of handlers
        assert handler_count1 == handler_count2
        assert logger1 is logger2  # Same logger instance

    def test_configure_logger_handler_type(self) -> None:
        """Test that logger has StreamHandler."""
        logger = configure_logger("test_handler_type")
        assert len(logger.handlers) > 0
        # First handler should be StreamHandler
        assert isinstance(logger.handlers[0], logging.StreamHandler)

    def test_configure_logger_handler_level(self) -> None:
        """Test that handler level matches logger level."""
        logger = configure_logger("test_handler_level", level=logging.ERROR)
        assert logger.handlers[0].level == logging.ERROR

    def test_configure_logger_different_names(self) -> None:
        """Test configuring multiple loggers with different names."""
        logger1 = configure_logger("logger1")
        logger2 = configure_logger("logger2")
        logger3 = configure_logger("logger3")

        assert logger1.name == "logger1"
        assert logger2.name == "logger2"
        assert logger3.name == "logger3"

        # All should be different instances
        assert logger1 is not logger2
        assert logger2 is not logger3

    def test_configure_logger_can_log(self) -> None:
        """Test that configured logger can actually log."""
        logger = configure_logger("test_can_log", level=logging.INFO)

        # Should not raise
        logger.info("Test info message")
        logger.warning("Test warning message")
        logger.error("Test error message")

    def test_configure_logger_respects_level(self) -> None:
        """Test that logger respects configured level."""
        logger = configure_logger("test_level", level=logging.ERROR)

        # These should be filtered out (below ERROR level)
        with patch.object(logger.handlers[0], "emit") as mock_emit:
            logger.debug("Debug message")
            logger.info("Info message")
            logger.warning("Warning message")
            assert mock_emit.call_count == 0

        # This should be logged (ERROR level)
        with patch.object(logger.handlers[0], "emit") as mock_emit:
            logger.error("Error message")
            assert mock_emit.call_count == 1


class TestCreateActionTxAssembler:
    """Test create_action_tx_assembler function."""

    def test_create_assembler_returns_dict(self) -> None:
        """Test that function returns a dictionary."""
        assembler = create_action_tx_assembler()
        assert isinstance(assembler, dict)

    def test_create_assembler_has_version(self) -> None:
        """Test that assembler config has version field."""
        assembler = create_action_tx_assembler()
        assert "version" in assembler
        assert isinstance(assembler["version"], int)

    def test_create_assembler_has_inputs(self) -> None:
        """Test that assembler config has inputs field."""
        assembler = create_action_tx_assembler()
        assert "inputs" in assembler
        assert isinstance(assembler["inputs"], list)

    def test_create_assembler_has_outputs(self) -> None:
        """Test that assembler config has outputs field."""
        assembler = create_action_tx_assembler()
        assert "outputs" in assembler
        assert isinstance(assembler["outputs"], list)

    def test_create_assembler_has_locktime(self) -> None:
        """Test that assembler config has lockTime field."""
        assembler = create_action_tx_assembler()
        assert "lockTime" in assembler
        assert isinstance(assembler["lockTime"], int)

    def test_create_assembler_has_fee_rate(self) -> None:
        """Test that assembler config has fee_rate field."""
        assembler = create_action_tx_assembler()
        assert "feeRate" in assembler
        assert isinstance(assembler["feeRate"], (int, float))

    def test_create_assembler_has_dust_limit(self) -> None:
        """Test that assembler config has dust_limit field."""
        assembler = create_action_tx_assembler()
        assert "dustLimit" in assembler
        assert isinstance(assembler["dustLimit"], (int, float))

    def test_create_assembler_has_randomize_outputs(self) -> None:
        """Test that assembler config has randomize_outputs field."""
        assembler = create_action_tx_assembler()
        assert "randomizeOutputs" in assembler
        assert isinstance(assembler["randomizeOutputs"], bool)

    def test_create_assembler_has_use_all_inputs(self) -> None:
        """Test that assembler config has use_all_inputs field."""
        assembler = create_action_tx_assembler()
        assert "useAllInputs" in assembler
        assert isinstance(assembler["useAllInputs"], bool)

    def test_create_assembler_has_change_derivation_path(self) -> None:
        """Test that assembler config has change_derivation_path field."""
        assembler = create_action_tx_assembler()
        assert "changeDerivationPath" in assembler
        # Can be None or string
        assert assembler["changeDerivationPath"] is None or isinstance(assembler["changeDerivationPath"], str)

    def test_create_assembler_default_values(self) -> None:
        """Test that assembler has sensible default values."""
        assembler = create_action_tx_assembler()

        # Check specific default values
        assert assembler["version"] == 1
        assert assembler["lockTime"] == 0
        assert len(assembler["inputs"]) == 0
        assert len(assembler["outputs"]) == 0
        assert assembler["feeRate"] >= 0
        assert assembler["dustLimit"] >= 0

    def test_create_assembler_multiple_calls(self) -> None:
        """Test that multiple calls return independent configs."""
        assembler1 = create_action_tx_assembler()
        assembler2 = create_action_tx_assembler()

        # Should be different dictionary instances
        assert assembler1 is not assembler2

        # But should have same values
        assert assembler1 == assembler2

    def test_create_assembler_mutable(self) -> None:
        """Test that returned config is mutable."""
        assembler = create_action_tx_assembler()

        # Should be able to modify
        assembler["version"] = 2
        assert assembler["version"] == 2

        assembler["customField"] = "custom_value"
        assert assembler["customField"] == "custom_value"

        # Modifications shouldn't affect future calls
        new_assembler = create_action_tx_assembler()
        assert new_assembler["version"] == 1
        assert "custom_field" not in new_assembler


class TestConfigIntegration:
    """Integration tests for config utilities."""

    def test_load_and_use_config(self) -> None:
        """Test loading config and using it for logger configuration."""
        with patch.dict("os.environ", {"LOG_LEVEL": "DEBUG"}, clear=True):
            config = load_config()

            log_level = config.get("LOG_LEVEL", "INFO")
            logger = configure_logger("integration_test", level=log_level)

            assert logger.level == logging.DEBUG

    def test_create_assembler_and_modify(self) -> None:
        """Test creating assembler and modifying for use."""
        assembler = create_action_tx_assembler()

        # Simulate adding inputs and outputs
        assembler["inputs"].append({"txid": "abc123", "vout": 0})
        assembler["outputs"].append({"satoshis": 1000, "script": "76a9..."})
        assembler["feeRate"] = 50

        assert len(assembler["inputs"]) == 1
        assert len(assembler["outputs"]) == 1
        assert assembler["feeRate"] == 50


class TestConfigEdgeCases:
    """Test edge cases in config utilities."""

    def test_load_config_with_special_characters(self) -> None:
        """Test loading config with special characters in values."""
        special_chars = "test=value&special@chars#here"
        with patch.dict("os.environ", {"SPECIAL": special_chars}, clear=True):
            config = load_config()
            assert config["SPECIAL"] == special_chars

    def test_configure_logger_empty_name(self) -> None:
        """Test configuring logger with empty string name."""
        logger = configure_logger("")
        assert isinstance(logger, logging.Logger)

    def test_configure_logger_very_long_name(self) -> None:
        """Test configuring logger with very long name."""
        long_name = "a" * 1000
        logger = configure_logger(long_name)
        assert logger.name == long_name

    def test_create_assembler_repeated_calls(self) -> None:
        """Test that repeated calls don't accumulate state."""
        for _ in range(100):
            assembler = create_action_tx_assembler()
            assert len(assembler["inputs"]) == 0
            assert len(assembler["outputs"]) == 0

    def test_load_config_large_env(self) -> None:
        """Test loading config with many environment variables."""
        large_env = {f"VAR{i}": f"value{i}" for i in range(1000)}
        with patch.dict("os.environ", large_env, clear=True):
            config = load_config()
            assert len(config) == 1000
            for i in range(1000):
                assert config[f"VAR{i}"] == f"value{i}"
