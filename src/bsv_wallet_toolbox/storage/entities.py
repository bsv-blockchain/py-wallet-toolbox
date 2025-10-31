"""Storage entities - minimal DTO wrappers for special-case entities.

This module provides user-friendly DTO (Data Transfer Object) classes for entities
that require special logic beyond simple ORM models. Most entities use models.py directly.

Reference: toolbox/ts-wallet-toolbox/src/storage/schema/entities/
"""

from datetime import datetime
from typing import Any


class User:
    """User entity DTO wrapper with special merge logic.
    
    Represents a wallet user with identity key and storage configuration.
    Unlike standard ORM models, this provides default values and merge semantics.
    
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
        """
        # Check if existing entity is newer
        ei_updated_at = ei.get('updated_at')
        if ei_updated_at and self.updated_at and ei_updated_at > self.updated_at:
            # Update with new data
            update_data = {
                'userId': ei.get('userId', self.user_id),
                'identityKey': ei.get('identityKey', self.identity_key),
                'activeStorage': ei.get('activeStorage', self.active_storage),
                'updated_at': ei_updated_at,
            }
            # Call storage to update
            if hasattr(storage, 'update_user'):
                try:
                    storage.update_user(self.user_id, update_data)
                except TypeError:
                    # If trx is expected, try with it
                    try:
                        storage.update_user(self.user_id, update_data, trx)
                    except Exception:
                        pass
            # Update self
            self.user_id = update_data['userId']
            self.identity_key = update_data['identityKey']
            self.active_storage = update_data['activeStorage']
            self.updated_at = update_data['updated_at']
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


class Transaction:
    """Transaction entity DTO wrapper.
    
    Represents a blockchain transaction with metadata.
    
    Reference: toolbox/ts-wallet-toolbox/src/storage/schema/entities/EntityTransaction.ts
    """

    def __init__(self, api_object: dict[str, Any] | None = None) -> None:
        """Initialize Transaction with optional API object.
        
        Args:
            api_object: Dictionary with keys transactionId, userId, txid, rawTx, created_at, updated_at.
                       If None, uses default values. If empty dict, fields are None.
        """
        if api_object is None:
            # Default values for new Transaction
            now = datetime.now()
            self.transaction_id: int = 0
            self.user_id: int = 0
            self.txid: str = ""
            self.raw_tx: bytes | None = None
            self.created_at: datetime = now
            self.updated_at: datetime = now
        elif not api_object:
            # Empty dict provided - use None for all fields
            self.transaction_id: int | None = None
            self.user_id: int | None = None
            self.txid: str | None = None
            self.raw_tx: bytes | None = None
            self.created_at: datetime | None = None
            self.updated_at: datetime | None = None
        else:
            # API object provided - use values or None
            self.transaction_id: int | None = api_object.get('transactionId')
            self.user_id: int | None = api_object.get('userId')
            self.txid: str | None = api_object.get('txid')
            self.raw_tx: bytes | None = api_object.get('rawTx')
            self.created_at: datetime | None = api_object.get('created_at')
            self.updated_at: datetime | None = api_object.get('updated_at')

    @property
    def entity_name(self) -> str:
        """Get entity type name."""
        return 'transaction'

    @property
    def entity_table(self) -> str:
        """Get database table name."""
        return 'transactions'

    def update_api(self) -> None:
        """Update internal state (if needed for synchronization)."""
        pass

    def to_api(self) -> dict[str, Any]:
        """Convert entity to API dict representation."""
        return {
            'transactionId': self.transaction_id,
            'userId': self.user_id,
            'txid': self.txid,
            'rawTx': self.raw_tx,
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
        """
        # Check if existing entity is newer
        ei_updated_at = ei.get('updated_at')
        if ei_updated_at and self.updated_at and ei_updated_at > self.updated_at:
            # Update with new data
            update_data = {
                'transactionId': ei.get('transactionId', self.transaction_id),
                'userId': ei.get('userId', self.user_id),
                'txid': ei.get('txid', self.txid),
                'rawTx': ei.get('rawTx', self.raw_tx),
                'updated_at': ei_updated_at,
            }
            # Call storage to update if method exists
            if hasattr(storage, 'update_transaction'):
                try:
                    storage.update_transaction(self.transaction_id, update_data)
                except TypeError:
                    try:
                        storage.update_transaction(self.transaction_id, update_data, trx)
                    except Exception:
                        pass
            # Update self
            self.transaction_id = update_data['transactionId']
            self.user_id = update_data['userId']
            self.txid = update_data['txid']
            self.raw_tx = update_data['rawTx']
            self.updated_at = update_data['updated_at']
            return True
        return False

    def merge_new(
        self, 
        storage: Any, 
        user_id: int, 
        sync_map: dict[str, Any] | None = None,
        trx: Any = None
    ) -> None:
        """Merge new entity - implementation placeholder.
        
        Args:
            storage: Storage provider instance
            user_id: User ID
            sync_map: Optional sync map
            trx: Optional transaction token
        """
        # Transactions can be created, so this is a valid operation
        # For now, raising to maintain consistency with User pattern
        raise NotImplementedError("Transaction merge_new requires provider context")

    def equals(self, other: Any, sync_map: dict[str, Any] | None = None) -> bool:
        """Check equality with another entity for Transaction.
        
        Transactions are equal if they have the same txid and user_id.
        
        Args:
            other: Another Transaction entity or API dict to compare
            sync_map: Optional sync map (not used for Transaction comparison)
            
        Returns:
            True if txid and user_id match
        """
        if isinstance(other, dict):
            other_txid = other.get('txid')
            other_user_id = other.get('userId')
        elif isinstance(other, Transaction):
            other_txid = other.txid
            other_user_id = other.user_id
        else:
            return False
        
        return self.txid == other_txid and self.user_id == other_user_id


__all__ = ['User', 'Transaction']
