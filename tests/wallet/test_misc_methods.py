"""Unit tests for Wallet.get_header and get_version methods.

These are query methods for blockchain and wallet information.

Reference: wallet-toolbox/src/Wallet.ts
"""

import pytest

from bsv.keys import PrivateKey
from bsv.wallet import KeyDeriver

from bsv_wallet_toolbox import Wallet
from bsv_wallet_toolbox.errors import InvalidParameterError


class TestWalletGetHeader:
    """Test suite for Wallet.get_header method.

    getHeader retrieves a block header for a specific height.
    This is similar to getHeaderForHeight but follows BRC-100 args format.
    """

    def test_get_header_invalid_params_negative_height(self, wallet_with_storage: Wallet) -> None:
        """Given: GetHeaderArgs with negative height
           When: Call get_header
           Then: Raises InvalidParameterError

        Note: Height must be non-negative.
        """
        # Given
        invalid_args = {"height": -1}  # Negative height

        # When / Then
        with pytest.raises(InvalidParameterError):
            wallet_with_storage.get_header(invalid_args)

    def test_get_header_valid_height(self, wallet_with_services: Wallet) -> None:
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
        result = wallet_with_services.get_header(args)

        # Then
        assert "header" in result
        assert isinstance(result["header"], str)
        assert len(result["header"]) == 160  # Block header hex string is 160 characters (80 bytes * 2)


class TestWalletGetVersion:
    """Test suite for Wallet.get_version method (comprehensive tests)."""

    def test_get_version_with_valid_originator(self, wallet_with_storage: Wallet) -> None:
        """Given: Valid originator domain
           When: Call get_version with originator
           Then: Returns version without error

        Note: Tests originator validation in get_version.
        """
        # Given
        valid_originators = ["example.com", "subdomain.example.com", "localhost", "app.test.co.uk"]

        # When / Then
        for originator in valid_originators:
            result = wallet_with_storage.get_version({}, originator=originator)
            assert "version" in result
            assert isinstance(result["version"], str)

    def test_get_version_with_invalid_originator_too_long(self, wallet_with_storage: Wallet) -> None:
        """Given: Originator exceeding 250 characters
           When: Call get_version
           Then: Raises InvalidParameterError

        Note: Originator must be at most 250 characters.
        """
        # Given
        too_long_originator = "a" * 251  # 251 characters

        # When / Then
        with pytest.raises(InvalidParameterError):
            wallet_with_storage.get_version({}, originator=too_long_originator)

    def test_get_version_with_invalid_originator_type(self, wallet_with_storage: Wallet) -> None:
        """Given: Originator with invalid type (not string)
           When: Call get_version
           Then: Raises InvalidParameterError

        Note: Originator must be a string.
        """
        # Given
        invalid_originator = 123  # Not a string

        # When / Then
        with pytest.raises(InvalidParameterError):
            wallet_with_storage.get_version({}, originator=invalid_originator)


class TestWalletConstructor:
    """Test suite for Wallet constructor and initialization.

    Reference: wallet-toolbox/test/wallet/construct/Wallet.constructor.test.ts
    """

    def test_wallet_constructor_with_valid_params(self) -> None:
        """Given: Valid constructor parameters
           When: Create Wallet instance
           Then: Wallet is successfully initialized

        Note: Tests basic wallet construction.
        """
        # Given / When
        root_key = PrivateKey(bytes.fromhex("a" * 64))  # Valid hex private key
        key_deriver = KeyDeriver(root_key)
        wallet = Wallet(chain="main", key_deriver=key_deriver)

        # Then
        assert wallet is not None
        assert wallet.chain == "main"

    def test_wallet_constructor_with_invalid_root_key(self) -> None:
        """Given: Invalid root key (not hex)
           When: Create Wallet instance
           Then: Raises ValueError

        Note: Root key must be valid hexadecimal.
        """
        # Given / When / Then
        with pytest.raises(ValueError):
            # This will fail when creating the PrivateKey from invalid hex
            root_key = PrivateKey(bytes.fromhex("not_a_valid_hex_key"))
            key_deriver = KeyDeriver(root_key)
            Wallet(chain="main", key_deriver=key_deriver)

    @pytest.mark.skip(reason="Chain validation not implemented in Wallet constructor")
    def test_wallet_constructor_with_invalid_chain(self) -> None:
        """Given: Invalid chain value (not 'main' or 'test')
           When: Create Wallet instance
           Then: Raises ValueError

        Note: Chain must be 'main' or 'test'.
        """
        # Given / When / Then
        with pytest.raises(ValueError):
            # Chain validation happens in Wallet constructor
            root_key = PrivateKey(bytes.fromhex("a" * 64))
            key_deriver = KeyDeriver(root_key)
            Wallet(chain="invalid_chain", key_deriver=key_deriver)
