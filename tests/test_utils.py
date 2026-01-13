"""Test utilities for integration and network tests.

Provides helper functions for conditional test execution based on environment setup.
"""

import os


class TestUtils:
    """Test utility functions for conditional test execution."""

    @staticmethod
    def no_env(chain: str) -> bool:
        """Check if environment is not configured for live testing.

        Args:
            chain: Blockchain chain ('main' or 'test')

        Returns:
            True if environment variables are NOT set (should skip test)
            False if environment IS configured (can run test)

        Note: This matches TypeScript test pattern where tests are skipped
              if live environment credentials are not available.
        """
        # Check for common test environment variables
        # TypeScript tests check for identity keys and API keys
        env_vars_to_check = [
            f"{chain.upper()}_IDENTITY_KEY",
            f"{chain.upper()}_TEST_KEY",
            "WALLET_TEST_ENV",
            "LIVE_TEST_ENABLED",
        ]

        # If any env var is set, environment IS configured
        return all(not os.environ.get(env_var) for env_var in env_vars_to_check)


class Setup:
    """Setup utilities for integration tests (alias for TestUtils)."""

    @staticmethod
    def no_env(chain: str) -> bool:
        """Check if environment is not configured for live testing.

        Args:
            chain: Blockchain chain ('main' or 'test')

        Returns:
            True if should skip test (no env configured)
        """
        return TestUtils.no_env(chain)
