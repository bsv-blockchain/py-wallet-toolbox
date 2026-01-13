"""Cryptographic utilities for wallet operations.

Provides cryptographic primitives used by CWI-style wallet management and
permission systems, including PBKDF2 key derivation, XOR operations, and
symmetric encryption.

Reference: wallet-toolbox/src/CWIStyleWalletManager.ts crypto operations
"""

import hashlib

# PBKDF2 rounds used in CWI-style wallet authentication
PBKDF2_NUM_ROUNDS = 7777


def pbkdf2_derive_key(password: bytes, salt: bytes, key_length: int = 32) -> bytes:
    """Derive key using PBKDF2 with fixed number of rounds.

    Args:
        password: Password bytes to derive from
        salt: Salt bytes for PBKDF2
        key_length: Desired key length in bytes (default: 32)

    Returns:
        Derived key bytes

    Reference: wallet-toolbox/src/CWIStyleWalletManager.ts PBKDF2 usage
    """
    return hashlib.pbkdf2_hmac("sha256", password, salt, PBKDF2_NUM_ROUNDS, dklen=key_length)


def xor_bytes(a: bytes, b: bytes) -> bytes:
    """XOR two byte sequences.

    If the sequences have different lengths, the shorter one is cycled
    to match the length of the longer one.

    Args:
        a: First byte sequence
        b: Second byte sequence

    Returns:
        XOR result

    Reference: wallet-toolbox/src/CWIStyleWalletManager.ts XOR operations
    """
    # Check for empty input edge case - cannot cycle empty sequence
    if (len(a) == 0 and len(b) > 0) or (len(b) == 0 and len(a) > 0):
        raise ValueError("different lengths")

    # Cycle the shorter sequence to match the longer one
    if len(a) > len(b):
        # Repeat b to match a's length
        b = (b * ((len(a) // len(b)) + 1))[: len(a)]
    elif len(b) > len(a):
        # Repeat a to match b's length
        a = (a * ((len(b) // len(a)) + 1))[: len(b)]

    return bytes(x ^ y for x, y in zip(a, b, strict=False))


def sha256_hash(data: bytes) -> bytes:
    """Compute SHA-256 hash of data.

    Args:
        data: Data to hash

    Returns:
        SHA-256 hash bytes (32 bytes)
    """
    return hashlib.sha256(data).digest()


def bytes_to_int_list(data: bytes) -> list[int]:
    """Convert bytes to list of integers.

    Args:
        data: Bytes to convert

    Returns:
        List of integers (0-255)
    """
    return list(data)


def int_list_to_bytes(data: list[int]) -> bytes:
    """Convert list of integers to bytes.

    Args:
        data: List of integers (0-255)

    Returns:
        Bytes object

    Raises:
        ValueError: If any value is outside 0-255 range
    """
    if any(not (0 <= x <= 255) for x in data):
        raise ValueError("All values must be in range 0-255")

    return bytes(data)


class SymmetricKey:
    """Simple symmetric key wrapper for XOR-based encryption.

    Uses XOR for encryption/decryption, suitable for the key derivation
    patterns used in CWI-style wallet authentication.

    Reference: wallet-toolbox/src/CWIStyleWalletManager.ts SymmetricKey usage
    """

    def __init__(self, key: bytes) -> None:
        """Initialize SymmetricKey.

        Args:
            key: Encryption/decryption key bytes
        """
        self._key = key

    def encrypt(self, plaintext: bytes) -> bytes:
        """Encrypt plaintext using XOR.

        Args:
            plaintext: Data to encrypt

        Returns:
            Encrypted ciphertext
        """
        return xor_bytes(plaintext, self._key)

    def decrypt(self, ciphertext: bytes) -> bytes:
        """Decrypt ciphertext using XOR.

        Note: XOR encryption is symmetric, so decrypt = encrypt.

        Args:
            ciphertext: Data to decrypt

        Returns:
            Decrypted plaintext
        """
        return self.encrypt(ciphertext)  # XOR is symmetric


def derive_password_key(password: str, salt: bytes) -> bytes:
    """Derive password key using PBKDF2.

    Args:
        password: Password string
        salt: Salt bytes

    Returns:
        Derived password key (32 bytes)
    """
    password_bytes = password.encode("utf-8")
    return pbkdf2_derive_key(password_bytes, salt)


def create_ump_key_derivations(
    presentation_key: bytes,
    recovery_key: bytes,
    password_key: bytes,
    primary_key: bytes,
    privileged_key: bytes,
) -> dict[str, bytes]:
    """Create all UMP token key derivations.

    Args:
        presentation_key: User's presentation key
        recovery_key: User's recovery key
        password_key: Derived password key
        primary_key: Wallet primary key
        privileged_key: Privileged key for admin operations

    Returns:
        Dictionary containing all key derivations for UMP token

    Reference: wallet-toolbox/src/CWIStyleWalletManager.ts UMP token construction
    """
    # Create symmetric keys for XOR encryption
    presentation_password = SymmetricKey(xor_bytes(presentation_key, password_key))
    presentation_recovery = SymmetricKey(xor_bytes(presentation_key, recovery_key))
    recovery_password = SymmetricKey(xor_bytes(recovery_key, password_key))
    primary_password = SymmetricKey(xor_bytes(primary_key, password_key))
    primary_presentation = SymmetricKey(xor_bytes(primary_key, presentation_key))
    primary_recovery = SymmetricKey(xor_bytes(primary_key, recovery_key))
    privileged_password = SymmetricKey(xor_bytes(privileged_key, password_key))
    privileged_presentation = SymmetricKey(xor_bytes(privileged_key, presentation_key))
    privileged_recovery = SymmetricKey(xor_bytes(privileged_key, recovery_key))

    return {
        "presentationPassword": presentation_password._key,
        "presentationRecovery": presentation_recovery._key,
        "recoveryPassword": recovery_password._key,
        "primaryPassword": primary_password._key,
        "primaryPresentation": primary_presentation._key,
        "primaryRecovery": primary_recovery._key,
        "privilegedPassword": privileged_password._key,
        "privilegedPresentation": privileged_presentation._key,
        "privilegedRecovery": privileged_recovery._key,
    }


def create_ump_token_fields(
    presentation_key: bytes,
    recovery_key: bytes,
    password_key: bytes,
    primary_key: bytes,
    privileged_key: bytes,
    password_salt: bytes,
) -> list[list[int]]:
    """Create UMP token fields for PushDrop script.

    Args:
        presentation_key: User's presentation key
        recovery_key: User's recovery key
        password_key: Derived password key
        primary_key: Wallet primary key
        privileged_key: Privileged key for admin operations
        password_salt: PBKDF2 salt

    Returns:
        List of field byte arrays for PushDrop script

    Reference: wallet-toolbox/src/CWIStyleWalletManager.ts buildAndSend fields construction
    """
    derivations = create_ump_key_derivations(presentation_key, recovery_key, password_key, primary_key, privileged_key)

    # Create encrypted copies of keys using privileged key
    privileged_key_obj = SymmetricKey(privileged_key)
    presentation_key_encrypted = privileged_key_obj.encrypt(presentation_key)
    recovery_key_encrypted = privileged_key_obj.encrypt(recovery_key)
    password_key_encrypted = privileged_key_obj.encrypt(password_key)

    # Create presentation and recovery hashes
    presentation_hash = sha256_hash(presentation_key)
    recovery_hash = sha256_hash(recovery_key)

    # Build fields array (matching TypeScript implementation order)
    fields = [
        bytes_to_int_list(password_salt),  # 0: passwordSalt
        bytes_to_int_list(derivations["primaryPassword"]),  # 1: passwordPresentationPrimary
        bytes_to_int_list(derivations["primaryRecovery"]),  # 2: passwordRecoveryPrimary
        bytes_to_int_list(derivations["primaryPresentation"]),  # 3: presentationRecoveryPrimary
        bytes_to_int_list(derivations["privilegedPassword"]),  # 4: passwordPrimaryPrivileged
        bytes_to_int_list(derivations["privilegedPresentation"]),  # 5: presentationRecoveryPrivileged
        bytes_to_int_list(presentation_hash),  # 6: presentationHash
        bytes_to_int_list(recovery_hash),  # 7: recoveryHash
        bytes_to_int_list(presentation_key_encrypted),  # 8: presentationKeyEncrypted
        bytes_to_int_list(password_key_encrypted),  # 9: passwordKeyEncrypted
        bytes_to_int_list(recovery_key_encrypted),  # 10: recoveryKeyEncrypted
    ]

    return fields


def validate_key_length(key: bytes, expected_length: int, name: str) -> None:
    """Validate that a key has the expected length.

    Args:
        key: Key bytes to validate
        expected_length: Expected length in bytes
        name: Key name for error messages

    Raises:
        ValueError: If key length is incorrect
    """
    if len(key) != expected_length:
        raise ValueError(f"{name} must be {expected_length} bytes, got {len(key)}")


def generate_random_bytes(length: int) -> bytes:
    """Generate random bytes of specified length.

    Args:
        length: Number of random bytes to generate

    Returns:
        Random bytes
    """
    import os

    return os.urandom(length)
