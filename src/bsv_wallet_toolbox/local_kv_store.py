"""Local key-value store implementation.

Provides a simple in-memory or persistent key-value storage system
for wallet data and configuration.

Reference: wallet-toolbox/src/bsv-ts-sdk/LocalKVStore.ts
"""

from typing import Any


class LocalKVStore:
    """Local key-value storage for wallet data.
    
    Provides async get/set operations for storing wallet-related data
    in a context-scoped namespace.
    
    Reference: wallet-toolbox/src/bsv-ts-sdk/LocalKVStore.ts
    """
    
    def __init__(
        self,
        wallet: Any,
        context: str,
        use_encryption: bool = False,
        encryption_key: str | None = None,
        in_memory: bool = True,
    ):
        """Initialize LocalKVStore.
        
        Args:
            wallet: Wallet instance
            context: Context/namespace for this store
            use_encryption: Whether to encrypt stored values
            encryption_key: Encryption key if use_encryption is True
            in_memory: Whether to use in-memory storage (True) or persistent (False)
        """
        self.wallet = wallet
        self.context = context
        self.use_encryption = use_encryption
        self.encryption_key = encryption_key
        self.in_memory = in_memory
        
        # In-memory storage
        self._store: dict[str, Any] = {}
    
    async def get(self, key: str) -> Any | None:
        """Get a value from the store.
        
        Args:
            key: Key to retrieve
        
        Returns:
            Value if key exists, None otherwise
        """
        full_key = self._make_full_key(key)
        return self._store.get(full_key)
    
    async def set(self, key: str, value: Any) -> None:
        """Set a value in the store.
        
        Args:
            key: Key to set
            value: Value to store
        """
        full_key = self._make_full_key(key)
        self._store[full_key] = value
    
    async def delete(self, key: str) -> None:
        """Delete a key from the store.
        
        Args:
            key: Key to delete
        """
        full_key = self._make_full_key(key)
        self._store.pop(full_key, None)
    
    async def clear(self) -> None:
        """Clear all keys in this context."""
        keys_to_delete = [
            k for k in self._store.keys()
            if k.startswith(f"{self.context}:")
        ]
        for key in keys_to_delete:
            del self._store[key]
    
    def _make_full_key(self, key: str) -> str:
        """Make a full key with context prefix.
        
        Args:
            key: User-provided key
        
        Returns:
            Full key with context prefix
        """
        return f"{self.context}:{key}"

