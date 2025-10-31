"""Unit tests for Wallet.is_authenticated method.

Note: TypeScript does not have dedicated unit tests for base Wallet.isAuthenticated
      (only tested through manager implementations in src/__tests/CWIStyleWalletManager.test.ts).

      This Python test verifies basic functionality to ensure the method works as expected,
      even though no direct TypeScript equivalent exists for the base Wallet class.
"""

import pytest

from bsv_wallet_toolbox import Wallet


class TestIsAuthenticated:
    """Tests for isAuthenticated method.

    Note: Python-specific test (no TypeScript equivalent for base Wallet class).
    """

    def test_resolves_with_authenticated_true(self) -> None:
        """Given: Wallet instance
           When: Call isAuthenticated with normal originator
           Then: Returns authenticated=true

        Note: Inspired by manager tests in TypeScript, but adapted for base Wallet class.
              We test the successful case with normal originator.
        """
        # Given
        wallet = Wallet(chain="test")

        # When
        result = wallet.is_authenticated({}, originator="normal.com")

        # Then
        assert result == {"authenticated": True}
