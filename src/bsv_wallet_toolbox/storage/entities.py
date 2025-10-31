"""Storage entities - User DTO wrapper.

This module provides the User DTO (Data Transfer Object) class that wraps
the SQLAlchemy ORM model to support TypeScript EntityUser functionality,
including custom __init__ with default values and entity methods
(merge_existing, merge_new, equals).

Reference: toolbox/ts-wallet-toolbox/src/storage/schema/entities/EntityUser.ts
"""

from datetime import datetime
from typing import Any


class User:
    """User entity DTO wrapper with special merge logic.
    
    Represents a wallet user with identity key and storage configuration.
    Unlike the ORM model, this provides default values and merge semantics.
    
    Reference: toolbox/ts-wallet-toolbox/src/storage/schema/entities/EntityUser.ts
    """

    def __init__(self, api_object: dict[str, Any] | None = None) -> None:
        """Initialize User with optional API object.
        
        Args:
            api_object: Dictionary with keys userId, identityKey, activeStorage, created_at, updated_at.
                       If None, uses default values. If empty dict, fields are None.
        """
        if api_object is None:
            # Default values for new User
            now = datetime.now()
            self.user_id: int = 0
            self.identity_key: str = ""
            self.active_storage: str = ""
            self.created_at: datetime = now
            self.updated_at: datetime = now
        elif not api_object:
            # Empty dict provided - use None for all fields
            self.user_id: int | None = None
            self.identity_key: str | None = None
            self.active_storage: str | None = None
            self.created_at: datetime | None = None
            self.updated_at: datetime | None = None
        else:
            # API object provided - use values or None
            self.user_id: int | None = api_object.get('userId')
            self.identity_key: str | None = api_object.get('identityKey')
            self.active_storage: str | None = api_object.get('activeStorage')
            self.created_at: datetime | None = api_object.get('created_at')
            self.updated_at: datetime | None = api_object.get('updated_at')

    @property
    def entity_name(self) -> str:
        """Get entity type name."""
        return 'user'

    @property
    def entity_table(self) -> str:
        """Get database table name."""
        return 'users'

    def update_api(self) -> None:
        """Update internal state (if needed for synchronization)."""
        pass

    def to_api(self) -> dict[str, Any]:
        """Convert entity to API dict representation."""
        return {
            'userId': self.user_id,
            'identityKey': self.identity_key,
            'activeStorage': self.active_storage,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
        }

    def merge_existing(
        self, 
        storage: Any, 
        user_id: int | None, 
        ei: dict[str, Any], 
        sync_map: dict[str, Any] | None = None,
        trx: Any = None
    ) -> bool:
        """Merge with existing entity from database.
        
        Args:
            storage: Storage provider instance
            user_id: User ID
            ei: Existing entity data
            sync_map: Optional sync map
            trx: Optional transaction token
            
        Returns:
            True if entity was updated, False otherwise
        
        Reference:
            toolbox/ts-wallet-toolbox/src/storage/schema/entities/EntityUser.ts:94-111
        """
        ei_updated_at = ei.get('updated_at')
        if ei_updated_at and self.updated_at and ei_updated_at > self.updated_at:
            self.active_storage = ei.get('activeStorage', self.active_storage)
            self.updated_at = ei_updated_at
            if hasattr(storage, 'update_user'):
                try:
                    storage.update_user(self.user_id, self.to_api(), trx)
                except TypeError:
                    try:
                        storage.update_user(self.user_id, self.to_api())
                    except Exception:
                        pass
            return True
        return False

    def merge_new(
        self, 
        storage: Any, 
        user_id: int, 
        sync_map: dict[str, Any] | None = None,
        trx: Any = None
    ) -> None:
        """Merge new entity - always throws for User.
        
        Args:
            storage: Storage provider instance
            user_id: User ID
            sync_map: Optional sync map
            trx: Optional transaction token
            
        Raises:
            Exception: Always, as sync chunk merge must never create a new user
        
        Reference:
            toolbox/ts-wallet-toolbox/src/storage/schema/entities/EntityUser.ts:91-93
        """
        raise Exception("a sync chunk merge must never create a new user")

    def equals(self, other: Any, sync_map: dict[str, Any] | None = None) -> bool:
        """Check equality with another entity for User.
        
        User entities are equal if they have the same identityKey and activeStorage,
        regardless of userId or timestamps.
        
        Args:
            other: Another User entity or API dict to compare
            sync_map: Optional sync map (not used for User comparison)
            
        Returns:
            True if identityKey and activeStorage match
        
        Reference:
            toolbox/ts-wallet-toolbox/src/storage/schema/entities/EntityBase.ts:47
        """
        if isinstance(other, dict):
            other_id_key = other.get('identityKey')
            other_active_storage = other.get('activeStorage')
        elif isinstance(other, User):
            other_id_key = other.identity_key
            other_active_storage = other.active_storage
        else:
            return False
        
        return (self.identity_key == other_id_key and 
                self.active_storage == other_active_storage)


__all__ = ['User']
