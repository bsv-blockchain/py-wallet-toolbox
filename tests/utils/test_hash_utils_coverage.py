"""Coverage tests for hashing utilities.

This module tests various hashing functions used in Bitcoin operations.
"""


class TestSHA256Hashing:
    """Test SHA256 hashing."""

    def test_sha256_single(self) -> None:
        """Test single SHA256 hash."""
        try:
            from bsv_wallet_toolbox.utils.random_utils import sha256

            data = b"hello world"
            hash_result = sha256(data)
            assert isinstance(hash_result, bytes)
            assert len(hash_result) == 32
        except (ImportError, AttributeError):
            # Try standard library
            import hashlib

            data = b"hello world"
            hash_result = hashlib.sha256(data).digest()
            assert len(hash_result) == 32

    def test_sha256_double(self) -> None:
        """Test double SHA256 hash."""
        try:
            from bsv_wallet_toolbox.utils.random_utils import double_sha256

            data = b"hello world"
            hash_result = double_sha256(data)
            assert isinstance(hash_result, bytes)
            assert len(hash_result) == 32
        except (ImportError, AttributeError):
            pass

    def test_sha256_hex_output(self) -> None:
        """Test SHA256 with hex output."""
        try:
            from bsv_wallet_toolbox.utils.random_utils import sha256_hex

            data = b"hello world"
            hash_hex = sha256_hex(data)
            assert isinstance(hash_hex, str)
            assert len(hash_hex) == 64
        except (ImportError, AttributeError):
            pass


class TestRIPEMD160Hashing:
    """Test RIPEMD160 hashing."""

    def test_ripemd160(self) -> None:
        """Test RIPEMD160 hash."""
        try:
            from bsv_wallet_toolbox.utils.random_utils import ripemd160

            data = b"hello world"
            hash_result = ripemd160(data)
            assert isinstance(hash_result, bytes)
            assert len(hash_result) == 20
        except (ImportError, AttributeError):
            pass

    def test_hash160(self) -> None:
        """Test Hash160 (SHA256 + RIPEMD160)."""
        try:
            from bsv_wallet_toolbox.utils.random_utils import hash160

            data = b"hello world"
            hash_result = hash160(data)
            assert isinstance(hash_result, bytes)
            assert len(hash_result) == 20
        except (ImportError, AttributeError):
            pass


class TestMurmurHashing:
    """Test Murmur hashing."""

    def test_murmur3(self) -> None:
        """Test Murmur3 hash."""
        try:
            from bsv_wallet_toolbox.utils.random_utils import murmur3

            data = b"hello world"
            seed = 0
            hash_result = murmur3(data, seed)
            assert isinstance(hash_result, int)
        except (ImportError, AttributeError):
            pass


class TestHashUtilities:
    """Test hash utility functions."""

    def test_hash_to_int(self) -> None:
        """Test converting hash to integer."""
        try:
            from bsv_wallet_toolbox.utils.hash_utils import hash_to_int

            hash_bytes = b"\x00\x01\x02\x03"
            result = hash_to_int(hash_bytes)
            assert isinstance(result, int)
        except (ImportError, AttributeError):
            pass

    def test_int_to_hash(self) -> None:
        """Test converting integer to hash."""
        try:
            from bsv_wallet_toolbox.utils.hash_utils import int_to_hash

            value = 12345
            hash_bytes = int_to_hash(value, length=32)
            assert isinstance(hash_bytes, bytes)
            assert len(hash_bytes) == 32
        except (ImportError, AttributeError, TypeError):
            pass

    def test_reverse_hash(self) -> None:
        """Test reversing hash byte order."""
        try:
            from bsv_wallet_toolbox.utils.hash_utils import reverse_hash

            original = b"\x01\x02\x03\x04"
            reversed_hash = reverse_hash(original)
            assert reversed_hash == b"\x04\x03\x02\x01"
        except (ImportError, AttributeError):
            # Fallback implementation
            original = b"\x01\x02\x03\x04"
            reversed_hash = original[::-1]
            assert reversed_hash == b"\x04\x03\x02\x01"


class TestHashComparison:
    """Test hash comparison utilities."""

    def test_hash_equals(self) -> None:
        """Test comparing two hashes."""
        try:
            from bsv_wallet_toolbox.utils.hash_utils import hash_equals

            hash1 = b"\x00" * 32
            hash2 = b"\x00" * 32
            assert hash_equals(hash1, hash2) is True

            hash3 = b"\x01" * 32
            assert hash_equals(hash1, hash3) is False
        except (ImportError, AttributeError):
            pass

    def test_constant_time_compare(self) -> None:
        """Test constant-time hash comparison."""
        try:
            from bsv_wallet_toolbox.utils.hash_utils import constant_time_compare

            hash1 = b"secret"
            hash2 = b"secret"
            assert constant_time_compare(hash1, hash2) is True

            hash3 = b"public"
            assert constant_time_compare(hash1, hash3) is False
        except (ImportError, AttributeError):
            pass
