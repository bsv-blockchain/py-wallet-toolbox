"""Unit tests for CWIStyleWalletManager.

CWIStyleWalletManager implements a wallet management system with:
- User authentication (presentation key, recovery key, password)
- Encrypted key storage using UMP tokens
- Primary key derivation and privileged key management

Reference: toolbox/ts-wallet-toolbox/src/__tests/CWIStyleWalletManager.test.ts
"""

import pytest
import hashlib
from typing import Optional, Dict, Any, List
from unittest.mock import Mock, AsyncMock, MagicMock
import os

try:
    from bsv_wallet_toolbox.cwi_style_wallet_manager import (
        CWIStyleWalletManager,
        PBKDF2_NUM_ROUNDS,
        UMPToken,
        UMPTokenInteractor
    )
    from bsv_wallet_toolbox.sdk import PrivilegedKeyManager
    from bsv.wallet.wallet_interface import WalletInterface
    IMPORTS_AVAILABLE = True
except ImportError:
    IMPORTS_AVAILABLE = False
    CWIStyleWalletManager = None
    PBKDF2_NUM_ROUNDS = 100000
    UMPToken = None
    UMPTokenInteractor = None
    PrivilegedKeyManager = None
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
    return bytes(x ^ y for x, y in zip(a, b))


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
    privileged_key: bytes
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
    
    temp_privileged_key_manager = PrivilegedKeyManager(
        lambda: PrivateKey(privileged_key)
    )
    
    return {
        "passwordSalt": list(password_salt),
        "passwordPresentationPrimary": list(presentation_password.encrypt(primary_key)),
        "passwordRecoveryPrimary": list(recovery_password.encrypt(primary_key)),
        "presentationRecoveryPrimary": list(presentation_recovery.encrypt(primary_key)),
        "passwordPrimaryPrivileged": list(primary_password.encrypt(privileged_key)),
        "presentationRecoveryPrivileged": list(presentation_recovery.encrypt(privileged_key)),
        "presentationHash": list(hashlib.sha256(presentation_key).digest()),
        "recoveryHash": list(hashlib.sha256(recovery_key).digest()),
        "presentationKeyEncrypted": (await temp_privileged_key_manager.encrypt({
            "plaintext": list(presentation_key),
            "protocolID": [2, "admin key wrapping"],
            "keyID": "1"
        }))["ciphertext"],
        "passwordKeyEncrypted": (await temp_privileged_key_manager.encrypt({
            "plaintext": list(password_key),
            "protocolID": [2, "admin key wrapping"],
            "keyID": "1"
        }))["ciphertext"],
        "recoveryKeyEncrypted": (await temp_privileged_key_manager.encrypt({
            "plaintext": list(recovery_key),
            "protocolID": [2, "admin key wrapping"],
            "keyID": "1"
        }))["ciphertext"],
        "currentOutpoint": "abcd:0"
    }


class TestCWIStyleWalletManagerXOR:
    """Test suite for XOR utility function."""
    
    @pytest.mark.skip(reason="Waiting for CWIStyleWalletManager implementation")
    def test_xor_function_verifies_correctness(self) -> None:
        """Given: Two byte arrays
           When: XOR them together
           Then: Result XORed with either input returns the other
           
        Reference: toolbox/ts-wallet-toolbox/src/__tests/CWIStyleWalletManager.test.ts
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
           
        Reference: toolbox/ts-wallet-toolbox/src/__tests/CWIStyleWalletManager.test.ts
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
            admin_originator="admin.test.com"
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
           
        Reference: toolbox/ts-wallet-toolbox/src/__tests/CWIStyleWalletManager.test.ts
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
            admin_originator="admin.test.com"
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
           
        Reference: toolbox/ts-wallet-toolbox/src/__tests/CWIStyleWalletManager.test.ts
                   test('Decryption of primary key and building the wallet')
        """
        presentation_key = os.urandom(32)
        recovery_key = os.urandom(32)
        password_salt = os.urandom(32)
        password_key = hashlib.pbkdf2_hmac(
            "sha512",
            b"test-password",
            password_salt,
            PBKDF2_NUM_ROUNDS,
            32
        )
        primary_key = os.urandom(32)
        privileged_key = os.urandom(32)
        
        existing_token = await create_mock_ump_token(
            presentation_key,
            recovery_key,
            password_salt,
            password_key,
            primary_key,
            privileged_key
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
            admin_originator="admin.test.com"
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
           
        Reference: toolbox/ts-wallet-toolbox/src/__tests/CWIStyleWalletManager.test.ts
                   test('Successfully decrypts with presentation+recovery')
        """
        presentation_key = os.urandom(32)
        recovery_key = os.urandom(32)
        password_salt = os.urandom(32)
        password_key = hashlib.pbkdf2_hmac(
            "sha512",
            b"test-password",
            password_salt,
            PBKDF2_NUM_ROUNDS,
            32
        )
        primary_key = os.urandom(32)
        privileged_key = os.urandom(32)
        
        existing_token = await create_mock_ump_token(
            presentation_key,
            recovery_key,
            password_salt,
            password_key,
            primary_key,
            privileged_key
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
            admin_originator="admin.test.com"
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
           
        Reference: toolbox/ts-wallet-toolbox/src/__tests/CWIStyleWalletManager.test.ts
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
            admin_originator="admin.test.com"
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
           
        Reference: toolbox/ts-wallet-toolbox/src/__tests/CWIStyleWalletManager.test.ts
                   test('Works with correct keys, sets mode as existing-user')
        """
        presentation_key = os.urandom(32)
        recovery_key = os.urandom(32)
        password_salt = os.urandom(32)
        password_key = hashlib.pbkdf2_hmac(
            "sha512",
            b"test-password",
            password_salt,
            PBKDF2_NUM_ROUNDS,
            32
        )
        primary_key = os.urandom(32)
        privileged_key = os.urandom(32)
        
        existing_token = await create_mock_ump_token(
            presentation_key,
            recovery_key,
            password_salt,
            password_key,
            primary_key,
            privileged_key
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
            admin_originator="admin.test.com"
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
           
        Reference: toolbox/ts-wallet-toolbox/src/__tests/CWIStyleWalletManager.test.ts
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
            admin_originator="admin.test.com"
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
           
        Reference: toolbox/ts-wallet-toolbox/src/__tests/CWIStyleWalletManager.test.ts
                   test('Saves a snapshot and can load it into a fresh manager instance')
        """
        presentation_key = os.urandom(32)
        recovery_key = os.urandom(32)
        password_salt = os.urandom(32)
        password_key = hashlib.pbkdf2_hmac(
            "sha512",
            b"test-password",
            password_salt,
            PBKDF2_NUM_ROUNDS,
            32
        )
        primary_key = os.urandom(32)
        privileged_key = os.urandom(32)
        
        existing_token = await create_mock_ump_token(
            presentation_key,
            recovery_key,
            password_salt,
            password_key,
            primary_key,
            privileged_key
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
            admin_originator="admin.test.com"
        )
        
        await manager1.authenticate(presentation_key)
        
        snapshot = await manager1.save_snapshot()
        
        manager2 = CWIStyleWalletManager(
            ump_token_interactor=mock_ump_interactor,
            wallet_builder=mock_wallet_builder,
            recovery_key_saver=mock_recovery_key_saver,
            password_retriever=mock_password_retriever,
            admin_originator="admin.test.com"
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
           
        Reference: toolbox/ts-wallet-toolbox/src/__tests/CWIStyleWalletManager.test.ts
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
            admin_originator="admin.test.com"
        )
        
        with pytest.raises(ValueError, match="not authenticated"):
            await manager.save_snapshot()
    
    @pytest.mark.skip(reason="Waiting for CWIStyleWalletManager implementation")
    @pytest.mark.asyncio
    async def test_throws_if_snapshot_is_corrupt_or_cannot_be_decrypted(self) -> None:
        """Given: Corrupted or invalid snapshot data
           When: Try to load snapshot
           Then: Raises decryption error
           
        Reference: toolbox/ts-wallet-toolbox/src/__tests/CWIStyleWalletManager.test.ts
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
            admin_originator="admin.test.com"
        )
        
        corrupted_snapshot = b"invalid data"
        
        with pytest.raises(ValueError, match="decryption failed"):
            await manager.load_snapshot(corrupted_snapshot)
