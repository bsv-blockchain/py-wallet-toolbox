"""Unit tests for Wallet.is_authenticated method.

Ported from TypeScript implementation to ensure compatibility.

Reference: toolbox/ts-wallet-toolbox/src/Wallet.ts (isAuthenticated method)
Note: TypeScript doesn't have dedicated test files for isAuthenticated,
      but the method is tested in manager tests.
"""

import pytest

from bsv_wallet_toolbox import Wallet
from bsv_wallet_toolbox.errors import InvalidParameterError


class TestIsAuthenticatedBasic:
    """Basic functionality tests for isAuthenticated method.

    Reference: toolbox/ts-wallet-toolbox/src/Wallet.ts (line 848-854)
    """

    @pytest.mark.asyncio
    async def test_returns_authenticated_true(self) -> None:
        """Given: Wallet instance
        When: Call isAuthenticated
        Then: Returns authenticated=true
        """
        # Given
        wallet = Wallet()

        # When
        result = await wallet.is_authenticated({})

        # Then
        assert result == {"authenticated": True}
        assert result["authenticated"] is True

    @pytest.mark.asyncio
    async def test_always_returns_true_for_base_wallet(self) -> None:
        """Given: Multiple calls to isAuthenticated
           When: Called multiple times
           Then: Always returns authenticated=true

        Note: Base Wallet class always returns true since it's initialized with keys
        """
        # Given
        wallet = Wallet()

        # When/Then
        for _ in range(3):
            result = await wallet.is_authenticated({})
            assert result["authenticated"] is True


class TestIsAuthenticatedOriginator:
    """Tests for originator parameter validation in isAuthenticated method."""

    @pytest.mark.asyncio
    async def test_with_valid_originator(self) -> None:
        """Given: Wallet and valid originator string
        When: Call isAuthenticated with originator
        Then: Returns authenticated=true without error
        """
        # Given
        wallet = Wallet()
        originator = "test.example.com"

        # When
        result = await wallet.is_authenticated({}, originator=originator)

        # Then
        assert result == {"authenticated": True}
        # No exception raised

    @pytest.mark.asyncio
    async def test_with_invalid_originator_type(self) -> None:
        """Given: Wallet and non-string originator
        When: Call isAuthenticated with invalid originator type
        Then: Raises InvalidParameterError
        """
        # Given
        wallet = Wallet()
        invalid_originator = 123  # Not a string

        # When/Then
        with pytest.raises(InvalidParameterError) as exc_info:
            await wallet.is_authenticated({}, originator=invalid_originator)  # type: ignore

        assert "originator" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_with_too_long_originator(self) -> None:
        """Given: Wallet and originator > 250 bytes
        When: Call isAuthenticated with too long originator
        Then: Raises InvalidParameterError
        """
        # Given
        wallet = Wallet()
        too_long_originator = "a" * 251  # 251 bytes > 250

        # When/Then
        with pytest.raises(InvalidParameterError) as exc_info:
            await wallet.is_authenticated({}, originator=too_long_originator)

        assert "originator" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_with_none_originator(self) -> None:
        """Given: Wallet and None originator
        When: Call isAuthenticated with originator=None
        Then: Returns authenticated=true without error
        """
        # Given
        wallet = Wallet()

        # When
        result = await wallet.is_authenticated({}, originator=None)

        # Then
        assert result == {"authenticated": True}
        # No exception raised
