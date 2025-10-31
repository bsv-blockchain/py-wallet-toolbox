"""Unit tests for Wallet.get_header and get_version methods.

These are query methods for blockchain and wallet information.

Reference: wallet-toolbox/src/Wallet.ts
"""

import pytest

from bsv_wallet_toolbox import Wallet
from bsv_wallet_toolbox.errors import InvalidParameterError


class TestWalletGetHeader:
    """Test suite for Wallet.get_header method.

    getHeader retrieves a block header for a specific height.
    This is similar to getHeaderForHeight but follows BRC-100 args format.
    """

    @pytest.mark.skip(reason="Waiting for get_header implementation")
    def test_get_header_invalid_params_negative_height(self, wallet: Wallet) -> None:
        """Given: GetHeaderArgs with negative height
           When: Call get_header
           Then: Raises InvalidParameterError

        Note: Height must be non-negative.
        """
        # Given
        invalid_args = {"height": -1}  # Negative height

        # When / Then
        with pytest.raises(InvalidParameterError):
            wallet.get_header(invalid_args)

    @pytest.mark.skip(reason="Waiting for get_header implementation with services")
    def test_get_header_valid_height(self, wallet: Wallet) -> None:
        """Given: GetHeaderArgs with valid height
           When: Call get_header
           Then: Returns block header for that height

        Note: This test requires:
        - Configured WalletServices
        - Network connectivity or mock services
        """
        # Given
        args = {"height": 850000}  # Known block height

        # When
        result = wallet.get_header(args)

        # Then
        assert "header" in result
        assert isinstance(result["header"], bytes)
        assert len(result["header"]) == 80  # Block header is always 80 bytes


class TestWalletGetVersion:
    """Test suite for Wallet.get_version method (comprehensive tests)."""

    @pytest.mark.skip(reason="Waiting for get_version originator validation")
    def test_get_version_with_valid_originator(self, wallet: Wallet) -> None:
        """Given: Valid originator domain
           When: Call get_version with originator
           Then: Returns version without error

        Note: Tests originator validation in get_version.
        """
        # Given
        valid_originators = ["example.com", "subdomain.example.com", "localhost", "app.test.co.uk"]

        # When / Then
        for originator in valid_originators:
            result = wallet.get_version({}, originator=originator)
            assert "version" in result
            assert isinstance(result["version"], str)

    @pytest.mark.skip(reason="Waiting for get_version originator validation")
    def test_get_version_with_invalid_originator_too_long(self, wallet: Wallet) -> None:
        """Given: Originator exceeding 250 characters
           When: Call get_version
           Then: Raises InvalidParameterError

        Note: Originator must be at most 250 characters.
        """
        # Given
        too_long_originator = "a" * 251  # 251 characters

        # When / Then
        with pytest.raises(InvalidParameterError):
            wallet.get_version({}, originator=too_long_originator)

    @pytest.mark.skip(reason="Waiting for get_version originator validation")
    def test_get_version_with_invalid_originator_type(self, wallet: Wallet) -> None:
        """Given: Originator with invalid type (not string)
           When: Call get_version
           Then: Raises InvalidParameterError

        Note: Originator must be a string.
        """
        # Given
        invalid_originator = 123  # Not a string

        # When / Then
        with pytest.raises(InvalidParameterError):
            wallet.get_version({}, originator=invalid_originator)


class TestWalletConstructor:
    """Test suite for Wallet constructor and initialization.

    Reference: wallet-toolbox/test/wallet/construct/Wallet.constructor.test.ts
    """

    @pytest.mark.skip(reason="Waiting for Wallet constructor implementation")
    def test_wallet_constructor_with_valid_params(self) -> None:
        """Given: Valid constructor parameters
           When: Create Wallet instance
           Then: Wallet is successfully initialized

        Note: Tests basic wallet construction.
        """
        # Given / When
        wallet = Wallet(chain="main", root_key="a" * 64)  # Valid hex private key

        # Then
        assert wallet is not None
        assert wallet.chain == "main"

    @pytest.mark.skip(reason="Waiting for Wallet constructor implementation")
    def test_wallet_constructor_with_invalid_root_key(self) -> None:
        """Given: Invalid root key (not hex)
           When: Create Wallet instance
           Then: Raises InvalidParameterError

        Note: Root key must be valid hexadecimal.
        """
        # Given / When / Then
        with pytest.raises(InvalidParameterError):
            Wallet(chain="main", root_key="not_a_valid_hex_key")

    @pytest.mark.skip(reason="Waiting for Wallet constructor implementation")
    def test_wallet_constructor_with_invalid_chain(self) -> None:
        """Given: Invalid chain value (not 'main' or 'test')
           When: Create Wallet instance
           Then: Raises InvalidParameterError

        Note: Chain must be 'main' or 'test'.
        """
        # Given / When / Then
        with pytest.raises(InvalidParameterError):
            Wallet(chain="invalid_chain", root_key="a" * 64)
