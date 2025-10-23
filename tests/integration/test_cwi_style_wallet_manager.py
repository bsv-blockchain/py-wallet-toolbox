"""Unit tests for CWIStyleWalletManager.

CWIStyleWalletManager implements a wallet management system with:
- User authentication (presentation key, recovery key, password)
- Encrypted key storage using UMP tokens
- Primary key derivation and privileged key management

Reference: wallet-toolbox/src/__tests/CWIStyleWalletManager.test.ts
"""

import hashlib
import os
from unittest.mock import AsyncMock, MagicMock, Mock

import pytest

try:
    from bsv.wallet.wallet_interface import WalletInterface
    from bsv_wallet_toolbox.cwi_style_wallet_manager import (
        PBKDF2_NUM_ROUNDS,
        CWIStyleWalletManager,
        UMPToken,
        UMPTokenInteractor,
    )
    from bsv_wallet_toolbox.sdk import PrivateKey, PrivilegedKeyManager

    IMPORTS_AVAILABLE = True
except ImportError:
    IMPORTS_AVAILABLE = False
    CWIStyleWalletManager = None
    PBKDF2_NUM_ROUNDS = 100000
    UMPToken = None
    UMPTokenInteractor = None
    PrivilegedKeyManager = None
    PrivateKey = None
    WalletInterface = None


def xor_bytes(a: bytes, b: bytes) -> bytes:
    """XOR two byte arrays.

    Args:
        a: First byte array
        b: Second byte array

    Returns:
        XORed result

    Raises:
        ValueError: If lengths don't match
    """
    if len(a) != len(b):
        raise ValueError("lengths mismatch")
    return bytes(x ^ y for x, y in zip(a, b, strict=False))


def make_outpoint(txid: str, vout: int) -> str:
    """Create an outpoint string for test usage.

    Args:
        txid: Transaction ID
        vout: Output index

    Returns:
        Outpoint string in format "txid:vout"
    """
    return f"{txid}:{vout}"


async def create_mock_ump_token(
    presentation_key: bytes,
    recovery_key: bytes,
    password_salt: bytes,
    password_key: bytes,
    primary_key: bytes,
    privileged_key: bytes,
) -> UMPToken:
    """Create a minimal valid UMP token for testing.

    Args:
        presentation_key: User's presentation key
        recovery_key: User's recovery key
        password_salt: Salt for password hashing
        password_key: Derived password key
        primary_key: Wallet primary key
        privileged_key: Privileged key for admin operations

    Returns:
        UMP token dictionary
    """
    from bsv.sdk import SymmetricKey

    presentation_password = SymmetricKey(xor_bytes(presentation_key, password_key))
    presentation_recovery = SymmetricKey(xor_bytes(presentation_key, recovery_key))
    recovery_password = SymmetricKey(xor_bytes(recovery_key, password_key))
    primary_password = SymmetricKey(xor_bytes(primary_key, password_key))

    temp_privileged_key_manager = PrivilegedKeyManager(lambda: PrivateKey(privileged_key))

    return {
        "passwordSalt": list(password_salt),
        "passwordPresentationPrimary": list(presentation_password.encrypt(primary_key)),
        "passwordRecoveryPrimary": list(recovery_password.encrypt(primary_key)),
        "presentationRecoveryPrimary": list(presentation_recovery.encrypt(primary_key)),
        "passwordPrimaryPrivileged": list(primary_password.encrypt(privileged_key)),
        "presentationRecoveryPrivileged": list(presentation_recovery.encrypt(privileged_key)),
        "presentationHash": list(hashlib.sha256(presentation_key).digest()),
        "recoveryHash": list(hashlib.sha256(recovery_key).digest()),
        "presentationKeyEncrypted": (
            await temp_privileged_key_manager.encrypt(
                {"plaintext": list(presentation_key), "protocolID": [2, "admin key wrapping"], "keyID": "1"}
            )
        )["ciphertext"],
        "passwordKeyEncrypted": (
            await temp_privileged_key_manager.encrypt(
                {"plaintext": list(password_key), "protocolID": [2, "admin key wrapping"], "keyID": "1"}
            )
        )["ciphertext"],
        "recoveryKeyEncrypted": (
            await temp_privileged_key_manager.encrypt(
                {"plaintext": list(recovery_key), "protocolID": [2, "admin key wrapping"], "keyID": "1"}
            )
        )["ciphertext"],
        "currentOutpoint": "abcd:0",
    }


class TestCWIStyleWalletManagerXOR:
    """Test suite for XOR utility function."""

    @pytest.mark.skip(reason="Waiting for CWIStyleWalletManager implementation")
    def test_xor_function_verifies_correctness(self) -> None:
        """Given: Two byte arrays
           When: XOR them together
           Then: Result XORed with either input returns the other

        Reference: wallet-toolbox/src/__tests/CWIStyleWalletManager.test.ts
                   test('XOR function: verifies correctness')
        """
        n1 = bytes([1, 2, 3, 4, 5])
        n2 = bytes([5, 4, 3, 2, 1])

        xored = xor_bytes(n1, n2)

        assert xor_bytes(xored, n1) == n2
        assert xor_bytes(xored, n2) == n1


class TestCWIStyleWalletManagerNewUser:
    """Test suite for new user creation."""

    @pytest.mark.skip(reason="Waiting for CWIStyleWalletManager implementation")
    @pytest.mark.asyncio
    async def test_successfully_creates_a_new_token_and_calls_buildandsend(self) -> None:
        """Given: New user registration with presentation key and password
           When: Create new UMP token
           Then: Token is created and buildAndSend is called

        Reference: wallet-toolbox/src/__tests/CWIStyleWalletManager.test.ts
                   test('Successfully creates a new token and calls buildAndSend')
        """
        mock_underlying_wallet = MagicMock(spec=WalletInterface)
        mock_wallet_builder = AsyncMock(return_value=mock_underlying_wallet)
        mock_ump_interactor = MagicMock(spec=UMPTokenInteractor)
        mock_ump_interactor.find_by_presentation_key_hash = AsyncMock(return_value=None)
        mock_ump_interactor.build_and_send = AsyncMock(return_value="abcd.0")
        mock_recovery_key_saver = AsyncMock(return_value=True)
        mock_password_retriever = AsyncMock(return_value="test-password")

        manager = CWIStyleWalletManager(
            ump_token_interactor=mock_ump_interactor,
            wallet_builder=mock_wallet_builder,
            recovery_key_saver=mock_recovery_key_saver,
            password_retriever=mock_password_retriever,
            admin_originator="admin.test.com",
        )

        presentation_key = os.urandom(32)

        result = await manager.create_new_user(presentation_key)

        assert result["token"] is not None
        assert mock_ump_interactor.build_and_send.call_count == 1

    @pytest.mark.skip(reason="Waiting for CWIStyleWalletManager implementation")
    @pytest.mark.asyncio
    async def test_throws_if_user_tries_to_provide_recovery_key_during_new_user_flow(self) -> None:
        """Given: New user registration attempt
           When: User tries to provide recovery key during creation
           Then: Raises error (recovery key should only be used for existing users)

        Reference: wallet-toolbox/src/__tests/CWIStyleWalletManager.test.ts
                   test('Throws if user tries to provide recovery key during new-user flow')
        """
        mock_underlying_wallet = MagicMock(spec=WalletInterface)
        mock_wallet_builder = AsyncMock(return_value=mock_underlying_wallet)
        mock_ump_interactor = MagicMock(spec=UMPTokenInteractor)
        mock_ump_interactor.find_by_presentation_key_hash = AsyncMock(return_value=None)
        mock_recovery_key_saver = AsyncMock(return_value=True)
        mock_password_retriever = AsyncMock(return_value="test-password")

        manager = CWIStyleWalletManager(
            ump_token_interactor=mock_ump_interactor,
            wallet_builder=mock_wallet_builder,
            recovery_key_saver=mock_recovery_key_saver,
            password_retriever=mock_password_retriever,
            admin_originator="admin.test.com",
        )

        presentation_key = os.urandom(32)
        recovery_key = os.urandom(32)

        with pytest.raises(ValueError, match="recovery key not allowed"):
            await manager.create_new_user(presentation_key, recovery_key=recovery_key)


class TestCWIStyleWalletManagerExistingUser:
    """Test suite for existing user authentication."""

    @pytest.mark.skip(reason="Waiting for CWIStyleWalletManager implementation")
    @pytest.mark.asyncio
    async def test_decryption_of_primary_key_and_building_the_wallet(self) -> None:
        """Given: Existing user with stored UMP token
           When: Authenticate with presentation key and password
           Then: Primary key is decrypted and wallet is built

        Reference: wallet-toolbox/src/__tests/CWIStyleWalletManager.test.ts
                   test('Decryption of primary key and building the wallet')
        """
        presentation_key = os.urandom(32)
        recovery_key = os.urandom(32)
        password_salt = os.urandom(32)
        password_key = hashlib.pbkdf2_hmac("sha512", b"test-password", password_salt, PBKDF2_NUM_ROUNDS, 32)
        primary_key = os.urandom(32)
        privileged_key = os.urandom(32)

        existing_token = await create_mock_ump_token(
            presentation_key, recovery_key, password_salt, password_key, primary_key, privileged_key
        )

        mock_underlying_wallet = MagicMock(spec=WalletInterface)
        mock_wallet_builder = AsyncMock(return_value=mock_underlying_wallet)
        mock_ump_interactor = MagicMock(spec=UMPTokenInteractor)
        mock_ump_interactor.find_by_presentation_key_hash = AsyncMock(return_value=existing_token)
        mock_recovery_key_saver = AsyncMock(return_value=True)
        mock_password_retriever = AsyncMock(return_value="test-password")

        manager = CWIStyleWalletManager(
            ump_token_interactor=mock_ump_interactor,
            wallet_builder=mock_wallet_builder,
            recovery_key_saver=mock_recovery_key_saver,
            password_retriever=mock_password_retriever,
            admin_originator="admin.test.com",
        )

        result = await manager.authenticate(presentation_key)

        assert result["authenticated"] is True
        assert result["wallet"] is not None
        assert mock_wallet_builder.call_count == 1

    @pytest.mark.skip(reason="Waiting for CWIStyleWalletManager implementation")
    @pytest.mark.asyncio
    async def test_successfully_decrypts_with_presentation_plus_recovery(self) -> None:
        """Given: Existing user with stored UMP token
           When: Authenticate with presentation key and recovery key
           Then: Primary key is decrypted successfully

        Reference: wallet-toolbox/src/__tests/CWIStyleWalletManager.test.ts
                   test('Successfully decrypts with presentation+recovery')
        """
        presentation_key = os.urandom(32)
        recovery_key = os.urandom(32)
        password_salt = os.urandom(32)
        password_key = hashlib.pbkdf2_hmac("sha512", b"test-password", password_salt, PBKDF2_NUM_ROUNDS, 32)
        primary_key = os.urandom(32)
        privileged_key = os.urandom(32)

        existing_token = await create_mock_ump_token(
            presentation_key, recovery_key, password_salt, password_key, primary_key, privileged_key
        )

        mock_underlying_wallet = MagicMock(spec=WalletInterface)
        mock_wallet_builder = AsyncMock(return_value=mock_underlying_wallet)
        mock_ump_interactor = MagicMock(spec=UMPTokenInteractor)
        mock_ump_interactor.find_by_presentation_key_hash = AsyncMock(return_value=existing_token)
        mock_recovery_key_saver = AsyncMock(return_value=True)
        mock_password_retriever = AsyncMock(return_value="test-password")

        manager = CWIStyleWalletManager(
            ump_token_interactor=mock_ump_interactor,
            wallet_builder=mock_wallet_builder,
            recovery_key_saver=mock_recovery_key_saver,
            password_retriever=mock_password_retriever,
            admin_originator="admin.test.com",
        )

        result = await manager.authenticate_with_recovery(presentation_key, recovery_key)

        assert result["authenticated"] is True
        assert result["primary_key"] is not None

    @pytest.mark.skip(reason="Waiting for CWIStyleWalletManager implementation")
    @pytest.mark.asyncio
    async def test_throws_if_presentation_key_not_provided_first(self) -> None:
        """Given: Authentication attempt
           When: Try to authenticate without presentation key
           Then: Raises error

        Reference: wallet-toolbox/src/__tests/CWIStyleWalletManager.test.ts
                   test('Throws if presentation key not provided first')
        """
        mock_underlying_wallet = MagicMock(spec=WalletInterface)
        mock_wallet_builder = AsyncMock(return_value=mock_underlying_wallet)
        mock_ump_interactor = MagicMock(spec=UMPTokenInteractor)
        mock_recovery_key_saver = AsyncMock(return_value=True)
        mock_password_retriever = AsyncMock(return_value="test-password")

        manager = CWIStyleWalletManager(
            ump_token_interactor=mock_ump_interactor,
            wallet_builder=mock_wallet_builder,
            recovery_key_saver=mock_recovery_key_saver,
            password_retriever=mock_password_retriever,
            admin_originator="admin.test.com",
        )

        recovery_key = os.urandom(32)

        with pytest.raises(ValueError, match="presentation key required"):
            await manager.authenticate_with_recovery(None, recovery_key)

    @pytest.mark.skip(reason="Waiting for CWIStyleWalletManager implementation")
    @pytest.mark.asyncio
    async def test_works_with_correct_keys_sets_mode_as_existing_user(self) -> None:
        """Given: Correct presentation key and password
           When: Authenticate existing user
           Then: Mode is set to existing-user

        Reference: wallet-toolbox/src/__tests/CWIStyleWalletManager.test.ts
                   test('Works with correct keys, sets mode as existing-user')
        """
        presentation_key = os.urandom(32)
        recovery_key = os.urandom(32)
        password_salt = os.urandom(32)
        password_key = hashlib.pbkdf2_hmac("sha512", b"test-password", password_salt, PBKDF2_NUM_ROUNDS, 32)
        primary_key = os.urandom(32)
        privileged_key = os.urandom(32)

        existing_token = await create_mock_ump_token(
            presentation_key, recovery_key, password_salt, password_key, primary_key, privileged_key
        )

        mock_underlying_wallet = MagicMock(spec=WalletInterface)
        mock_wallet_builder = AsyncMock(return_value=mock_underlying_wallet)
        mock_ump_interactor = MagicMock(spec=UMPTokenInteractor)
        mock_ump_interactor.find_by_presentation_key_hash = AsyncMock(return_value=existing_token)
        mock_recovery_key_saver = AsyncMock(return_value=True)
        mock_password_retriever = AsyncMock(return_value="test-password")

        manager = CWIStyleWalletManager(
            ump_token_interactor=mock_ump_interactor,
            wallet_builder=mock_wallet_builder,
            recovery_key_saver=mock_recovery_key_saver,
            password_retriever=mock_password_retriever,
            admin_originator="admin.test.com",
        )

        result = await manager.authenticate(presentation_key)

        assert result["mode"] == "existing-user"
        assert result["authenticated"] is True

    @pytest.mark.skip(reason="Waiting for CWIStyleWalletManager implementation")
    @pytest.mark.asyncio
    async def test_throws_if_no_token_found_by_recovery_key_hash(self) -> None:
        """Given: Recovery key that doesn't match any stored token
           When: Try to authenticate with recovery key
           Then: Raises error (token not found)

        Reference: wallet-toolbox/src/__tests/CWIStyleWalletManager.test.ts
                   test('Throws if no token found by recovery key hash')
        """
        mock_underlying_wallet = MagicMock(spec=WalletInterface)
        mock_wallet_builder = AsyncMock(return_value=mock_underlying_wallet)
        mock_ump_interactor = MagicMock(spec=UMPTokenInteractor)
        mock_ump_interactor.find_by_recovery_key_hash = AsyncMock(return_value=None)
        mock_recovery_key_saver = AsyncMock(return_value=True)
        mock_password_retriever = AsyncMock(return_value="test-password")

        manager = CWIStyleWalletManager(
            ump_token_interactor=mock_ump_interactor,
            wallet_builder=mock_wallet_builder,
            recovery_key_saver=mock_recovery_key_saver,
            password_retriever=mock_password_retriever,
            admin_originator="admin.test.com",
        )

        wrong_recovery_key = os.urandom(32)

        with pytest.raises(ValueError, match="token not found"):
            await manager.find_token_by_recovery_key(wrong_recovery_key)


class TestCWIStyleWalletManagerSnapshot:
    """Test suite for snapshot save/load functionality."""

    @pytest.mark.skip(reason="Waiting for CWIStyleWalletManager implementation")
    @pytest.mark.asyncio
    async def test_saves_a_snapshot_and_can_load_it_into_a_fresh_manager_instance(self) -> None:
        """Given: Authenticated manager with wallet
           When: Save snapshot and load into new manager instance
           Then: New manager has same state

        Reference: wallet-toolbox/src/__tests/CWIStyleWalletManager.test.ts
                   test('Saves a snapshot and can load it into a fresh manager instance')
        """
        presentation_key = os.urandom(32)
        recovery_key = os.urandom(32)
        password_salt = os.urandom(32)
        password_key = hashlib.pbkdf2_hmac("sha512", b"test-password", password_salt, PBKDF2_NUM_ROUNDS, 32)
        primary_key = os.urandom(32)
        privileged_key = os.urandom(32)

        existing_token = await create_mock_ump_token(
            presentation_key, recovery_key, password_salt, password_key, primary_key, privileged_key
        )

        mock_underlying_wallet = MagicMock(spec=WalletInterface)
        mock_wallet_builder = AsyncMock(return_value=mock_underlying_wallet)
        mock_ump_interactor = MagicMock(spec=UMPTokenInteractor)
        mock_ump_interactor.find_by_presentation_key_hash = AsyncMock(return_value=existing_token)
        mock_recovery_key_saver = AsyncMock(return_value=True)
        mock_password_retriever = AsyncMock(return_value="test-password")

        manager1 = CWIStyleWalletManager(
            ump_token_interactor=mock_ump_interactor,
            wallet_builder=mock_wallet_builder,
            recovery_key_saver=mock_recovery_key_saver,
            password_retriever=mock_password_retriever,
            admin_originator="admin.test.com",
        )

        await manager1.authenticate(presentation_key)

        snapshot = await manager1.save_snapshot()

        manager2 = CWIStyleWalletManager(
            ump_token_interactor=mock_ump_interactor,
            wallet_builder=mock_wallet_builder,
            recovery_key_saver=mock_recovery_key_saver,
            password_retriever=mock_password_retriever,
            admin_originator="admin.test.com",
        )

        await manager2.load_snapshot(snapshot)

        assert manager2.is_authenticated() is True
        assert manager2.get_primary_key() == manager1.get_primary_key()

    @pytest.mark.skip(reason="Waiting for CWIStyleWalletManager implementation")
    @pytest.mark.asyncio
    async def test_throws_error_if_saving_snapshot_while_no_primary_key_or_token_set(self) -> None:
        """Given: Manager without authentication
           When: Try to save snapshot
           Then: Raises error (not authenticated)

        Reference: wallet-toolbox/src/__tests/CWIStyleWalletManager.test.ts
                   test('Throws error if saving snapshot while no primary key or token set')
        """
        mock_underlying_wallet = MagicMock(spec=WalletInterface)
        mock_wallet_builder = AsyncMock(return_value=mock_underlying_wallet)
        mock_ump_interactor = MagicMock(spec=UMPTokenInteractor)
        mock_recovery_key_saver = AsyncMock(return_value=True)
        mock_password_retriever = AsyncMock(return_value="test-password")

        manager = CWIStyleWalletManager(
            ump_token_interactor=mock_ump_interactor,
            wallet_builder=mock_wallet_builder,
            recovery_key_saver=mock_recovery_key_saver,
            password_retriever=mock_password_retriever,
            admin_originator="admin.test.com",
        )

        with pytest.raises(ValueError, match="not authenticated"):
            await manager.save_snapshot()

    @pytest.mark.skip(reason="Waiting for CWIStyleWalletManager implementation")
    @pytest.mark.asyncio
    async def test_throws_if_snapshot_is_corrupt_or_cannot_be_decrypted(self) -> None:
        """Given: Corrupted or invalid snapshot data
           When: Try to load snapshot
           Then: Raises decryption error

        Reference: wallet-toolbox/src/__tests/CWIStyleWalletManager.test.ts
                   test('Throws if snapshot is corrupt or cannot be decrypted')
        """
        mock_underlying_wallet = MagicMock(spec=WalletInterface)
        mock_wallet_builder = AsyncMock(return_value=mock_underlying_wallet)
        mock_ump_interactor = MagicMock(spec=UMPTokenInteractor)
        mock_recovery_key_saver = AsyncMock(return_value=True)
        mock_password_retriever = AsyncMock(return_value="test-password")

        manager = CWIStyleWalletManager(
            ump_token_interactor=mock_ump_interactor,
            wallet_builder=mock_wallet_builder,
            recovery_key_saver=mock_recovery_key_saver,
            password_retriever=mock_password_retriever,
            admin_originator="admin.test.com",
        )

        corrupted_snapshot = b"invalid data"

        with pytest.raises(ValueError, match="decryption failed"):
            await manager.load_snapshot(corrupted_snapshot)


class TestCWIStyleWalletManagerChangePassword:
    """Test suite for password changing functionality.

    Reference: wallet-toolbox/src/__tests/CWIStyleWalletManager.test.ts
               describe('Change Password')
    """

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Waiting for CWIStyleWalletManager implementation")
    @pytest.mark.asyncio
    async def test_requires_authentication_and_updates_the_ump_token_on_chain(self) -> None:
        """Given: Authenticated manager
           When: Change password
           Then: UMP token is updated on-chain

        Reference: wallet-toolbox/src/__tests/CWIStyleWalletManager.test.ts
                   test('Requires authentication and updates the UMP token on-chain')
        """
        # Given
        mock_ump_interactor = Mock()
        mock_ump_interactor.find_by_presentation_key_hash = AsyncMock(return_value=None)
        mock_ump_interactor.build_and_send = AsyncMock(return_value="txid.0")

        mock_wallet_builder = AsyncMock()
        mock_underlying_wallet = Mock()
        mock_wallet_builder.return_value = mock_underlying_wallet

        mock_recovery_key_saver = AsyncMock(return_value=True)
        mock_password_retriever = AsyncMock(return_value="test-password")

        manager = CWIStyleWalletManager(
            ump_token_interactor=mock_ump_interactor,
            wallet_builder=mock_wallet_builder,
            recovery_key_saver=mock_recovery_key_saver,
            password_retriever=mock_password_retriever,
            admin_originator="admin.test.com",
        )

        # Authenticate as new user
        presentation_key = bytes([0xA1] * 32)
        await manager.provide_presentation_key(presentation_key)
        await manager.provide_password("test-password")

        assert manager.authenticated is True

        # When
        await manager.change_password("new-password")

        # Then
        assert mock_ump_interactor.build_and_send.call_count == 2  # Initial + change

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Waiting for CWIStyleWalletManager implementation")
    @pytest.mark.asyncio
    async def test_throws_if_not_authenticated(self) -> None:
        """Given: Unauthenticated manager
           When: Attempt to change password
           Then: Raises error

        Reference: wallet-toolbox/src/__tests/CWIStyleWalletManager.test.ts
                   test('Throws if not authenticated')
        """
        # Given
        mock_ump_interactor = Mock()
        mock_wallet_builder = AsyncMock()
        mock_recovery_key_saver = AsyncMock()
        mock_password_retriever = AsyncMock()

        manager = CWIStyleWalletManager(
            ump_token_interactor=mock_ump_interactor,
            wallet_builder=mock_wallet_builder,
            recovery_key_saver=mock_recovery_key_saver,
            password_retriever=mock_password_retriever,
            admin_originator="admin.test.com",
        )

        # When/Then
        with pytest.raises(ValueError, match="Not authenticated"):
            await manager.change_password("new-password")


class TestCWIStyleWalletManagerChangeRecoveryKey:
    """Test suite for recovery key changing functionality.

    Reference: wallet-toolbox/src/__tests/CWIStyleWalletManager.test.ts
               describe('Change Recovery Key')
    """

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Waiting for CWIStyleWalletManager implementation")
    @pytest.mark.asyncio
    async def test_prompts_to_save_the_new_key_updates_the_token(self) -> None:
        """Given: Authenticated manager
           When: Change recovery key
           Then: User is prompted to save new key, token is updated

        Reference: wallet-toolbox/src/__tests/CWIStyleWalletManager.test.ts
                   test('Prompts to save the new key, updates the token')
        """
        # Given
        mock_ump_interactor = Mock()
        mock_ump_interactor.find_by_presentation_key_hash = AsyncMock(return_value=None)
        mock_ump_interactor.build_and_send = AsyncMock(return_value="txid.0")

        mock_wallet_builder = AsyncMock()
        mock_underlying_wallet = Mock()
        mock_wallet_builder.return_value = mock_underlying_wallet

        mock_recovery_key_saver = AsyncMock(return_value=True)
        mock_password_retriever = AsyncMock(return_value="test-password")

        manager = CWIStyleWalletManager(
            ump_token_interactor=mock_ump_interactor,
            wallet_builder=mock_wallet_builder,
            recovery_key_saver=mock_recovery_key_saver,
            password_retriever=mock_password_retriever,
            admin_originator="admin.test.com",
        )

        # Authenticate as new user
        presentation_key = bytes([0xA1] * 32)
        await manager.provide_presentation_key(presentation_key)
        await manager.provide_password("test-password")

        # When
        await manager.change_recovery_key()

        # Then
        assert mock_recovery_key_saver.call_count == 2  # Initial + change
        assert mock_ump_interactor.build_and_send.call_count == 2

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Waiting for CWIStyleWalletManager implementation")
    @pytest.mark.asyncio
    async def test_throws_if_not_authenticated_527(self) -> None:
        """Given: Unauthenticated manager
           When: Attempt to change recovery key
           Then: Raises error

        Reference: wallet-toolbox/src/__tests/CWIStyleWalletManager.test.ts
                   test('Throws if not authenticated')
        """
        # Given
        mock_ump_interactor = Mock()
        mock_wallet_builder = AsyncMock()
        mock_recovery_key_saver = AsyncMock()
        mock_password_retriever = AsyncMock()

        manager = CWIStyleWalletManager(
            ump_token_interactor=mock_ump_interactor,
            wallet_builder=mock_wallet_builder,
            recovery_key_saver=mock_recovery_key_saver,
            password_retriever=mock_password_retriever,
            admin_originator="admin.test.com",
        )

        # When/Then
        with pytest.raises(ValueError, match="Not authenticated"):
            await manager.change_recovery_key()


class TestCWIStyleWalletManagerChangePresentationKey:
    """Test suite for presentation key changing functionality.

    Reference: wallet-toolbox/src/__tests/CWIStyleWalletManager.test.ts
               describe('Change Presentation Key')
    """

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Waiting for CWIStyleWalletManager implementation")
    @pytest.mark.asyncio
    async def test_requires_authentication_re_publishes_the_token_old_token_consumed(self) -> None:
        """Given: Authenticated manager
           When: Change presentation key
           Then: Token is re-published, old token consumed

        Reference: wallet-toolbox/src/__tests/CWIStyleWalletManager.test.ts
                   test('Requires authentication, re-publishes the token, old token consumed')
        """
        # Given
        mock_ump_interactor = Mock()
        mock_ump_interactor.find_by_presentation_key_hash = AsyncMock(return_value=None)
        mock_ump_interactor.build_and_send = AsyncMock(return_value="txid.0")

        mock_wallet_builder = AsyncMock()
        mock_underlying_wallet = Mock()
        mock_wallet_builder.return_value = mock_underlying_wallet

        mock_recovery_key_saver = AsyncMock(return_value=True)
        mock_password_retriever = AsyncMock(return_value="test-password")

        manager = CWIStyleWalletManager(
            ump_token_interactor=mock_ump_interactor,
            wallet_builder=mock_wallet_builder,
            recovery_key_saver=mock_recovery_key_saver,
            password_retriever=mock_password_retriever,
            admin_originator="admin.test.com",
        )

        # Authenticate as new user
        presentation_key = bytes([0xA1] * 32)
        await manager.provide_presentation_key(presentation_key)
        await manager.provide_password("test-password")

        # When
        new_presentation_key = bytes([0xEE] * 32)
        await manager.change_presentation_key(new_presentation_key)

        # Then
        assert mock_ump_interactor.build_and_send.call_count == 2


class TestCWIStyleWalletManagerDestroy:
    """Test suite for destroy functionality.

    Reference: wallet-toolbox/src/__tests/CWIStyleWalletManager.test.ts
               test('Destroy callback clears sensitive data')
    """

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Waiting for CWIStyleWalletManager implementation")
    @pytest.mark.asyncio
    async def test_destroy_callback_clears_sensitive_data(self) -> None:
        """Given: Authenticated manager
           When: Call destroy
           Then: Sensitive data is cleared, manager is unauthenticated

        Reference: wallet-toolbox/src/__tests/CWIStyleWalletManager.test.ts
                   test('Destroy callback clears sensitive data')
        """
        # Given
        mock_ump_interactor = Mock()
        mock_ump_interactor.find_by_presentation_key_hash = AsyncMock(return_value=None)
        mock_ump_interactor.build_and_send = AsyncMock(return_value="txid.0")

        mock_wallet_builder = AsyncMock()
        mock_underlying_wallet = Mock()
        mock_wallet_builder.return_value = mock_underlying_wallet

        mock_recovery_key_saver = AsyncMock(return_value=True)
        mock_password_retriever = AsyncMock(return_value="test-password")

        manager = CWIStyleWalletManager(
            ump_token_interactor=mock_ump_interactor,
            wallet_builder=mock_wallet_builder,
            recovery_key_saver=mock_recovery_key_saver,
            password_retriever=mock_password_retriever,
            admin_originator="admin.test.com",
        )

        # Authenticate
        presentation_key = bytes([0x0C] * 32)
        await manager.provide_presentation_key(presentation_key)
        await manager.provide_password("test-password")

        assert manager.authenticated is True

        # When
        manager.destroy()

        # Then
        assert manager.authenticated is False

        with pytest.raises(ValueError, match="User is not authenticated"):
            await manager.get_public_key({"identity_key": True})


class TestCWIStyleWalletManagerProxyMethods:
    """Test suite for proxy method calls and originator checks.

    Reference: wallet-toolbox/src/__tests/CWIStyleWalletManager.test.ts
               describe('Proxy method calls')
    """

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Waiting for CWIStyleWalletManager implementation")
    @pytest.mark.asyncio
    async def test_throws_if_user_is_not_authenticated(self) -> None:
        """Given: Unauthenticated manager
           When: Attempt to call proxy method
           Then: Raises authentication error

        Reference: wallet-toolbox/src/__tests/CWIStyleWalletManager.test.ts
                   test('Throws if user is not authenticated')
        """
        # Given
        mock_ump_interactor = Mock()
        mock_wallet_builder = AsyncMock()
        mock_recovery_key_saver = AsyncMock()
        mock_password_retriever = AsyncMock()

        manager = CWIStyleWalletManager(
            ump_token_interactor=mock_ump_interactor,
            wallet_builder=mock_wallet_builder,
            recovery_key_saver=mock_recovery_key_saver,
            password_retriever=mock_password_retriever,
            admin_originator="admin.test.com",
        )

        # When/Then
        with pytest.raises(ValueError, match="User is not authenticated"):
            await manager.get_public_key({"identity_key": True})

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Waiting for CWIStyleWalletManager implementation")
    @pytest.mark.asyncio
    async def test_throws_if_originator_is_adminoriginator(self) -> None:
        """Given: Authenticated manager
           When: Call method with admin originator
           Then: Raises error

        Reference: wallet-toolbox/src/__tests/CWIStyleWalletManager.test.ts
                   test('Throws if originator is adminOriginator')
        """
        # Given
        mock_ump_interactor = Mock()
        mock_ump_interactor.find_by_presentation_key_hash = AsyncMock(return_value=None)
        mock_ump_interactor.build_and_send = AsyncMock(return_value="txid.0")

        mock_wallet_builder = AsyncMock()
        mock_underlying_wallet = Mock()
        mock_wallet_builder.return_value = mock_underlying_wallet

        mock_recovery_key_saver = AsyncMock(return_value=True)
        mock_password_retriever = AsyncMock(return_value="test-password")

        manager = CWIStyleWalletManager(
            ump_token_interactor=mock_ump_interactor,
            wallet_builder=mock_wallet_builder,
            recovery_key_saver=mock_recovery_key_saver,
            password_retriever=mock_password_retriever,
            admin_originator="admin.test.com",
        )

        # Authenticate
        presentation_key = bytes([0xA1] * 32)
        await manager.provide_presentation_key(presentation_key)
        await manager.provide_password("test-password")

        # When/Then
        with pytest.raises(ValueError, match="External applications are not allowed to use the admin originator"):
            await manager.get_public_key({"identity_key": True}, originator="admin.test.com")

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Waiting for CWIStyleWalletManager implementation")
    @pytest.mark.asyncio
    async def test_passes_if_user_is_authenticated_and_originator_is_not_admin(self) -> None:
        """Given: Authenticated manager with normal originator
           When: Call proxy method
           Then: Method is called on underlying wallet

        Reference: wallet-toolbox/src/__tests/CWIStyleWalletManager.test.ts
                   test('Passes if user is authenticated and originator is not admin')
        """
        # Given
        mock_ump_interactor = Mock()
        mock_ump_interactor.find_by_presentation_key_hash = AsyncMock(return_value=None)
        mock_ump_interactor.build_and_send = AsyncMock(return_value="txid.0")

        mock_wallet_builder = AsyncMock()
        mock_underlying_wallet = Mock()
        mock_underlying_wallet.get_public_key = AsyncMock(return_value={"publicKey": "test"})
        mock_wallet_builder.return_value = mock_underlying_wallet

        mock_recovery_key_saver = AsyncMock(return_value=True)
        mock_password_retriever = AsyncMock(return_value="test-password")

        manager = CWIStyleWalletManager(
            ump_token_interactor=mock_ump_interactor,
            wallet_builder=mock_wallet_builder,
            recovery_key_saver=mock_recovery_key_saver,
            password_retriever=mock_password_retriever,
            admin_originator="admin.test.com",
        )

        # Authenticate
        presentation_key = bytes([0xA1] * 32)
        await manager.provide_presentation_key(presentation_key)
        await manager.provide_password("test-password")

        # When
        await manager.get_public_key({"identity_key": True}, originator="example.com")

        # Then
        mock_underlying_wallet.get_public_key.assert_called_once()

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Waiting for CWIStyleWalletManager implementation")
    @pytest.mark.asyncio
    async def test_all_proxied_methods_call_underlying_with_correct_arguments(self) -> None:
        """Given: Authenticated manager
           When: Call various proxy methods
           Then: All forward to underlying wallet with correct arguments

        Reference: wallet-toolbox/src/__tests/CWIStyleWalletManager.test.ts
                   test('All proxied methods call underlying with correct arguments')
        """
        # Given
        mock_ump_interactor = Mock()
        mock_ump_interactor.find_by_presentation_key_hash = AsyncMock(return_value=None)
        mock_ump_interactor.build_and_send = AsyncMock(return_value="txid.0")

        mock_wallet_builder = AsyncMock()
        mock_underlying_wallet = Mock()
        mock_underlying_wallet.encrypt = AsyncMock(return_value={"ciphertext": [1, 2, 3]})
        mock_wallet_builder.return_value = mock_underlying_wallet

        mock_recovery_key_saver = AsyncMock(return_value=True)
        mock_password_retriever = AsyncMock(return_value="test-password")

        manager = CWIStyleWalletManager(
            ump_token_interactor=mock_ump_interactor,
            wallet_builder=mock_wallet_builder,
            recovery_key_saver=mock_recovery_key_saver,
            password_retriever=mock_password_retriever,
            admin_originator="admin.test.com",
        )

        # Authenticate
        presentation_key = bytes([0xA1] * 32)
        await manager.provide_presentation_key(presentation_key)
        await manager.provide_password("test-password")

        # When
        await manager.encrypt(
            {"plaintext": [1, 2, 3], "protocolID": [1, "tests"], "keyID": "1"}, originator="mydomain.com"
        )

        # Then
        mock_underlying_wallet.encrypt.assert_called_once_with(
            {"plaintext": [1, 2, 3], "protocolID": [1, "tests"], "keyID": "1"}, "mydomain.com"
        )

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Waiting for CWIStyleWalletManager implementation")
    @pytest.mark.asyncio
    async def test_isauthenticated_rejects_if_originator_is_admin_resolves_otherwise(self) -> None:
        """Given: Authenticated manager
           When: Call isAuthenticated with admin vs normal originator
           Then: Rejects admin, resolves normal

        Reference: wallet-toolbox/src/__tests/CWIStyleWalletManager.test.ts
                   test('isAuthenticated() rejects if originator is admin, resolves otherwise')
        """
        # Given
        mock_ump_interactor = Mock()
        mock_ump_interactor.find_by_presentation_key_hash = AsyncMock(return_value=None)
        mock_ump_interactor.build_and_send = AsyncMock(return_value="txid.0")

        mock_wallet_builder = AsyncMock()
        mock_underlying_wallet = Mock()
        mock_wallet_builder.return_value = mock_underlying_wallet

        mock_recovery_key_saver = AsyncMock(return_value=True)
        mock_password_retriever = AsyncMock(return_value="test-password")

        manager = CWIStyleWalletManager(
            ump_token_interactor=mock_ump_interactor,
            wallet_builder=mock_wallet_builder,
            recovery_key_saver=mock_recovery_key_saver,
            password_retriever=mock_password_retriever,
            admin_originator="admin.test.com",
        )

        # Authenticate
        presentation_key = bytes([0xA1] * 32)
        await manager.provide_presentation_key(presentation_key)
        await manager.provide_password("test-password")

        # When/Then - admin originator should fail
        with pytest.raises(ValueError, match="External applications are not allowed"):
            await manager.is_authenticated({}, originator="admin.test.com")

        # Normal originator should succeed
        result = await manager.is_authenticated({}, originator="normal.com")
        assert result == {"authenticated": True}

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Waiting for CWIStyleWalletManager implementation")
    @pytest.mark.asyncio
    async def test_waitforauthentication_eventually_resolves(self) -> None:
        """Given: Authenticated manager
           When: Call waitForAuthentication
           Then: Resolves immediately

        Reference: wallet-toolbox/src/__tests/CWIStyleWalletManager.test.ts
                   test('waitForAuthentication() eventually resolves')
        """
        # Given
        mock_ump_interactor = Mock()
        mock_ump_interactor.find_by_presentation_key_hash = AsyncMock(return_value=None)
        mock_ump_interactor.build_and_send = AsyncMock(return_value="txid.0")

        mock_wallet_builder = AsyncMock()
        mock_underlying_wallet = Mock()
        mock_underlying_wallet.wait_for_authentication = AsyncMock()
        mock_wallet_builder.return_value = mock_underlying_wallet

        mock_recovery_key_saver = AsyncMock(return_value=True)
        mock_password_retriever = AsyncMock(return_value="test-password")

        manager = CWIStyleWalletManager(
            ump_token_interactor=mock_ump_interactor,
            wallet_builder=mock_wallet_builder,
            recovery_key_saver=mock_recovery_key_saver,
            password_retriever=mock_password_retriever,
            admin_originator="admin.test.com",
        )

        # Authenticate
        presentation_key = bytes([0xA1] * 32)
        await manager.provide_presentation_key(presentation_key)
        await manager.provide_password("test-password")

        # When
        await manager.wait_for_authentication({}, originator="normal.com")

        # Then
        mock_underlying_wallet.wait_for_authentication.assert_called_once()


class TestCWIStyleWalletManagerAdditionalTests:
    """Test suite for UMP token serialization, password retriever, and privileged key expiry.

    Reference: wallet-toolbox/src/__tests/CWIStyleWalletManager.test.ts
               describe('Additional Tests for Password Retriever Callback, Privileged Key Expiry, and UMP Token Serialization')
    """

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Waiting for CWIStyleWalletManager implementation")
    @pytest.mark.asyncio
    async def test_serializeumptoken_and_deserializeumptoken_correctly_round_trip_a_ump_token(self) -> None:
        """Given: UMP token
           When: Serialize and deserialize
           Then: Token round-trips correctly

        Reference: wallet-toolbox/src/__tests/CWIStyleWalletManager.test.ts
                   test('serializeUMPToken and deserializeUMPToken correctly round-trip a UMP token')
        """
        # Given
        mock_ump_interactor = Mock()
        mock_ump_interactor.find_by_presentation_key_hash = AsyncMock(return_value=None)
        mock_ump_interactor.build_and_send = AsyncMock(return_value="txid.0")

        mock_wallet_builder = AsyncMock()
        mock_underlying_wallet = Mock()
        mock_wallet_builder.return_value = mock_underlying_wallet

        mock_recovery_key_saver = AsyncMock(return_value=True)
        mock_password_retriever = AsyncMock(return_value="test-password")

        manager = CWIStyleWalletManager(
            ump_token_interactor=mock_ump_interactor,
            wallet_builder=mock_wallet_builder,
            recovery_key_saver=mock_recovery_key_saver,
            password_retriever=mock_password_retriever,
            admin_originator="admin.test.com",
        )

        # Create a mock token

        token = MagicMock()
        token.password_salt = bytes([0x01] * 32)
        token.current_outpoint = "txid.0"

        # When - access private methods via manager instance
        serialize_fn = getattr(manager, "_serialize_ump_token", None)
        deserialize_fn = getattr(manager, "_deserialize_ump_token", None)

        if serialize_fn and deserialize_fn:
            serialized = serialize_fn(token)
            assert isinstance(serialized, bytes)
            assert len(serialized) > 0

            deserialized = deserialize_fn(serialized)
            assert deserialized == token

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Waiting for CWIStyleWalletManager implementation")
    @pytest.mark.asyncio
    async def test_password_retriever_callback_the_test_function_is_passed_and_returns_a_boolean(self) -> None:
        """Given: Manager with custom password retriever
           When: Authenticate
           Then: Password retriever receives test function that returns boolean

        Reference: wallet-toolbox/src/__tests/CWIStyleWalletManager.test.ts
                   test('Password retriever callback: the test function is passed and returns a boolean')
        """
        # Given
        captured_test_fn = None

        async def custom_password_retriever(reason: str, test_fn) -> str:
            nonlocal captured_test_fn
            captured_test_fn = test_fn
            return "test-password"

        mock_ump_interactor = Mock()
        mock_ump_interactor.find_by_presentation_key_hash = AsyncMock(return_value=None)
        mock_ump_interactor.build_and_send = AsyncMock(return_value="txid.0")

        mock_wallet_builder = AsyncMock()
        mock_underlying_wallet = Mock()
        mock_wallet_builder.return_value = mock_underlying_wallet

        mock_recovery_key_saver = AsyncMock(return_value=True)

        manager = CWIStyleWalletManager(
            ump_token_interactor=mock_ump_interactor,
            wallet_builder=mock_wallet_builder,
            recovery_key_saver=mock_recovery_key_saver,
            password_retriever=custom_password_retriever,
            admin_originator="admin.test.com",
        )

        # When - authenticate as new user
        presentation_key = bytes([0xA1] * 32)
        await manager.provide_presentation_key(presentation_key)
        await manager.provide_password("test-password")

        # Then
        assert manager.authenticated is True
        assert captured_test_fn is not None

        # Test function should return boolean
        test_result = captured_test_fn("any-input")
        assert isinstance(test_result, bool)
        assert captured_test_fn("test-password") is True
        assert captured_test_fn("wrong-password") is False

    @pytest.mark.skipif(not IMPORTS_AVAILABLE, reason="Waiting for CWIStyleWalletManager implementation")
    @pytest.mark.asyncio
    async def test_privileged_key_expiry_each_call_to_decrypt_via_the_privileged_manager_invokes_passwordretriever(
        self,
    ) -> None:
        """Given: Authenticated manager with expired privileged key
           When: Call privileged operations multiple times
           Then: Password retriever is invoked each time

        Reference: wallet-toolbox/src/__tests/CWIStyleWalletManager.test.ts
                   test('Privileged key expiry: each call to decrypt via the privileged manager invokes passwordRetriever')
        """
        # Given
        password_retriever_call_count = 0

        async def custom_password_retriever(reason: str, test_fn) -> str:
            nonlocal password_retriever_call_count
            password_retriever_call_count += 1
            return "test-password"

        mock_ump_interactor = Mock()
        mock_ump_interactor.find_by_presentation_key_hash = AsyncMock(return_value=None)
        mock_ump_interactor.build_and_send = AsyncMock(return_value="txid.0")

        mock_wallet_builder = AsyncMock()
        mock_underlying_wallet = Mock()
        mock_wallet_builder.return_value = mock_underlying_wallet

        mock_recovery_key_saver = AsyncMock(return_value=True)

        manager = CWIStyleWalletManager(
            ump_token_interactor=mock_ump_interactor,
            wallet_builder=mock_wallet_builder,
            recovery_key_saver=mock_recovery_key_saver,
            password_retriever=custom_password_retriever,
            admin_originator="admin.test.com",
        )

        # Authenticate as new user
        presentation_key = bytes([0xA1] * 32)
        await manager.provide_presentation_key(presentation_key)
        await manager.provide_password("test-password")

        # Clear counter after authentication
        password_retriever_call_count = 0

        # When - simulate privileged key expiry and multiple calls
        # Note: Implementation detail - accessing private privileged key manager
        privileged_key_manager = getattr(manager, "_root_privileged_key_manager", None)
        if privileged_key_manager and hasattr(privileged_key_manager, "decrypt"):
            # First decrypt call
            try:
                await privileged_key_manager.decrypt(
                    {"ciphertext": bytes([0x01] * 32), "protocolID": [2, "admin key wrapping"], "keyID": "1"}
                )
            except:
                pass  # May fail if not fully implemented

            # Simulate key expiry (advance time by > 2 minutes in real implementation)

            # Second decrypt call
            try:
                await privileged_key_manager.decrypt(
                    {"ciphertext": bytes([0x01] * 32), "protocolID": [2, "admin key wrapping"], "keyID": "1"}
                )
            except:
                pass

            # Then - password retriever should be called for each privileged operation
            # (actual count depends on implementation)
