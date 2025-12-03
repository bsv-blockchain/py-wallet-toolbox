"""Unit tests for Wallet.wait_for_authentication method.

Note: TypeScript does not have dedicated unit tests for base Wallet.waitForAuthentication
      This Python test verifies basic functionality to ensure the method works as expected,
      even though no direct TypeScript equivalent exists for the base Wallet class.
"""

from bsv_wallet_toolbox import Wallet


class TestWaitForAuthentication:
    """Tests for waitForAuthentication method.

    Note: Python-specific test (no TypeScript equivalent for base Wallet class).
    """

    def test_eventually_resolves(self, test_key_deriver) -> None:
        """Given: Wallet instance
           When: Call waitForAuthentication
           Then: Returns authenticated=true

        Note: Inspired by manager tests in TypeScript, but adapted for base Wallet class.
              Base Wallet class returns immediately since it's always authenticated.
        """
        # Given
        wallet = Wallet(chain="test", key_deriver=test_key_deriver)

        # When
        result = wallet.wait_for_authentication({}, originator="normal.com")

        # Then
        assert result == {"authenticated": True}
