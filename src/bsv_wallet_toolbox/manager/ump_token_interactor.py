"""UMPTokenInteractor - Interface for finding and publishing UMP tokens on-chain.

UMP (User Management Protocol) tokens store encrypted key material for CWI-style
wallet authentication. This module provides interfaces and implementations for
interacting with UMP tokens on the blockchain.

Reference: wallet-toolbox/src/CWIStyleWalletManager.ts
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Protocol

from bsv_wallet_toolbox.manager.wallet_interface import WalletInterface


class UMPToken:
    """UMP (User Management Protocol) token data structure.

    Contains encrypted key material for CWI-style wallet authentication.
    All fields are byte arrays representing encrypted or hashed data.

    Reference: wallet-toolbox/src/CWIStyleWalletManager.ts
    """

    def __init__(
        self,
        password_presentation_primary: list[int],
        password_recovery_primary: list[int],
        presentation_recovery_primary: list[int],
        password_primary_privileged: list[int],
        presentation_recovery_privileged: list[int],
        presentation_hash: list[int],
        password_salt: list[int],
        recovery_hash: list[int],
        presentation_key_encrypted: list[int],
        recovery_key_encrypted: list[int],
        password_key_encrypted: list[int],
        profiles_encrypted: list[int] | None = None,
        current_outpoint: str | None = None,
    ) -> None:
        """Initialize UMPToken.

        Args:
            password_presentation_primary: Root Primary key encrypted by XOR of password and presentation keys
            password_recovery_primary: Root Primary key encrypted by XOR of password and recovery keys
            presentation_recovery_primary: Root Primary key encrypted by XOR of presentation and recovery keys
            password_primary_privileged: Root Privileged key encrypted by XOR of password and primary keys
            presentation_recovery_privileged: Root Privileged key encrypted by XOR of presentation and recovery keys
            presentation_hash: SHA-256 hash of the presentation key
            password_salt: PBKDF2 salt used with password to derive password key
            recovery_hash: SHA-256 hash of the recovery key
            presentation_key_encrypted: Presentation key encrypted with root privileged key
            recovery_key_encrypted: Recovery key encrypted with root privileged key
            password_key_encrypted: Password key encrypted with root privileged key
            profiles_encrypted: Optional encrypted profile data (JSON string encrypted with root privileged key)
            current_outpoint: Outpoint where this token is located on-chain (format: "txid.vout")
        """
        self.password_presentation_primary = password_presentation_primary
        self.password_recovery_primary = password_recovery_primary
        self.presentation_recovery_primary = presentation_recovery_primary
        self.password_primary_privileged = password_primary_privileged
        self.presentation_recovery_privileged = presentation_recovery_privileged
        self.presentation_hash = presentation_hash
        self.password_salt = password_salt
        self.recovery_hash = recovery_hash
        self.presentation_key_encrypted = presentation_key_encrypted
        self.recovery_key_encrypted = recovery_key_encrypted
        self.password_key_encrypted = password_key_encrypted
        self.profiles_encrypted = profiles_encrypted
        self.current_outpoint = current_outpoint


class UMPTokenInteractor(Protocol):
    """Protocol for UMP token interaction.

    Defines interface for finding and publishing UMP tokens on-chain.
    """

    @abstractmethod
    async def find_by_presentation_key_hash(self, hash_value: list[int]) -> UMPToken | None:
        """Find UMP token by presentation key hash.

        Args:
            hash_value: SHA-256 hash of the presentation key

        Returns:
            UMPToken if found, None otherwise
        """
        ...

    @abstractmethod
    async def find_by_recovery_key_hash(self, hash_value: list[int]) -> UMPToken | None:
        """Find UMP token by recovery key hash.

        Args:
            hash_value: SHA-256 hash of the recovery key

        Returns:
            UMPToken if found, None otherwise
        """
        ...

    @abstractmethod
    async def build_and_send(
        self,
        wallet: WalletInterface,
        admin_originator: str,
        token: UMPToken,
        old_token_to_consume: UMPToken | None = None,
    ) -> str:
        """Create or update UMP token on-chain.

        Args:
            wallet: Wallet instance to use for building transaction (must be default profile)
            admin_originator: Domain/FQDN of administrative originator
            token: New UMP token to create
            old_token_to_consume: Optional existing token to consume in same transaction

        Returns:
            Outpoint string of newly created token (format: "txid.vout")

        Raises:
            RuntimeError: If token creation fails
        """
        ...


class OverlayUMPTokenInteractor:
    """Concrete implementation using overlay services and SHIP broadcasting.

    Interacts with overlay services to find UMP tokens and publishes them
    using SHIP broadcasting under the tm_users topic.

    Reference: wallet-toolbox/src/CWIStyleWalletManager.ts OverlayUMPTokenInteractor
    """

    def __init__(
        self,
        resolver: Any | None = None,  # LookupResolver equivalent
        broadcaster: Any | None = None,  # SHIPBroadcaster equivalent
    ) -> None:
        """Initialize OverlayUMPTokenInteractor.

        Args:
            resolver: Lookup resolver for overlay queries (ls_users service)
            broadcaster: SHIP broadcaster for publishing tokens to tm_users topic
        """
        # TODO: Initialize resolver and broadcaster when overlay services are available
        # For now, use placeholder implementations
        self._resolver = resolver
        self._broadcaster = broadcaster

    async def find_by_presentation_key_hash(self, hash_value: list[int]) -> UMPToken | None:
        """Find UMP token by presentation key hash using overlay lookup.

        Args:
            hash_value: SHA-256 hash of the presentation key

        Returns:
            UMPToken if found, None otherwise
        """
        # TODO: Implement overlay lookup when ls_users service is available
        # For now, return None (no tokens found)
        return None

    async def find_by_recovery_key_hash(self, hash_value: list[int]) -> UMPToken | None:
        """Find UMP token by recovery key hash using overlay lookup.

        Args:
            hash_value: SHA-256 hash of the recovery key

        Returns:
            UMPToken if found, None otherwise
        """
        # TODO: Implement overlay lookup when ls_users service is available
        # For now, return None (no tokens found)
        return None

    async def build_and_send(
        self,
        wallet: WalletInterface,
        admin_originator: str,
        token: UMPToken,
        old_token_to_consume: UMPToken | None = None,
    ) -> str:
        """Create or update UMP token on-chain.

        Args:
            wallet: Wallet instance to use for building transaction (must be default profile)
            admin_originator: Domain/FQDN of administrative originator
            token: New UMP token to create
            old_token_to_consume: Optional existing token to consume in same transaction

        Returns:
            Outpoint string of newly created token (format: "txid.vout")

        Raises:
            RuntimeError: If token creation fails
        """
        # TODO: Implement full PushDrop token creation and transaction building
        # For now, raise NotImplementedError
        raise NotImplementedError("UMP token creation not yet implemented")

    async def _parse_lookup_answer(self, answer: Any) -> UMPToken | None:
        """Parse lookup service answer into UMPToken.

        Args:
            answer: Lookup service response

        Returns:
            Parsed UMPToken or None if parsing fails
        """
        # TODO: Implement PushDrop decoding and field extraction
        # Reference: OverlayUMPTokenInteractor.parseLookupAnswer in TypeScript
        return None

    async def _find_by_outpoint(self, outpoint: str) -> dict[str, Any] | None:
        """Find token data by outpoint for unlocking.

        Args:
            outpoint: Outpoint string to search for

        Returns:
            Token data with beef and outputIndex, or None if not found
        """
        # TODO: Implement outpoint lookup
        return None
