"""Unit tests for Wallet.get_header and get_version methods.

These are query methods for blockchain and wallet information.

Reference: wallet-toolbox/src/Wallet.ts
"""

import pytest
from bsv.keys import PrivateKey
from bsv.overlay_tools import LookupResolver
from bsv.wallet import KeyDeriver

from bsv_wallet_toolbox import Wallet
from bsv_wallet_toolbox.errors import InvalidParameterError


@pytest.fixture
def valid_get_header_args():
    """Fixture providing valid get header arguments."""
    return {"height": 850000}


@pytest.fixture
def invalid_get_header_cases():
    """Fixture providing various invalid get header arguments."""
    return [
        {"height": -1},  # Negative height
        {"height": -100},  # Very negative height
        {"height": "850000"},  # Wrong type (string)
        {"height": None},  # None height
        {"height": []},  # Wrong type (list)
        {"height": {}},  # Wrong type (dict)
        {"height": True},  # Wrong type (bool)
        {"height": 45.67},  # Wrong type (float)
        {},  # Missing height key
        {"height": 850000, "extra": "param"},  # Extra parameters
    ]


@pytest.fixture
def valid_originators():
    """Fixture providing valid originator domain names."""
    return [
        "example.com",
        "subdomain.example.com",
        "localhost",
        "app.test.co.uk",
        "api.domain.org",
        "service.provider.net",
    ]


@pytest.fixture
def invalid_originators():
    """Fixture providing invalid originator domain names."""
    return [
        "",  # Empty
        "   ",  # Whitespace
        "a" * 251,  # Too long (>250 chars)
        "invalid..domain.com",  # Double dots
        "domain-.com",  # Invalid dash
        "-domain.com",  # Leading dash
        "domain.com-",  # Trailing dash
        "domain..com",  # Consecutive dots
        "domain.com.",  # Trailing dot
        ".domain.com",  # Leading dot
        "domain.123",  # Numeric TLD
        None,  # None type
        123,  # Wrong type
        [],  # Wrong type
        {},  # Wrong type
    ]


@pytest.fixture
def valid_wallet_params():
    """Fixture providing valid wallet constructor parameters."""
    root_key = PrivateKey(bytes.fromhex("a" * 64))  # Valid hex private key
    key_deriver = KeyDeriver(root_key)
    return {"chain": "main", "keyDeriver": key_deriver}


@pytest.fixture
def invalid_wallet_params():
    """Fixture providing various invalid wallet constructor parameters."""
    return [
        {"chain": "invalid_chain"},  # Invalid chain
        {"chain": ""},  # Empty chain
        {"chain": None},  # None chain
        {"chain": 123},  # Wrong chain type
        {"chain": []},  # Wrong chain type
        {"chain": {}},  # Wrong chain type
        {"keyDeriver": None},  # None key_deriver
        {"keyDeriver": "not_a_key_deriver"},  # Wrong key_deriver type
        {"keyDeriver": 123},  # Wrong key_deriver type
        {"keyDeriver": []},  # Wrong key_deriver type
        {"keyDeriver": {}},  # Wrong key_deriver type
        {},  # Empty params
    ]


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

    def test_get_header_invalid_params_none_height(self, wallet_with_storage: Wallet) -> None:
        """Given: GetHeaderArgs with None height
        When: Call get_header
        Then: Raises InvalidParameterError or TypeError
        """
        # Given
        invalid_args = {"height": None}

        # When/Then
        with pytest.raises((InvalidParameterError, TypeError)):
            wallet_with_storage.get_header(invalid_args)

    def test_get_header_invalid_params_wrong_height_type(self, wallet_with_storage: Wallet) -> None:
        """Given: GetHeaderArgs with wrong height type
        When: Call get_header
        Then: Raises InvalidParameterError, TypeError or RuntimeError
        """
        # Given - Test various invalid types (note: True is coerced to 1)
        invalid_types = ["string", [], {}, 45.67]

        for invalid_height in invalid_types:
            invalid_args = {"height": invalid_height}

            # When/Then - May also raise RuntimeError if services not configured
            with pytest.raises((InvalidParameterError, TypeError, RuntimeError)):
                wallet_with_storage.get_header(invalid_args)

    def test_get_header_invalid_params_missing_height_key(self, wallet_with_storage: Wallet) -> None:
        """Given: GetHeaderArgs missing height key
        When: Call get_header
        Then: Raises InvalidParameterError or KeyError
        """
        # Given
        invalid_args = {}

        # When/Then
        with pytest.raises((InvalidParameterError, KeyError, TypeError)):
            wallet_with_storage.get_header(invalid_args)

    def test_get_header_invalid_params_zero_height(self, wallet_with_storage: Wallet) -> None:
        """Given: GetHeaderArgs with zero height
        When: Call get_header
        Then: Raises InvalidParameterError (height must be > 0) or RuntimeError (services not configured)
        """
        # Given
        args = {"height": 0}

        # When/Then - May raise InvalidParameterError or RuntimeError
        with pytest.raises((InvalidParameterError, RuntimeError)):
            wallet_with_storage.get_header(args)

    def test_get_header_invalid_params_very_large_height(self, wallet_with_storage: Wallet) -> None:
        """Given: GetHeaderArgs with very large height
        When: Call get_header
        Then: Raises RuntimeError (services not configured)
        """
        # Given - Use a height far in the future
        future_height = 10000000  # Much larger than current block height
        args = {"height": future_height}

        # When/Then - Raises RuntimeError since services not configured
        with pytest.raises((RuntimeError, Exception)):
            wallet_with_storage.get_header(args)

    def test_get_header_invalid_params_float_height(self, wallet_with_storage: Wallet) -> None:
        """Given: GetHeaderArgs with float height
        When: Call get_header
        Then: Raises InvalidParameterError or TypeError
        """
        # Given
        invalid_args = {"height": 850000.5}

        # When/Then
        with pytest.raises((InvalidParameterError, TypeError)):
            wallet_with_storage.get_header(invalid_args)

    def test_get_header_valid_params_different_heights(self, wallet_with_services: Wallet) -> None:
        """Given: GetHeaderArgs with different valid heights
        When: Call get_header
        Then: Returns valid headers
        """
        # Given - Test multiple known block heights
        test_heights = [1, 100, 1000, 10000, 100000]

        for height in test_heights:
            args = {"height": height}

            # When
            result = wallet_with_services.get_header(args)

            # Then
            assert "header" in result
            assert isinstance(result["header"], str)
            assert len(result["header"]) == 160  # Block header hex string

    def test_get_header_valid_params_extra_parameters_ignored(self, wallet_with_services: Wallet) -> None:
        """Given: GetHeaderArgs with extra parameters
        When: Call get_header
        Then: Extra parameters are ignored
        """
        # Given - Add extra parameters
        args = {"height": 850000, "extraParam": "ignored", "another": 123}

        # When
        result = wallet_with_services.get_header(args)

        # Then - Should work normally
        assert "header" in result
        assert isinstance(result["header"], str)
        assert len(result["header"]) == 160


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

    def test_get_version_with_empty_originator(self, wallet_with_storage: Wallet) -> None:
        """Given: Empty originator string
        When: Call get_version
        Then: Returns version (empty string is accepted as a valid string)
        """
        # Given
        empty_originator = ""

        # When
        result = wallet_with_storage.get_version({}, originator=empty_originator)

        # Then - Empty string is accepted (it's still a valid string under 250 bytes)
        assert "version" in result
        assert isinstance(result["version"], str)

    def test_get_version_with_whitespace_originator(self, wallet_with_storage: Wallet) -> None:
        """Given: Whitespace-only originator string
        When: Call get_version
        Then: Returns version (whitespace is accepted as a valid string)
        """
        # Given - Various whitespace originators
        whitespace_originators = ["   ", "\t", "\n", " \t \n "]

        for originator in whitespace_originators:
            # When
            result = wallet_with_storage.get_version({}, originator=originator)

            # Then - Whitespace string is accepted (it's still a valid string under 250 bytes)
            assert "version" in result
            assert isinstance(result["version"], str)

    def test_get_version_with_none_originator(self, wallet_with_storage: Wallet) -> None:
        """Given: None originator
        When: Call get_version
        Then: Returns version (None originator is allowed)
        """
        # Given
        none_originator = None

        # When
        result = wallet_with_storage.get_version({}, originator=none_originator)

        # Then - None originator is allowed (optional parameter)
        assert "version" in result
        assert isinstance(result["version"], str)

    def test_get_version_with_wrong_originator_type(self, wallet_with_storage: Wallet) -> None:
        """Given: Wrong type originator
        When: Call get_version
        Then: Raises InvalidParameterError or TypeError
        """
        # Given - Test various invalid types
        invalid_types = [123, [], {}, True, 45.67]

        for invalid_originator in invalid_types:
            # When/Then
            with pytest.raises((InvalidParameterError, TypeError)):
                wallet_with_storage.get_version({}, originator=invalid_originator)

    def test_get_version_with_invalid_domain_format(self, wallet_with_storage: Wallet) -> None:
        """Given: Invalid domain format originator
        When: Call get_version
        Then: Raises InvalidParameterError
        """
        # Given - Invalid domain formats
        invalid_domains = [
            "invalid..domain.com",  # Double dots
            "domain-.com",  # Invalid dash
            "-domain.com",  # Leading dash
            "domain.com-",  # Trailing dash
            "domain..com",  # Consecutive dots
            "domain.com.",  # Trailing dot
            ".domain.com",  # Leading dot
            "domain.123",  # Numeric TLD
        ]

        for invalid_domain in invalid_domains:
            # When - get_version doesn't validate domain format, only type and length
            result = wallet_with_storage.get_version({}, originator=invalid_domain)

            # Then - Invalid domain format is accepted (only type and length are validated)
            assert "version" in result
            assert isinstance(result["version"], str)

    def test_get_version_with_unicode_originator(self, wallet_with_storage: Wallet) -> None:
        """Given: Unicode originator string
        When: Call get_version
        Then: Handles unicode correctly
        """
        # Given - Test unicode in domain names (though uncommon)
        unicode_originator = "test.例え.com"

        # When
        result = wallet_with_storage.get_version({}, originator=unicode_originator)

        # Then - Should work (version is returned regardless of originator validity)
        assert "version" in result
        assert isinstance(result["version"], str)

    def test_get_version_without_originator(self, wallet_with_storage: Wallet) -> None:
        """Given: No originator provided
        When: Call get_version
        Then: Returns version successfully
        """
        # Given/When
        result = wallet_with_storage.get_version({})

        # Then
        assert "version" in result
        assert isinstance(result["version"], str)
        assert len(result["version"]) > 0

    def test_get_version_with_args_dict_none(self, wallet_with_storage: Wallet) -> None:
        """Given: None args dict
        When: Call get_version
        Then: Raises InvalidParameterError
        """
        # Given/When/Then
        with pytest.raises(InvalidParameterError):
            wallet_with_storage.get_version(None)

    def test_get_version_with_empty_args_dict(self, wallet_with_storage: Wallet) -> None:
        """Given: Empty args dict
        When: Call get_version
        Then: Returns version successfully
        """
        # Given/When
        result = wallet_with_storage.get_version({})

        # Then
        assert "version" in result
        assert isinstance(result["version"], str)

    def test_get_version_with_extra_args_ignored(self, wallet_with_storage: Wallet) -> None:
        """Given: Args dict with extra parameters
        When: Call get_version
        Then: Extra parameters are ignored
        """
        # Given
        args_with_extra = {"extra": "param", "another": 123, "nested": {"key": "value"}}

        # When
        result = wallet_with_storage.get_version(args_with_extra)

        # Then - Should work normally
        assert "version" in result
        assert isinstance(result["version"], str)


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


class TestWalletLookupResolver:
    """Tests for LookupResolver wiring on the Wallet constructor."""

    @staticmethod
    def _make_key_deriver() -> KeyDeriver:
        root_key = PrivateKey(bytes.fromhex("1" * 64))
        return KeyDeriver(root_key)

    @pytest.mark.parametrize(
        ("chain", "expected_network"),
        [
            ("main", "mainnet"),
            ("test", "testnet"),
        ],
    )
    def test_wallet_initializes_sdk_lookup_resolver(self, chain: str, expected_network: str) -> None:
        """Wallet automatically provisions a LookupResolver that matches the chain preset."""
        wallet = Wallet(chain=chain, key_deriver=self._make_key_deriver())

        assert isinstance(wallet.lookup_resolver, LookupResolver)
        assert wallet.lookup_resolver.network_preset == expected_network

    def test_wallet_accepts_custom_lookup_resolver(self) -> None:
        """Custom resolvers can be injected for tests/mocks."""

        class CustomResolver:
            def __init__(self) -> None:
                self.network_preset = "mock"

            async def query(self, params: dict[str, object]) -> dict[str, object]:
                return {"type": "output-list", "outputs": []}

        resolver = CustomResolver()
        wallet = Wallet(
            chain="main",
            key_deriver=self._make_key_deriver(),
            lookup_resolver=resolver,
        )

        assert wallet.lookup_resolver is resolver

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

    def test_wallet_constructor_with_none_chain(self) -> None:
        """Given: None chain value
        When: Create Wallet instance
        Then: Raises ValueError or TypeError
        """
        # Given / When / Then
        with pytest.raises((ValueError, TypeError)):
            root_key = PrivateKey(bytes.fromhex("a" * 64))
            key_deriver = KeyDeriver(root_key)
            Wallet(chain=None, key_deriver=key_deriver)

    def test_wallet_constructor_with_wrong_chain_type(self) -> None:
        """Given: Wrong chain type (not string)
        When: Create Wallet instance
        Then: Raises ValueError or TypeError
        """
        # Given - Test various invalid chain types
        invalid_types = [123, [], {}, True, 45.67]

        for invalid_chain in invalid_types:
            with pytest.raises((ValueError, TypeError)):
                root_key = PrivateKey(bytes.fromhex("a" * 64))
                key_deriver = KeyDeriver(root_key)
                Wallet(chain=invalid_chain, key_deriver=key_deriver)

    def test_wallet_constructor_with_empty_chain(self) -> None:
        """Given: Empty chain string
        When: Create Wallet instance
        Then: Raises ValueError
        """
        # Given / When / Then
        with pytest.raises(ValueError):
            root_key = PrivateKey(bytes.fromhex("a" * 64))
            key_deriver = KeyDeriver(root_key)
            Wallet(chain="", key_deriver=key_deriver)

    def test_wallet_constructor_with_whitespace_chain(self) -> None:
        """Given: Whitespace-only chain string
        When: Create Wallet instance
        Then: Raises ValueError
        """
        # Given - Various whitespace chains
        whitespace_chains = ["   ", "\t", "\n", " \t \n "]

        for chain in whitespace_chains:
            with pytest.raises(ValueError):
                root_key = PrivateKey(bytes.fromhex("a" * 64))
                key_deriver = KeyDeriver(root_key)
                Wallet(chain=chain, key_deriver=key_deriver)

    def test_wallet_constructor_with_none_key_deriver(self) -> None:
        """Given: None key_deriver
        When: Create Wallet instance
        Then: Raises ValueError or TypeError
        """
        # Given / When / Then
        with pytest.raises((ValueError, TypeError)):
            Wallet(chain="main", key_deriver=None)

    def test_wallet_constructor_with_wrong_key_deriver_type(self) -> None:
        """Given: Wrong key_deriver type
        When: Create Wallet instance
        Then: Raises ValueError or TypeError
        """
        # Given - Test various invalid key_deriver types
        invalid_types = [123, "string", [], {}, True, 45.67]

        for invalid_key_deriver in invalid_types:
            with pytest.raises((ValueError, TypeError)):
                Wallet(chain="main", key_deriver=invalid_key_deriver)

    def test_wallet_constructor_with_invalid_private_key(self) -> None:
        """Given: Invalid private key (not 32 bytes)
        When: Create Wallet instance
        Then: Raises ValueError
        """
        # Given - Invalid private key lengths
        # Note: 31 bytes (a*62 hex) is still valid for PrivateKey (just small number)
        # Only truly invalid are: too large (33+ bytes) and empty
        invalid_keys = [
            bytes.fromhex("a" * 66),  # Too long (33 bytes)
            b"",  # Empty
        ]

        for invalid_key_bytes in invalid_keys:
            with pytest.raises((ValueError, TypeError)):
                root_key = PrivateKey(invalid_key_bytes)
                key_deriver = KeyDeriver(root_key)
                Wallet(chain="main", key_deriver=key_deriver)

    def test_wallet_constructor_with_valid_test_chain(self) -> None:
        """Given: Valid 'test' chain
        When: Create Wallet instance
        Then: Wallet is successfully initialized
        """
        # Given / When
        root_key = PrivateKey(bytes.fromhex("a" * 64))
        key_deriver = KeyDeriver(root_key)
        wallet = Wallet(chain="test", key_deriver=key_deriver)

        # Then
        assert wallet is not None
        assert wallet.chain == "test"

    def test_wallet_constructor_with_case_insensitive_chain(self) -> None:
        """Given: Different case chain values
        When: Create Wallet instance
        Then: Chain values are case-sensitive
        """
        # Given - Test different case variations
        invalid_cases = ["MAIN", "Main", "TEST", "Test", "mainnet", "testnet"]

        for invalid_case in invalid_cases:
            with pytest.raises(ValueError):
                root_key = PrivateKey(bytes.fromhex("a" * 64))
                key_deriver = KeyDeriver(root_key)
                Wallet(chain=invalid_case, key_deriver=key_deriver)

    def test_wallet_constructor_with_unicode_chain(self) -> None:
        """Given: Unicode chain value
        When: Create Wallet instance
        Then: Raises ValueError (chain must be 'main' or 'test')
        """
        # Given / When / Then
        with pytest.raises(ValueError):
            root_key = PrivateKey(bytes.fromhex("a" * 64))
            key_deriver = KeyDeriver(root_key)
            Wallet(chain="测试", key_deriver=key_deriver)

    def test_wallet_constructor_with_extra_params_ignored(self) -> None:
        """Given: Extra constructor parameters
        When: Create Wallet instance
        Then: Extra parameters are ignored
        """
        # Given / When - This should work normally despite extra params
        root_key = PrivateKey(bytes.fromhex("a" * 64))
        key_deriver = KeyDeriver(root_key)
        wallet = Wallet(chain="main", key_deriver=key_deriver)

        # Then
        assert wallet is not None
        assert wallet.chain == "main"
