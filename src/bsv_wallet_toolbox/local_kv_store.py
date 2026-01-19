"""Local key-value store implementation.

Provides a simple in-memory or persistent key-value storage system
for wallet data and configuration.

Reference: wallet-toolbox/src/bsv-ts-sdk/LocalKVStore.ts
"""

from __future__ import annotations

from typing import Any


class LocalKVStore:
    """Local key-value storage for wallet data.

    Provides synchronous helpers plus async-compatible wrappers so that the
    Python port can remain predominantly synchronous while preserving the
    TypeScript API shape.
    """

    def __init__(
        self,
        wallet: Any,
        context: str,
        use_encryption: bool = False,
        encryption_key: str | None = None,
        in_memory: bool = True,
    ):
        self.wallet = wallet
        self.context = context
        self.use_encryption = use_encryption
        self.encryption_key = encryption_key
        self.in_memory = in_memory
        self._store: dict[str, Any] = {}

    # ------------------------------------------------------------------ #
    # Synchronous helpers (preferred for Python code paths)
    # ------------------------------------------------------------------ #

    def get_value(self, key: str) -> Any | None:
        return self._store.get(self._make_full_key(key))

    def set_value(self, key: str, value: Any) -> None:
        self._store[self._make_full_key(key)] = value

    def remove_value(self, key: str) -> None:
        self._store.pop(self._make_full_key(key), None)

    def clear_values(self) -> None:
        prefix = f"{self.context}:"
        keys_to_delete = [k for k in self._store if k.startswith(prefix)]
        for key in keys_to_delete:
            del self._store[key]

    # ------------------------------------------------------------------ #
    # Async wrappers (compatibility with existing async-facing tests)
    # ------------------------------------------------------------------ #

    async def get(self, key: str) -> Any | None:
        return self.get_value(key)

    async def set(self, key: str, value: Any) -> None:
        self.set_value(key, value)

    async def delete(self, key: str) -> None:
        self.remove_value(key)

    async def clear(self) -> None:
        self.clear_values()

    # ------------------------------------------------------------------ #

    def _make_full_key(self, key: str) -> str:
        return f"{self.context}:{key}"
